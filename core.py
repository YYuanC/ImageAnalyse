import os
import re
import math  # 新增：用于判断 nan
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from PIL import Image
from PIL.ExifTags import TAGS
import numpy as np
from tqdm import tqdm

def configure_matplotlib_fonts():
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Noto Sans CJK SC']
    plt.rcParams['axes.unicode_minus'] = False

def get_exif_data(image_path):
    """提取图片的 EXIF 信息"""
    try:
        image = Image.open(image_path)
        exif_data = image._getexif()
        if not exif_data:
            return {}

        return {TAGS.get(tag, tag): value for tag, value in exif_data.items()}
    except Exception as e:
        print(f"Error in get_exif_data('{image_path}'): {e}")
        return {}

def process_focal_length(focal_length):
    """处理焦段数据"""
    try:
        # 判断数值是否为 nan
        if isinstance(focal_length, (float, int)) and math.isnan(focal_length):
            return None
        if isinstance(focal_length, tuple):
            # 检查各项是否为 nan
            if any(isinstance(v, (float, int)) and math.isnan(v) for v in focal_length):
                return None
            if focal_length[1] == 0:
                return None  # 防止除零错误
            return round(float(focal_length[0]) / float(focal_length[1]))
        return round(float(focal_length))
    except Exception as e:
        print(f"Error in process_focal_length({focal_length}): {e}")
        return None

def process_iso_value(iso_value):
    """处理 ISO 数据"""
    try:
        if isinstance(iso_value, (tuple, list)):
            iso_value = iso_value[0]
        elif isinstance(iso_value, str):
            iso_value = int(iso_value)
        
        iso_value = int(iso_value)
        return iso_value if 50 <= iso_value <= 512000 else None
    except Exception as e:
        print(f"Error in process_iso_value({iso_value}): {e}")
        return None

def process_aperture(aperture):
    """处理光圈数据"""
    try:
        if isinstance(aperture, (float, int)) and math.isnan(aperture):
            return None
        if isinstance(aperture, tuple):
            if any(isinstance(v, (float, int)) and math.isnan(v) for v in aperture):
                return None
            if aperture[1] == 0:
                return None  # 防止除零错误
            return round(float(aperture[0]) / float(aperture[1]), 1)
        return round(float(aperture), 1)
    except Exception as e:
        print(f"Error in process_aperture({aperture}): {e}")
        return None

def process_shutter_speed(shutter_speed):
    """处理快门速度数据"""
    try:
        if isinstance(shutter_speed, (float, int)) and math.isnan(shutter_speed):
            return None
        if isinstance(shutter_speed, tuple):
            if any(isinstance(v, (float, int)) and math.isnan(v) for v in shutter_speed):
                return None
            if shutter_speed[1] == 0:
                return None  # 防止除零错误
            speed = float(shutter_speed[0]) / float(shutter_speed[1])
        else:
            speed = float(shutter_speed)
        return round(speed, 4)
    except Exception as e:
        print(f"Error in process_shutter_speed({shutter_speed}): {e}")
        return None

def try_parse_date(date_string):
    """尝试使用多种格式解析日期字符串"""
    date_formats = [
        '%Y:%m:%d %H:%M:%S',  # 标准 EXIF 格式
        '%Y-%m-%d %H:%M:%S',  # 带连字符的格式
        '%Y%m%d_%H%M%S',      # 紧凑格式
        '%Y_%m_%d %H:%M:%S',  # 带下划线的格式
        '%Y%m%d%H%M%S'        # 纯数字格式
    ]
    
    if not date_string or not isinstance(date_string, str):
        return None
        
    # 清理日期字符串
    date_string = date_string.replace('\x00', '').strip()
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
    return None

def process_folder(folder_path):
    """处理文件夹中的图片并统计数据"""
    focal_lengths = []
    dates = {}
    hours = {}
    iso = {}
    apertures = {}
    shutter_speeds = {}
    hourly_settings = {i: {
        'apertures': [], 
        'shutter_speeds': [],
        'isos': []  # 添加ISO数组
    } for i in range(24)}

    # 获取所有图片文件
    image_files = []
    for root, _, files in os.walk(folder_path):
        image_files.extend(
            os.path.join(root, file)
            for file in files
            if re.match(r'.*\.(jpg|jpeg|png|bmp|tiff)$', file, re.IGNORECASE)
        )

    # 处理图片文件
    for image_path in tqdm(image_files, desc="处理图片"):
        exif_data = get_exif_data(image_path)
        if not exif_data:
            continue

        # 处理焦段数据
        if 'FocalLength' in exif_data:
            focal_length = process_focal_length(exif_data['FocalLength'])
            if focal_length:
                focal_lengths.append(focal_length)

        # 处理拍摄日期
        if 'DateTimeOriginal' in exif_data:
            raw_date = exif_data['DateTimeOriginal']
            dt = try_parse_date(raw_date)
            if dt:
                dates[dt.date()] = dates.get(dt.date(), 0) + 1
                hours[dt.hour] = hours.get(dt.hour, 0) + 1

        # 处理 ISO 数据
        if 'ISOSpeedRatings' in exif_data:
            iso_value = process_iso_value(exif_data['ISOSpeedRatings'])
            if iso_value:
                iso[iso_value] = iso.get(iso_value, 0) + 1
                if 'DateTimeOriginal' in exif_data:
                    try:
                        dt = datetime.strptime(exif_data['DateTimeOriginal'], '%Y:%m:%d %H:%M:%S')
                        hourly_settings[dt.hour]['isos'].append(iso_value)
                    except ValueError as e:
                        print(f"Error parsing DateTimeOriginal for ISO in '{image_path}': {e}")
                        pass

        # 处理光圈数据
        if 'FNumber' in exif_data:
            aperture = process_aperture(exif_data['FNumber'])
            if aperture:
                apertures[aperture] = apertures.get(aperture, 0) + 1
                if 'DateTimeOriginal' in exif_data:
                    try:
                        dt = datetime.strptime(exif_data['DateTimeOriginal'], '%Y:%m:%d %H:%M:%S')
                        hourly_settings[dt.hour]['apertures'].append(aperture)
                    except ValueError as e:
                        print(f"Error parsing DateTimeOriginal for FNumber in '{image_path}': {e}")
                        pass

        # 处理快门速度数据
        if 'ExposureTime' in exif_data:
            shutter_speed = process_shutter_speed(exif_data['ExposureTime'])
            if shutter_speed:
                shutter_speeds[shutter_speed] = shutter_speeds.get(shutter_speed, 0) + 1
                if 'DateTimeOriginal' in exif_data:
                    try:
                        dt = datetime.strptime(exif_data['DateTimeOriginal'], '%Y:%m:%d %H:%M:%S')
                        hourly_settings[dt.hour]['shutter_speeds'].append(shutter_speed)
                    except ValueError as e:
                        print(f"Error parsing DateTimeOriginal for ExposureTime in '{image_path}': {e}")
                        pass

    return focal_lengths, dates, hours, iso, apertures, shutter_speeds, hourly_settings

def generate_chart(data, title, x_label, y_label, output_file):
    """生成统计图表"""
    plt.figure(figsize=(12, 7))
    
    if isinstance(data, dict):
        if not data:
            plt.text(0.5, 0.5, '没有数据', 
                    ha='center', va='center',
                    transform=plt.gca().transAxes,
                    fontsize=14)
        else:
            sorted_data = sorted(data.items())
            keys, values = zip(*sorted_data)
            
            plt.bar(range(len(keys)), values, color='skyblue', alpha=0.7)
            
            # 设置x轴标签
            if keys and isinstance(keys[0], type(datetime.now().date())):
                plt.xticks(range(len(keys)), [k.strftime('%Y-%m-%d') for k in keys], rotation=45)
            else:
                # 特殊处理快门速度的显示
                if title.startswith('快门速度'):
                    formatted_labels = []
                    for k in keys:
                        if k < 1:
                            formatted_labels.append(f'1/{int(1/k)}')
                        else:
                            formatted_labels.append(f'{k:.1f}')
                    
                    # 设置适当的标签间隔
                    if len(keys) > 20:
                        step = len(keys) // 10  # 只显示约10个标签
                        plt.xticks(range(0, len(keys), step), 
                                 [formatted_labels[i] for i in range(0, len(keys), step)],
                                 rotation=45)
                    else:
                        plt.xticks(range(len(keys)), formatted_labels, rotation=45)
                else:
                    plt.xticks(range(len(keys)), keys, rotation=45 if title.startswith('ISO') else 0)
                
                if title.startswith('ISO') or title.startswith('快门速度'):
                    plt.yscale('log')

            # 添加数值标签
            max_value = max(values)
            for i, v in enumerate(values):
                if v > max_value * 0.05:
                    plt.text(i, v, str(v), ha='center', va='bottom', fontsize=8)
    else:
        if not data:
            plt.text(0.5, 0.5, '没有数据', 
                    ha='center', va='center',
                    transform=plt.gca().transAxes,
                    fontsize=14)
        else:
            # 处理焦段数据
            counts, bins, patches = plt.hist(data, bins=20, color='skyblue', alpha=0.7)
            
            # 计算每个区间的中点
            bin_centers = [(bins[i] + bins[i+1])/2 for i in range(len(bins)-1)]
            
            # 计算累积分布
            total_photos = sum(counts)
            half_photos = total_photos / 2
            cumsum = 0
            
            # 找到照片数量平分点
            for i, (count, left_edge, right_edge) in enumerate(zip(counts, bins[:-1], bins[1:])):
                cumsum += count
                if cumsum >= half_photos:
                    # 使用线性插值找到更精确的分割点
                    prev_sum = cumsum - count
                    ratio = (half_photos - prev_sum) / count
                    split_point = left_edge + ratio * (right_edge - left_edge)
                    break
            
            # 添加分割线
            plt.axvline(x=split_point, color='red', linestyle='--', alpha=0.7)
            plt.text(split_point, plt.ylim()[1], 
                    f'数量中点: {split_point:.1f}mm',
                    rotation=0,
                    ha='right',
                    va='bottom',
                    fontsize=10)
            
            # 添加数值标签
            max_count = max(counts)
            for i in range(len(counts)):
                if counts[i] > max_count * 0.05:
                    plt.text((bins[i] + bins[i+1])/2, counts[i], 
                            f'{int(counts[i])}', 
                            ha='center', va='bottom', fontsize=8)
            
            plt.xticks(bins, [f'{int(x)}' for x in bins], rotation=45)
    
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.tight_layout()
    
    os.makedirs('output', exist_ok=True)
    output_path = os.path.join('output', output_file)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def generate_hourly_settings_chart(hourly_settings, output_file):
    """生成每小时光圈和快门速度的折线图"""
    plt.figure(figsize=(15, 8))
    
    # 创建三个y轴
    fig, ax1 = plt.subplots(figsize=(15, 8))
    ax2 = ax1.twinx()
    ax3 = ax1.twinx()  # 创建第三个y轴用于ISO
    
    # 调整第三个y轴的位置
    ax3.spines['right'].set_position(('outward', 60))

    hours = range(24)
    avg_apertures = []
    avg_shutter_speeds = []
    avg_isos = []

    for hour in hours:
        apertures = hourly_settings[hour]['apertures']
        shutter_speeds = hourly_settings[hour]['shutter_speeds']
        isos = hourly_settings[hour]['isos']
        
        avg_aperture = np.mean(apertures) if apertures else None
        avg_shutter = np.mean(shutter_speeds) if shutter_speeds else None
        avg_iso = np.mean(isos) if isos else None
        
        avg_apertures.append(avg_aperture)
        avg_shutter_speeds.append(avg_shutter)
        avg_isos.append(avg_iso)

    # 设置更柔和的颜色
    aperture_color = '#3498db'  # 柔和的蓝色
    shutter_color = '#e74c3c'   # 柔和的红色
    iso_color = '#2ecc71'       # 柔和的绿色

    # 绘制光圈数据
    line1 = ax1.plot(hours, avg_apertures, color=aperture_color, label='平均光圈', 
                     marker='o', linewidth=2, markersize=8, alpha=0.8)
    ax1.set_xlabel('小时')
    ax1.set_ylabel('光圈值 (f)', color=aperture_color)
    ax1.tick_params(axis='y', labelcolor=aperture_color)
    
    # 添加光圈数值标签
    for i, aperture in enumerate(avg_apertures):
        if aperture is not None:
            ax1.annotate(f'f/{aperture:.1f}', 
                        xy=(i, aperture),
                        xytext=(0, 10),
                        textcoords='offset points',
                        ha='center',
                        va='bottom',
                        color=aperture_color,
                        fontsize=8)

    # 绘制快门速度数据
    line2 = ax2.plot(hours, avg_shutter_speeds, color=shutter_color, label='平均快门速度', 
                     marker='o', linewidth=2, markersize=8, alpha=0.8)
    ax2.set_ylabel('快门速度 (秒)', color=shutter_color)
    ax2.tick_params(axis='y', labelcolor=shutter_color)
    ax2.set_yscale('log', base=2)  # 使用以2为底的对数坐标
    
    # 设置快门速度y轴的刻度，使用更均匀的间隔
    shutter_ticks = [1/8000, 1/4000, 1/2000, 1/1000, 1/500, 1/250, 1/125, 1/60, 1/30, 1/15, 1/8, 1/4, 1/2, 1, 2, 4, 8]
    ax2.set_yticks(shutter_ticks)
    ax2.set_yticklabels([f'1/{int(1/x)}' if x < 1 else str(int(x)) for x in shutter_ticks])
    ax2.set_yscale('log', base=2)  # 使用以2为底的对数坐标

    # 添加快门速度数值标签
    for i, shutter_speed in enumerate(avg_shutter_speeds):
        if shutter_speed is not None:
            label = f'1/{int(1/shutter_speed)}' if shutter_speed < 1 else f'{shutter_speed:.1f}'
            ax2.annotate(label,
                        xy=(i, shutter_speed),
                        xytext=(0, 10),
                        textcoords='offset points',
                        ha='center',
                        va='bottom',
                        color=shutter_color,
                        fontsize=8)

    # 动态设置光圈值的合适范围
    if avg_apertures:
        ax1.set_ylim(min(filter(None, avg_apertures)) * 0.9, max(filter(None, avg_apertures)) * 1.1)

    # 绘制ISO数据
    line3 = ax3.plot(hours, avg_isos, color=iso_color, label='平均ISO', 
                     marker='o', linewidth=2, markersize=8, alpha=0.8)
    ax3.set_ylabel('ISO', color=iso_color)
    ax3.tick_params(axis='y', labelcolor=iso_color)

    # 动态设置ISO的y轴范围
    if avg_isos:
        ax3.set_ylim(min(filter(None, avg_isos)) * 0.8, max(filter(None, avg_isos)) * 1.1)

    # 设置ISO的y轴刻度为100的整数，且只需要五个刻度
    if avg_isos:
        min_iso = int(np.floor(min(filter(None, avg_isos)) / 100) * 100)
        max_iso = int(np.ceil(max(filter(None, avg_isos)) / 100) * 100)
        ax3.set_yticks(np.linspace(min_iso, max_iso, num=5).astype(int))
    
    # 添加ISO数值标签
    for i, iso in enumerate(avg_isos):
        if iso is not None:
            ax3.annotate(f'ISO {int(iso)}',
                        xy=(i, iso),
                        xytext=(0, 10),
                        textcoords='offset points',
                        ha='center',
                        va='bottom',
                        color=iso_color,
                        fontsize=8)

    # 设置网格线
    ax1.grid(True, alpha=0.2)
    
    # 合并图例
    lines = line1 + line2 + line3
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper right')

    plt.title('每小时平均拍摄参数', pad=20)
    plt.tight_layout()
    
    os.makedirs('output', exist_ok=True)
    output_path = os.path.join('output', output_file)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def analyze_folder(folder_path):
    """分析文件夹并返回所有统计数据"""
    configure_matplotlib_fonts()
    
    if not os.path.exists(folder_path):
        return None, "路径不存在，请检查路径是否正确。"
    
    # 创建输出目录
    output_dir = os.path.join(os.getcwd(), "output")  # 修改：将输出目录设置为程序所在目录
    os.makedirs(output_dir, exist_ok=True)
    
    results = process_folder(folder_path)
    focal_lengths, dates, hours, iso, apertures, shutter_speeds, hourly_settings = results
    
    # 生成统计图表
    charts = [
        (focal_lengths, '照片焦段统计', '焦段 (mm)', '照片数量', 'focal_length_chart.png'),
        (dates, '每日照片数量统计', '日期', '照片数量', 'daily_count_chart.png'),
        (hours, '每小时照片数量统计', '小时', '照片数量', 'hourly_count_chart.png'),
        (iso, 'ISO 统计', 'ISO', '照片数量', 'iso_chart.png'),
        (apertures, '光圈统计', '光圈值 (f)', '照片数量', 'aperture_chart.png'),
        (shutter_speeds, '快门速度统计', '快门速度 (秒)', '照片数量', 'shutter_speed_chart.png')
    ]
    
    chart_paths = {}
    for chart_data in tqdm(charts, desc="生成图表"):
        data, title, x_label, y_label, filename = chart_data
        output_path = os.path.join(output_dir, filename)
        generate_chart(data, title, x_label, y_label, filename)
        chart_paths[filename] = output_path
    
    # 生成每小时设置统计图表
    hourly_settings_path = os.path.join(output_dir, 'hourly_settings_chart.png')
    generate_hourly_settings_chart(hourly_settings, 'hourly_settings_chart.png')
    chart_paths['hourly_settings_chart.png'] = hourly_settings_path

    # 计算额外的统计数据
    total_photos = sum(dates.values())  # 修改：计算所有日期的照片总和
    
    # 计算焦距中位数
    valid_focal_lengths = [f for f in focal_lengths if f]
    focal_length_median = 0
    if valid_focal_lengths:
        valid_focal_lengths.sort()
        mid = len(valid_focal_lengths) // 2
        if len(valid_focal_lengths) % 2 == 0:
            focal_length_median = (valid_focal_lengths[mid-1] + valid_focal_lengths[mid]) / 2
        else:
            focal_length_median = valid_focal_lengths[mid]
    
    # 计算日均照片数
    num_days = len(dates)  # 获取拍摄天数
    daily_average = total_photos / num_days if num_days > 0 else 0  # 修改：使用总照片数除以天数

    return (
        focal_lengths, dates, hours, iso, apertures, shutter_speeds, hourly_settings,
        total_photos,
        focal_length_median,
        daily_average
    ), chart_paths

def main():
    try:
        folder_path = input("请输入图片文件夹路径: ")
        results, chart_paths = analyze_folder(folder_path)
        if results:
            print("统计图表已生成在 output 文件夹中！")
    except Exception as e:
        print(f"程序运行过程中发生异常: {e}")

if __name__ == "__main__":
    main()