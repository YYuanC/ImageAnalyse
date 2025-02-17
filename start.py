#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import subprocess
import time

def countdown(seconds):
    while seconds > 0:
        print(f"\r默认{seconds}秒后启动命令行界面...(按回车键立即选择)", end='', flush=True)
        if input_with_timeout():
            return True
        seconds -= 1
    print("\r")
    return False

def input_with_timeout():
    import msvcrt
    if msvcrt.kbhit():
        msvcrt.getch()  # 清除缓冲区
        return True
    time.sleep(1)
    return False

def main():
    print("请选择启动模式:")
    print("1. 命令行界面", end='')
    if not countdown(5):
        choice = "1"
    else:
        print("\n2. 网页界面")
        choice = input("\n请输入选项: ").strip()
    
    if choice == "1":
        subprocess.run(["python", "main.py"])
    elif choice == "2":
        subprocess.run(["streamlit", "run", "app.py"])
    else:
        print("无效的选项，请重新运行并选择。")

if __name__ == "__main__":
    main()
