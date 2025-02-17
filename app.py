import streamlit as st
import os
from core import analyze_folder
import base64
from PIL import Image

def load_image(image_path):
    """加载图片并转换为 base64"""
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception as e:
        st.error(f"无法加载图片: {e}")
        return None

def main():
    st.set_page_config(
        page_title="照片参数分析工具",
        page_icon="📸",
        layout="wide"
    )

    st.title("照片参数分析工具")
    st.write("这个工具可以分析你的照片集合，生成各种参数统计图表。")

    # 添加output文件夹路径
    output_dir = os.path.join(os.getcwd(), 'output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 文件夹选择
    folder_path = st.text_input("请输入照片文件夹路径：")
    analyze_button = st.button("开始分析")

    if analyze_button and folder_path:
        if not os.path.exists(folder_path):
            st.error("文件夹路径不存在，请检查输入是否正确！")
        else:
            with st.spinner("正在分析照片，请稍候..."):
                try:
                    analysis_data, _ = analyze_folder(folder_path)
                    if analysis_data:
                        (focal_lengths, dates, hours, iso, apertures, 
                         shutter_speeds, hourly_settings,
                         total_photos, focal_length_median, daily_average) = analysis_data
                        
                        # 显示基本统计信息
                        st.subheader("📊 基本统计信息")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("总照片数", total_photos)
                        with col2:
                            if focal_lengths:
                                st.metric("焦距中位数", f"{focal_length_median:.1f}mm")
                        with col3:
                            st.metric("日均照片数", f"{daily_average:.1f}")
                        
                        # 更新图表显示逻辑
                        chart_titles = {
                            'focal_length_chart.png': "焦段分布",
                            'daily_count_chart.png': "每日拍摄数量",
                            'hourly_count_chart.png': "每小时拍摄数量",
                            'iso_chart.png': "ISO分布",
                            'aperture_chart.png': "光圈分布",
                            'shutter_speed_chart.png': "快门速度分布",
                            'hourly_settings_chart.png': "每小时参数变化"
                        }
                        
                        for filename, title in chart_titles.items():
                            chart_path = os.path.join(output_dir, filename)
                            if os.path.exists(chart_path):
                                st.subheader(title)
                                img = Image.open(chart_path)
                                st.image(img, use_column_width=True)
                            else:
                                st.warning(f"未能找到{title}图表")
                                
                except Exception as e:
                    st.error(f"分析过程中发生错误: {str(e)}")

    st.sidebar.title("关于")
    st.sidebar.info(
        "这是一个照片参数分析工具，可以帮助你了解自己的拍摄习惯。"
        "\n\n它会分析照片的EXIF信息，生成各种统计图表。"
    )

if __name__ == "__main__":
    main()
