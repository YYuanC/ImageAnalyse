from core import analyze_folder

def main():
    folder_path = input("请输入照片文件夹路径: ").strip()
    
    print(f"\n正在分析文件夹: {folder_path}")
    try:
        analysis_data, chart_paths = analyze_folder(folder_path)
        if not analysis_data:
            print(f"错误: {chart_paths}")
            return

        if analysis_data:
            (focal_lengths, dates, hours, iso, apertures, 
             shutter_speeds, hourly_settings,
             total_photos, focal_length_median, daily_average) = analysis_data
            
            print(f"\n总照片数: {total_photos}")
            print(f"日均照片数: {daily_average:.1f}")
            print("图表已保存到 output 文件夹中。")

    except Exception as e:
        print(f"分析过程中发生错误: {str(e)}")

if __name__ == "__main__":
    main()
