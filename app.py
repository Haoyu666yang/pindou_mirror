#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
💕 拼豆图纸镜像工具
在线版本 - 支持手机和电脑浏览器
"""

import streamlit as st
import numpy as np
import cv2
from PIL import Image
from io import BytesIO
from collections import Counter
from streamlit_cropper import st_cropper

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
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        text-align: center;
        color: #a6adc8;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">🎨 拼豆图纸镜像工具</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">上传图纸 → 拖动红框选择区域 → 一键镜像 ✨</p>', unsafe_allow_html=True)


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


# 主界面
uploaded_file = st.file_uploader("📁 上传拼豆图纸", type=['png', 'jpg', 'jpeg', 'bmp', 'webp'])

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert('RGB')
    width, height = image.size
    
    st.markdown("---")
    
    # ========== 设置参数 ==========
    st.subheader("1️⃣ 设置格子数量")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        preset = st.selectbox("预设尺寸", ["52×47", "20×20", "29×29", "50×50", "100×100", "自定义"])
        
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
        cols = st.number_input("列数", 1, 200, default_cols)
        rows = st.number_input("行数", 1, 200, default_rows)
    
    with col3:
        remove_watermark = st.checkbox("🧹 去除水印", value=True)
        st.info(f"📐 图片尺寸: {width} × {height} 像素")
    
    st.markdown("---")
    
    # ========== 拖动选择区域 ==========
    st.subheader("2️⃣ 拖动红框选择格子区域")
    st.caption("👆 用手指/鼠标拖动红框的边缘和角落来调整区域，框内是格子区域，框外是坐标轴")
    
    # 使用 cropper 组件
    # 默认选区
    default_box = {
        'left': int(width * 0.025),
        'top': int(height * 0.035),
        'width': int(width * 0.95),
        'height': int(height * 0.795)
    }
    
    # 创建两列布局
    col_crop, col_result = st.columns(2)
    
    with col_crop:
        st.markdown("**📷 拖动红框选择区域**")
        
        # st_cropper 返回裁剪后的图片，但我们需要坐标
        box = st_cropper(
            image,
            realtime_update=True,
            box_color='red',
            aspect_ratio=None,
            return_type='box',
            default_coords=(
                default_box['left'],
                default_box['top'],
                default_box['left'] + default_box['width'],
                default_box['top'] + default_box['height']
            )
        )
        
        # 获取坐标
        if box:
            x1 = int(box['left'])
            y1 = int(box['top'])
            x2 = int(box['left'] + box['width'])
            y2 = int(box['top'] + box['height'])
        else:
            x1 = default_box['left']
            y1 = default_box['top']
            x2 = default_box['left'] + default_box['width']
            y2 = default_box['top'] + default_box['height']
        
        st.caption(f"选区坐标: ({x1}, {y1}) - ({x2}, {y2})")
    
    with col_result:
        st.markdown("**🔄 镜像结果**")
        
        if st.button("🚀 开始镜像处理", type="primary", use_container_width=True):
            if x1 >= x2 or y1 >= y2:
                st.error("❌ 区域设置错误！")
            else:
                with st.spinner("正在处理... ⏳"):
                    result = process_image(image, x1, y1, x2, y2, cols, rows, remove_watermark)
                    st.session_state['result'] = result
                st.success(f"✅ 完成！{cols}列 × {rows}行")
                st.balloons()
        
        if 'result' in st.session_state:
            st.image(st.session_state['result'], use_container_width=True)
            
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
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="background: #313244; padding: 1.5rem; border-radius: 10px; text-align: center;">
            <h3>📤 第一步</h3>
            <p style="color: #a6adc8;">上传拼豆图纸图片</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: #313244; padding: 1.5rem; border-radius: 10px; text-align: center;">
            <h3>✋ 第二步</h3>
            <p style="color: #a6adc8;">拖动红框选择格子区域</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="background: #313244; padding: 1.5rem; border-radius: 10px; text-align: center;">
            <h3>✨ 第三步</h3>
            <p style="color: #a6adc8;">点击处理并下载</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("""
    ### 💡 这个工具可以做什么？
    
    当你想按**镜像方向**拼拼豆时，直接翻转图纸会导致格子里的文字也变成镜像，很难看清。
    
    这个工具可以：
    - 🔄 **镜像格子位置** - 整体图案左右翻转
    - 📝 **保持文字正常** - 每个格子里的颜色代码保持正常方向
    - 🧹 **去除水印** - 可选去除图片上的水印
    
    ---
    *Made with 💕*
    """)
