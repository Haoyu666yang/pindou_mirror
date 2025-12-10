#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打包脚本 - 将拼豆镜像工具打包成 Windows .exe
运行方法: python build_exe.py
"""

import subprocess
import sys
import os

def main():
    print("=" * 50)
    print("拼豆图纸镜像工具 - 打包脚本")
    print("=" * 50)
    
    # 检查并安装 PyInstaller
    try:
        import PyInstaller
        print("✓ PyInstaller 已安装")
    except ImportError:
        print("正在安装 PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✓ PyInstaller 安装完成")
    
    # 获取脚本目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(script_dir, "pindou_mirror.py")
    
    if not os.path.exists(main_script):
        print(f"❌ 找不到主程序: {main_script}")
        sys.exit(1)
    
    # PyInstaller 打包命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",              # 打包成单个exe文件
        "--windowed",             # 不显示控制台窗口
        "--name", "拼豆镜像工具",   # exe文件名
        "--clean",                # 清理临时文件
        "--noconfirm",            # 不询问确认
        main_script
    ]
    
    print(f"\n正在打包...")
    print(f"命令: {' '.join(cmd)}\n")
    
    try:
        subprocess.check_call(cmd, cwd=script_dir)
        
        exe_path = os.path.join(script_dir, "dist", "拼豆镜像工具.exe")
        
        print("\n" + "=" * 50)
        print("✅ 打包成功！")
        print(f"📁 exe文件位置: {exe_path}")
        print("=" * 50)
        print("\n提示: 将 dist 文件夹中的 exe 文件复制到其他电脑即可使用")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 打包失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
