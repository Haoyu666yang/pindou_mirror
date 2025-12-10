#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
拼豆图纸镜像工具 v3.2
功能：将拼豆图纸水平镜像，保持文字正常，去除水印
- 支持自动检测格子数量
- 适配各种尺寸的图纸
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageDraw
import numpy as np
import cv2
import os
from collections import Counter


class PindouMirrorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("拼豆图纸镜像工具 v3.2")
        self.root.geometry("1400x950")
        self.root.configure(bg='#2b2b2b')
        
        # 图片变量
        self.original_image = None
        self.processed_image = None
        self.image_path = None
        self.display_scale = 1.0
        
        # 网格参数
        self.grid_cols = tk.IntVar(value=52)
        self.grid_rows = tk.IntVar(value=47)
        
        # 格子区域边界
        self.cell_x1 = tk.IntVar(value=0)
        self.cell_y1 = tk.IntVar(value=0)
        self.cell_x2 = tk.IntVar(value=0)
        self.cell_y2 = tk.IntVar(value=0)
        
        # 点击模式
        self.click_mode = tk.StringVar(value="none")
        
        # 去水印选项
        self.remove_watermark = tk.BooleanVar(value=True)
        
        self.setup_ui()
    
    def setup_ui(self):
        main_frame = tk.Frame(self.root, bg='#2b2b2b')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        control_frame = tk.Frame(main_frame, bg='#3c3c3c', relief=tk.RAISED, bd=2)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        btn_style = {'font': ('Microsoft YaHei', 10, 'bold'),
                     'relief': tk.FLAT, 'padx': 10, 'pady': 6, 'cursor': 'hand2'}
        
        # 第一行：上传和区域设置
        row1 = tk.Frame(control_frame, bg='#3c3c3c')
        row1.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(row1, text="📁 上传图片", command=self.upload_image, 
                  bg='#4a90d9', fg='white', **btn_style).pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(row1, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=5)
        
        tk.Button(row1, text="📍 设置左上角", command=lambda: self.set_click_mode("topleft"),
                  bg='#e67e22', fg='white', **btn_style).pack(side=tk.LEFT, padx=3)
        tk.Button(row1, text="📍 设置右下角", command=lambda: self.set_click_mode("bottomright"),
                  bg='#e67e22', fg='white', **btn_style).pack(side=tk.LEFT, padx=3)
        
        ttk.Separator(row1, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=5)
        
        # 自动检测格子数按钮
        tk.Button(row1, text="🔍 自动检测格子数", command=self.auto_detect_grid_size,
                  bg='#9b59b6', fg='white', **btn_style).pack(side=tk.LEFT, padx=3)
        
        ttk.Separator(row1, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=5)
        
        # 网格设置
        tk.Label(row1, text="列:", bg='#3c3c3c', fg='white', font=('Microsoft YaHei', 9)).pack(side=tk.LEFT)
        tk.Entry(row1, textvariable=self.grid_cols, width=5, font=('Microsoft YaHei', 9)).pack(side=tk.LEFT, padx=(3, 8))
        
        tk.Label(row1, text="行:", bg='#3c3c3c', fg='white', font=('Microsoft YaHei', 9)).pack(side=tk.LEFT)
        tk.Entry(row1, textvariable=self.grid_rows, width=5, font=('Microsoft YaHei', 9)).pack(side=tk.LEFT, padx=3)
        
        # 常用预设
        ttk.Separator(row1, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=5)
        tk.Label(row1, text="预设:", bg='#3c3c3c', fg='#aaa', font=('Microsoft YaHei', 9)).pack(side=tk.LEFT)
        
        preset_btn_style = {'font': ('Microsoft YaHei', 8), 'relief': tk.FLAT, 'padx': 6, 'pady': 3, 
                           'cursor': 'hand2', 'bg': '#555', 'fg': 'white'}
        tk.Button(row1, text="20×20", command=lambda: self.set_grid_size(20, 20), **preset_btn_style).pack(side=tk.LEFT, padx=2)
        tk.Button(row1, text="29×29", command=lambda: self.set_grid_size(29, 29), **preset_btn_style).pack(side=tk.LEFT, padx=2)
        tk.Button(row1, text="50×50", command=lambda: self.set_grid_size(50, 50), **preset_btn_style).pack(side=tk.LEFT, padx=2)
        tk.Button(row1, text="52×47", command=lambda: self.set_grid_size(52, 47), **preset_btn_style).pack(side=tk.LEFT, padx=2)
        tk.Button(row1, text="100×100", command=lambda: self.set_grid_size(100, 100), **preset_btn_style).pack(side=tk.LEFT, padx=2)
        
        # 第二行：处理选项和操作
        row2 = tk.Frame(control_frame, bg='#3c3c3c')
        row2.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(row2, text="格子区域 - 左上角:", bg='#3c3c3c', fg='#aaa', font=('Microsoft YaHei', 9)).pack(side=tk.LEFT)
        tk.Entry(row2, textvariable=self.cell_x1, width=5, font=('Microsoft YaHei', 9)).pack(side=tk.LEFT, padx=2)
        tk.Entry(row2, textvariable=self.cell_y1, width=5, font=('Microsoft YaHei', 9)).pack(side=tk.LEFT, padx=(2, 10))
        
        tk.Label(row2, text="右下角:", bg='#3c3c3c', fg='#aaa', font=('Microsoft YaHei', 9)).pack(side=tk.LEFT)
        tk.Entry(row2, textvariable=self.cell_x2, width=5, font=('Microsoft YaHei', 9)).pack(side=tk.LEFT, padx=2)
        tk.Entry(row2, textvariable=self.cell_y2, width=5, font=('Microsoft YaHei', 9)).pack(side=tk.LEFT, padx=2)
        
        self.mode_label = tk.Label(row2, text="", bg='#3c3c3c', fg='#ffcc00', font=('Microsoft YaHei', 9, 'bold'))
        self.mode_label.pack(side=tk.LEFT, padx=15)
        
        # 右侧操作按钮
        tk.Button(row2, text="💾 保存图片", command=self.save_image,
                  bg='#ff6b6b', fg='white', **btn_style).pack(side=tk.RIGHT, padx=5)
        tk.Button(row2, text="🔄 镜像处理", command=self.process_image,
                  bg='#50c878', fg='white', **btn_style).pack(side=tk.RIGHT, padx=5)
        
        tk.Checkbutton(row2, text="去除水印", variable=self.remove_watermark,
                       bg='#3c3c3c', fg='white', selectcolor='#2b2b2b',
                       font=('Microsoft YaHei', 9), activebackground='#3c3c3c').pack(side=tk.RIGHT, padx=10)
        
        # 图片显示区域
        image_frame = tk.Frame(main_frame, bg='#2b2b2b')
        image_frame.pack(fill=tk.BOTH, expand=True)
        
        left_frame = tk.LabelFrame(image_frame, text="原图 (点击设置区域)", bg='#2b2b2b', fg='white',
                                    font=('Microsoft YaHei', 11, 'bold'))
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.left_canvas = tk.Canvas(left_frame, bg='#1e1e1e', highlightthickness=0, cursor='crosshair')
        self.left_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.left_canvas.bind('<Button-1>', self.on_canvas_click)
        
        right_frame = tk.LabelFrame(image_frame, text="镜像后", bg='#2b2b2b', fg='white',
                                     font=('Microsoft YaHei', 11, 'bold'))
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.right_canvas = tk.Canvas(right_frame, bg='#1e1e1e', highlightthickness=0)
        self.right_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.status_var = tk.StringVar(value="步骤: 1.上传图片 → 2.设置格子区域 → 3.自动检测或手动设置格子数 → 4.镜像处理")
        status_bar = tk.Label(self.root, textvariable=self.status_var, bg='#1e1e1e', fg='#aaaaaa',
                              font=('Microsoft YaHei', 9), anchor=tk.W, padx=10, pady=5)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.root.bind('<Configure>', self.on_resize)
    
    def set_grid_size(self, cols, rows):
        """设置预设的格子数量"""
        self.grid_cols.set(cols)
        self.grid_rows.set(rows)
        self.status_var.set(f"已设置格子数: {cols}列 × {rows}行")
    
    def set_click_mode(self, mode):
        self.click_mode.set(mode)
        if mode == "topleft":
            self.mode_label.config(text="👆 请点击格子区域的左上角", fg='#ffcc00')
        elif mode == "bottomright":
            self.mode_label.config(text="👆 请点击格子区域的右下角", fg='#ffcc00')
        else:
            self.mode_label.config(text="")
    
    def on_canvas_click(self, event):
        if self.original_image is None:
            return
        
        mode = self.click_mode.get()
        if mode == "none":
            return
        
        canvas_width = self.left_canvas.winfo_width()
        canvas_height = self.left_canvas.winfo_height()
        
        img_width, img_height = self.original_image.size
        scale = min(canvas_width / img_width, canvas_height / img_height, 1.0)
        
        display_width = int(img_width * scale)
        display_height = int(img_height * scale)
        
        offset_x = (canvas_width - display_width) // 2
        offset_y = (canvas_height - display_height) // 2
        
        img_x = int((event.x - offset_x) / scale)
        img_y = int((event.y - offset_y) / scale)
        
        img_x = max(0, min(img_x, img_width - 1))
        img_y = max(0, min(img_y, img_height - 1))
        
        if mode == "topleft":
            self.cell_x1.set(img_x)
            self.cell_y1.set(img_y)
            self.mode_label.config(text=f"✓ 左上角: ({img_x}, {img_y})", fg='#50c878')
        elif mode == "bottomright":
            self.cell_x2.set(img_x)
            self.cell_y2.set(img_y)
            self.mode_label.config(text=f"✓ 右下角: ({img_x}, {img_y})", fg='#50c878')
        
        self.click_mode.set("none")
        self.display_image_with_selection()
    
    def upload_image(self):
        file_types = [
            ('图片文件', '*.png *.jpg *.jpeg *.bmp *.gif *.webp'),
            ('所有文件', '*.*')
        ]
        file_path = filedialog.askopenfilename(title="选择拼豆图纸", filetypes=file_types)
        
        if file_path:
            try:
                self.image_path = file_path
                self.original_image = Image.open(file_path).convert('RGB')
                self.processed_image = None
                self.display_image(self.original_image, self.left_canvas)
                self.right_canvas.delete("all")
                
                self.auto_detect_region()
                
                self.status_var.set(f"已加载: {os.path.basename(file_path)} - 请设置格子区域并检测格子数")
            except Exception as e:
                messagebox.showerror("错误", f"无法加载图片: {str(e)}")
    
    def auto_detect_region(self):
        """自动检测格子区域"""
        if self.original_image is None:
            return
        
        width, height = self.original_image.size
        
        # 基于典型布局估计
        self.cell_x1.set(int(width * 0.025))
        self.cell_y1.set(int(height * 0.035))
        self.cell_x2.set(int(width * 0.975))
        self.cell_y2.set(int(height * 0.83))
        
        self.display_image_with_selection()
    
    def auto_detect_grid_size(self):
        """自动检测格子数量"""
        if self.original_image is None:
            messagebox.showwarning("警告", "请先上传图片！")
            return
        
        x1 = self.cell_x1.get()
        y1 = self.cell_y1.get()
        x2 = self.cell_x2.get()
        y2 = self.cell_y2.get()
        
        if x1 >= x2 or y1 >= y2:
            messagebox.showwarning("警告", "请先设置正确的格子区域！")
            return
        
        try:
            self.status_var.set("正在检测格子数量...")
            self.root.update()
            
            # 提取格子区域
            img_array = np.array(self.original_image)
            region = img_array[y1:y2, x1:x2]
            
            gray = cv2.cvtColor(region, cv2.COLOR_RGB2GRAY)
            
            # 边缘检测
            edges = cv2.Canny(gray, 30, 100)
            
            # 检测直线
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=30, minLineLength=20, maxLineGap=5)
            
            if lines is None:
                self.status_var.set("无法自动检测，请手动设置格子数")
                return
            
            h_lines = []  # 水平线的y坐标
            v_lines = []  # 垂直线的x坐标
            
            for line in lines:
                x1_l, y1_l, x2_l, y2_l = line[0]
                
                # 判断是水平线还是垂直线
                if abs(y2_l - y1_l) < 3:  # 水平线
                    h_lines.append((y1_l + y2_l) // 2)
                elif abs(x2_l - x1_l) < 3:  # 垂直线
                    v_lines.append((x1_l + x2_l) // 2)
            
            # 聚类去重（合并相近的线）
            def cluster_lines(lines, threshold=5):
                if not lines:
                    return []
                lines = sorted(lines)
                clusters = [[lines[0]]]
                for line in lines[1:]:
                    if line - clusters[-1][-1] < threshold:
                        clusters[-1].append(line)
                    else:
                        clusters.append([line])
                return [sum(c) // len(c) for c in clusters]
            
            h_unique = cluster_lines(h_lines, threshold=8)
            v_unique = cluster_lines(v_lines, threshold=8)
            
            # 估计格子数
            region_height = y2 - y1
            region_width = x2 - x1
            
            # 方法1：根据检测到的线条数量
            detected_rows = max(1, len(h_unique) - 1)
            detected_cols = max(1, len(v_unique) - 1)
            
            # 方法2：根据线条间距估计
            if len(h_unique) >= 3:
                h_gaps = [h_unique[i+1] - h_unique[i] for i in range(len(h_unique)-1)]
                avg_h_gap = sum(h_gaps) / len(h_gaps)
                estimated_rows = round(region_height / avg_h_gap) if avg_h_gap > 5 else detected_rows
            else:
                estimated_rows = detected_rows
            
            if len(v_unique) >= 3:
                v_gaps = [v_unique[i+1] - v_unique[i] for i in range(len(v_unique)-1)]
                avg_v_gap = sum(v_gaps) / len(v_gaps)
                estimated_cols = round(region_width / avg_v_gap) if avg_v_gap > 5 else detected_cols
            else:
                estimated_cols = detected_cols
            
            # 选择更合理的值
            final_cols = estimated_cols if 5 < estimated_cols < 200 else detected_cols
            final_rows = estimated_rows if 5 < estimated_rows < 200 else detected_rows
            
            # 确保在合理范围内
            final_cols = max(5, min(200, final_cols))
            final_rows = max(5, min(200, final_rows))
            
            self.grid_cols.set(final_cols)
            self.grid_rows.set(final_rows)
            
            self.status_var.set(f"✓ 检测到格子数: {final_cols}列 × {final_rows}行 (检测到 {len(v_unique)} 条垂直线, {len(h_unique)} 条水平线)")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.status_var.set(f"检测失败: {str(e)}")
    
    def remove_watermark_from_cell(self, cell_array):
        """从格子中去除水印"""
        h, w = cell_array.shape[:2]
        result = cell_array.copy()
        
        pixels = cell_array.reshape(-1, 3)
        
        # 找背景色
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
        
        # 替换水印像素
        for y in range(h):
            for x in range(w):
                r, g, b = int(result[y, x, 0]), int(result[y, x, 1]), int(result[y, x, 2])
                brightness = (r + g + b) / 3
                diff = max(abs(r - g), abs(g - b), abs(r - b))
                
                if diff < 20 and 90 < brightness < 210:
                    result[y, x] = bg_color
        
        return result
    
    def process_image(self):
        """处理图片：镜像格子区域"""
        if self.original_image is None:
            messagebox.showwarning("警告", "请先上传图片！")
            return
        
        x1 = self.cell_x1.get()
        y1 = self.cell_y1.get()
        x2 = self.cell_x2.get()
        y2 = self.cell_y2.get()
        
        if x1 >= x2 or y1 >= y2:
            messagebox.showwarning("警告", "请正确设置格子区域！")
            return
        
        try:
            self.status_var.set("正在处理...")
            self.root.update()
            
            cols = self.grid_cols.get()
            rows = self.grid_rows.get()
            
            img_array = np.array(self.original_image)
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
                    
                    if self.remove_watermark.get():
                        cell = self.remove_watermark_from_cell(cell)
                    
                    target_h = dst_bottom - dst_top
                    target_w = dst_right - dst_left
                    
                    if cell.shape[0] != target_h or cell.shape[1] != target_w:
                        cell = cv2.resize(cell, (target_w, target_h), interpolation=cv2.INTER_NEAREST)
                    
                    new_img_array[dst_top:dst_bottom, dst_left:dst_right] = cell
            
            self.processed_image = Image.fromarray(new_img_array)
            self.display_image(self.processed_image, self.right_canvas)
            self.status_var.set(f"✓ 处理完成！{cols}列 × {rows}行")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("错误", f"处理失败: {str(e)}")
    
    def display_image(self, image, canvas):
        if image is None:
            return
        
        canvas.update()
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = 650
            canvas_height = 750
        
        img_width, img_height = image.size
        scale = min(canvas_width / img_width, canvas_height / img_height, 1.0)
        self.display_scale = scale
        
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(resized)
        
        canvas.delete("all")
        canvas.create_image(canvas_width // 2, canvas_height // 2, anchor=tk.CENTER, image=photo)
        canvas.image = photo
    
    def display_image_with_selection(self):
        if self.original_image is None:
            return
        
        img_copy = self.original_image.copy()
        draw = ImageDraw.Draw(img_copy)
        
        x1 = self.cell_x1.get()
        y1 = self.cell_y1.get()
        x2 = self.cell_x2.get()
        y2 = self.cell_y2.get()
        
        if x1 > 0 and y1 > 0 and x2 > x1 and y2 > y1:
            for i in range(3):
                draw.rectangle([x1-i, y1-i, x2+i, y2+i], outline='red')
        
        self.display_image(img_copy, self.left_canvas)
    
    def save_image(self):
        if self.processed_image is None:
            messagebox.showwarning("警告", "请先处理图片！")
            return
        
        if self.image_path:
            dir_name = os.path.dirname(self.image_path)
            base_name = os.path.splitext(os.path.basename(self.image_path))[0]
            default_name = f"{base_name}_镜像.png"
        else:
            dir_name = ""
            default_name = "镜像图片.png"
        
        file_path = filedialog.asksaveasfilename(
            title="保存镜像图片",
            initialdir=dir_name,
            initialfile=default_name,
            defaultextension=".png",
            filetypes=[('PNG图片', '*.png'), ('JPEG图片', '*.jpg'), ('所有文件', '*.*')]
        )
        
        if file_path:
            try:
                self.processed_image.save(file_path, quality=95)
                self.status_var.set(f"✓ 已保存: {file_path}")
                messagebox.showinfo("成功", f"图片已保存到:\n{file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {str(e)}")
    
    def on_resize(self, event):
        if event.widget == self.root:
            if self.original_image:
                self.root.after(100, self.display_image_with_selection)
            if self.processed_image:
                self.root.after(100, lambda: self.display_image(self.processed_image, self.right_canvas))


def main():
    root = tk.Tk()
    app = PindouMirrorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
