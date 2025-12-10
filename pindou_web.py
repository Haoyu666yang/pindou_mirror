#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
拼豆图纸镜像工具 - Web版本 (支持手机浏览器)
运行方法: streamlit run pindou_web.py
"""

import streamlit as st
import numpy as np
import cv2
from PIL import Image
from io import BytesIO
from collections import Counter

st.set_page_config(
    page_title="拼豆图纸镜像工具",
    page_icon="🎨",
    layout="wide"
)

# 自定义CSS
st.markdown("""
<style>
    .stApp {
        background-color: #1e1e2e;
    }
    .main-title {
        text-align: center;
        color: #cdd6f4;
        font-size: 2rem;
        margin-bottom: 1rem;
    }
    .stButton > button {
        width: 100%;
        background-color: #89b4fa;
        color: #1e1e2e;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #b4befe;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">🎨 拼豆图纸镜像工具</h1>', unsafe_allow_html=True)


def remove_watermark_from_cell(cell_array):
    """去除水印"""
    h, w = cell_array.shape[:2]
    result = cell_array.copy()
    
    pixels = cell_array.reshape(-1, 3)
    
    bg_candidates = []
    for pixel in pixels:
        r, g, b = int(pixel[0]), int(pixel[1]), int(pixel[2])
        brightness = (r + g + b) / 3
        
        if brightness < 60:
            continue
        
        diff = max(abs(r - g), abs(g - b), abs(r - b))
        if diff < 15 and 100 < brightness < 200:
            continue
        
        bg_candidates.append((r, g, b))
    
    if not bg_candidates:
        return result
    
    color_counts = Counter([(c[0]//8*8, c[1]//8*8, c[2]//8*8) for c in bg_candidates])
    if not color_counts:
        return result
    
    dominant_quantized = color_counts.most_common(1)[0][0]
    
    bg_color = None
    best_dist = float('inf')
    for c in bg_candidates:
        dist = sum((a - b) ** 2 for a, b in zip(c, dominant_quantized))
        if dist < best_dist:
            best_dist = dist
            bg_color = c
    
    if bg_color is None:
        bg_color = (255, 255, 255)
    
    for y in range(h):
        for x in range(w):
            r, g, b = int(result[y, x, 0]), int(result[y, x, 1]), int(result[y, x, 2])
            brightness = (r + g + b) / 3
            diff = max(abs(r - g), abs(g - b), abs(r - b))
            
            if diff < 20 and 90 < brightness < 210:
                result[y, x] = bg_color
    
    return result


def process_image(image, x1, y1, x2, y2, cols, rows, remove_watermark):
    """处理图片"""
    img_array = np.array(image)
    new_img_array = img_array.copy()
    
    grid_width = x2 - x1
    grid_height = y2 - y1
    cell_width = grid_width / cols
    cell_height = grid_height / rows
    
    for row in range(rows):
        for col in range(cols):
            src_left = int(x1 + col * cell_width)
            src_right = int(x1 + (col + 1) * cell_width)
            src_top = int(y1 + row * cell_height)
            src_bottom = int(y1 + (row + 1) * cell_height)
            
            dst_col = cols - 1 - col
            dst_left = int(x1 + dst_col * cell_width)
            dst_right = int(x1 + (dst_col + 1) * cell_width)
            dst_top = src_top
            dst_bottom = src_bottom
            
            cell = img_array[src_top:src_bottom, src_left:src_right].copy()
            
            if cell.size == 0:
                continue
            
            if remove_watermark:
                cell = remove_watermark_from_cell(cell)
            
            target_h = dst_bottom - dst_top
            target_w = dst_right - dst_left
            
            if cell.shape[0] != target_h or cell.shape[1] != target_w:
                cell = cv2.resize(cell, (target_w, target_h), interpolation=cv2.INTER_NEAREST)
            
            new_img_array[dst_top:dst_bottom, dst_left:dst_right] = cell
    
    return Image.fromarray(new_img_array)


# 侧边栏设置
with st.sidebar:
    st.header("⚙️ 设置")
    
    # 上传图片
    uploaded_file = st.file_uploader("📁 上传拼豆图纸", type=['png', 'jpg', 'jpeg', 'bmp', 'webp'])
    
    st.divider()
    
    # 格子数量
    st.subheader("📐 格子数量")
    
    preset = st.selectbox("常用预设", ["自定义", "20×20", "29×29", "50×50", "52×47", "100×100"])
    
    if preset == "20×20":
        default_cols, default_rows = 20, 20
    elif preset == "29×29":
        default_cols, default_rows = 29, 29
    elif preset == "50×50":
        default_cols, default_rows = 50, 50
    elif preset == "52×47":
        default_cols, default_rows = 52, 47
    elif preset == "100×100":
        default_cols, default_rows = 100, 100
    else:
        default_cols, default_rows = 52, 47
    
    col1, col2 = st.columns(2)
    with col1:
        cols = st.number_input("列数", min_value=1, max_value=200, value=default_cols)
    with col2:
        rows = st.number_input("行数", min_value=1, max_value=200, value=default_rows)
    
    st.divider()
    
    # 格子区域设置
    st.subheader("📍 格子区域 (像素)")
    st.caption("设置格子区域的边界，不包括坐标轴")
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file).convert('RGB')
        width, height = image.size
        
        default_x1 = int(width * 0.025)
        default_y1 = int(height * 0.035)
        default_x2 = int(width * 0.975)
        default_y2 = int(height * 0.83)
    else:
        default_x1, default_y1, default_x2, default_y2 = 0, 0, 100, 100
        width, height = 100, 100
    
    col1, col2 = st.columns(2)
    with col1:
        x1 = st.number_input("左边界 X1", min_value=0, max_value=width, value=default_x1)
        y1 = st.number_input("上边界 Y1", min_value=0, max_value=height, value=default_y1)
    with col2:
        x2 = st.number_input("右边界 X2", min_value=0, max_value=width, value=default_x2)
        y2 = st.number_input("下边界 Y2", min_value=0, max_value=height, value=default_y2)
    
    st.divider()
    
    # 去水印选项
    remove_watermark = st.checkbox("🧹 去除水印", value=True)


# 主内容区
if uploaded_file is not None:
    image = Image.open(uploaded_file).convert('RGB')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📷 原图")
        st.image(image, use_container_width=True)
    
    with col2:
        st.subheader("🔄 镜像后")
        
        if st.button("🚀 开始镜像处理", type="primary", use_container_width=True):
            if x1 >= x2 or y1 >= y2:
                st.error("❌ 格子区域设置错误！请确保左边界<右边界，上边界<下边界")
            else:
                with st.spinner("处理中..."):
                    result = process_image(image, x1, y1, x2, y2, cols, rows, remove_watermark)
                    st.session_state['result'] = result
                st.success(f"✅ 处理完成！{cols}列 × {rows}行")
        
        if 'result' in st.session_state:
            st.image(st.session_state['result'], use_container_width=True)
            
            # 下载按钮
            buf = BytesIO()
            st.session_state['result'].save(buf, format='PNG')
            buf.seek(0)
            
            st.download_button(
                label="💾 下载镜像图片",
                data=buf,
                file_name="镜像图纸.png",
                mime="image/png",
                use_container_width=True
            )
else:
    st.info("👆 请在左侧上传拼豆图纸图片")
    
    st.markdown("""
    ### 📖 使用说明
    
    1. **上传图片** - 在左侧上传你的拼豆图纸
    2. **设置格子数** - 选择预设或手动输入行列数
    3. **调整区域** - 设置格子区域的边界（不包括坐标轴和颜色条）
    4. **镜像处理** - 点击按钮进行镜像
    5. **下载结果** - 保存处理后的图片
    
    ### ✨ 功能特点
    
    - 📱 支持手机浏览器访问
    - 🔄 格子位置镜像，文字保持正常
    - 🧹 可选去除水印
    - 📐 支持各种尺寸的图纸
    """)

