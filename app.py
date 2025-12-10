#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
💕 拼豆图纸镜像工具
在线版本 - 支持手机和电脑浏览器
点击图片设置区域，更适合手机操作
"""

import streamlit as st
import numpy as np
import cv2
from PIL import Image, ImageDraw
from io import BytesIO
from collections import Counter
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(
    page_title="拼豆图纸镜像工具 💕",
    page_icon="🎨",
    layout="wide"
)

# 美化CSS
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
    }
    .main-title {
        text-align: center;
        background: linear-gradient(90deg, #ff6b9d, #c44569, #ff6b9d);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        text-align: center;
        color: #a6adc8;
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }
    .coord-box {
        background: #313244;
        border-radius: 8px;
        padding: 15px;
        margin: 5px 0;
        text-align: center;
        font-size: 1.2rem;
        font-weight: bold;
    }
    .coord-box-red {
        background: linear-gradient(135deg, #ff6b6b 0%, #c0392b 100%);
        border-radius: 8px;
        padding: 15px;
        margin: 5px 0;
        text-align: center;
        font-size: 1.1rem;
        font-weight: bold;
        color: white;
    }
    .coord-box-blue {
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
        border-radius: 8px;
        padding: 15px;
        margin: 5px 0;
        text-align: center;
        font-size: 1.1rem;
        font-weight: bold;
        color: white;
    }
    .click-hint {
        background: #89b4fa;
        color: #1e1e2e;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">🎨 拼豆图纸镜像工具</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">点击图片设置区域 → 一键镜像 ✨</p>', unsafe_allow_html=True)


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


def draw_selection(image, x1, y1, x2, y2):
    """绘制选区"""
    img_copy = image.copy()
    draw = ImageDraw.Draw(img_copy)
    
    if x1 is not None and y1 is not None:
        # 画左上角标记
        r = 15
        draw.ellipse([x1-r, y1-r, x1+r, y1+r], fill='red', outline='white')
        
    if x2 is not None and y2 is not None:
        # 画右下角标记
        r = 15
        draw.ellipse([x2-r, y2-r, x2+r, y2+r], fill='blue', outline='white')
    
    if x1 is not None and y1 is not None and x2 is not None and y2 is not None:
        # 确保坐标有效再画矩形
        rect_x1 = min(x1, x2)
        rect_y1 = min(y1, y2)
        rect_x2 = max(x1, x2)
        rect_y2 = max(y1, y2)
        
        if rect_x1 < rect_x2 and rect_y1 < rect_y2:
            for i in range(3):
                draw.rectangle([rect_x1-i, rect_y1-i, rect_x2+i, rect_y2+i], outline='lime')
    
    return img_copy


# 初始化 session state
if 'click_mode' not in st.session_state:
    st.session_state.click_mode = None
if 'x1' not in st.session_state:
    st.session_state.x1 = None
if 'y1' not in st.session_state:
    st.session_state.y1 = None
if 'x2' not in st.session_state:
    st.session_state.x2 = None
if 'y2' not in st.session_state:
    st.session_state.y2 = None
if 'last_action' not in st.session_state:
    st.session_state.last_action = None


# 主界面
uploaded_file = st.file_uploader("📁 上传拼豆图纸", type=['png', 'jpg', 'jpeg', 'bmp', 'webp'])

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert('RGB')
    width, height = image.size
    
    # 设置默认值
    if st.session_state.x1 is None:
        st.session_state.x1 = int(width * 0.025)
        st.session_state.y1 = int(height * 0.035)
        st.session_state.x2 = int(width * 0.975)
        st.session_state.y2 = int(height * 0.83)
    
    # ===== 参数设置 =====
    with st.expander("⚙️ 格子设置", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            preset = st.selectbox("预设", ["52×47", "20×20", "29×29", "50×50", "100×100"])
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
        with col2:
            cols = st.number_input("列", 1, 200, default_cols)
            rows = st.number_input("行", 1, 200, default_rows)
        with col3:
            remove_watermark = st.checkbox("去水印", value=True)
            st.caption(f"图片: {width}×{height}")
    
    st.markdown("---")
    
    # ===== 点击设置区域 =====
    st.subheader("📍 点击设置格子区域")
    
    # 按钮行
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    with col_btn1:
        if st.button("🔴 设置左上角", use_container_width=True, type="secondary"):
            st.session_state.click_mode = 'topleft'
    
    with col_btn2:
        if st.button("🔵 设置右下角", use_container_width=True, type="secondary"):
            st.session_state.click_mode = 'bottomright'
    
    with col_btn3:
        if st.button("🔄 重置", use_container_width=True):
            st.session_state.x1 = int(width * 0.025)
            st.session_state.y1 = int(height * 0.035)
            st.session_state.x2 = int(width * 0.975)
            st.session_state.y2 = int(height * 0.83)
            st.session_state.click_mode = None
            st.rerun()
    
    # 显示当前模式或成功提示
    if st.session_state.last_action:
        st.success(st.session_state.last_action)
        st.session_state.last_action = None  # 清除提示
    
    if st.session_state.click_mode == 'topleft':
        st.markdown('<div class="click-hint">👆 现在点击图片设置【左上角】位置</div>', unsafe_allow_html=True)
    elif st.session_state.click_mode == 'bottomright':
        st.markdown('<div class="click-hint">👆 现在点击图片设置【右下角】位置</div>', unsafe_allow_html=True)
    
    # 显示坐标（更醒目）
    col_coord1, col_coord2 = st.columns(2)
    with col_coord1:
        st.markdown(f'<div class="coord-box-red">🔴 左上角<br/>({st.session_state.x1}, {st.session_state.y1})</div>', unsafe_allow_html=True)
    with col_coord2:
        st.markdown(f'<div class="coord-box-blue">🔵 右下角<br/>({st.session_state.x2}, {st.session_state.y2})</div>', unsafe_allow_html=True)
    
    # 绘制带标记的图片
    display_image = draw_selection(image, st.session_state.x1, st.session_state.y1, 
                                   st.session_state.x2, st.session_state.y2)
    
    # 可点击的图片
    coords = streamlit_image_coordinates(display_image, key="main_image")
    
    # 处理点击
    if coords is not None:
        click_x = coords["x"]
        click_y = coords["y"]
        
        if st.session_state.click_mode == 'topleft':
            st.session_state.x1 = click_x
            st.session_state.y1 = click_y
            st.session_state.click_mode = None
            st.session_state.last_action = f"✅ 左上角已设置: ({click_x}, {click_y})"
            st.toast(f"🔴 左上角已设置!", icon="✅")
            st.rerun()
        elif st.session_state.click_mode == 'bottomright':
            st.session_state.x2 = click_x
            st.session_state.y2 = click_y
            st.session_state.click_mode = None
            st.session_state.last_action = f"✅ 右下角已设置: ({click_x}, {click_y})"
            st.toast(f"🔵 右下角已设置!", icon="✅")
            st.rerun()
    
    st.markdown("---")
    
    # ===== 处理按钮 =====
    st.subheader("🚀 镜像处理")
    
    if st.button("✨ 开始镜像处理", type="primary", use_container_width=True):
        # 自动校正坐标顺序
        x1 = min(st.session_state.x1, st.session_state.x2)
        y1 = min(st.session_state.y1, st.session_state.y2)
        x2 = max(st.session_state.x1, st.session_state.x2)
        y2 = max(st.session_state.y1, st.session_state.y2)
        
        if x1 == x2 or y1 == y2:
            st.error("❌ 区域太小！请重新设置")
        else:
            with st.spinner("处理中... ⏳"):
                result = process_image(image, x1, y1, x2, y2, cols, rows, remove_watermark)
                st.session_state['result'] = result
            st.success(f"✅ 完成！{cols}列 × {rows}行")
            st.balloons()
    
    # 显示结果
    if 'result' in st.session_state:
        st.image(st.session_state['result'], caption="镜像结果", use_container_width=True)
        
        buf = BytesIO()
        st.session_state['result'].save(buf, format='PNG')
        buf.seek(0)
        
        st.download_button(
            label="💾 下载镜像图片",
            data=buf,
            file_name="拼豆镜像图纸.png",
            mime="image/png",
            use_container_width=True,
            type="primary"
        )

else:
    # 欢迎页面
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h2 style="color: #cdd6f4;">👆 上传图片开始使用</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    ### 📖 使用方法
    
    1. **上传图片** - 选择你的拼豆图纸
    2. **设置格子数** - 选择预设或手动输入
    3. **点击设置区域**：
       - 点击「🔴 设置左上角」按钮，然后点击图片上格子区域的左上角
       - 点击「🔵 设置右下角」按钮，然后点击图片上格子区域的右下角
    4. **镜像处理** - 点击处理并下载
    
    ### 💡 功能特点
    - 🔄 镜像格子位置，文字保持正常
    - 🧹 可选去除水印
    - 📱 支持手机操作
    
    ---
    *Made with 💕*
    """)
