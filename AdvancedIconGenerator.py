import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter, ImageEnhance
import os
import threading
from queue import Queue
import io
import base64
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 在导入pyplot之前设置
from matplotlib import pyplot as plt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
try:
    import emoji
    EMOJI_SUPPORT = True
except ImportError:
    EMOJI_SUPPORT = False
    print("警告: emoji模块未安装，Emoji功能将受限")

import svgwrite
import warnings
from io import BytesIO
import cairosvg
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
import cssutils
import re

class AdvancedIconGenerator:
    def __init__(self, root):
        self.root = root
        root.title("高级图标生成工具 v6.0.4")
        root.geometry("900x700")  # 稍微缩小默认尺寸
        root.minsize(800, 600)    # 设置最小尺寸
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        
        # 初始化样式
        self.setup_styles()
        
        # 主界面布局
        self.setup_main_layout()
        
        # 图片转图标标签页
        self.setup_image_tab()
        
        # 文字转图标标签页
        self.setup_text_tab()
        
        # SVG转图标标签页
        self.setup_svg_tab()
        
        # Emoji转图标标签页
        self.setup_emoji_tab()
        
        # Unicode符号转图标标签页
        self.setup_unicode_tab()
        
        # CSS样式转图标标签页
        self.setup_css_tab()
        
        # Matplotlib绘图转图标标签页
        self.setup_matplotlib_tab()
        
        # 预览和保存区域
        self.setup_preview_section()
        
        # 状态栏
        self.setup_status_bar()
        
        # 初始化变量
        self.current_icon = None
        self.icon_previews = []
        self.progress_queue = Queue()
        self.check_progress()
        
    def setup_styles(self):
        """初始化所有UI样式"""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # 通用样式
        self.style.configure('.', background='#f5f5f5', font=('微软雅黑', 9))
        self.style.configure('TFrame', background='#f5f5f5')
        self.style.configure('TLabel', background='#f5f5f5')
        self.style.configure('TButton', padding=5)
        self.style.configure('Header.TLabel', font=('微软雅黑', 14, 'bold'))
        self.style.configure('TNotebook', background='#f5f5f5', padding=5)
        self.style.configure('TNotebook.Tab', padding=5, font=('微软雅黑', 10))
        self.style.configure('TLabelframe', padding=5, relief=tk.GROOVE)
        self.style.configure('TLabelframe.Label', background='#f5f5f5')
        self.style.configure('TProgressbar', thickness=10)
        
    def setup_main_layout(self):
        """设置主窗口布局 - 优化版"""
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 配置网格权重
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=1)  # 给标签页区域最大权重
        
        # 标题栏 - 更紧凑的布局
        self.header_frame = ttk.Frame(self.main_frame)
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        self.title_label = ttk.Label(self.header_frame, text="高级图标生成工具", style='Header.TLabel')
        self.title_label.pack(side=tk.LEFT, padx=5)
        
        self.help_btn = ttk.Button(self.header_frame, text="帮助", command=self.show_help, width=8)
        self.help_btn.pack(side=tk.RIGHT, padx=5)
        
        # 标签页控件 - 使用grid并设置权重
        self.tab_control = ttk.Notebook(self.main_frame)
        self.tab_control.grid(row=1, column=0, sticky="nsew")
        
        # 创建各标签页
        self.image_tab = ttk.Frame(self.tab_control)
        self.text_tab = ttk.Frame(self.tab_control)
        self.svg_tab = ttk.Frame(self.tab_control)
        self.emoji_tab = ttk.Frame(self.tab_control)
        self.unicode_tab = ttk.Frame(self.tab_control)
        self.css_tab = ttk.Frame(self.tab_control)
        self.matplotlib_tab = ttk.Frame(self.tab_control)
        
        # 添加标签页
        self.tab_control.add(self.image_tab, text=" 🖼️ 图片转图标 ")
        self.tab_control.add(self.text_tab, text=" 🔤 文字转图标 ")
        self.tab_control.add(self.svg_tab, text=" 🖍️ SVG转图标 ")
        self.tab_control.add(self.emoji_tab, text=" 😊 Emoji转图标 ")
        self.tab_control.add(self.unicode_tab, text=" ✨ Unicode转图标 ")
        self.tab_control.add(self.css_tab, text=" 🎨 CSS转图标 ")
        self.tab_control.add(self.matplotlib_tab, text=" 📊 图表转图标 ")
        
        # 进度条 - 放在标签页下方
        self.progress_bar = ttk.Progressbar(self.main_frame, mode='determinate')
        self.progress_bar.grid(row=2, column=0, sticky="ew", pady=(5, 0))
        self.progress_bar.grid_remove()  # 默认隐藏
        
        # 最终预览和保存区域
        self.setup_preview_section()
        
        # 状态栏
        self.status_bar = ttk.Label(self.root, text="准备就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
    def setup_image_tab(self):
        """设置图片转图标标签页 - 优化版"""
        # 主容器使用Frame+Canvas+Scrollbar实现可滚动区域
        container = ttk.Frame(self.image_tab)
        container.pack(fill=tk.BOTH, expand=True)
        
        # 创建画布和滚动条
        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        # 配置滚动区域
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 布局
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 图片选择区域 - 更紧凑的布局
        frame = ttk.LabelFrame(scrollable_frame, text="图片设置", padding=5)
        frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=2)
        frame.columnconfigure(0, weight=1)  # 让输入框扩展
        
        self.image_path = tk.StringVar()
        self.image_entry = ttk.Entry(frame, textvariable=self.image_path)
        self.image_entry.grid(row=0, column=0, padx=5, pady=2, sticky="ew")
        
        self.browse_btn = ttk.Button(frame, text="浏览...", command=self.select_image, width=8)
        self.browse_btn.grid(row=0, column=1, padx=5, pady=2)
        
        # 图片调整选项 - 使用Grid布局更紧凑
        adjust_frame = ttk.LabelFrame(scrollable_frame, text="图片调整", padding=5)
        adjust_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=2)
        
        # 亮度
        ttk.Label(adjust_frame, text="亮度:").grid(row=0, column=0, padx=2, pady=2, sticky=tk.W)
        self.brightness = tk.DoubleVar(value=1.0)
        ttk.Scale(adjust_frame, from_=0.1, to=2.0, variable=self.brightness,
                orient=tk.HORIZONTAL, length=120, command=lambda _: self.update_realtime_preview()).grid(row=0, column=1, padx=2, pady=2)
        
        # 对比度
        ttk.Label(adjust_frame, text="对比度:").grid(row=1, column=0, padx=2, pady=2, sticky=tk.W)
        self.contrast = tk.DoubleVar(value=1.0)
        ttk.Scale(adjust_frame, from_=0.1, to=2.0, variable=self.contrast,
                orient=tk.HORIZONTAL, length=120, command=lambda _: self.update_realtime_preview()).grid(row=1, column=1, padx=2, pady=2)
        
        # 饱和度
        ttk.Label(adjust_frame, text="饱和度:").grid(row=2, column=0, padx=2, pady=2, sticky=tk.W)
        self.saturation = tk.DoubleVar(value=1.0)
        ttk.Scale(adjust_frame, from_=0.0, to=2.0, variable=self.saturation,
                orient=tk.HORIZONTAL, length=120, command=lambda _: self.update_realtime_preview()).grid(row=2, column=1, padx=2, pady=2)
        
        # 透明度
        ttk.Label(adjust_frame, text="透明度:").grid(row=3, column=0, padx=2, pady=2, sticky=tk.W)
        self.alpha = tk.DoubleVar(value=1.0)
        ttk.Scale(adjust_frame, from_=0.0, to=1.0, variable=self.alpha,
                orient=tk.HORIZONTAL, length=120, command=lambda _: self.update_realtime_preview()).grid(row=3, column=1, padx=2, pady=2)
        
        # 效果
        ttk.Label(adjust_frame, text="效果:").grid(row=0, column=2, padx=5, pady=2, sticky=tk.W)
        self.effect_var = tk.StringVar()
        effects = ["无", "模糊", "轮廓", "锐化", "浮雕", "边缘增强", "平滑", "细节增强", 
                "反色", "黑白", "棕褐色", "油画", "像素化", "高斯模糊", "查找边缘"]
        ttk.Combobox(adjust_frame, textvariable=self.effect_var, values=effects, width=12).grid(row=0, column=3, padx=5, pady=2)
        self.effect_var.trace_add('write', lambda *_: self.update_realtime_preview())
        
        # 压缩质量
        ttk.Label(adjust_frame, text="压缩质量:").grid(row=1, column=2, padx=5, pady=2, sticky=tk.W)
        self.quality = tk.IntVar(value=95)
        ttk.Scale(adjust_frame, from_=1, to=100, variable=self.quality,
                orient=tk.HORIZONTAL, length=120).grid(row=1, column=3, padx=5, pady=2)
        
        # 形状蒙版选项 - 更紧凑的布局
        shape_frame = ttk.LabelFrame(scrollable_frame, text="形状蒙版", padding=5)
        shape_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=2)
        
        self.shape_var = tk.StringVar(value="方形")
        shapes = ["方形", "圆形", "圆角矩形", "星形", "心形", "三角形"]
        ttk.Combobox(shape_frame, textvariable=self.shape_var, values=shapes, width=12).grid(row=0, column=0, padx=5, pady=2, columnspan=2)
        
        # 圆角半径设置
        ttk.Label(shape_frame, text="圆角半径:").grid(row=1, column=0, padx=2, pady=2, sticky=tk.W)
        self.radius = tk.IntVar(value=20)
        ttk.Scale(shape_frame, from_=0, to=100, variable=self.radius,
                orient=tk.HORIZONTAL, length=120).grid(row=1, column=1, padx=2, pady=2)
        
        # 形状预览
        self.shape_preview = tk.Canvas(shape_frame, width=80, height=80, bg='white')
        self.shape_preview.grid(row=2, column=0, columnspan=2, pady=5)
        
        # 绑定形状变化事件
        self.shape_var.trace_add('write', self.update_shape_preview)
        self.radius.trace_add('write', self.update_shape_preview)
        
        # 尺寸设置 - 更紧凑的布局
        size_frame = ttk.LabelFrame(scrollable_frame, text="尺寸设置", padding=5)
        size_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=2)
        
        # 预设尺寸
        ttk.Label(size_frame, text="预设尺寸:").grid(row=0, column=0, padx=2, pady=2, sticky=tk.W)
        self.preset_sizes = tk.StringVar(value="16,24,32,48,64,128,256")
        ttk.Entry(size_frame, textvariable=self.preset_sizes, width=25).grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        
        # 自定义尺寸
        ttk.Label(size_frame, text="自定义尺寸:").grid(row=1, column=0, padx=2, pady=2, sticky=tk.W)
        self.custom_size = tk.StringVar()
        ttk.Entry(size_frame, textvariable=self.custom_size, width=25).grid(row=1, column=1, padx=2, pady=2, sticky="ew")
        
        # 尺寸定制复选框
        self.customize_sizes = tk.BooleanVar(value=False)
        ttk.Checkbutton(size_frame, text="单独定制尺寸", variable=self.customize_sizes,
                    command=self.toggle_custom_sizes).grid(row=2, column=0, columnspan=2, pady=2)
        
        # 尺寸定制表格 (初始隐藏)
        self.size_table_frame = ttk.Frame(size_frame)
        self.size_table_frame.grid(row=3, column=0, columnspan=2, sticky="ew")
        self.size_table_frame.grid_remove()
        
        # 生成按钮
        self.gen_preview_btn = ttk.Button(scrollable_frame, text="生成预览", command=self.start_image_preview_thread)
        self.gen_preview_btn.grid(row=3, column=0, columnspan=2, pady=10)
        
        # 配置网格权重
        scrollable_frame.columnconfigure(0, weight=1)
        scrollable_frame.columnconfigure(1, weight=1)
        adjust_frame.columnconfigure(1, weight=1)
        adjust_frame.columnconfigure(3, weight=1)
        size_frame.columnconfigure(1, weight=1)
        
    def setup_image_selection(self, parent):
        """设置图片选择区域"""
        frame = ttk.LabelFrame(parent, text="1. 选择源图片")
        frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        
        self.image_path = tk.StringVar()
        self.image_entry = ttk.Entry(frame, textvariable=self.image_path)
        self.image_entry.pack(side=tk.LEFT, padx=5, pady=2, fill=tk.X, expand=True)
        
        self.browse_btn = ttk.Button(frame, text="浏览...", command=self.select_image, width=8)
        self.browse_btn.pack(side=tk.RIGHT, padx=5, pady=2)
        
        # 实时预览绑定
        self.image_path.trace_add('write', self.check_image_input)
        
    def select_image(self):
        """打开文件对话框选择图片"""
        filetypes = [
            ('图片文件', '*.png;*.jpg;*.jpeg;*.bmp;*.gif;*.svg'),
            ('所有文件', '*.*')
        ]
        filename = filedialog.askopenfilename(
            title="选择图片",
            initialdir=os.path.expanduser("~"),
            filetypes=filetypes
        )
        if filename:
            self.image_path.set(filename)

    def setup_image_adjustments(self, parent):
        """设置图片调整选项"""
        frame = ttk.LabelFrame(parent, text="2. 图片调整选项")
        frame.grid(row=1, column=0, sticky="ew", pady=(0, 5))
        
        # 亮度
        ttk.Label(frame, text="亮度:").grid(row=0, column=0, padx=2, sticky=tk.W)
        self.brightness = tk.DoubleVar(value=1.0)
        ttk.Scale(frame, from_=0.1, to=2.0, variable=self.brightness,
                 orient=tk.HORIZONTAL, length=120, command=lambda _: self.update_realtime_preview()).grid(row=0, column=1, padx=2)
        
        # 对比度
        ttk.Label(frame, text="对比度:").grid(row=1, column=0, padx=2, sticky=tk.W)
        self.contrast = tk.DoubleVar(value=1.0)
        ttk.Scale(frame, from_=0.1, to=2.0, variable=self.contrast,
                 orient=tk.HORIZONTAL, length=120, command=lambda _: self.update_realtime_preview()).grid(row=1, column=1, padx=2)
        
        # 饱和度
        ttk.Label(frame, text="饱和度:").grid(row=2, column=0, padx=2, sticky=tk.W)
        self.saturation = tk.DoubleVar(value=1.0)
        ttk.Scale(frame, from_=0.0, to=2.0, variable=self.saturation,
                 orient=tk.HORIZONTAL, length=120, command=lambda _: self.update_realtime_preview()).grid(row=2, column=1, padx=2)
        
        # 透明度
        ttk.Label(frame, text="透明度:").grid(row=3, column=0, padx=2, sticky=tk.W)
        self.alpha = tk.DoubleVar(value=1.0)
        ttk.Scale(frame, from_=0.0, to=1.0, variable=self.alpha,
                 orient=tk.HORIZONTAL, length=120, command=lambda _: self.update_realtime_preview()).grid(row=3, column=1, padx=2)
        
        # 效果
        ttk.Label(frame, text="效果:").grid(row=0, column=2, padx=2, sticky=tk.W)
        self.effect_var = tk.StringVar()
        effects = ["无", "模糊", "轮廓", "锐化", "浮雕", "边缘增强", "平滑", "细节增强", 
                  "反色", "黑白", "棕褐色", "油画", "像素化", "高斯模糊", "查找边缘"]
        combobox = ttk.Combobox(frame, textvariable=self.effect_var, values=effects, width=12)
        combobox.grid(row=0, column=3, padx=2)
        combobox.bind("<<ComboboxSelected>>", lambda e: self.update_realtime_preview())
        
        # 压缩质量
        ttk.Label(frame, text="压缩质量:").grid(row=1, column=2, padx=2, sticky=tk.W)
        self.quality = tk.IntVar(value=95)
        ttk.Scale(frame, from_=1, to=100, variable=self.quality,
                 orient=tk.HORIZONTAL, length=120).grid(row=1, column=3, padx=2)
        
    def setup_size_settings(self, parent):
        """设置尺寸选项"""
        frame = ttk.LabelFrame(parent, text="3. 图标尺寸设置")
        frame.grid(row=2, column=0, sticky="ew", pady=(0, 5))
        
        # 预设尺寸
        ttk.Label(frame, text="预设尺寸:").grid(row=0, column=0, padx=2, sticky=tk.W)
        self.preset_sizes = tk.StringVar(value="16,24,32,48,64,128,256")
        ttk.Entry(frame, textvariable=self.preset_sizes, width=30).grid(row=0, column=1, padx=2)
        
        # 自定义尺寸
        ttk.Label(frame, text="自定义尺寸:").grid(row=1, column=0, padx=2, sticky=tk.W)
        self.custom_size = tk.StringVar()
        ttk.Entry(frame, textvariable=self.custom_size, width=30).grid(row=1, column=1, padx=2)
        
        # 尺寸定制复选框
        self.customize_sizes = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="单独定制尺寸", variable=self.customize_sizes,
                       command=self.toggle_custom_sizes).grid(row=2, column=0, columnspan=2, pady=2)
        
        # 尺寸定制表格 (初始隐藏)
        self.size_table_frame = ttk.Frame(frame)
        self.size_table_frame.grid(row=3, column=0, columnspan=2, sticky="ew")
        self.size_table_frame.grid_remove()
        
        # 表格标题
        ttk.Label(self.size_table_frame, text="尺寸").grid(row=0, column=0)
        ttk.Label(self.size_table_frame, text="亮度").grid(row=0, column=1)
        ttk.Label(self.size_table_frame, text="对比度").grid(row=0, column=2)
        ttk.Label(self.size_table_frame, text="饱和度").grid(row=0, column=3)
        ttk.Label(self.size_table_frame, text="透明度").grid(row=0, column=4)
        
        # 尺寸定制数据存储
        self.size_settings = {}
        
    def toggle_custom_sizes(self):
        """切换尺寸定制表格的显示"""
        if self.customize_sizes.get():
            self.size_table_frame.grid()
            self.update_size_table()
        else:
            self.size_table_frame.grid_remove()
        
    def update_size_table(self):
        """更新尺寸定制表格"""
        sizes = self.parse_sizes(self.preset_sizes.get(), self.custom_size.get())
        
        # 清除旧控件
        for widget in self.size_table_frame.winfo_children():
            if widget.grid_info()["row"] > 0:  # 保留标题行
                widget.destroy()
        
        # 添加新行
        for i, size in enumerate(sizes, start=1):
            # 尺寸标签
            ttk.Label(self.size_table_frame, text=str(size)).grid(row=i, column=0)
            
            # 初始化设置
            if size not in self.size_settings:
                self.size_settings[size] = {
                    'brightness': tk.DoubleVar(value=self.brightness.get()),
                    'contrast': tk.DoubleVar(value=self.contrast.get()),
                    'saturation': tk.DoubleVar(value=self.saturation.get()),
                    'alpha': tk.DoubleVar(value=self.alpha.get())
                }
            
            # 亮度滑块
            ttk.Scale(self.size_table_frame, from_=0.1, to=2.0, 
                     variable=self.size_settings[size]['brightness'],
                     orient=tk.HORIZONTAL, length=80).grid(row=i, column=1, padx=2)
            
            # 对比度滑块
            ttk.Scale(self.size_table_frame, from_=0.1, to=2.0,
                     variable=self.size_settings[size]['contrast'],
                     orient=tk.HORIZONTAL, length=80).grid(row=i, column=2, padx=2)
            
            # 饱和度滑块
            ttk.Scale(self.size_table_frame, from_=0.0, to=2.0,
                     variable=self.size_settings[size]['saturation'],
                     orient=tk.HORIZONTAL, length=80).grid(row=i, column=3, padx=2)
            
            # 透明度滑块
            ttk.Scale(self.size_table_frame, from_=0.0, to=1.0,
                     variable=self.size_settings[size]['alpha'],
                     orient=tk.HORIZONTAL, length=80).grid(row=i, column=4, padx=2)
    
    def setup_shape_mask(self, parent):
        """设置形状蒙版选项"""
        frame = ttk.LabelFrame(parent, text="4. 形状蒙版")
        frame.grid(row=1, column=1, sticky="nsew", pady=(0, 5))
        
        self.shape_var = tk.StringVar(value="方形")
        shapes = ["方形", "圆形", "圆角矩形", "星形", "心形", "三角形"]
        ttk.Combobox(frame, textvariable=self.shape_var, values=shapes, width=12).grid(row=0, column=0, padx=5, pady=2)
        
        # 圆角半径设置 (仅当选择圆角矩形时显示)
        self.radius_label = ttk.Label(frame, text="圆角半径:")
        self.radius_label.grid(row=1, column=0, padx=2, sticky=tk.W)
        
        self.radius = tk.IntVar(value=20)
        self.radius_slider = ttk.Scale(frame, from_=0, to=100, variable=self.radius,
                                      orient=tk.HORIZONTAL, length=120)
        self.radius_slider.grid(row=1, column=1, padx=2)
        
        # 形状预览
        self.shape_preview = tk.Canvas(frame, width=100, height=100, bg='white')
        self.shape_preview.grid(row=2, column=0, columnspan=2, pady=5)
        
        # 绑定形状变化事件
        self.shape_var.trace_add('write', self.update_shape_preview)
        self.radius.trace_add('write', self.update_shape_preview)
        
        # 初始绘制
        self.update_shape_preview()
        
    def update_shape_preview(self, *args):
        """更新形状预览"""
        canvas = self.shape_preview
        canvas.delete("all")
        
        shape = self.shape_var.get()
        w, h = 100, 100
        
        if shape == "圆形":
            canvas.create_oval(5, 5, w-5, h-5, outline='black', width=2, fill='#e0e0e0')
        elif shape == "圆角矩形":
            radius = self.radius.get()
            canvas.create_round_rectangle(5, 5, w-5, h-5, radius=radius, outline='black', width=2, fill='#e0e0e0')
        elif shape == "星形":
            points = self.calculate_star_points(5, w//2, h//2, w//2-5, w//4)
            canvas.create_polygon(points, outline='black', width=2, fill='#e0e0e0')
        elif shape == "心形":
            points = self.calculate_heart_points(w//2, h//2, w//2-5)
            canvas.create_polygon(points, outline='black', width=2, fill='#e0e0e0', smooth=True)
        elif shape == "三角形":
            points = [w//2, 5, w-5, h-5, 5, h-5]
            canvas.create_polygon(points, outline='black', width=2, fill='#e0e0e0')
        else:  # 方形
            canvas.create_rectangle(5, 5, w-5, h-5, outline='black', width=2, fill='#e0e0e0')
    
    def calculate_star_points(self, spikes, cx, cy, outer_radius, inner_radius):
        """计算星形点坐标"""
        points = []
        step = 2 * np.pi / spikes
        rot = np.pi / 2 * 3
        
        for i in range(spikes * 2):
            r = outer_radius if i % 2 == 0 else inner_radius
            x = cx + np.cos(i * step + rot) * r
            y = cy + np.sin(i * step + rot) * r
            points.extend([x, y])
        
        return points
    
    def calculate_heart_points(self, cx, cy, size):
        """计算心形点坐标"""
        points = []
        for t in np.linspace(0, 2*np.pi, 30):
            x = 16 * np.sin(t)**3
            y = 13 * np.cos(t) - 5 * np.cos(2*t) - 2 * np.cos(3*t) - np.cos(4*t)
            points.extend([cx + x*size/16, cy - y*size/16])
        return points
    
    def setup_text_tab(self):
        """设置文字转图标标签页"""
        container = ttk.Frame(self.text_tab)
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        container.grid_propagate(False)
        
        # 文字输入区域
        self.setup_text_input(container)
        
        # 字体设置
        self.setup_font_settings(container)
        
        # 背景设置
        self.setup_background_settings(container)
        
        # 尺寸设置
        self.setup_text_size_settings(container)
        
        # 生成按钮
        self.gen_text_preview_btn = ttk.Button(container, text="生成预览", command=self.start_text_preview_thread)
        self.gen_text_preview_btn.grid(row=4, column=0, columnspan=2, pady=10)
        
        # 配置网格权重
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)
        
    def setup_text_input(self, parent):
        """设置文字输入区域"""
        frame = ttk.LabelFrame(parent, text="1. 文字内容")
        frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        
        self.text_var = tk.StringVar()
        self.text_entry = ttk.Entry(frame, textvariable=self.text_var)
        self.text_entry.pack(side=tk.LEFT, padx=5, pady=2, fill=tk.X, expand=True)
        
        # 实时预览绑定
        self.text_var.trace_add('write', self.update_realtime_preview)
        
    def setup_font_settings(self, parent):
        """设置字体选项"""
        frame = ttk.LabelFrame(parent, text="2. 字体设置")
        frame.grid(row=1, column=0, sticky="ew", pady=(0, 5))
        
        # 字体家族
        ttk.Label(frame, text="字体:").grid(row=0, column=0, padx=2, sticky=tk.W)
        self.font_family = tk.StringVar(value="微软雅黑")
        try:
            import tkinter.font
            fonts = list(tkinter.font.families())
            if "微软雅黑" not in fonts:
                fonts.insert(0, "微软雅黑")
        except:
            fonts = ["微软雅黑", "Arial", "Times New Roman", "Courier New"]

        font_combo = ttk.Combobox(frame, textvariable=self.font_family, values=fonts, width=15)
        font_combo.grid(row=0, column=1, padx=2)
        font_combo.bind("<<ComboboxSelected>>", lambda e: self.update_realtime_preview())

        # 字体大小
        ttk.Label(frame, text="大小:").grid(row=0, column=2, padx=2, sticky=tk.W)
        self.font_size = tk.IntVar(value=100)
        ttk.Spinbox(frame, from_=8, to=300, textvariable=self.font_size, width=5,
                   command=self.update_realtime_preview).grid(row=0, column=3, padx=2)
        
        # 字体样式
        ttk.Label(frame, text="样式:").grid(row=1, column=0, padx=2, sticky=tk.W)
        self.font_style = tk.StringVar(value="normal")
        styles = ["normal", "bold", "italic", "bold italic"]
        style_combo = ttk.Combobox(frame, textvariable=self.font_style, values=styles, width=10)
        style_combo.grid(row=1, column=1, padx=2)
        style_combo.bind("<<ComboboxSelected>>", lambda e: self.update_realtime_preview())
        
        # 文字颜色
        ttk.Label(frame, text="文字颜色:").grid(row=1, column=2, padx=2, sticky=tk.W)
        self.text_color = tk.StringVar(value="#000000")
        ttk.Button(frame, text="选择...", command=lambda: self.choose_color(self.text_color, self.update_realtime_preview),
                  width=8).grid(row=1, column=3, padx=2)
        
    def setup_background_settings(self, parent):
        """设置背景选项"""
        frame = ttk.LabelFrame(parent, text="3. 背景设置")
        frame.grid(row=1, column=1, sticky="nsew", pady=(0, 5))
        
        # 背景类型
        ttk.Label(frame, text="背景类型:").grid(row=0, column=0, padx=2, sticky=tk.W)
        self.bg_type = tk.StringVar(value="纯色")
        bg_types = ["纯色", "渐变", "透明"]
        bg_type_combo = ttk.Combobox(frame, textvariable=self.bg_type, values=bg_types, width=8)
        bg_type_combo.grid(row=0, column=1, padx=2)
        bg_type_combo.bind("<<ComboboxSelected>>", lambda e: self.update_bg_controls())
        
        # 背景颜色
        ttk.Label(frame, text="背景颜色:").grid(row=0, column=2, padx=2, sticky=tk.W)
        self.bg_color = tk.StringVar(value="#FFFFFF")
        ttk.Button(frame, text="选择...", 
                  command=lambda: self.choose_color(self.bg_color, self.update_realtime_preview),
                  width=8).grid(row=0, column=3, padx=2)
        
        # 渐变方向 (仅当背景类型为渐变时显示)
        self.gradient_dir_label = ttk.Label(frame, text="渐变方向:")
        self.gradient_dir_label.grid(row=1, column=0, padx=2, sticky=tk.W)
        
        self.gradient_dir = tk.StringVar(value="水平")
        self.gradient_dir_combo = ttk.Combobox(frame, textvariable=self.gradient_dir, 
                                            values=["水平", "垂直", "对角"], width=8)
        self.gradient_dir_combo.bind("<<ComboboxSelected>>", lambda e: self.update_realtime_preview())
        self.gradient_dir_combo.grid(row=1, column=1, padx=2)
        
        # 第二颜色 (仅当背景类型为渐变时显示)
        self.bg_color2_label = ttk.Label(frame, text="第二颜色:")
        self.bg_color2_label.grid(row=1, column=2, padx=2, sticky=tk.W)
        
        self.bg_color2 = tk.StringVar(value="#CCCCCC")
        self.bg_color2_btn = ttk.Button(frame, text="选择...", 
                                       command=lambda: self.choose_color(self.bg_color2, self.update_realtime_preview),
                                       width=8)
        self.bg_color2_btn.grid(row=1, column=3, padx=2)
        
        # 背景透明度
        ttk.Label(frame, text="透明度:").grid(row=2, column=0, padx=2, sticky=tk.W)
        self.bg_alpha = tk.DoubleVar(value=1.0)
        ttk.Scale(frame, from_=0.0, to=1.0, variable=self.bg_alpha,
                 orient=tk.HORIZONTAL, length=120, command=lambda _: self.update_realtime_preview()).grid(row=2, column=1, columnspan=3, padx=2, sticky="ew")
        
        # 初始显示/隐藏渐变控件
        self.update_bg_controls()
        
    def update_bg_controls(self, *args):
        """根据背景类型显示/隐藏渐变控件"""
        if self.bg_type.get() == "渐变":
            self.gradient_dir_label.grid()
            self.gradient_dir_combo.grid()
            self.bg_color2_label.grid()
            self.bg_color2_btn.grid()
        else:
            self.gradient_dir_label.grid_remove()
            self.gradient_dir_combo.grid_remove()
            self.bg_color2_label.grid_remove()
            self.bg_color2_btn.grid_remove()
        self.update_realtime_preview()
        
    def setup_text_size_settings(self, parent):
        """设置文字图标的尺寸选项"""
        frame = ttk.LabelFrame(parent, text="4. 图标尺寸设置")
        frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        
        # 预设尺寸
        ttk.Label(frame, text="预设尺寸:").grid(row=0, column=0, padx=2, sticky=tk.W)
        self.text_preset_sizes = tk.StringVar(value="16,24,32,48,64,128,256")
        ttk.Entry(frame, textvariable=self.text_preset_sizes, width=30).grid(row=0, column=1, padx=2)
        
        # 自定义尺寸
        ttk.Label(frame, text="自定义尺寸:").grid(row=1, column=0, padx=2, sticky=tk.W)
        self.text_custom_size = tk.StringVar()
        ttk.Entry(frame, textvariable=self.text_custom_size, width=30).grid(row=1, column=1, padx=2)
        
    def setup_svg_tab(self):
        """设置SVG转图标标签页"""
        container = ttk.Frame(self.svg_tab)
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # SVG输入区域
        frame = ttk.LabelFrame(container, text="1. SVG代码")
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        self.svg_text = tk.Text(frame, wrap=tk.WORD, height=10)
        scrollbar = ttk.Scrollbar(frame, command=self.svg_text.yview)
        self.svg_text.configure(yscrollcommand=scrollbar.set)
        
        self.svg_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 示例SVG按钮
        example_frame = ttk.Frame(container)
        example_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(example_frame, text="示例1: 圆形", command=lambda: self.load_svg_example(1)).pack(side=tk.LEFT, padx=2)
        ttk.Button(example_frame, text="示例2: 矩形", command=lambda: self.load_svg_example(2)).pack(side=tk.LEFT, padx=2)
        ttk.Button(example_frame, text="示例3: 星形", command=lambda: self.load_svg_example(3)).pack(side=tk.LEFT, padx=2)
        ttk.Button(example_frame, text="示例4: 路径", command=lambda: self.load_svg_example(4)).pack(side=tk.LEFT, padx=2)
        
        # 尺寸设置
        frame = ttk.LabelFrame(container, text="2. 图标尺寸设置")
        frame.pack(fill=tk.X, pady=(0, 5))
        
        # 预设尺寸
        ttk.Label(frame, text="预设尺寸:").grid(row=0, column=0, padx=2, sticky=tk.W)
        self.svg_preset_sizes = tk.StringVar(value="16,24,32,48,64,128,256")
        ttk.Entry(frame, textvariable=self.svg_preset_sizes, width=30).grid(row=0, column=1, padx=2)
        
        # 自定义尺寸
        ttk.Label(frame, text="自定义尺寸:").grid(row=1, column=0, padx=2, sticky=tk.W)
        self.svg_custom_size = tk.StringVar()
        ttk.Entry(frame, textvariable=self.svg_custom_size, width=30).grid(row=1, column=1, padx=2)
        
        # 背景颜色
        ttk.Label(frame, text="背景颜色:").grid(row=0, column=2, padx=2, sticky=tk.W)
        self.svg_bg_color = tk.StringVar(value="#FFFFFF")
        ttk.Button(frame, text="选择...", command=lambda: self.choose_color(self.svg_bg_color),
                  width=8).grid(row=0, column=3, padx=2)
        
        # 透明度
        ttk.Label(frame, text="透明度:").grid(row=1, column=2, padx=2, sticky=tk.W)
        self.svg_alpha = tk.DoubleVar(value=1.0)
        ttk.Scale(frame, from_=0.0, to=1.0, variable=self.svg_alpha,
                 orient=tk.HORIZONTAL, length=120).grid(row=1, column=3, padx=2)
        
        # 生成按钮
        self.gen_svg_preview_btn = ttk.Button(container, text="生成预览", command=self.start_svg_preview_thread)
        self.gen_svg_preview_btn.pack(pady=10)
        
    def load_svg_example(self, num):
        """加载SVG示例"""
        examples = {
            1: """<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
  <circle cx="50" cy="50" r="40" stroke="black" stroke-width="2" fill="red" />
</svg>""",
            2: """<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
  <rect x="10" y="10" width="80" height="80" stroke="black" stroke-width="2" fill="blue" />
</svg>""",
            3: """<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
  <polygon points="50,5 20,95 95,35 5,35 80,95" stroke="black" stroke-width="2" fill="gold" />
</svg>""",
            4: """<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
  <path d="M10 80 Q 50 10, 90 80 T 170 80" stroke="black" stroke-width="2" fill="none" />
</svg>"""
        }
        
        self.svg_text.delete("1.0", tk.END)
        self.svg_text.insert("1.0", examples.get(num, ""))
        
    def setup_emoji_tab(self):
        """设置Emoji转图标标签页"""
        container = ttk.Frame(self.emoji_tab)
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        if not EMOJI_SUPPORT:
            ttk.Label(container, text="需要安装emoji模块才能使用此功能\n请运行: pip install emoji", 
                    justify=tk.CENTER).pack(expand=True)
            return

        # Emoji选择区域
        frame = ttk.LabelFrame(container, text="1. 选择Emoji")
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Emoji选择按钮
        emoji_frame = ttk.Frame(frame)
        emoji_frame.pack(fill=tk.X, pady=5)
        
        categories = ["笑脸", "动物", "食物", "活动", "旅行", "物品", "符号", "旗帜"]
        for i, cat in enumerate(categories):
            ttk.Button(emoji_frame, text=cat, command=lambda c=cat: self.show_emoji_palette(c)).pack(side=tk.LEFT, padx=2)
        
        # 自定义Emoji输入
        self.emoji_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.emoji_var).pack(fill=tk.X, padx=5, pady=5)
        
        # 尺寸设置
        frame = ttk.LabelFrame(container, text="2. 图标尺寸设置")
        frame.pack(fill=tk.X, pady=(0, 5))
        
        # 预设尺寸
        ttk.Label(frame, text="预设尺寸:").grid(row=0, column=0, padx=2, sticky=tk.W)
        self.emoji_preset_sizes = tk.StringVar(value="16,24,32,48,64,128,256")
        ttk.Entry(frame, textvariable=self.emoji_preset_sizes, width=30).grid(row=0, column=1, padx=2)
        
        # 自定义尺寸
        ttk.Label(frame, text="自定义尺寸:").grid(row=1, column=0, padx=2, sticky=tk.W)
        self.emoji_custom_size = tk.StringVar()
        ttk.Entry(frame, textvariable=self.emoji_custom_size, width=30).grid(row=1, column=1, padx=2)
        
        # 背景颜色
        ttk.Label(frame, text="背景颜色:").grid(row=0, column=2, padx=2, sticky=tk.W)
        self.emoji_bg_color = tk.StringVar(value="#FFFFFF")
        ttk.Button(frame, text="选择...", command=lambda: self.choose_color(self.emoji_bg_color),
                  width=8).grid(row=0, column=3, padx=2)
        
        # 透明度
        ttk.Label(frame, text="透明度:").grid(row=1, column=2, padx=2, sticky=tk.W)
        self.emoji_alpha = tk.DoubleVar(value=1.0)
        ttk.Scale(frame, from_=0.0, to=1.0, variable=self.emoji_alpha,
                 orient=tk.HORIZONTAL, length=120).grid(row=1, column=3, padx=2)
        
        # 生成按钮
        self.gen_emoji_preview_btn = ttk.Button(container, text="生成预览", command=self.start_emoji_preview_thread)
        self.gen_emoji_preview_btn.pack(pady=10)
        
    def show_emoji_palette(self, category):
        """显示Emoji选择面板"""
        emoji_map = {
            "笑脸": ["😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣", "😊", "😇"],
            "动物": ["🐶", "🐱", "🐭", "🐹", "🐰", "🦊", "🐻", "🐼", "🐨", "🐯"],
            "食物": ["🍏", "🍎", "🍐", "🍊", "🍋", "🍌", "🍉", "🍇", "🍓", "🍈"],
            "活动": ["⚽", "🏀", "🏈", "⚾", "🎾", "🏐", "🏉", "🎱", "🏓", "🏸"],
            "旅行": ["🚗", "🚕", "🚙", "🚌", "🚎", "🏎", "🚓", "🚑", "🚒", "🚐"],
            "物品": ["⌚", "📱", "💻", "⌨️", "🖥", "🖨", "🖱", "🖲", "💽", "💾"],
            "符号": ["❤️", "💛", "💚", "💙", "💜", "🖤", "💔", "❣️", "💕", "💞"],
            "旗帜": ["🏳️", "🏴", "🏁", "🚩", "🏳️‍🌈", "🏴‍☠️", "🇨🇳", "🇺🇸", "🇬🇧", "🇯🇵"]
        }
        
        top = tk.Toplevel(self.root)
        top.title(f"选择 {category} Emoji")
        
        for i, emoji_char in enumerate(emoji_map.get(category, [])):
            btn = ttk.Button(top, text=emoji_char, command=lambda e=emoji_char: self.select_emoji(e, top))
            btn.grid(row=i//5, column=i%5, padx=5, pady=5)
            
    def select_emoji(self, emoji_char, window):
        """选择Emoji"""
        self.emoji_var.set(emoji_char)
        window.destroy()
        
    def setup_unicode_tab(self):
        """设置Unicode符号转图标标签页"""
        container = ttk.Frame(self.unicode_tab)
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Unicode符号选择区域
        frame = ttk.LabelFrame(container, text="1. 选择Unicode符号")
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Unicode符号选择按钮
        unicode_frame = ttk.Frame(frame)
        unicode_frame.pack(fill=tk.X, pady=5)
        
        categories = ["数学", "几何", "箭头", "货币", "标点", "其他"]
        for i, cat in enumerate(categories):
            ttk.Button(unicode_frame, text=cat, command=lambda c=cat: self.show_unicode_palette(c)).pack(side=tk.LEFT, padx=2)
        
        # 自定义Unicode输入
        self.unicode_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.unicode_var).pack(fill=tk.X, padx=5, pady=5)
        
        # 字体设置
        self.setup_unicode_font_settings(frame)
        
        # 尺寸设置
        frame = ttk.LabelFrame(container, text="2. 图标尺寸设置")
        frame.pack(fill=tk.X, pady=(0, 5))
        
        # 预设尺寸
        ttk.Label(frame, text="预设尺寸:").grid(row=0, column=0, padx=2, sticky=tk.W)
        self.unicode_preset_sizes = tk.StringVar(value="16,24,32,48,64,128,256")
        ttk.Entry(frame, textvariable=self.unicode_preset_sizes, width=30).grid(row=0, column=1, padx=2)
        
        # 自定义尺寸
        ttk.Label(frame, text="自定义尺寸:").grid(row=1, column=0, padx=2, sticky=tk.W)
        self.unicode_custom_size = tk.StringVar()
        ttk.Entry(frame, textvariable=self.unicode_custom_size, width=30).grid(row=1, column=1, padx=2)
        
        # 背景颜色
        ttk.Label(frame, text="背景颜色:").grid(row=0, column=2, padx=2, sticky=tk.W)
        self.unicode_bg_color = tk.StringVar(value="#FFFFFF")
        ttk.Button(frame, text="选择...", command=lambda: self.choose_color(self.unicode_bg_color),
                  width=8).grid(row=0, column=3, padx=2)
        
        # 透明度
        ttk.Label(frame, text="透明度:").grid(row=1, column=2, padx=2, sticky=tk.W)
        self.unicode_alpha = tk.DoubleVar(value=1.0)
        ttk.Scale(frame, from_=0.0, to=1.0, variable=self.unicode_alpha,
                 orient=tk.HORIZONTAL, length=120).grid(row=1, column=3, padx=2)
        
        # 生成按钮
        self.gen_unicode_preview_btn = ttk.Button(container, text="生成预览", command=self.start_unicode_preview_thread)
        self.gen_unicode_preview_btn.pack(pady=10)
        
    def setup_unicode_font_settings(self, parent):
        """设置Unicode符号字体选项"""
        frame = ttk.LabelFrame(parent, text="字体设置")
        frame.pack(fill=tk.X, pady=(0, 5))
        
        # 字体家族
        ttk.Label(frame, text="字体:").grid(row=0, column=0, padx=2, sticky=tk.W)
        self.unicode_font_family = tk.StringVar(value="Arial Unicode MS")
        try:
            import tkinter.font
            fonts = list(tkinter.font.families())
            if "Arial Unicode MS" not in fonts:
                fonts.insert(0, "Arial Unicode MS")
        except:
            fonts = ["Arial Unicode MS", "Segoe UI Symbol", "Symbola", "Noto Sans"]
            
        font_combo = ttk.Combobox(frame, textvariable=self.unicode_font_family, values=fonts, width=15)
        font_combo.grid(row=0, column=1, padx=2)
        font_combo.bind("<<ComboboxSelected>>", lambda e: self.update_realtime_preview())
        
        # 字体大小
        ttk.Label(frame, text="大小:").grid(row=0, column=2, padx=2, sticky=tk.W)
        self.unicode_font_size = tk.IntVar(value=100)
        ttk.Spinbox(frame, from_=8, to=300, textvariable=self.unicode_font_size, width=5).grid(row=0, column=3, padx=2)
        
        # 字体颜色
        ttk.Label(frame, text="颜色:").grid(row=1, column=0, padx=2, sticky=tk.W)
        self.unicode_font_color = tk.StringVar(value="#000000")
        ttk.Button(frame, text="选择...", command=lambda: self.choose_color(self.unicode_font_color),
                  width=8).grid(row=1, column=1, padx=2)
        
    def show_unicode_palette(self, category):
        """显示Unicode符号选择面板"""
        unicode_map = {
            "数学": ["∀", "∁", "∂", "∃", "∄", "∅", "∆", "∇", "∈", "∉"],
            "几何": ["□", "△", "○", "◇", "☆", "▽", "◯", "◊", "⧉", "⬠"],
            "箭头": ["←", "↑", "→", "↓", "↔", "↕", "↖", "↗", "↘", "↙"],
            "货币": ["$", "€", "£", "¥", "₽", "₩", "₪", "₫", "₭", "₮"],
            "标点": ["!", "?", ".", ",", ";", ":", "'", "\"", "(", ")"],
            "其他": ["☀", "☁", "☂", "☃", "☎", "☑", "☘", "☝", "☠", "☢"]
        }
        
        top = tk.Toplevel(self.root)
        top.title(f"选择 {category} Unicode符号")
        
        for i, unicode_char in enumerate(unicode_map.get(category, [])):
            btn = ttk.Button(top, text=unicode_char, command=lambda u=unicode_char: self.select_unicode(u, top))
            btn.grid(row=i//5, column=i%5, padx=5, pady=5)
            
    def select_unicode(self, unicode_char, window):
        """选择Unicode符号"""
        self.unicode_var.set(unicode_char)
        window.destroy()
        
    def setup_css_tab(self):
        """设置CSS样式转图标标签页"""
        container = ttk.Frame(self.css_tab)
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # CSS输入区域
        frame = ttk.LabelFrame(container, text="1. CSS样式")
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        self.css_text = tk.Text(frame, wrap=tk.WORD, height=10)
        scrollbar = ttk.Scrollbar(frame, command=self.css_text.yview)
        self.css_text.configure(yscrollcommand=scrollbar.set)
        
        self.css_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 示例CSS按钮
        example_frame = ttk.Frame(container)
        example_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(example_frame, text="示例1: 圆形", command=lambda: self.load_css_example(1)).pack(side=tk.LEFT, padx=2)
        ttk.Button(example_frame, text="示例2: 按钮", command=lambda: self.load_css_example(2)).pack(side=tk.LEFT, padx=2)
        ttk.Button(example_frame, text="示例3: 渐变", command=lambda: self.load_css_example(3)).pack(side=tk.LEFT, padx=2)
        ttk.Button(example_frame, text="示例4: 阴影", command=lambda: self.load_css_example(4)).pack(side=tk.LEFT, padx=2)
        
        # 尺寸设置
        frame = ttk.LabelFrame(container, text="2. 图标尺寸设置")
        frame.pack(fill=tk.X, pady=(0, 5))
        
        # 预设尺寸
        ttk.Label(frame, text="预设尺寸:").grid(row=0, column=0, padx=2, sticky=tk.W)
        self.css_preset_sizes = tk.StringVar(value="16,24,32,48,64,128,256")
        ttk.Entry(frame, textvariable=self.css_preset_sizes, width=30).grid(row=0, column=1, padx=2)
        
        # 自定义尺寸
        ttk.Label(frame, text="自定义尺寸:").grid(row=1, column=0, padx=2, sticky=tk.W)
        self.css_custom_size = tk.StringVar()
        ttk.Entry(frame, textvariable=self.css_custom_size, width=30).grid(row=1, column=1, padx=2)
        
        # 生成按钮
        self.gen_css_preview_btn = ttk.Button(container, text="生成预览", command=self.start_css_preview_thread)
        self.gen_css_preview_btn.pack(pady=10)
        
    def load_css_example(self, num):
        """加载CSS示例"""
        examples = {
            1: """width: 100px;
height: 100px;
background-color: red;
border-radius: 50%;
border: 2px solid black;""",
            2: """width: 100px;
height: 40px;
background-color: #4CAF50;
color: white;
text-align: center;
line-height: 40px;
border-radius: 5px;
box-shadow: 0 2px 5px rgba(0,0,0,0.3);""",
            3: """width: 100px;
height: 100px;
background: linear-gradient(45deg, #ff0000, #ffff00);
border-radius: 10px;""",
            4: """width: 100px;
height: 100px;
background-color: white;
box-shadow: 5px 5px 10px rgba(0,0,0,0.5);
border-radius: 0;"""
        }
        
        self.css_text.delete("1.0", tk.END)
        self.css_text.insert("1.0", examples.get(num, ""))
        
    def setup_matplotlib_tab(self):
        """设置Matplotlib绘图转图标标签页"""
        container = ttk.Frame(self.matplotlib_tab)
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 图表类型选择
        frame = ttk.LabelFrame(container, text="1. 图表类型")
        frame.pack(fill=tk.X, pady=(0, 5))
        
        self.matplotlib_type = tk.StringVar(value="折线图")
        types = ["折线图", "柱状图", "饼图", "散点图", "雷达图", "面积图"]
        ttk.Combobox(frame, textvariable=self.matplotlib_type, values=types, width=15).grid(row=0, column=0, padx=2)
        
        # 图表数据输入
        frame = ttk.LabelFrame(container, text="2. 图表数据")
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        self.matplotlib_data = tk.Text(frame, wrap=tk.WORD, height=8)
        scrollbar = ttk.Scrollbar(frame, command=self.matplotlib_data.yview)
        self.matplotlib_data.configure(yscrollcommand=scrollbar.set)
        
        self.matplotlib_data.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 示例数据按钮
        example_frame = ttk.Frame(container)
        example_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(example_frame, text="示例1: 简单数据", command=lambda: self.load_matplotlib_example(1)).pack(side=tk.LEFT, padx=2)
        ttk.Button(example_frame, text="示例2: 多系列", command=lambda: self.load_matplotlib_example(2)).pack(side=tk.LEFT, padx=2)
        ttk.Button(example_frame, text="示例3: 随机数据", command=lambda: self.load_matplotlib_example(3)).pack(side=tk.LEFT, padx=2)
        
        # 图表样式设置
        frame = ttk.LabelFrame(container, text="3. 图表样式")
        frame.pack(fill=tk.X, pady=(0, 5))
        
        # 背景颜色
        ttk.Label(frame, text="背景颜色:").grid(row=0, column=0, padx=2, sticky=tk.W)
        self.matplotlib_bg_color = tk.StringVar(value="#FFFFFF")
        ttk.Button(frame, text="选择...", command=lambda: self.choose_color(self.matplotlib_bg_color),
                  width=8).grid(row=0, column=1, padx=2)
        
        # 透明度
        ttk.Label(frame, text="透明度:").grid(row=0, column=2, padx=2, sticky=tk.W)
        self.matplotlib_alpha = tk.DoubleVar(value=1.0)
        ttk.Scale(frame, from_=0.0, to=1.0, variable=self.matplotlib_alpha,
                 orient=tk.HORIZONTAL, length=120).grid(row=0, column=3, padx=2)
        
        # 尺寸设置
        frame = ttk.LabelFrame(container, text="4. 图标尺寸设置")
        frame.pack(fill=tk.X, pady=(0, 5))
        
        # 预设尺寸
        ttk.Label(frame, text="预设尺寸:").grid(row=0, column=0, padx=2, sticky=tk.W)
        self.matplotlib_preset_sizes = tk.StringVar(value="16,24,32,48,64,128,256")
        ttk.Entry(frame, textvariable=self.matplotlib_preset_sizes, width=30).grid(row=0, column=1, padx=2)
        
        # 自定义尺寸
        ttk.Label(frame, text="自定义尺寸:").grid(row=1, column=0, padx=2, sticky=tk.W)
        self.matplotlib_custom_size = tk.StringVar()
        ttk.Entry(frame, textvariable=self.matplotlib_custom_size, width=30).grid(row=1, column=1, padx=2)
        
        # 生成按钮
        self.gen_matplotlib_preview_btn = ttk.Button(container, text="生成预览", command=self.start_matplotlib_preview_thread)
        self.gen_matplotlib_preview_btn.pack(pady=10)
        
    def load_matplotlib_example(self, num):
        """加载Matplotlib示例数据"""
        examples = {
            1: """x = [1, 2, 3, 4, 5]
y = [2, 3, 5, 7, 11]""",
            2: """x = ['A', 'B', 'C', 'D']
y1 = [10, 20, 30, 40]
y2 = [15, 25, 35, 45]""",
            3: """import numpy as np
x = np.linspace(0, 10, 100)
y = np.sin(x) + np.random.normal(0, 0.1, 100)"""
        }
        
        self.matplotlib_data.delete("1.0", tk.END)
        self.matplotlib_data.insert("1.0", examples.get(num, ""))
        
    def setup_preview_section(self):
        """设置预览和保存区域 - 优化版"""
        self.final_frame = ttk.LabelFrame(self.main_frame, text="最终预览和保存", padding=5)
        self.final_frame.grid(row=3, column=0, sticky="nsew", pady=(5, 0))
        
        # 配置网格权重
        self.final_frame.columnconfigure(0, weight=1)
        self.final_frame.rowconfigure(0, weight=1)  # 给预览区域最大权重
        
        # 预览容器
        preview_container = ttk.Frame(self.final_frame)
        preview_container.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
        preview_container.columnconfigure(0, weight=1)
        preview_container.rowconfigure(0, weight=1)
        
        # 水平和垂直滚动条
        self.canvas_scroll_y = ttk.Scrollbar(preview_container, orient=tk.VERTICAL)
        self.canvas_scroll_y.grid(row=0, column=1, sticky="ns")
        
        self.canvas_scroll_x = ttk.Scrollbar(preview_container, orient=tk.HORIZONTAL)
        self.canvas_scroll_x.grid(row=1, column=0, sticky="ew")
        
        # 预览画布
        self.preview_canvas = tk.Canvas(preview_container, bg='white',
                                    yscrollcommand=self.canvas_scroll_y.set,
                                    xscrollcommand=self.canvas_scroll_x.set)
        self.preview_canvas.grid(row=0, column=0, sticky="nsew")
        
        self.canvas_scroll_y.config(command=self.preview_canvas.yview)
        self.canvas_scroll_x.config(command=self.preview_canvas.xview)
        
        # 底部控制区域
        control_frame = ttk.Frame(self.final_frame)
        control_frame.grid(row=1, column=0, sticky="ew")
        
        # 实时预览
        preview_label = ttk.Label(control_frame, text="实时预览:")
        preview_label.pack(side=tk.LEFT, padx=(5, 0))
        
        self.realtime_preview = tk.Canvas(control_frame, width=60, height=60, bg='white')
        self.realtime_preview.pack(side=tk.LEFT, padx=5)
        
        # 保存控件
        self.save_btn = ttk.Button(control_frame, text="保存图标", command=self.save_icon, state=tk.DISABLED)
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = ttk.Button(control_frame, text="清除预览", command=self.clear_preview)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        # 输出格式选择
        ttk.Label(control_frame, text="输出格式:").pack(side=tk.LEFT, padx=(10, 2))
        self.output_format = tk.StringVar(value="ICO (多尺寸)")
        formats = ["ICO (多尺寸)", "PNG", "JPG", "WebP"]
        ttk.Combobox(control_frame, textvariable=self.output_format, values=formats, width=12).pack(side=tk.LEFT)
        
        # 尺寸显示
        self.sizes_label = ttk.Label(control_frame, text="包含尺寸: 无")
        self.sizes_label.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

    def setup_status_bar(self):
        """设置状态栏"""
        self.status_bar = ttk.Label(self.root, text="准备就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
    def check_image_input(self, *args):
        """检查图片输入是否有效"""
        if self.image_path.get() and os.path.isfile(self.image_path.get()):
            self.gen_preview_btn['state'] = tk.NORMAL
            self.update_realtime_preview()
        else:
            self.gen_preview_btn['state'] = tk.DISABLED
    
    def choose_color(self, color_var, callback=None):
        """打开颜色选择对话框"""
        color = colorchooser.askcolor(title="选择颜色", initialcolor=color_var.get())
        if color[1]:
            color_var.set(color[1])
            if callback:
                callback()
    
    def parse_sizes(self, preset_sizes, custom_sizes):
        """解析尺寸字符串为整数列表"""
        sizes = []
        
        # 添加预设尺寸
        for size in preset_sizes.split(","):
            try:
                size = int(size.strip())
                if 8 <= size <= 512:  # 合理的限制范围
                    sizes.append(size)
            except ValueError:
                continue
        
        # 添加自定义尺寸
        for size in custom_sizes.split(","):
            try:
                size = int(size.strip())
                if 8 <= size <= 512 and size not in sizes:
                    sizes.append(size)
            except ValueError:
                continue
        
        # 去重并排序
        return sorted(list(set(sizes)))
    
    def start_image_preview_thread(self):
        """启动图片预览线程"""
        if not self.image_path.get() or not os.path.isfile(self.image_path.get()):
            messagebox.showerror("错误", "请选择有效的图片文件")
            return
        
        sizes = self.parse_sizes(self.preset_sizes.get(), self.custom_size.get())
        if not sizes:
            messagebox.showerror("错误", "请输入有效的尺寸")
            return
        
        # 更新尺寸定制表格
        if self.customize_sizes.get():
            self.update_size_table()
        
        # 禁用按钮显示进度条
        self.gen_preview_btn['state'] = tk.DISABLED
        self.progress_bar.grid(row=2, column=0, sticky="ew", pady=5)
        self.progress_bar.grid()  # 显示进度条
        self.progress_bar['maximum'] = len(sizes)
        self.progress_bar['value'] = 0
        
        # 启动线程
        thread = threading.Thread(
            target=self.generate_image_preview,
            args=(sizes,),
            daemon=True
        )
        thread.start()
    
    def generate_image_preview(self, sizes):
        """生成图片预览 (在后台线程中运行)"""
        try:
            # 加载原始图片
            img = Image.open(self.image_path.get())
            
            # 应用全局调整
            if self.brightness.get() != 1.0 or self.contrast.get() != 1.0 or self.saturation.get() != 1.0:
                if self.brightness.get() != 1.0:
                    enhancer = ImageEnhance.Brightness(img)
                    img = enhancer.enhance(self.brightness.get())
                if self.contrast.get() != 1.0:
                    enhancer = ImageEnhance.Contrast(img)
                    img = enhancer.enhance(self.contrast.get())
                if self.saturation.get() != 1.0:
                    enhancer = ImageEnhance.Color(img)
                    img = enhancer.enhance(self.saturation.get())
            
            # 应用效果
            effect = self.effect_var.get()
            if effect == "模糊":
                img = img.filter(ImageFilter.BLUR)
            elif effect == "轮廓":
                img = img.filter(ImageFilter.CONTOUR)
            elif effect == "锐化":
                img = img.filter(ImageFilter.SHARPEN)
            elif effect == "浮雕":
                img = img.filter(ImageFilter.EMBOSS)
            elif effect == "边缘增强":
                img = img.filter(ImageFilter.EDGE_ENHANCE)
            elif effect == "平滑":
                img = img.filter(ImageFilter.SMOOTH)
            elif effect == "细节增强":
                img = img.filter(ImageFilter.DETAIL)
            elif effect == "反色":
                img = ImageOps.invert(img)
            elif effect == "黑白":
                img = img.convert("L")
            elif effect == "棕褐色":
                img = self.apply_sepia(img)
            elif effect == "油画":
                img = self.apply_oil_painting(img)
            elif effect == "像素化":
                img = self.apply_pixelate(img)
            elif effect == "高斯模糊":
                img = img.filter(ImageFilter.GaussianBlur(radius=2))
            elif effect == "查找边缘":
                img = img.filter(ImageFilter.FIND_EDGES)
            
            # 生成图标
            icons = []
            for i, size in enumerate(sizes):
                # 应用尺寸特定的调整
                if self.customize_sizes.get() and size in self.size_settings:
                    settings = self.size_settings[size]
                    temp_img = img.copy()
                    
                    if settings['brightness'].get() != 1.0:
                        enhancer = ImageEnhance.Brightness(temp_img)
                        temp_img = enhancer.enhance(settings['brightness'].get())
                    
                    if settings['contrast'].get() != 1.0:
                        enhancer = ImageEnhance.Contrast(temp_img)
                        temp_img = enhancer.enhance(settings['contrast'].get())
                    
                    if settings['saturation'].get() != 1.0:
                        enhancer = ImageEnhance.Color(temp_img)
                        temp_img = enhancer.enhance(settings['saturation'].get())
                    
                    if settings['alpha'].get() < 1.0:
                        temp_img = self.apply_alpha(temp_img, settings['alpha'].get())
                    
                    icon = temp_img.resize((size, size), Image.Resampling.LANCZOS)
                else:
                    # 应用全局透明度
                    if self.alpha.get() < 1.0:
                        temp_img = self.apply_alpha(img, self.alpha.get())
                        icon = temp_img.resize((size, size), Image.Resampling.LANCZOS)
                    else:
                        icon = img.resize((size, size), Image.Resampling.LANCZOS)
                
                # 应用形状蒙版
                icon = self.apply_shape_mask(icon)
                
                icons.append(icon)
                
                # 更新进度
                self.progress_queue.put(i + 1)
            
            self.current_icon = icons
            
            # 完成处理
            self.progress_queue.put("done")
            
        except Exception as e:
            self.progress_queue.put(("error", str(e)))
    
    def apply_sepia(self, img):
        """应用棕褐色效果"""
        width, height = img.size
        pixels = img.load()
        
        for py in range(height):
            for px in range(width):
                r, g, b = img.getpixel((px, py))[:3]
                
                tr = int(0.393 * r + 0.769 * g + 0.189 * b)
                tg = int(0.349 * r + 0.686 * g + 0.168 * b)
                tb = int(0.272 * r + 0.534 * g + 0.131 * b)
                
                pixels[px, py] = (
                    min(255, tr),
                    min(255, tg),
                    min(255, tb)
                )
        
        return img
    
    def apply_oil_painting(self, img, brush_size=3, roughness=30):
        """应用油画效果"""
        img = img.convert("RGB")
        width, height = img.size
        pixels = img.load()
        
        for y in range(height):
            for x in range(width):
                # 获取画笔区域内的像素
                x1 = max(0, x - brush_size)
                y1 = max(0, y - brush_size)
                x2 = min(width, x + brush_size + 1)
                y2 = min(height, y + brush_size + 1)
                
                # 统计颜色出现频率
                color_counts = {}
                for i in range(x1, x2):
                    for j in range(y1, y2):
                        r, g, b = pixels[i, j]
                        # 量化颜色以减少颜色数量
                        r = r // roughness * roughness
                        g = g // roughness * roughness
                        b = b // roughness * roughness
                        color = (r, g, b)
                        color_counts[color] = color_counts.get(color, 0) + 1
                
                # 找到出现频率最高的颜色
                if color_counts:
                    most_common = max(color_counts.items(), key=lambda x: x[1])[0]
                    pixels[x, y] = most_common
        
        return img
    
    def apply_pixelate(self, img, pixel_size=8):
        """应用像素化效果"""
        width, height = img.size
        
        # 缩小图像
        small = img.resize(
            (width // pixel_size, height // pixel_size),
            resample=Image.Resampling.NEAREST
        )
        
        # 放大回原始尺寸
        result = small.resize(
            (width, height),
            resample=Image.Resampling.NEAREST
        )
        
        return result
    
    def apply_alpha(self, img, alpha):
        """应用透明度到图像"""
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # 创建一个新的alpha通道
        alpha_channel = img.split()[3]
        alpha_channel = ImageEnhance.Brightness(alpha_channel).enhance(alpha)
        
        # 合并回图像
        r, g, b, _ = img.split()
        img = Image.merge('RGBA', (r, g, b, alpha_channel))
        
        return img
    
    def apply_shape_mask(self, img):
        """应用形状蒙版到图像"""
        shape = self.shape_var.get()
        if shape == "方形":
            return img
        
        # 创建蒙版
        mask = Image.new('L', img.size, 0)
        draw = ImageDraw.Draw(mask)
        
        if shape == "圆形":
            draw.ellipse((0, 0, img.size[0], img.size[1]), fill=255)
        elif shape == "圆角矩形":
            radius = self.radius.get()
            draw.rounded_rectangle((0, 0, img.size[0], img.size[1]), radius=radius, fill=255)
        elif shape == "星形":
            points = self.calculate_star_points(5, img.size[0]//2, img.size[1]//2, img.size[0]//2-5, img.size[0]//4)
            draw.polygon(points, fill=255)
        elif shape == "心形":
            points = self.calculate_heart_points(img.size[0]//2, img.size[1]//2, img.size[0]//2-5)
            draw.polygon(points, fill=255)
        elif shape == "三角形":
            points = [img.size[0]//2, 5, img.size[0]-5, img.size[1]-5, 5, img.size[1]-5]
            draw.polygon(points, fill=255)
        
        # 应用蒙版
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        img.putalpha(mask)
        return img
    
    def start_text_preview_thread(self):
        """启动文字预览线程"""
        if not self.text_var.get():
            messagebox.showerror("错误", "请输入文字内容")
            return
        
        sizes = self.parse_sizes(self.text_preset_sizes.get(), self.text_custom_size.get())
        if not sizes:
            messagebox.showerror("错误", "请输入有效的尺寸")
            return
        
        # 禁用按钮显示进度条
        self.gen_text_preview_btn['state'] = tk.DISABLED
        self.progress_bar.grid(row=2, column=0, sticky="ew", pady=5)
        self.progress_bar.grid()  # 显示进度条
        self.progress_bar['maximum'] = len(sizes)
        self.progress_bar['value'] = 0
        
        # 启动线程
        thread = threading.Thread(
            target=self.generate_text_preview,
            args=(sizes,),
            daemon=True
        )
        thread.start()
    
    def generate_text_preview(self, sizes):
        """生成文字预览 (在后台线程中运行)"""
        try:
            text = self.text_var.get()
            icons = []
            
            for i, size in enumerate(sizes):
                # 创建背景
                if self.bg_type.get() == "透明":
                    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
                elif self.bg_type.get() == "渐变":
                    img = self.create_gradient_image(size)
                else:  # 纯色
                    img = Image.new("RGB", (size, size), self.bg_color.get())
                
                # 应用背景透明度
                if self.bg_alpha.get() < 1.0 and img.mode == 'RGBA':
                    alpha = img.split()[3]
                    alpha = ImageEnhance.Brightness(alpha).enhance(self.bg_alpha.get())
                    r, g, b, _ = img.split()
                    img = Image.merge('RGBA', (r, g, b, alpha))
                
                draw = ImageDraw.Draw(img)
                
                # 获取字体
                try:
                    font_size = int(self.font_size.get() * (size/256))
                    font = ImageFont.truetype(self.font_family.get(), font_size)
                except:
                    font = ImageFont.load_default()
                
                # 计算文字位置
                try:
                    # 新版Pillow使用textbbox
                    bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                except AttributeError:
                    try:
                        # 旧版使用textsize
                        text_width, text_height = draw.textsize(text, font=font)
                    except AttributeError:
                        # 如果都不支持，使用字体对象的getsize
                        text_width, text_height = font.getsize(text)
                
                position = ((size - text_width) // 2, (size - text_height) // 2)
                
                # 绘制文字
                draw.text(position, text, fill=self.text_color.get(), font=font)
                
                # 应用形状蒙版
                icon = self.apply_shape_mask(img)
                icons.append(icon)
                
                # 更新进度
                self.progress_queue.put(i + 1)
            
            self.current_icon = icons
            self.progress_queue.put("done")
            
        except Exception as e:
            self.progress_queue.put(("error", str(e)))
    
    def start_svg_preview_thread(self):
        """启动SVG预览线程"""
        svg_code = self.svg_text.get("1.0", tk.END).strip()
        if not svg_code:
            messagebox.showerror("错误", "请输入SVG代码")
            return
        
        sizes = self.parse_sizes(self.svg_preset_sizes.get(), self.svg_custom_size.get())
        if not sizes:
            messagebox.showerror("错误", "请输入有效的尺寸")
            return
        
        # 禁用按钮显示进度条
        self.gen_svg_preview_btn['state'] = tk.DISABLED
        self.progress_bar.grid(row=2, column=0, sticky="ew", pady=5)
        self.progress_bar.grid()  # 显示进度条
        self.progress_bar['maximum'] = len(sizes)
        self.progress_bar['value'] = 0
        
        # 启动线程
        thread = threading.Thread(
            target=self.generate_svg_preview,
            args=(svg_code, sizes),
            daemon=True
        )
        thread.start()
    
    def generate_svg_preview(self, svg_code, sizes):
        """生成SVG预览 (在后台线程中运行)"""
        try:
            icons = []
            
            for i, size in enumerate(sizes):
                try:
                    # 方法1：使用cairosvg直接渲染
                    output = BytesIO()
                    cairosvg.svg2png(bytestring=svg_code.encode('utf-8'), 
                                    write_to=output,
                                    output_width=size,
                                    output_height=size)
                    img = Image.open(output)
                except Exception as e:
                    # 方法1失败，尝试方法2：使用reportlab的备用方法
                    warnings.warn(f"使用cairosvg渲染失败，尝试备用方法: {str(e)}")
                    try:
                        # 将SVG代码保存到临时文件
                        temp_svg = os.path.join(os.getcwd(), f"temp_{size}.svg")
                        with open(temp_svg, "w", encoding="utf-8") as f:
                            f.write(svg_code)
                        
                        # 转换为PNG
                        drawing = svg2rlg(temp_svg)
                        img = renderPM.drawToPIL(drawing, dpi=72 * size / drawing.width)
                        os.remove(temp_svg)
                    except Exception as e:
                        # 方法2失败，尝试方法3：使用Pillow的简单SVG渲染
                        warnings.warn(f"备用方法也失败，使用简单渲染: {str(e)}")
                        img = Image.new("RGBA", (size, size), (255, 255, 255, 0))
                        draw = ImageDraw.Draw(img)
                        draw.text((10, 10), "SVG预览", fill="black")
                        # 尝试简单解析SVG中的矩形和圆形
                        try:
                            if "<rect" in svg_code:
                                draw.rectangle([10, 30, size-10, size-10], outline="red")
                            if "<circle" in svg_code:
                                draw.ellipse([10, 30, size-10, size-10], outline="blue")
                        except:
                            pass
                
                # 添加背景
                if self.svg_bg_color.get() != "#FFFFFF" or self.svg_alpha.get() < 1.0:
                    bg = Image.new("RGBA", img.size, self.svg_bg_color.get())
                    if self.svg_alpha.get() < 1.0:
                        alpha = int(255 * self.svg_alpha.get())
                        bg.putalpha(alpha)
                    img = Image.alpha_composite(bg, img.convert("RGBA"))
                
                icons.append(img)
                # 更新进度
                self.progress_queue.put(i + 1)
            
            self.current_icon = icons
            self.progress_queue.put("done")
            
        except Exception as e:
            self.progress_queue.put(("error", str(e)))


    
    def start_emoji_preview_thread(self):
        """启动Emoji预览线程"""
        emoji_char = self.emoji_var.get()
        if not emoji_char:
            messagebox.showerror("错误", "请选择Emoji")
            return
        
        sizes = self.parse_sizes(self.emoji_preset_sizes.get(), self.emoji_custom_size.get())
        if not sizes:
            messagebox.showerror("错误", "请输入有效的尺寸")
            return
        
        # 禁用按钮显示进度条
        self.gen_emoji_preview_btn['state'] = tk.DISABLED
        self.progress_bar.grid(row=2, column=0, sticky="ew", pady=5)
        self.progress_bar.grid()  # 显示进度条
        self.progress_bar['maximum'] = len(sizes)
        self.progress_bar['value'] = 0
        
        # 启动线程
        thread = threading.Thread(
            target=self.generate_emoji_preview,
            args=(emoji_char, sizes),
            daemon=True
        )
        thread.start()
    
    def generate_emoji_preview(self, emoji_char, sizes):
        """生成Emoji预览 (在后台线程中运行)"""
        if not EMOJI_SUPPORT:
            self.progress_queue.put(("error", "需要安装emoji模块才能使用此功能"))
            return
        try:
            icons = []
            
            for i, size in enumerate(sizes):
                # 创建背景
                if self.emoji_bg_color.get() == "透明":
                    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
                else:
                    img = Image.new("RGB", (size, size), self.emoji_bg_color.get())
                
                # 应用背景透明度
                if self.emoji_alpha.get() < 1.0 and img.mode == 'RGBA':
                    alpha = img.split()[3]
                    alpha = ImageEnhance.Brightness(alpha).enhance(self.emoji_alpha.get())
                    r, g, b, _ = img.split()
                    img = Image.merge('RGBA', (r, g, b, alpha))
                
                draw = ImageDraw.Draw(img)
                
                # 获取字体
                try:
                    font_size = int(size * 0.8)  # Emoji通常占据大部分空间
                    font = ImageFont.truetype("seguiemj.ttf", font_size)  # Windows Emoji字体
                except:
                    try:
                        font = ImageFont.truetype("Apple Color Emoji.ttf", font_size)  # macOS
                    except:
                        try:
                            font = ImageFont.truetype("NotoColorEmoji.ttf", font_size)  # Linux
                        except:
                            font = ImageFont.load_default()
                
                # 计算文字位置
                try:
                    bbox = draw.textbbox((0, 0), emoji_char, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                except AttributeError:
                    try:
                        text_width, text_height = draw.textsize(emoji_char, font=font)
                    except AttributeError:
                        text_width, text_height = font.getsize(emoji_char)
                
                position = ((size - text_width) // 2, (size - text_height) // 2)
                
                # 绘制Emoji
                draw.text(position, emoji_char, font=font, embedded_color=True)
                
                icons.append(img)
                
                # 更新进度
                self.progress_queue.put(i + 1)
            
            self.current_icon = icons
            self.progress_queue.put("done")
            
        except Exception as e:
            self.progress_queue.put(("error", str(e)))
    
    def start_unicode_preview_thread(self):
        """启动Unicode符号预览线程"""
        unicode_char = self.unicode_var.get()
        if not unicode_char:
            messagebox.showerror("错误", "请选择Unicode符号")
            return
        
        sizes = self.parse_sizes(self.unicode_preset_sizes.get(), self.unicode_custom_size.get())
        if not sizes:
            messagebox.showerror("错误", "请输入有效的尺寸")
            return
        
        # 禁用按钮显示进度条
        self.gen_unicode_preview_btn['state'] = tk.DISABLED
        self.progress_bar.grid(row=2, column=0, sticky="ew", pady=5)
        self.progress_bar.grid()  # 显示进度条
        self.progress_bar['maximum'] = len(sizes)
        self.progress_bar['value'] = 0
        
        # 启动线程
        thread = threading.Thread(
            target=self.generate_unicode_preview,
            args=(unicode_char, sizes),
            daemon=True
        )
        thread.start()
    
    def generate_unicode_preview(self, unicode_char, sizes):
        """生成Unicode符号预览 (在后台线程中运行)"""
        try:
            icons = []
            
            for i, size in enumerate(sizes):
                # 创建背景
                if self.unicode_bg_color.get() == "透明":
                    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
                else:
                    img = Image.new("RGB", (size, size), self.unicode_bg_color.get())
                
                # 应用背景透明度
                if self.unicode_alpha.get() < 1.0 and img.mode == 'RGBA':
                    alpha = img.split()[3]
                    alpha = ImageEnhance.Brightness(alpha).enhance(self.unicode_alpha.get())
                    r, g, b, _ = img.split()
                    img = Image.merge('RGBA', (r, g, b, alpha))
                
                draw = ImageDraw.Draw(img)
                
                # 获取字体
                try:
                    font_size = int(size * 0.8)
                    font = ImageFont.truetype(self.unicode_font_family.get(), font_size)
                except:
                    font = ImageFont.load_default()
                
                # 计算文字位置
                try:
                    bbox = draw.textbbox((0, 0), unicode_char, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                except AttributeError:
                    try:
                        text_width, text_height = draw.textsize(unicode_char, font=font)
                    except AttributeError:
                        text_width, text_height = font.getsize(unicode_char)
                
                position = ((size - text_width) // 2, (size - text_height) // 2)
                
                # 绘制Unicode符号
                draw.text(position, unicode_char, fill=self.unicode_font_color.get(), font=font)
                
                icons.append(img)
                
                # 更新进度
                self.progress_queue.put(i + 1)
            
            self.current_icon = icons
            self.progress_queue.put("done")
            
        except Exception as e:
            self.progress_queue.put(("error", str(e)))
    
    def start_css_preview_thread(self):
        """启动CSS样式预览线程"""
        css_code = self.css_text.get("1.0", tk.END).strip()
        if not css_code:
            messagebox.showerror("错误", "请输入CSS样式")
            return
        
        sizes = self.parse_sizes(self.css_preset_sizes.get(), self.css_custom_size.get())
        if not sizes:
            messagebox.showerror("错误", "请输入有效的尺寸")
            return
        
        # 禁用按钮显示进度条
        self.gen_css_preview_btn['state'] = tk.DISABLED
        self.progress_bar.grid(row=2, column=0, sticky="ew", pady=5)
        self.progress_bar.grid()  # 显示进度条
        self.progress_bar['maximum'] = len(sizes)
        self.progress_bar['value'] = 0
        
        # 启动线程
        thread = threading.Thread(
            target=self.generate_css_preview,
            args=(css_code, sizes),
            daemon=True
        )
        thread.start()
    
    def generate_css_preview(self, css_code, sizes):
        """生成CSS样式预览 (在后台线程中运行)"""
        try:
            icons = []
            
            # 解析CSS
            styles = self.parse_css(css_code)
            
            for i, size in enumerate(sizes):
                # 创建图像
                img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                
                # 应用背景颜色或渐变
                if "background-color" in styles:
                    bg_color = styles["background-color"]
                    draw.rectangle([0, 0, size, size], fill=bg_color)
                elif "background" in styles and "gradient" in styles["background"]:
                    # 简单处理线性渐变
                    colors = re.findall(r"rgb\((\d+),\s*(\d+),\s*(\d+)\)", styles["background"])
                    if len(colors) >= 2:
                        color1 = tuple(map(int, colors[0]))
                        color2 = tuple(map(int, colors[1]))
                        
                        if "to right" in styles["background"]:
                            # 水平渐变
                            for x in range(size):
                                ratio = x / size
                                r = int(color1[0] + (color2[0] - color1[0]) * ratio)
                                g = int(color1[1] + (color2[1] - color1[1]) * ratio)
                                b = int(color1[2] + (color2[2] - color1[2]) * ratio)
                                draw.line([(x, 0), (x, size)], fill=(r, g, b))
                        else:
                            # 垂直渐变
                            for y in range(size):
                                ratio = y / size
                                r = int(color1[0] + (color2[0] - color1[0]) * ratio)
                                g = int(color1[1] + (color2[1] - color1[1]) * ratio)
                                b = int(color1[2] + (color2[2] - color1[2]) * ratio)
                                draw.line([(0, y), (size, y)], fill=(r, g, b))
                
                # 应用边框
                if "border" in styles:
                    border_parts = styles["border"].split()
                    if len(border_parts) >= 3:
                        border_width = int(border_parts[0].replace("px", ""))
                        border_style = border_parts[1]
                        border_color = border_parts[2]
                        
                        if border_style != "none":
                            draw.rectangle([0, 0, size-1, size-1], outline=border_color, width=border_width)
                
                # 应用圆角
                if "border-radius" in styles:
                    radius = int(styles["border-radius"].replace("px", "").replace("%", ""))
                    if "%" in styles["border-radius"]:
                        radius = int(size * radius / 100)
                    
                    # 创建圆角蒙版
                    mask = Image.new("L", (size, size), 0)
                    mask_draw = ImageDraw.Draw(mask)
                    mask_draw.rounded_rectangle([0, 0, size, size], radius=radius, fill=255)
                    
                    # 应用蒙版
                    img.putalpha(mask)
                
                icons.append(img)
                
                # 更新进度
                self.progress_queue.put(i + 1)
            
            self.current_icon = icons
            self.progress_queue.put("done")
            
        except Exception as e:
            self.progress_queue.put(("error", str(e)))
    
    #def parse_css(self, css_code):
    #    """解析CSS代码为字典"""
    #    styles = {}
    #    sheet = cssutils.parseString(css_code)
    #    
    #    for rule in sheet:
    #        if rule.type == rule.STYLE_RULE:
    #            for property in rule.style:
    #                styles[property.name] = property.value
    #    
    #    return styles

    def parse_css(self, css_code):
        """简单的CSS属性解析器"""
        styles = {}
        for line in css_code.split(';'):
            line = line.strip()
            if ':' in line:
                prop, value = line.split(':', 1)
                styles[prop.strip()] = value.strip()
        return styles
    
    def start_matplotlib_preview_thread(self):
        """启动Matplotlib预览线程"""
        code = self.matplotlib_data.get("1.0", tk.END).strip()
        if not code:
            messagebox.showerror("错误", "请输入图表数据")
            return
        
        sizes = self.parse_sizes(self.matplotlib_preset_sizes.get(), self.matplotlib_custom_size.get())
        if not sizes:
            messagebox.showerror("错误", "请输入有效的尺寸")
            return
        
        # 禁用按钮显示进度条
        self.gen_matplotlib_preview_btn['state'] = tk.DISABLED
        self.progress_bar.grid(row=2, column=0, sticky="ew", pady=5)
        self.progress_bar.grid()  # 显示进度条
        self.progress_bar['maximum'] = len(sizes)
        self.progress_bar['value'] = 0
        
        # 启动线程
        thread = threading.Thread(
            target=self.generate_matplotlib_preview,
            args=(code, sizes),
            daemon=True
        )
        thread.start()
    
    def generate_matplotlib_preview(self, code, sizes):
        """生成Matplotlib预览 (在后台线程中运行)"""
        try:
            icons = []
            
            # 准备绘图环境
            plt.style.use('ggplot')
            plt.rcParams['axes.facecolor'] = self.matplotlib_bg_color.get()
            
            # 执行用户代码
            local_vars = {}
            exec(code, globals(), local_vars)
            
            # 获取数据
            x = local_vars.get('x', [1, 2, 3, 4, 5])
            y = local_vars.get('y', [2, 3, 5, 7, 11])
            y1 = local_vars.get('y1', None)
            y2 = local_vars.get('y2', None)
            
            for i, size in enumerate(sizes):
                # 创建图表
                fig, ax = plt.subplots(figsize=(size/100, size/100), dpi=100)
                
                # 根据类型绘制图表
                chart_type = self.matplotlib_type.get()
                if chart_type == "折线图":
                    ax.plot(x, y, marker='o')
                    if y1 is not None:
                        ax.plot(x, y1, marker='o')
                elif chart_type == "柱状图":
                    ax.bar(x, y)
                    if y1 is not None:
                        ax.bar(x, y1, bottom=y)
                elif chart_type == "饼图":
                    ax.pie(y, labels=x, autopct='%1.1f%%')
                elif chart_type == "散点图":
                    ax.scatter(x, y)
                elif chart_type == "雷达图":
                    theta = np.linspace(0, 2*np.pi, len(x), endpoint=False)
                    ax.plot(theta, y)
                    ax.fill(theta, y, alpha=0.25)
                    ax.set_xticks(theta)
                    ax.set_xticklabels(x)
                elif chart_type == "面积图":
                    ax.stackplot(x, y)
                
                # 调整图表
                ax.set_facecolor(self.matplotlib_bg_color.get())
                fig.patch.set_alpha(self.matplotlib_alpha.get())
                
                # 转换为PIL图像
                canvas = FigureCanvasAgg(fig)
                canvas.draw()
                
                buf = canvas.buffer_rgba()
                img = Image.fromarray(np.asarray(buf))
                
                icons.append(img)
                
                # 关闭图表释放内存
                plt.close(fig)
                
                # 更新进度
                self.progress_queue.put(i + 1)
            
            self.current_icon = icons
            self.progress_queue.put("done")
            
        except Exception as e:
            self.progress_queue.put(("error", str(e)))
    
    def create_gradient_image(self, size):
        """创建渐变背景图像"""
        img = Image.new("RGB", (size, size))
        draw = ImageDraw.Draw(img)
        
        color1 = self.bg_color.get()
        color2 = self.bg_color2.get()
        
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        r1, g1, b1 = hex_to_rgb(color1)
        r2, g2, b2 = hex_to_rgb(color2)
        
        direction = self.gradient_dir.get()
        if direction == "水平":
            for x in range(size):
                ratio = x / size
                r = int(r1 + (r2 - r1) * ratio)
                g = int(g1 + (g2 - g1) * ratio)
                b = int(b1 + (b2 - b1) * ratio)
                draw.line([(x, 0), (x, size)], fill=(r, g, b))
        elif direction == "垂直":
            for y in range(size):
                ratio = y / size
                r = int(r1 + (r2 - r1) * ratio)
                g = int(g1 + (g2 - g1) * ratio)
                b = int(b1 + (b2 - b1) * ratio)
                draw.line([(0, y), (size, y)], fill=(r, g, b))
        else:  # 对角
            for y in range(size):
                for x in range(size):
                    ratio = (x + y) / (size * 2)
                    r = int(r1 + (r2 - r1) * ratio)
                    g = int(g1 + (g2 - g1) * ratio)
                    b = int(b1 + (b2 - b1) * ratio)
                    draw.point((x, y), fill=(r, g, b))
        
        return img
    
    def check_progress(self):
        """检查进度队列更新UI"""
        try:
            while True:
                msg = self.progress_queue.get_nowait()
                
                if msg == "done":
                    self.progress_bar.grid_remove()
                    self.show_final_preview()
                    self.save_btn['state'] = tk.NORMAL
                    
                    sizes = [str(img.size[0]) for img in self.current_icon]
                    self.sizes_label.config(text=f"包含尺寸: {', '.join(sizes)}")
                    
                    # 根据当前标签页启用相应的生成按钮
                    current_tab = self.tab_control.index("current")
                    if current_tab == 0:  # 图片标签页
                        self.gen_preview_btn['state'] = tk.NORMAL
                    elif current_tab == 1:  # 文字标签页
                        self.gen_text_preview_btn['state'] = tk.NORMAL
                    elif current_tab == 2:  # SVG标签页
                        self.gen_svg_preview_btn['state'] = tk.NORMAL
                    elif current_tab == 3:  # Emoji标签页
                        self.gen_emoji_preview_btn['state'] = tk.NORMAL
                    elif current_tab == 4:  # Unicode标签页
                        self.gen_unicode_preview_btn['state'] = tk.NORMAL
                    elif current_tab == 5:  # CSS标签页
                        self.gen_css_preview_btn['state'] = tk.NORMAL
                    elif current_tab == 6:  # Matplotlib标签页
                        self.gen_matplotlib_preview_btn['state'] = tk.NORMAL
                    
                    self.status_bar["text"] = "预览生成完成"
                
                elif isinstance(msg, tuple) and msg[0] == "error":
                    self.progress_bar.pack_forget()
                    messagebox.showerror("错误", f"生成预览时出错:\n{msg[1]}")
                    print(f"[DEBUG] 生成预览时出错: {msg[1]}")
                    self.status_bar["text"] = f"错误: {msg[1]}"
                    
                    # 根据当前标签页启用相应的生成按钮
                    current_tab = self.tab_control.index("current")
                    if current_tab == 0:  # 图片标签页
                        self.gen_preview_btn['state'] = tk.NORMAL
                    elif current_tab == 1:  # 文字标签页
                        self.gen_text_preview_btn['state'] = tk.NORMAL
                    elif current_tab == 2:  # SVG标签页
                        self.gen_svg_preview_btn['state'] = tk.NORMAL
                    elif current_tab == 3:  # Emoji标签页
                        self.gen_emoji_preview_btn['state'] = tk.NORMAL
                    elif current_tab == 4:  # Unicode标签页
                        self.gen_unicode_preview_btn['state'] = tk.NORMAL
                    elif current_tab == 5:  # CSS标签页
                        self.gen_css_preview_btn['state'] = tk.NORMAL
                    elif current_tab == 6:  # Matplotlib标签页
                        self.gen_matplotlib_preview_btn['state'] = tk.NORMAL
                
                else:  # 更新进度
                    self.progress_bar['value'] = msg
                    self.status_bar["text"] = f"正在生成预览... ({msg}/{self.progress_bar['maximum']})"
        
        except:
            pass
        
        self.root.after(100, self.check_progress)
    
    def update_realtime_preview(self, *args):
        """更新实时预览小窗口"""
        if not hasattr(self, 'realtime_preview'):
            return
        
        # 清除旧预览
        self.realtime_preview.delete("all")
        
        try:
            current_tab = self.tab_control.index("current")
            
            if current_tab == 0:  # 图片标签页
                if not self.image_path.get() or not os.path.isfile(self.image_path.get()):
                    return
                
                # 创建缩小的预览图
                img = Image.open(self.image_path.get())
                img.thumbnail((80, 80))
                
                # 应用调整
                if self.brightness.get() != 1.0:
                    enhancer = ImageEnhance.Brightness(img)
                    img = enhancer.enhance(self.brightness.get())
                
                if self.contrast.get() != 1.0:
                    enhancer = ImageEnhance.Contrast(img)
                    img = enhancer.enhance(self.contrast.get())
                
                if self.saturation.get() != 1.0:
                    enhancer = ImageEnhance.Color(img)
                    img = enhancer.enhance(self.saturation.get())
                
                if self.alpha.get() < 1.0:
                    img = self.apply_alpha(img, self.alpha.get())
                
                # 应用效果
                effect = self.effect_var.get()
                if effect == "模糊":
                    img = img.filter(ImageFilter.BLUR)
                elif effect == "轮廓":
                    img = img.filter(ImageFilter.CONTOUR)
                elif effect == "锐化":
                    img = img.filter(ImageFilter.SHARPEN)
                elif effect == "浮雕":
                    img = img.filter(ImageFilter.EMBOSS)
                elif effect == "边缘增强":
                    img = img.filter(ImageFilter.EDGE_ENHANCE)
                elif effect == "平滑":
                    img = img.filter(ImageFilter.SMOOTH)
                elif effect == "细节增强":
                    img = img.filter(ImageFilter.DETAIL)
                elif effect == "反色":
                    img = ImageOps.invert(img)
                elif effect == "黑白":
                    img = img.convert("L")
                elif effect == "棕褐色":
                    img = self.apply_sepia(img)
                elif effect == "油画":
                    img = self.apply_oil_painting(img)
                elif effect == "像素化":
                    img = self.apply_pixelate(img)
                elif effect == "高斯模糊":
                    img = img.filter(ImageFilter.GaussianBlur(radius=2))
                elif effect == "查找边缘":
                    img = img.filter(ImageFilter.FIND_EDGES)
                
                # 应用形状蒙版
                img = self.apply_shape_mask(img)
                
            elif current_tab == 1:  # 文字标签页
                if not self.text_var.get():
                    return
                
                # 创建文字预览
                size = 80
                if self.bg_type.get() == "透明":
                    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
                elif self.bg_type.get() == "渐变":
                    img = self.create_gradient_image(size)
                else:  # 纯色
                    img = Image.new("RGB", (size, size), self.bg_color.get())
                
                # 应用背景透明度
                if self.bg_alpha.get() < 1.0 and img.mode == 'RGBA':
                    alpha = img.split()[3]
                    alpha = ImageEnhance.Brightness(alpha).enhance(self.bg_alpha.get())
                    r, g, b, _ = img.split()
                    img = Image.merge('RGBA', (r, g, b, alpha))
                
                draw = ImageDraw.Draw(img)
                
                # 获取字体
                try:
                    font_size = int(self.font_size.get() * (size/256))
                    font = ImageFont.truetype(self.font_family.get(), font_size)
                except:
                    font = ImageFont.load_default()
                
                # 计算文字位置
                try:
                    bbox = draw.textbbox((0, 0), self.text_var.get(), font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                except AttributeError:
                    try:
                        text_width, text_height = draw.textsize(self.text_var.get(), font=font)
                    except AttributeError:
                        text_width, text_height = font.getsize(self.text_var.get())
                
                position = ((size - text_width) // 2, (size - text_height) // 2)
                
                # 绘制文字
                draw.text(position, self.text_var.get(), fill=self.text_color.get(), font=font)
                
                # 应用形状蒙版
                img = self.apply_shape_mask(img)
            
            elif current_tab == 2:  # SVG标签页
                svg_code = self.svg_text.get("1.0", tk.END).strip()
                if not svg_code:
                    return
                
                try:
                    # 使用 cairosvg 直接渲染
                    import cairosvg
                    from io import BytesIO
                    
                    output = BytesIO()
                    cairosvg.svg2png(
                        bytestring=svg_code.encode('utf-8'),
                        write_to=output,
                        output_width=80,
                        output_height=80
                    )
                    img = Image.open(output)
                
                    # 添加背景
                    if self.svg_bg_color.get() != "#FFFFFF" or self.svg_alpha.get() < 1.0:
                        bg = Image.new("RGBA", img.size, self.svg_bg_color.get())
                        if self.svg_alpha.get() < 1.0:
                            alpha = int(255 * self.svg_alpha.get())
                            bg.putalpha(alpha)
                        img = Image.alpha_composite(bg, img.convert("RGBA"))
                except Exception as e:
                    print(f"SVG渲染错误: {e}")
                    # 渲染失败时显示错误提示
                    img = Image.new("RGBA", (80, 80), (255, 255, 255, 0))
                    draw = ImageDraw.Draw(img)
                    draw.text((10, 10), "SVG渲染失败", fill="red")
            
            elif current_tab == 3:  # Emoji标签页
                emoji_char = self.emoji_var.get()
                if not emoji_char:
                    return
                
                size = 80
                if self.emoji_bg_color.get() == "透明":
                    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
                else:
                    img = Image.new("RGB", (size, size), self.emoji_bg_color.get())
                
                # 应用背景透明度
                if self.emoji_alpha.get() < 1.0 and img.mode == 'RGBA':
                    alpha = img.split()[3]
                    alpha = ImageEnhance.Brightness(alpha).enhance(self.emoji_alpha.get())
                    r, g, b, _ = img.split()
                    img = Image.merge('RGBA', (r, g, b, alpha))
                
                draw = ImageDraw.Draw(img)
                
                # 获取字体
                try:
                    font_size = int(size * 0.8)
                    font = ImageFont.truetype("seguiemj.ttf", font_size)
                except:
                    try:
                        font = ImageFont.truetype("Apple Color Emoji.ttf", font_size)
                    except:
                        try:
                            font = ImageFont.truetype("NotoColorEmoji.ttf", font_size)
                        except:
                            font = ImageFont.load_default()
                
                # 计算文字位置
                try:
                    bbox = draw.textbbox((0, 0), emoji_char, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                except AttributeError:
                    try:
                        text_width, text_height = draw.textsize(emoji_char, font=font)
                    except AttributeError:
                        text_width, text_height = font.getsize(emoji_char)
                
                position = ((size - text_width) // 2, (size - text_height) // 2)
                
                # 绘制Emoji
                draw.text(position, emoji_char, font=font, embedded_color=True)
            
            elif current_tab == 4:  # Unicode标签页
                unicode_char = self.unicode_var.get()
                if not unicode_char:
                    return
                
                size = 80
                if self.unicode_bg_color.get() == "透明":
                    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
                else:
                    img = Image.new("RGB", (size, size), self.unicode_bg_color.get())
                
                # 应用背景透明度
                if self.unicode_alpha.get() < 1.0 and img.mode == 'RGBA':
                    alpha = img.split()[3]
                    alpha = ImageEnhance.Brightness(alpha).enhance(self.unicode_alpha.get())
                    r, g, b, _ = img.split()
                    img = Image.merge('RGBA', (r, g, b, alpha))
                
                draw = ImageDraw.Draw(img)
                
                # 获取字体
                try:
                    font_size = int(size * 0.8)
                    font = ImageFont.truetype(self.unicode_font_family.get(), font_size)
                except:
                    font = ImageFont.load_default()
                
                # 计算文字位置
                try:
                    bbox = draw.textbbox((0, 0), unicode_char, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                except AttributeError:
                    try:
                        text_width, text_height = draw.textsize(unicode_char, font=font)
                    except AttributeError:
                        text_width, text_height = font.getsize(unicode_char)
                
                position = ((size - text_width) // 2, (size - text_height) // 2)
                
                # 绘制Unicode符号
                draw.text(position, unicode_char, fill=self.unicode_font_color.get(), font=font)
            
            elif current_tab == 5:  # CSS标签页
                css_code = self.css_text.get("1.0", tk.END).strip()
                if not css_code:
                    return
                
                size = 80
                img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                
                # 解析CSS
                styles = self.parse_css(css_code)
                
                # 应用背景颜色或渐变
                if "background-color" in styles:
                    bg_color = styles["background-color"]
                    draw.rectangle([0, 0, size, size], fill=bg_color)
                elif "background" in styles and "gradient" in styles["background"]:
                    # 简单处理线性渐变
                    colors = re.findall(r"rgb\((\d+),\s*(\d+),\s*(\d+)\)", styles["background"])
                    if len(colors) >= 2:
                        color1 = tuple(map(int, colors[0]))
                        color2 = tuple(map(int, colors[1]))
                        
                        if "to right" in styles["background"]:
                            # 水平渐变
                            for x in range(size):
                                ratio = x / size
                                r = int(color1[0] + (color2[0] - color1[0]) * ratio)
                                g = int(color1[1] + (color2[1] - color1[1]) * ratio)
                                b = int(color1[2] + (color2[2] - color1[2]) * ratio)
                                draw.line([(x, 0), (x, size)], fill=(r, g, b))
                        else:
                            # 垂直渐变
                            for y in range(size):
                                ratio = y / size
                                r = int(color1[0] + (color2[0] - color1[0]) * ratio)
                                g = int(color1[1] + (color2[1] - color1[1]) * ratio)
                                b = int(color1[2] + (color2[2] - color1[2]) * ratio)
                                draw.line([(0, y), (size, y)], fill=(r, g, b))
                
                # 应用边框
                if "border" in styles:
                    border_parts = styles["border"].split()
                    if len(border_parts) >= 3:
                        border_width = int(border_parts[0].replace("px", ""))
                        border_style = border_parts[1]
                        border_color = border_parts[2]
                        
                        if border_style != "none":
                            draw.rectangle([0, 0, size-1, size-1], outline=border_color, width=border_width)
                
                # 应用圆角
                if "border-radius" in styles:
                    radius = int(styles["border-radius"].replace("px", "").replace("%", ""))
                    if "%" in styles["border-radius"]:
                        radius = int(size * radius / 100)
                    
                    # 创建圆角蒙版
                    mask = Image.new("L", (size, size), 0)
                    mask_draw = ImageDraw.Draw(mask)
                    mask_draw.rounded_rectangle([0, 0, size, size], radius=radius, fill=255)
                    
                    # 应用蒙版
                    img.putalpha(mask)
            
            elif current_tab == 6:  # Matplotlib标签页
                code = self.matplotlib_data.get("1.0", tk.END).strip()
                if not code:
                    return
                
                size = 80
                
                # 准备绘图环境
                plt.style.use('ggplot')
                plt.rcParams['axes.facecolor'] = self.matplotlib_bg_color.get()
                
                # 执行用户代码
                local_vars = {}
                exec(code, globals(), local_vars)
                
                # 获取数据
                x = local_vars.get('x', [1, 2, 3, 4, 5])
                y = local_vars.get('y', [2, 3, 5, 7, 11])
                y1 = local_vars.get('y1', None)
                y2 = local_vars.get('y2', None)
                
                # 创建图表
                fig, ax = plt.subplots(figsize=(size/100, size/100), dpi=100)
                
                # 根据类型绘制图表
                chart_type = self.matplotlib_type.get()
                if chart_type == "折线图":
                    ax.plot(x, y, marker='o')
                    if y1 is not None:
                        ax.plot(x, y1, marker='o')
                elif chart_type == "柱状图":
                    ax.bar(x, y)
                    if y1 is not None:
                        ax.bar(x, y1, bottom=y)
                elif chart_type == "饼图":
                    ax.pie(y, labels=x, autopct='%1.1f%%')
                elif chart_type == "散点图":
                    ax.scatter(x, y)
                elif chart_type == "雷达图":
                    theta = np.linspace(0, 2*np.pi, len(x), endpoint=False)
                    ax.plot(theta, y)
                    ax.fill(theta, y, alpha=0.25)
                    ax.set_xticks(theta)
                    ax.set_xticklabels(x)
                elif chart_type == "面积图":
                    ax.stackplot(x, y)
                
                # 调整图表
                ax.set_facecolor(self.matplotlib_bg_color.get())
                fig.patch.set_alpha(self.matplotlib_alpha.get())
                
                # 转换为PIL图像
                canvas = FigureCanvasAgg(fig)
                canvas.draw()
                
                buf = canvas.buffer_rgba()
                img = Image.fromarray(np.asarray(buf))
                
                # 关闭图表释放内存
                plt.close(fig)
            
            # 显示预览
            from PIL import ImageTk
            img_tk = ImageTk.PhotoImage(img)
            self.realtime_preview.image = img_tk  # 保持引用
            self.realtime_preview.create_image(40, 40, image=img_tk)
            
        except Exception as e:
            print(f"实时预览错误: {e}")
    
    def show_final_preview(self):
        """显示最终预览"""
        if not self.current_icon:
            return
        
        # 清除旧预览
        self.preview_canvas.delete("all")
        self.icon_previews = []
        
        # 计算布局
        canvas_width = self.preview_canvas.winfo_width()
        if canvas_width < 10:  # 尚未显示
            canvas_width = 700
        
        icon_count = len(self.current_icon)
        max_icon_size = max(icon.size[0] for icon in self.current_icon)
        icons_per_row = max(1, min(icon_count, canvas_width // (max_icon_size + 20)))
        
        # 在画布上排列图标
        x, y = 20, 20
        row_height = 0
        
        for i, icon in enumerate(self.current_icon):
            # 转换为PhotoImage
            from PIL import ImageTk
            img_tk = ImageTk.PhotoImage(icon)
            self.icon_previews.append(img_tk)  # 保持引用
            
            # 绘制图标
            self.preview_canvas.create_image(x, y, anchor=tk.NW, image=img_tk)
            self.preview_canvas.create_text(x + icon.size[0]//2, y + icon.size[1] + 5, 
                                           text=f"{icon.size[0]}x{icon.size[1]}")
            
            # 更新位置
            x += icon.size[0] + 20
            row_height = max(row_height, icon.size[1] + 30)
            
            # 换行
            if (i + 1) % icons_per_row == 0:
                x = 20
                y += row_height
                row_height = 0
        
        # 更新滚动区域
        total_width = max(20 + (max_icon_size + 20) * min(icon_count, icons_per_row) - 20, canvas_width)
        total_height = y + row_height if row_height > 0 else y
        self.preview_canvas.config(scrollregion=(0, 0, total_width, total_height))
        self.preview_canvas.yview_moveto(0)
        self.preview_canvas.xview_moveto(0)
    
    def save_icon(self):
        """保存图标文件"""
        if not self.current_icon:
            messagebox.showerror("错误", "没有可保存的图标")
            return
        
        format_map = {
            "ICO (多尺寸)": ("ico", ".ico"),
            "PNG": ("png", ".png"),
            "JPG": ("jpeg", ".jpg"),
            "WebP": ("webp", ".webp")
        }
        
        format_name = self.output_format.get()
        if format_name not in format_map:
            messagebox.showerror("错误", "不支持的输出格式")
            print("不支持的输出格式")
            return
        
        format_type, ext = format_map[format_name]
        
        filepath = filedialog.asksaveasfilename(
            title="保存图标文件",
            defaultextension=ext,
            filetypes=[(f"{format_name} 文件", f"*{ext}"), ('所有文件', '*.*')]
        )
        
        if not filepath:
            return
        
        try:
            if format_type == "ico":
                # 保存为ICO格式 (多尺寸)
                self.current_icon[0].save(
                    filepath,
                    format="ICO",
                    append_images=self.current_icon[1:],
                    quality=self.quality.get()
                )
            else:
                # 保存为其他格式 (单尺寸，使用最大尺寸)
                largest = max(self.current_icon, key=lambda img: img.size[0])
                
                # 转换为目标格式
                if format_type == "jpeg" and largest.mode == 'RGBA':
                    largest = largest.convert('RGB')
                
                save_kwargs = {
                    'format': format_type,
                    'quality': self.quality.get()
                }
                
                if format_type == "png":
                    save_kwargs['compress_level'] = 9 - int(self.quality.get() / 11.1)  # 0-9
                
                largest.save(filepath, **save_kwargs)
            
            self.status_bar["text"] = f"图标已保存到: {filepath}"
            messagebox.showinfo("成功", f"图标已成功保存到:\n{filepath}")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存图标时出错:\n{str(e)}")
            self.status_bar["text"] = f"错误: {str(e)}"
    
    def clear_preview(self):
        """清除当前预览"""
        self.preview_canvas.delete("all")
        self.realtime_preview.delete("all")
        self.icon_previews = []
        self.current_icon = None
        self.save_btn['state'] = tk.DISABLED
        self.sizes_label.config(text="包含尺寸: 无")
        self.status_bar["text"] = "预览已清除"

        # 强制重绘实时预览（显示空白）
        self.realtime_preview.config(bg='white')  # 可选：设置背景色
    
    def show_help(self):
        """显示帮助信息"""
        help_text = """高级图标生成工具 使用说明

1. 图片转图标:
   - 点击"浏览"选择图片或直接输入图片路径
   - 调整亮度、对比度、饱和度和透明度
   - 选择多种图像效果(模糊、轮廓、锐化、浮雕等)
   - 设置需要的图标尺寸
   - 使用"单独定制尺寸"为不同尺寸设置不同参数
   - 选择形状蒙版 (圆形/圆角矩形/星形/心形等)
   - 点击"生成预览"查看效果
   - 选择输出格式和质量后点击"保存图标"

2. 文字转图标:
   - 输入要显示的文字
   - 设置字体、大小、样式和颜色
   - 选择背景类型和颜色(纯色、渐变、透明)
   - 设置需要的图标尺寸
   - 点击"生成预览"查看效果
   - 选择输出格式和质量后点击"保存图标"

3. SVG转图标:
   - 输入SVG代码或使用示例
   - 设置背景颜色和透明度
   - 设置需要的图标尺寸
   - 点击"生成预览"查看效果
   - 选择输出格式和质量后点击"保存图标"

4. Emoji转图标:
   - 选择Emoji或直接输入
   - 设置背景颜色和透明度
   - 设置需要的图标尺寸
   - 点击"生成预览"查看效果
   - 选择输出格式和质量后点击"保存图标"

5. Unicode符号转图标:
   - 选择Unicode符号或直接输入
   - 设置字体、大小和颜色
   - 设置背景颜色和透明度
   - 设置需要的图标尺寸
   - 点击"生成预览"查看效果
   - 选择输出格式和质量后点击"保存图标"

6. CSS样式转图标:
   - 输入CSS样式代码或使用示例
   - 设置需要的图标尺寸
   - 点击"生成预览"查看效果
   - 选择输出格式和质量后点击"保存图标"

7. 图表转图标:
   - 选择图表类型(折线图、柱状图、饼图等)
   - 输入图表数据或使用示例
   - 设置背景颜色和透明度
   - 设置需要的图标尺寸
   - 点击"生成预览"查看效果
   - 选择输出格式和质量后点击"保存图标"

提示:
- 实时预览窗口会显示当前设置的预览效果
- 生成大尺寸图标或复杂效果时请耐心等待
- 支持多种输出格式: ICO/PNG/JPG/WebP
"""
        messagebox.showinfo("帮助", help_text)

if __name__ == "__main__":
    # 创建圆形和圆角矩形的绘制方法
    def _create_round_rect(self, x1, y1, x2, y2, radius=25, **kwargs):
        points = [
            x1+radius, y1,
            x1+radius, y1,
            x2-radius, y1,
            x2-radius, y1,
            x2, y1,
            x2, y1+radius,
            x2, y1+radius,
            x2, y2-radius,
            x2, y2-radius,
            x2, y2,
            x2-radius, y2,
            x2-radius, y2,
            x1+radius, y2,
            x1+radius, y2,
            x1, y2,
            x1, y2-radius,
            x1, y2-radius,
            x1, y1+radius,
            x1, y1+radius,
            x1, y1
        ]
        return self.create_polygon(points, **kwargs, smooth=True)
    
    # 将方法添加到Canvas类
    tk.Canvas.create_round_rectangle = _create_round_rect
    
    window = tk.Tk()
    try:
        window.iconbitmap(default='icon.ico')
    except:
        pass
    
    app = AdvancedIconGenerator(window)
    window.mainloop()