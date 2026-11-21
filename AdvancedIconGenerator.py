__version__ = "6.3.0"  # 版本号更新

import sys
import os
import json
import threading
import re
import traceback
import warnings
import platform
from queue import Queue
from io import BytesIO
from functools import lru_cache
import time

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QLineEdit, QComboBox,
    QCheckBox, QSpinBox, QDoubleSpinBox, QSlider, QTextEdit,
    QScrollArea, QFrame, QGridLayout, QFileDialog, QMessageBox,
    QProgressBar, QStatusBar, QButtonGroup, QGroupBox, QSplitter,
    QToolBar, QSizePolicy, QDialog, QDialogButtonBox, QInputDialog
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QSize
from PySide6.QtGui import (
    QPixmap, QImage, QPainter, QColor, QFont, QFontDatabase,
    QLinearGradient, QRadialGradient, QBrush, QPen, QPainterPath
)
from PySide6.QtSvg import QSvgRenderer

from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter, ImageEnhance
import numpy as np

# 修复1: 添加matplotlib导入检查
try:
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    MATPLOTLIB_SUPPORT = True
except ImportError:
    MATPLOTLIB_SUPPORT = False
    print("警告: matplotlib模块未安装，图表功能将受限")

try:
    import cairosvg
    CAIROSVG_SUPPORT = True
except ImportError:
    CAIROSVG_SUPPORT = False
    print("警告: cairosvg模块未安装，SVG渲染将使用Qt SVG")

try:
    import emoji
    EMOJI_SUPPORT = True
except ImportError:
    EMOJI_SUPPORT = False
    print("警告: emoji模块未安装，Emoji功能将受限")


class IconGeneratorWorker(QThread):
    """工作线程 - 处理图标生成任务"""
    progress_updated = Signal(int)
    finished = Signal(object)
    error_occurred = Signal(str)

    def __init__(self, task_type, params):
        super().__init__()
        self.task_type = task_type
        self.params = params
        self._is_cancelled = False

    def cancel(self):
        """取消任务"""
        self._is_cancelled = True

    def run(self):
        try:
            icons = []
            sizes = self.params.get('sizes', [])

            # 修复2: 检查matplotlib支持
            if self.task_type == 'matplotlib' and not MATPLOTLIB_SUPPORT:
                raise Exception("需要安装matplotlib模块才能使用此功能")

            if self.task_type == 'image':
                icons = self.generate_image_icons()
            elif self.task_type == 'text':
                icons = self.generate_text_icons()
            elif self.task_type == 'svg':
                icons = self.generate_svg_icons()
            elif self.task_type == 'emoji':
                icons = self.generate_emoji_icons()
            elif self.task_type == 'unicode':
                icons = self.generate_unicode_icons()
            elif self.task_type == 'css':
                icons = self.generate_css_icons()
            elif self.task_type == 'matplotlib':
                icons = self.generate_matplotlib_icons()

            if self._is_cancelled:
                return

            for i in range(len(sizes)):
                if self._is_cancelled:
                    return
                self.progress_updated.emit(i + 1)

            self.finished.emit(icons)

        except Exception as e:
            self.error_occurred.emit(str(e))

    def generate_image_icons(self):
        """生成图片图标"""
        sizes = self.params['sizes']
        img_path = self.params['image_path']
        brightness = self.params['brightness']
        contrast = self.params['contrast']
        saturation = self.params['saturation']
        alpha = self.params['alpha']
        effect = self.params['effect']
        shape = self.params['shape']
        radius = self.params['radius']
        customize_sizes = self.params['customize_sizes']
        size_settings = self.params['size_settings']

        # 加载原始图片
        try:
            img = Image.open(img_path)
        except Exception as e:
            raise Exception(f"无法加载图片: {str(e)}")

        # 修复3: 确保图片是RGBA模式
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # 应用全局调整
        temp_img = img.copy()
        if brightness != 1.0:
            enhancer = ImageEnhance.Brightness(temp_img)
            temp_img = enhancer.enhance(brightness)
        if contrast != 1.0:
            enhancer = ImageEnhance.Contrast(temp_img)
            temp_img = enhancer.enhance(contrast)
        if saturation != 1.0:
            enhancer = ImageEnhance.Color(temp_img)
            temp_img = enhancer.enhance(saturation)

        # 应用透明度
        if alpha < 1.0:
            temp_img = self.apply_alpha(temp_img, alpha)

        # 应用效果（在调整后应用效果）
        temp_img = self.apply_image_effect(temp_img, effect)

        icons = []
        for size in sizes:
            if self._is_cancelled:
                return icons

            # 应用尺寸特定的调整
            if customize_sizes and size in size_settings:
                settings = size_settings[size]
                size_img = img.copy()

                if settings.get('brightness', 1.0) != 1.0:
                    enhancer = ImageEnhance.Brightness(size_img)
                    size_img = enhancer.enhance(settings['brightness'])
                if settings.get('contrast', 1.0) != 1.0:
                    enhancer = ImageEnhance.Contrast(size_img)
                    size_img = enhancer.enhance(settings['contrast'])
                if settings.get('saturation', 1.0) != 1.0:
                    enhancer = ImageEnhance.Color(size_img)
                    size_img = enhancer.enhance(settings['saturation'])
                if settings.get('alpha', 1.0) < 1.0:
                    size_img = self.apply_alpha(size_img, settings['alpha'])

                # 应用效果（单独尺寸）
                if effect != "无":
                    size_img = self.apply_image_effect(size_img, effect)

                icon = size_img.resize((size, size), Image.Resampling.LANCZOS)
            else:
                icon = temp_img.resize((size, size), Image.Resampling.LANCZOS)

            # 应用形状蒙版
            icon = self.apply_shape_mask(icon, shape, radius)
            icons.append(icon)

        return icons

    def generate_text_icons(self):
        """生成文字图标"""
        sizes = self.params['sizes']
        text = self.params['text']
        font_family = self.params['font_family']
        font_size = self.params['font_size']
        font_style = self.params['font_style']
        text_color = self.params['text_color']
        bg_type = self.params['bg_type']
        bg_color = self.params['bg_color']
        bg_color2 = self.params['bg_color2']
        bg_alpha = self.params['bg_alpha']
        gradient_dir = self.params['gradient_dir']
        shape = self.params['shape']
        radius = self.params['radius']

        icons = []
        for size in sizes:
            if self._is_cancelled:
                return icons

            # 创建背景
            if bg_type == "透明":
                img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            elif bg_type == "渐变":
                img = self.create_gradient_image(size, bg_color, bg_color2, gradient_dir)
            else:  # 纯色
                img = Image.new("RGBA", (size, size), self.hex_to_rgba(bg_color))

            # 应用背景透明度
            if bg_alpha < 1.0 and img.mode == 'RGBA':
                alpha_channel = img.split()[3]
                alpha_channel = ImageEnhance.Brightness(alpha_channel).enhance(bg_alpha)
                r, g, b, _ = img.split()
                img = Image.merge('RGBA', (r, g, b, alpha_channel))

            draw = ImageDraw.Draw(img)

            # 获取字体
            font = self.get_font(font_family, int(font_size * (size / 256)), font_style)

            # 计算文字位置
            try:
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            except AttributeError:
                try:
                    text_width, text_height = draw.textsize(text, font=font)
                except AttributeError:
                    try:
                        text_width, text_height = font.getsize(text)
                    except:
                        text_width, text_height = size // 2, size // 2

            position = ((size - text_width) // 2, (size - text_height) // 2)

            # 绘制文字
            draw.text(position, text, fill=text_color, font=font)

            # 应用形状蒙版
            img = self.apply_shape_mask(img, shape, radius)
            icons.append(img)

        return icons

    def generate_svg_icons(self):
        """生成SVG图标"""
        sizes = self.params['sizes']
        svg_code = self.params['svg_code']
        bg_color = self.params['bg_color']
        alpha = self.params['alpha']

        icons = []
        for size in sizes:
            if self._is_cancelled:
                return icons

            try:
                # 尝试使用cairosvg
                if CAIROSVG_SUPPORT:
                    output = BytesIO()
                    cairosvg.svg2png(
                        bytestring=svg_code.encode('utf-8'),
                        write_to=output,
                        output_width=size,
                        output_height=size
                    )
                    output.seek(0)
                    img = Image.open(output)
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                else:
                    # 使用Qt SVG渲染
                    img = self.render_svg_with_qt(svg_code, size)

                # 添加背景
                if bg_color != "#FFFFFF" or alpha < 1.0:
                    bg = Image.new("RGBA", img.size, self.hex_to_rgba(bg_color))
                    if alpha < 1.0:
                        bg.putalpha(int(255 * alpha))
                    img = Image.alpha_composite(bg, img)

                icons.append(img)

            except Exception as e:
                # 渲染失败时创建占位图
                print(f"SVG渲染错误: {e}")
                img = Image.new("RGBA", (size, size), (255, 255, 255, 0))
                draw = ImageDraw.Draw(img)
                draw.text((10, 10), "SVG Error", fill="red")
                icons.append(img)

        return icons

    def generate_emoji_icons(self):
        """生成Emoji图标"""
        if not EMOJI_SUPPORT:
            raise Exception("需要安装emoji模块才能使用此功能")

        sizes = self.params['sizes']
        emoji_char = self.params['emoji']
        bg_color = self.params['bg_color']
        alpha = self.params['alpha']

        icons = []
        for size in sizes:
            if self._is_cancelled:
                return icons

            # 创建背景
            if bg_color == "透明":
                img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            else:
                img = Image.new("RGBA", (size, size), self.hex_to_rgba(bg_color))

            # 应用背景透明度
            if alpha < 1.0 and img.mode == 'RGBA':
                alpha_channel = img.split()[3]
                alpha_channel = ImageEnhance.Brightness(alpha_channel).enhance(alpha)
                r, g, b, _ = img.split()
                img = Image.merge('RGBA', (r, g, b, alpha_channel))

            draw = ImageDraw.Draw(img)

            # 获取字体
            font = self.get_emoji_font(size)

            # 计算文字位置
            try:
                bbox = draw.textbbox((0, 0), emoji_char, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            except AttributeError:
                try:
                    text_width, text_height = draw.textsize(emoji_char, font=font)
                except AttributeError:
                    try:
                        text_width, text_height = font.getsize(emoji_char)
                    except:
                        text_width, text_height = size // 2, size // 2

            position = ((size - text_width) // 2, (size - text_height) // 2)

            # 绘制Emoji
            draw.text(position, emoji_char, font=font, embedded_color=True)

            icons.append(img)

        return icons

    def generate_unicode_icons(self):
        """生成Unicode符号图标"""
        sizes = self.params['sizes']
        unicode_char = self.params['unicode']
        font_family = self.params['font_family']
        font_color = self.params['font_color']
        bg_color = self.params['bg_color']
        alpha = self.params['alpha']

        icons = []
        for size in sizes:
            if self._is_cancelled:
                return icons

            # 创建背景
            if bg_color == "透明":
                img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            else:
                img = Image.new("RGBA", (size, size), self.hex_to_rgba(bg_color))

            # 应用背景透明度
            if alpha < 1.0 and img.mode == 'RGBA':
                alpha_channel = img.split()[3]
                alpha_channel = ImageEnhance.Brightness(alpha_channel).enhance(alpha)
                r, g, b, _ = img.split()
                img = Image.merge('RGBA', (r, g, b, alpha_channel))

            draw = ImageDraw.Draw(img)

            # 获取字体
            font = self.get_font(font_family, int(size * 0.8))

            # 计算文字位置
            try:
                bbox = draw.textbbox((0, 0), unicode_char, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            except AttributeError:
                try:
                    text_width, text_height = draw.textsize(unicode_char, font=font)
                except AttributeError:
                    try:
                        text_width, text_height = font.getsize(unicode_char)
                    except:
                        text_width, text_height = size // 2, size // 2

            position = ((size - text_width) // 2, (size - text_height) // 2)

            # 绘制Unicode符号
            draw.text(position, unicode_char, fill=font_color, font=font)

            icons.append(img)

        return icons

    def generate_css_icons(self):
        """生成CSS样式图标"""
        sizes = self.params['sizes']
        css_code = self.params['css_code']

        styles = self.parse_css(css_code)

        icons = []
        for size in sizes:
            if self._is_cancelled:
                return icons

            img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            # 应用背景颜色或渐变
            if "background-color" in styles:
                bg_color = self.parse_css_color(styles["background-color"])
                draw.rectangle([0, 0, size, size], fill=bg_color)
            elif "background" in styles:
                if "gradient" in styles["background"].lower():
                    self.apply_css_gradient(draw, size, styles["background"])
                else:
                    bg_color = self.parse_css_color(styles["background"])
                    draw.rectangle([0, 0, size, size], fill=bg_color)

            # 应用边框
            if "border" in styles:
                border_parts = styles["border"].split()
                if len(border_parts) >= 3:
                    try:
                        border_width = int(re.search(r'\d+', border_parts[0]).group())
                    except (ValueError, AttributeError):
                        border_width = 1
                    border_style = border_parts[1]
                    border_color = border_parts[2]

                    if border_style != "none":
                        for i in range(border_width):
                            draw.rectangle([i, i, size-1-i, size-1-i],
                                         outline=self.parse_css_color(border_color))

            # 应用圆角
            if "border-radius" in styles:
                try:
                    radius_str = styles["border-radius"]
                    radius = int(re.search(r'\d+', radius_str).group())
                    if '%' in radius_str:
                        radius = int(size * radius / 100)
                except (ValueError, AttributeError):
                    radius = 0

                if radius > 0:
                    # 创建圆角蒙版
                    mask = Image.new("L", (size, size), 0)
                    mask_draw = ImageDraw.Draw(mask)
                    mask_draw.rounded_rectangle([0, 0, size, size],
                                              radius=radius,
                                              fill=255)
                    img.putalpha(mask)

            icons.append(img)

        return icons

    def generate_matplotlib_icons(self):
        """生成Matplotlib图表图标"""
        if not MATPLOTLIB_SUPPORT:
            raise Exception("需要安装matplotlib模块才能使用此功能")

        sizes = self.params['sizes']
        code = self.params['code']
        chart_type = self.params['chart_type']
        bg_color = self.params['bg_color']
        alpha = self.params['alpha']

        icons = []
        fig = None

        try:
            # 准备绘图环境
            plt.style.use('ggplot')
            plt.rcParams['axes.facecolor'] = bg_color

            # 执行用户代码
            local_vars = {}
            try:
                exec(code, globals(), local_vars)
            except Exception as e:
                raise Exception(f"执行代码错误: {str(e)}")

            # 获取数据
            x = local_vars.get('x', [1, 2, 3, 4, 5])
            y = local_vars.get('y', [2, 3, 5, 7, 11])
            y1 = local_vars.get('y1', None)
            y2 = local_vars.get('y2', None)

            for size in sizes:
                if self._is_cancelled:
                    return icons

                # 创建图表
                fig, ax = plt.subplots(figsize=(size/100, size/100), dpi=100)

                # 根据类型绘制图表
                try:
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
                    ax.set_facecolor(bg_color)
                    fig.patch.set_alpha(alpha)

                    # 转换为PIL图像
                    canvas = FigureCanvasAgg(fig)
                    canvas.draw()

                    buf = canvas.buffer_rgba()
                    img = Image.fromarray(np.asarray(buf))
                    icons.append(img)

                except Exception as e:
                    raise Exception(f"绘制图表错误: {str(e)}")
                finally:
                    plt.close(fig)
                    fig = None

        except Exception as e:
            if fig:
                plt.close(fig)
            raise e

        return icons

    # 辅助方法
    def hex_to_rgba(self, hex_color, alpha=255):
        """将十六进制颜色转换为RGBA元组，支持#RGB、#RRGGBB、#RRGGBBAA格式"""
        hex_color = hex_color.lstrip('#').upper()
        
        # 处理 #RGB 格式
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])
            return (int(hex_color[0:2], 16), int(hex_color[2:4], 16), 
                    int(hex_color[4:6], 16), alpha)
        
        # 处理 #RRGGBB 格式
        elif len(hex_color) == 6:
            return (int(hex_color[0:2], 16), int(hex_color[2:4], 16),
                    int(hex_color[4:6], 16), alpha)
        
        # 处理 #RRGGBBAA 格式
        elif len(hex_color) == 8:
            return (int(hex_color[0:2], 16), int(hex_color[2:4], 16),
                    int(hex_color[4:6], 16), int(hex_color[6:8], 16))
        
        return (255, 255, 255, alpha)

    def parse_css_color(self, color_str):
        """解析CSS颜色字符串"""
        color_str = color_str.strip().lower()
        
        # 处理十六进制颜色
        if color_str.startswith('#'):
            return self.hex_to_rgba(color_str)
        
        # 处理rgb颜色
        elif color_str.startswith('rgb'):
            rgb_match = re.search(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', color_str)
            if rgb_match:
                r, g, b = map(int, rgb_match.groups())
                return (r, g, b, 255)
        
        # 处理rgba颜色
        elif color_str.startswith('rgba'):
            rgba_match = re.search(r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*([0-9.]+)\)', color_str)
            if rgba_match:
                r, g, b = map(int, rgba_match.groups()[:3])
                a = int(float(rgba_match.group(4)) * 255)
                return (r, g, b, a)
        
        # 处理预定义颜色
        color_map = {
            'red': (255, 0, 0, 255),
            'green': (0, 255, 0, 255),
            'blue': (0, 0, 255, 255),
            'black': (0, 0, 0, 255),
            'white': (255, 255, 255, 255),
            'yellow': (255, 255, 0, 255),
            'cyan': (0, 255, 255, 255),
            'magenta': (255, 0, 255, 255),
            'transparent': (0, 0, 0, 0)
        }
        
        if color_str in color_map:
            return color_map[color_str]
        
        return (0, 0, 0, 255)

    @lru_cache(maxsize=32)
    def get_font(self, font_family, size, style="normal"):
        """获取字体（带缓存）"""
        try:
            # 尝试加载字体
            font = ImageFont.truetype(font_family, size)
            
            # 应用样式（简化处理）
            if "bold" in style and "italic" in style:
                # 无法直接设置bold+italic，返回普通字体
                pass
            elif "bold" in style:
                # 无法直接设置bold，返回普通字体
                pass
            elif "italic" in style:
                # 无法直接设置italic，返回普通字体
                pass
            
            return font
        except:
            try:
                # 尝试使用系统默认字体
                return ImageFont.truetype("arial.ttf", size)
            except:
                return ImageFont.load_default()

    def apply_image_effect(self, img, effect):
        """应用图像效果"""
        if effect == "无":
            return img
        
        # 创建副本避免修改原图
        result = img.copy()
        
        try:
            if effect == "模糊":
                return result.filter(ImageFilter.BLUR)
            elif effect == "轮廓":
                return result.filter(ImageFilter.CONTOUR)
            elif effect == "锐化":
                return result.filter(ImageFilter.SHARPEN)
            elif effect == "浮雕":
                return result.filter(ImageFilter.EMBOSS)
            elif effect == "边缘增强":
                return result.filter(ImageFilter.EDGE_ENHANCE)
            elif effect == "平滑":
                return result.filter(ImageFilter.SMOOTH)
            elif effect == "细节增强":
                return result.filter(ImageFilter.DETAIL)
            elif effect == "反色":
                return ImageOps.invert(result)
            elif effect == "黑白":
                return result.convert("L").convert("RGBA")
            elif effect == "棕褐色":
                return self.apply_sepia(result)
            elif effect == "油画":
                return self.apply_oil_painting_optimized(result)
            elif effect == "像素化":
                return self.apply_pixelate(result)
            elif effect == "高斯模糊":
                return result.filter(ImageFilter.GaussianBlur(radius=2))
            elif effect == "查找边缘":
                return result.filter(ImageFilter.FIND_EDGES)
        except Exception as e:
            print(f"应用效果出错: {e}")
            return img
        
        return img

    def apply_sepia(self, img):
        """应用棕褐色效果（优化版）"""
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # 分离通道
        r, g, b, a = img.split()
        
        # 转换为numpy数组加速处理
        r_array = np.array(r, dtype=np.float32)
        g_array = np.array(g, dtype=np.float32)
        b_array = np.array(b, dtype=np.float32)
        
        # 应用棕褐色变换
        tr = 0.393 * r_array + 0.769 * g_array + 0.189 * b_array
        tg = 0.349 * r_array + 0.686 * g_array + 0.168 * b_array
        tb = 0.272 * r_array + 0.534 * g_array + 0.131 * b_array
        
        # 裁剪到有效范围
        tr = np.clip(tr, 0, 255).astype(np.uint8)
        tg = np.clip(tg, 0, 255).astype(np.uint8)
        tb = np.clip(tb, 0, 255).astype(np.uint8)
        
        # 合并通道
        return Image.merge('RGBA', (Image.fromarray(tr), Image.fromarray(tg),
                                   Image.fromarray(tb), a))

    def apply_oil_painting_optimized(self, img, brush_size=3):
        """应用油画效果（优化版）"""
        # 缩小图像加速处理
        width, height = img.size
        scale_factor = min(1.0, 200 / max(width, height))
        if scale_factor < 1.0:
            small_img = img.resize((int(width * scale_factor), int(height * scale_factor)))
        else:
            small_img = img
        
        # 转换为numpy数组
        img_array = np.array(small_img)
        
        # 简化油画效果：应用中值滤波
        from scipy import ndimage
        result_array = ndimage.median_filter(img_array, size=(brush_size, brush_size, 1))
        
        result = Image.fromarray(result_array)
        
        # 恢复原始大小
        if scale_factor < 1.0:
            result = result.resize((width, height), Image.Resampling.LANCZOS)
        
        return result

    def apply_pixelate(self, img, pixel_size=8):
        """应用像素化效果"""
        width, height = img.size
        pixel_size = max(2, min(pixel_size, min(width, height) // 4))
        
        # 缩小后放大
        small = img.resize(
            (width // pixel_size, height // pixel_size),
            resample=Image.Resampling.NEAREST
        )
        result = small.resize(
            (width, height),
            resample=Image.Resampling.NEAREST
        )
        return result

    def apply_alpha(self, img, alpha):
        """应用透明度"""
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        alpha = max(0.0, min(1.0, alpha))
        alpha_channel = img.split()[3]
        alpha_array = np.array(alpha_channel, dtype=np.float32) * alpha
        alpha_array = np.clip(alpha_array, 0, 255).astype(np.uint8)
        
        r, g, b, _ = img.split()
        return Image.merge('RGBA', (r, g, b, Image.fromarray(alpha_array)))

    def apply_shape_mask(self, img, shape, radius):
        """应用形状蒙版"""
        if shape == "方形":
            return img

        mask = Image.new('L', img.size, 0)
        draw = ImageDraw.Draw(mask)

        if shape == "圆形":
            draw.ellipse((0, 0, img.size[0], img.size[1]), fill=255)
        elif shape == "圆角矩形":
            radius = min(radius, min(img.size) // 2)
            draw.rounded_rectangle((0, 0, img.size[0], img.size[1]),
                                 radius=radius, fill=255)
        elif shape == "星形":
            points = self.calculate_star_points(5,
                                               img.size[0]//2,
                                               img.size[1]//2,
                                               img.size[0]//2-5,
                                               img.size[0]//4)
            draw.polygon(points, fill=255)
        elif shape == "心形":
            points = self.calculate_heart_points(img.size[0]//2,
                                                img.size[1]//2,
                                                img.size[0]//2-5)
            draw.polygon(points, fill=255)
        elif shape == "三角形":
            points = [img.size[0]//2, 5, img.size[0]-5, img.size[1]-5, 5, img.size[1]-5]
            draw.polygon(points, fill=255)

        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        img.putalpha(mask)
        return img

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

    def create_gradient_image(self, size, color1, color2, direction):
        """创建渐变图像（优化版）"""
        img = Image.new("RGBA", (size, size))
        draw = ImageDraw.Draw(img)

        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            if len(hex_color) == 3:
                hex_color = ''.join([c*2 for c in hex_color])
            if len(hex_color) == 6:
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            return (255, 255, 255)

        r1, g1, b1 = hex_to_rgb(color1)
        r2, g2, b2 = hex_to_rgb(color2)

        # 创建渐变数组
        gradient = np.zeros((size, size, 3), dtype=np.uint8)
        
        if direction == "水平":
            for x in range(size):
                ratio = x / size
                r = int(r1 + (r2 - r1) * ratio)
                g = int(g1 + (g2 - g1) * ratio)
                b = int(b1 + (b2 - b1) * ratio)
                gradient[:, x] = [r, g, b]
        elif direction == "垂直":
            for y in range(size):
                ratio = y / size
                r = int(r1 + (r2 - r1) * ratio)
                g = int(g1 + (g2 - g1) * ratio)
                b = int(b1 + (b2 - b1) * ratio)
                gradient[y, :] = [r, g, b]
        else:  # 对角
            for y in range(size):
                for x in range(size):
                    ratio = (x + y) / (size * 2)
                    r = int(r1 + (r2 - r1) * ratio)
                    g = int(g1 + (g2 - g1) * ratio)
                    b = int(b1 + (b2 - b1) * ratio)
                    gradient[y, x] = [r, g, b]

        return Image.fromarray(gradient, 'RGB').convert('RGBA')

    def render_svg_with_qt(self, svg_code, size):
        """使用Qt渲染SVG"""
        renderer = QSvgRenderer()
        if not renderer.load(svg_code.encode('utf-8')):
            raise Exception("无效的SVG代码")

        image = QImage(size, size, QImage.Format_ARGB32)
        image.fill(Qt.transparent)

        painter = QPainter(image)
        renderer.render(painter)
        painter.end()

        # 转换为PIL图像
        ptr = image.bits()
        ptr.setsize(image.sizeInBytes())
        arr = np.array(ptr).reshape((size, size, 4))  # 形状 (height, width, 4)
        return Image.fromarray(arr, 'RGBA')

    def get_emoji_font(self, size):
        """获取Emoji字体"""
        font_size = int(size * 0.8)
        system = platform.system()
        
        if system == "Windows":
            font_paths = [
                "C:/Windows/Fonts/seguiemj.ttf",
                "C:/Windows/Fonts/seguiemj.ttc",
                "C:/Windows/Fonts/SEGUIEMJ.TTF"
            ]
        elif system == "Darwin":  # macOS
            font_paths = [
                "/System/Library/Fonts/Apple Color Emoji.ttc",
                "/System/Library/Fonts/Apple Color Emoji.ttf"
            ]
        else:  # Linux
            font_paths = [
                "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
                "/usr/share/fonts/truetype/emoji/emoji.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
            ]

        for font_path in font_paths:
            try:
                if os.path.exists(font_path):
                    return ImageFont.truetype(font_path, font_size)
            except:
                continue

        return ImageFont.load_default()

    def parse_css(self, css_code):
        """解析CSS代码（改进版）"""
        styles = {}
        
        # 移除注释
        css_code = re.sub(r'/\*.*?\*/', '', css_code, flags=re.DOTALL)
        
        # 按行解析
        for line in css_code.split(';'):
            line = line.strip()
            if ':' in line:
                prop, value = line.split(':', 1)
                prop = prop.strip().lower()
                value = value.strip()
                
                # 处理多个值的情况
                if prop in styles:
                    if isinstance(styles[prop], list):
                        styles[prop].append(value)
                    else:
                        styles[prop] = [styles[prop], value]
                else:
                    styles[prop] = value
        
        return styles

    def apply_css_gradient(self, draw, size, gradient_str):
        """应用CSS渐变（改进版）"""
        # 提取颜色值
        colors = re.findall(r'#[0-9a-fA-F]{3,8}|rgba?\([^)]+\)|[a-zA-Z]+', gradient_str)
        colors = [c for c in colors if c and c.lower() not in ['to', 'left', 'right', 'top', 'bottom']]
        
        if len(colors) >= 2:
            color1 = self.parse_css_color(colors[0])
            color2 = self.parse_css_color(colors[1])

            # 检查方向
            if "to right" in gradient_str.lower():
                # 水平渐变
                for x in range(size):
                    ratio = x / size
                    r = int(color1[0] + (color2[0] - color1[0]) * ratio)
                    g = int(color1[1] + (color2[1] - color1[1]) * ratio)
                    b = int(color1[2] + (color2[2] - color1[2]) * ratio)
                    draw.line([(x, 0), (x, size)], fill=(r, g, b))
            elif "to bottom" in gradient_str.lower():
                # 垂直渐变
                for y in range(size):
                    ratio = y / size
                    r = int(color1[0] + (color2[0] - color1[0]) * ratio)
                    g = int(color1[1] + (color2[1] - color1[1]) * ratio)
                    b = int(color1[2] + (color2[2] - color1[2]) * ratio)
                    draw.line([(0, y), (size, y)], fill=(r, g, b))
            else:
                # 默认：垂直渐变
                for y in range(size):
                    ratio = y / size
                    r = int(color1[0] + (color2[0] - color1[0]) * ratio)
                    g = int(color1[1] + (color2[1] - color1[1]) * ratio)
                    b = int(color1[2] + (color2[2] - color1[2]) * ratio)
                    draw.line([(0, y), (size, y)], fill=(r, g, b))


class SizeSettingsDialog(QDialog):
    """尺寸定制设置对话框"""
    def __init__(self, sizes, parent=None):
        super().__init__(parent)
        self.sizes = sizes
        self.settings = {}
        self.setWindowTitle("定制尺寸设置")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        grid = QGridLayout(scroll_content)

        # 标题
        grid.addWidget(QLabel("尺寸"), 0, 0)
        grid.addWidget(QLabel("亮度"), 0, 1)
        grid.addWidget(QLabel("对比度"), 0, 2)
        grid.addWidget(QLabel("饱和度"), 0, 3)
        grid.addWidget(QLabel("透明度"), 0, 4)

        # 为每个尺寸创建控件
        for i, size in enumerate(self.sizes):
            grid.addWidget(QLabel(f"{size}x{size}"), i+1, 0)

            self.settings[size] = {
                'brightness': QDoubleSpinBox(),
                'contrast': QDoubleSpinBox(),
                'saturation': QDoubleSpinBox(),
                'alpha': QDoubleSpinBox()
            }

            # 亮度
            sb = self.settings[size]['brightness']
            sb.setRange(0.1, 2.0)
            sb.setValue(1.0)
            sb.setSingleStep(0.1)
            grid.addWidget(sb, i+1, 1)

            # 对比度
            sb = self.settings[size]['contrast']
            sb.setRange(0.1, 2.0)
            sb.setValue(1.0)
            sb.setSingleStep(0.1)
            grid.addWidget(sb, i+1, 2)

            # 饱和度
            sb = self.settings[size]['saturation']
            sb.setRange(0.0, 2.0)
            sb.setValue(1.0)
            sb.setSingleStep(0.1)
            grid.addWidget(sb, i+1, 3)

            # 透明度
            sb = self.settings[size]['alpha']
            sb.setRange(0.0, 1.0)
            sb.setValue(1.0)
            sb.setSingleStep(0.05)
            grid.addWidget(sb, i+1, 4)

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_settings(self):
        """获取设置"""
        result = {}
        for size, settings in self.settings.items():
            result[size] = {
                'brightness': settings['brightness'].value(),
                'contrast': settings['contrast'].value(),
                'saturation': settings['saturation'].value(),
                'alpha': settings['alpha'].value()
            }
        return result


class IconPreviewWidget(QWidget):
    """图标预览控件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.icons = []
        self.setMinimumSize(200, 150)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_icons(self, icons):
        """设置图标列表"""
        self.icons = icons
        self.update()

    def clear(self):
        """清除图标"""
        self.icons = []
        self.update()

    def paintEvent(self, event):
        """绘制事件"""
        if not self.icons:
            painter = QPainter(self)
            painter.drawText(self.rect(), Qt.AlignCenter, "暂无预览")
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 计算布局
        available_width = self.width() - 40
        max_icon_size = max(icon.width for icon in self.icons)
        icons_per_row = max(1, available_width // (max_icon_size + 20))

        x, y = 20, 20
        row_height = 0

        for i, icon in enumerate(self.icons):
            # 转换为QPixmap
            if icon.mode != 'RGBA':
                icon = icon.convert('RGBA')
            
            # 确保图像数据正确
            try:
                img_data = icon.tobytes()
                qimage = QImage(img_data, icon.width, icon.height,
                              QImage.Format_RGBA8888)
                pixmap = QPixmap.fromImage(qimage)
            except Exception as e:
                print(f"转换预览图像错误: {e}")
                continue

            # 绘制图标
            painter.drawPixmap(x, y, pixmap)

            # 绘制尺寸标签
            painter.drawText(x + icon.width//2 - 15,
                           y + icon.height + 15,
                           f"{icon.width}x{icon.height}")

            # 更新位置
            x += icon.width + 20
            row_height = max(row_height, icon.height + 30)

            # 换行
            if (i + 1) % icons_per_row == 0:
                x = 20
                y += row_height
                row_height = 0


class ColorButton(QPushButton):
    """颜色选择按钮"""
    colorChanged = Signal(QColor)

    def __init__(self, color=QColor(255, 255, 255), parent=None):
        super().__init__(parent)
        self._color = color
        self.setText("选择颜色")
        self.clicked.connect(self.choose_color)
        self.update_style()

    def update_style(self):
        """更新按钮样式"""
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._color.name()};
                border: 1px solid gray;
                padding: 5px;
                min-width: 80px;
            }}
        """)

    def choose_color(self):
        """选择颜色"""
        from PySide6.QtWidgets import QColorDialog
        color = QColorDialog.getColor(self._color, self)
        if color.isValid():
            self._color = color
            self.update_style()
            self.colorChanged.emit(color)

    def get_color(self):
        """获取颜色"""
        return self._color

    def set_color(self, color):
        """设置颜色"""
        self._color = color
        self.update_style()


class AdvancedIconGenerator(QMainWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        self.current_icons = []
        self.worker = None
        self.size_settings = {}
        self._start_maximized = False
        self.preview_timer = QTimer()
        self.preview_timer.setInterval(500)  # 500ms
        self.preview_timer.setSingleShot(True)  # 设置为单次触发
        self.preview_timer.timeout.connect(self.update_realtime_preview)

        # 设置持久化：实时自动保存（防抖） + 退出强制保存
        self.settings_timer = QTimer(self)
        self.settings_timer.setSingleShot(True)
        self.settings_timer.setInterval(800)  # 800ms 防抖
        self.settings_timer.timeout.connect(self._save_settings_now)

        self.setup_ui()
        self.setup_status_bar()
        self.setup_connections()
        self._load_settings()        # 启动时恢复上次设置
        self._connect_autosave()     # 所有控件变更 → 实时自动保存

    def closeEvent(self, event):
        """关闭事件 - 清理资源并强制保存设置"""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(2000)  # 等待2秒
        self._save_settings_now()   # 退出时立即持久保存
        event.accept()

    # ============ 设置持久化（实时自动保存 + 持久保存） ============
    def settings_path(self):
        """设置文件路径（兼容打包后 exe 目录，源码用文件目录）"""
        if getattr(sys, 'frozen', False):
            base = os.path.dirname(sys.executable)
        else:
            base = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base, 'ai_icon_generator_settings.json')

    def autosave(self):
        """实时自动保存入口：控件变化后防抖延迟写盘"""
        self.settings_timer.start()

    def _collect_settings(self):
        """收集当前所有控件值到字典"""
        s = {}
        # 图片转图标
        s['image_path'] = self.image_path_edit.text()
        s['image_brightness'] = self.brightness_slider.value()
        s['image_contrast'] = self.contrast_slider.value()
        s['image_saturation'] = self.saturation_slider.value()
        s['image_alpha'] = self.alpha_slider.value()
        s['image_effect'] = self.effect_combo.currentText()
        s['image_shape'] = self.shape_combo.currentText()
        s['image_radius'] = self.radius_spin.value()
        s['image_preset_sizes'] = self.preset_sizes_edit.text()
        s['image_custom_size'] = self.custom_size_edit.text()
        s['image_customize'] = self.customize_check.isChecked()
        s['image_size_settings'] = self.size_settings
        # 文字转图标
        s['text_content'] = self.text_edit.text()
        s['text_font'] = self.font_combo.currentText()
        s['text_font_size'] = self.font_size_spin.value()
        s['text_style'] = self.style_combo.currentText()
        s['text_color'] = self.text_color_btn.get_color().name()
        s['text_bg_type'] = self.bg_type_combo.currentText()
        s['text_bg_color'] = self.bg_color_btn.get_color().name()
        s['text_bg_color2'] = self.bg_color2_btn.get_color().name()
        s['text_bg_alpha'] = self.bg_alpha_slider.value()
        s['text_gradient_dir'] = self.gradient_combo.currentText()
        s['text_shape'] = self.text_shape_combo.currentText()
        s['text_radius'] = self.text_radius_spin.value()
        s['text_preset_sizes'] = self.text_preset_sizes.text()
        s['text_custom_size'] = self.text_custom_size.text()
        # SVG 转图标
        s['svg_code'] = self.svg_text.toPlainText()
        s['svg_preset_sizes'] = self.svg_preset_sizes.text()
        s['svg_custom_size'] = self.svg_custom_size.text()
        s['svg_bg_color'] = self.svg_bg_color_btn.get_color().name()
        s['svg_alpha'] = self.svg_alpha_slider.value()
        # Emoji 转图标
        s['emoji_char'] = self.emoji_edit.text()
        s['emoji_preset_sizes'] = self.emoji_preset_sizes.text()
        s['emoji_custom_size'] = self.emoji_custom_size.text()
        s['emoji_bg_color'] = self.emoji_bg_color_btn.get_color().name()
        s['emoji_alpha'] = self.emoji_alpha_slider.value()
        # Unicode 转图标
        s['unicode_char'] = self.unicode_edit.text()
        s['unicode_font'] = self.unicode_font_combo.currentText()
        s['unicode_font_size'] = self.unicode_font_size.value()
        s['unicode_color'] = self.unicode_color_btn.get_color().name()
        s['unicode_preset_sizes'] = self.unicode_preset_sizes.text()
        s['unicode_custom_size'] = self.unicode_custom_size.text()
        s['unicode_bg_color'] = self.unicode_bg_color_btn.get_color().name()
        s['unicode_alpha'] = self.unicode_alpha_slider.value()
        # CSS 转图标
        s['css_code'] = self.css_text.toPlainText()
        s['css_preset_sizes'] = self.css_preset_sizes.text()
        s['css_custom_size'] = self.css_custom_size.text()
        # 图表转图标
        s['chart_type'] = self.chart_type_combo.currentText()
        s['chart_data'] = self.chart_data_text.toPlainText()
        s['chart_bg_color'] = self.chart_bg_color_btn.get_color().name()
        s['chart_alpha'] = self.chart_alpha_slider.value()
        s['chart_preset_sizes'] = self.chart_preset_sizes.text()
        s['chart_custom_size'] = self.chart_custom_size.text()
        # 输出与窗口
        s['output_format'] = self.format_combo.currentText()
        s['output_quality'] = self.quality_spin.value()
        geom = self.geometry()
        s['window_geometry'] = [geom.x(), geom.y(), geom.width(), geom.height()]
        s['window_maximized'] = self.isMaximized()
        s['last_updated'] = time.strftime('%Y-%m-%d %H:%M:%S')
        return s

    def _save_settings_now(self):
        """立即持久保存设置（原子写入，防止写一半损坏）"""
        try:
            data = self._collect_settings()
            path = self.settings_path()
            tmp = path + '.tmp'
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, path)
        except Exception as e:
            print(f"保存设置失败: {e}")

    def _load_settings(self):
        """启动时读取设置并应用到控件"""
        path = self.settings_path()
        if not os.path.exists(path):
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"读取设置失败: {e}")
            return
        if not isinstance(data, dict):
            return
        self._apply_settings(data)

    def _apply_settings(self, data):
        """把设置值应用到控件（blockSignals 避免加载时触发保存/预览）"""
        def set_combo(combo, key):
            if key in data:
                combo.blockSignals(True)
                combo.setCurrentText(str(data[key]))
                combo.blockSignals(False)

        def set_text(edit, key):
            if key in data:
                edit.blockSignals(True)
                edit.setText(str(data[key]))
                edit.blockSignals(False)

        def set_plain(edit, key):
            if key in data:
                edit.blockSignals(True)
                edit.setPlainText(str(data[key]))
                edit.blockSignals(False)

        def set_spin(spin, key):
            if key in data:
                spin.blockSignals(True)
                try:
                    spin.setValue(int(data[key]))
                except (TypeError, ValueError):
                    pass
                spin.blockSignals(False)

        def set_slider(slider, key):
            if key in data:
                slider.blockSignals(True)
                try:
                    slider.setValue(int(data[key]))
                except (TypeError, ValueError):
                    pass
                slider.blockSignals(False)

        def set_check(check, key):
            if key in data:
                check.blockSignals(True)
                check.setChecked(bool(data[key]))
                check.blockSignals(False)

        def set_color(btn, key):
            if key in data:
                btn.blockSignals(True)
                try:
                    btn.set_color(QColor(str(data[key])))
                except Exception:
                    pass
                btn.blockSignals(False)

        # 图片转图标
        set_text(self.image_path_edit, 'image_path')
        set_slider(self.brightness_slider, 'image_brightness')
        set_slider(self.contrast_slider, 'image_contrast')
        set_slider(self.saturation_slider, 'image_saturation')
        set_slider(self.alpha_slider, 'image_alpha')
        set_combo(self.effect_combo, 'image_effect')
        set_combo(self.shape_combo, 'image_shape')
        set_spin(self.radius_spin, 'image_radius')
        set_text(self.preset_sizes_edit, 'image_preset_sizes')
        set_text(self.custom_size_edit, 'image_custom_size')
        set_check(self.customize_check, 'image_customize')
        if isinstance(data.get('image_size_settings'), dict):
            self.size_settings = data['image_size_settings']
        # 文字转图标
        set_text(self.text_edit, 'text_content')
        set_combo(self.font_combo, 'text_font')
        set_spin(self.font_size_spin, 'text_font_size')
        set_combo(self.style_combo, 'text_style')
        set_color(self.text_color_btn, 'text_color')
        set_combo(self.bg_type_combo, 'text_bg_type')
        set_color(self.bg_color_btn, 'text_bg_color')
        set_color(self.bg_color2_btn, 'text_bg_color2')
        set_slider(self.bg_alpha_slider, 'text_bg_alpha')
        set_combo(self.gradient_combo, 'text_gradient_dir')
        set_combo(self.text_shape_combo, 'text_shape')
        set_spin(self.text_radius_spin, 'text_radius')
        set_text(self.text_preset_sizes, 'text_preset_sizes')
        set_text(self.text_custom_size, 'text_custom_size')
        # SVG 转图标
        set_plain(self.svg_text, 'svg_code')
        set_text(self.svg_preset_sizes, 'svg_preset_sizes')
        set_text(self.svg_custom_size, 'svg_custom_size')
        set_color(self.svg_bg_color_btn, 'svg_bg_color')
        set_slider(self.svg_alpha_slider, 'svg_alpha')
        # Emoji 转图标
        set_text(self.emoji_edit, 'emoji_char')
        set_text(self.emoji_preset_sizes, 'emoji_preset_sizes')
        set_text(self.emoji_custom_size, 'emoji_custom_size')
        set_color(self.emoji_bg_color_btn, 'emoji_bg_color')
        set_slider(self.emoji_alpha_slider, 'emoji_alpha')
        # Unicode 转图标
        set_text(self.unicode_edit, 'unicode_char')
        set_combo(self.unicode_font_combo, 'unicode_font')
        set_spin(self.unicode_font_size, 'unicode_font_size')
        set_color(self.unicode_color_btn, 'unicode_color')
        set_text(self.unicode_preset_sizes, 'unicode_preset_sizes')
        set_text(self.unicode_custom_size, 'unicode_custom_size')
        set_color(self.unicode_bg_color_btn, 'unicode_bg_color')
        set_slider(self.unicode_alpha_slider, 'unicode_alpha')
        # CSS 转图标
        set_plain(self.css_text, 'css_code')
        set_text(self.css_preset_sizes, 'css_preset_sizes')
        set_text(self.css_custom_size, 'css_custom_size')
        # 图表转图标
        set_combo(self.chart_type_combo, 'chart_type')
        set_plain(self.chart_data_text, 'chart_data')
        set_color(self.chart_bg_color_btn, 'chart_bg_color')
        set_slider(self.chart_alpha_slider, 'chart_alpha')
        set_text(self.chart_preset_sizes, 'chart_preset_sizes')
        set_text(self.chart_custom_size, 'chart_custom_size')
        # 输出
        set_combo(self.format_combo, 'output_format')
        set_spin(self.quality_spin, 'output_quality')

        # 刷新依赖控件的显示状态与标签（不触发保存/对话框）
        self.update_brightness_label()
        self.update_contrast_label()
        self.update_saturation_label()
        self.update_alpha_label()
        self.on_bg_type_changed()

        # 窗口几何恢复
        geom = data.get('window_geometry')
        if isinstance(geom, list) and len(geom) == 4:
            try:
                self.setGeometry(int(geom[0]), int(geom[1]), int(geom[2]), int(geom[3]))
            except Exception:
                pass
        self._start_maximized = bool(data.get('window_maximized', False))

    def _connect_autosave(self):
        """把所有控件的变更信号接到实时自动保存"""
        # 图片转图标
        self.image_path_edit.textChanged.connect(self.autosave)
        self.brightness_slider.valueChanged.connect(self.autosave)
        self.contrast_slider.valueChanged.connect(self.autosave)
        self.saturation_slider.valueChanged.connect(self.autosave)
        self.alpha_slider.valueChanged.connect(self.autosave)
        self.effect_combo.currentTextChanged.connect(self.autosave)
        self.shape_combo.currentTextChanged.connect(self.autosave)
        self.radius_spin.valueChanged.connect(self.autosave)
        self.preset_sizes_edit.textChanged.connect(self.autosave)
        self.custom_size_edit.textChanged.connect(self.autosave)
        self.customize_check.toggled.connect(self.autosave)
        # 文字转图标
        self.text_edit.textChanged.connect(self.autosave)
        self.font_combo.currentTextChanged.connect(self.autosave)
        self.font_size_spin.valueChanged.connect(self.autosave)
        self.style_combo.currentTextChanged.connect(self.autosave)
        self.text_color_btn.colorChanged.connect(self.autosave)
        self.bg_type_combo.currentTextChanged.connect(self.autosave)
        self.bg_color_btn.colorChanged.connect(self.autosave)
        self.bg_color2_btn.colorChanged.connect(self.autosave)
        self.bg_alpha_slider.valueChanged.connect(self.autosave)
        self.gradient_combo.currentTextChanged.connect(self.autosave)
        self.text_shape_combo.currentTextChanged.connect(self.autosave)
        self.text_radius_spin.valueChanged.connect(self.autosave)
        self.text_preset_sizes.textChanged.connect(self.autosave)
        self.text_custom_size.textChanged.connect(self.autosave)
        # SVG 转图标
        self.svg_text.textChanged.connect(self.autosave)
        self.svg_preset_sizes.textChanged.connect(self.autosave)
        self.svg_custom_size.textChanged.connect(self.autosave)
        self.svg_bg_color_btn.colorChanged.connect(self.autosave)
        self.svg_alpha_slider.valueChanged.connect(self.autosave)
        # Emoji 转图标
        self.emoji_edit.textChanged.connect(self.autosave)
        self.emoji_preset_sizes.textChanged.connect(self.autosave)
        self.emoji_custom_size.textChanged.connect(self.autosave)
        self.emoji_bg_color_btn.colorChanged.connect(self.autosave)
        self.emoji_alpha_slider.valueChanged.connect(self.autosave)
        # Unicode 转图标
        self.unicode_edit.textChanged.connect(self.autosave)
        self.unicode_font_combo.currentTextChanged.connect(self.autosave)
        self.unicode_font_size.valueChanged.connect(self.autosave)
        self.unicode_color_btn.colorChanged.connect(self.autosave)
        self.unicode_preset_sizes.textChanged.connect(self.autosave)
        self.unicode_custom_size.textChanged.connect(self.autosave)
        self.unicode_bg_color_btn.colorChanged.connect(self.autosave)
        self.unicode_alpha_slider.valueChanged.connect(self.autosave)
        # CSS 转图标
        self.css_text.textChanged.connect(self.autosave)
        self.css_preset_sizes.textChanged.connect(self.autosave)
        self.css_custom_size.textChanged.connect(self.autosave)
        # 图表转图标
        self.chart_type_combo.currentTextChanged.connect(self.autosave)
        self.chart_data_text.textChanged.connect(self.autosave)
        self.chart_bg_color_btn.colorChanged.connect(self.autosave)
        self.chart_alpha_slider.valueChanged.connect(self.autosave)
        self.chart_preset_sizes.textChanged.connect(self.autosave)
        self.chart_custom_size.textChanged.connect(self.autosave)
        # 输出
        self.format_combo.currentTextChanged.connect(self.autosave)
        self.quality_spin.valueChanged.connect(self.autosave)

    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle(f"高级图标生成工具 v{__version__}")
        self.setMinimumSize(900, 800)

        # 中央控件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)

        # 标题
        title_layout = QHBoxLayout()
        title = QLabel("高级图标生成工具")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        title_layout.addWidget(title)

        help_btn = QPushButton("帮助")
        help_btn.clicked.connect(self.show_help)
        title_layout.addWidget(help_btn, alignment=Qt.AlignRight)

        main_layout.addLayout(title_layout)

        # 标签页
        self.tab_widget = QTabWidget()

        # 创建各标签页
        self.image_tab = self.create_image_tab()
        self.text_tab = self.create_text_tab()
        self.svg_tab = self.create_svg_tab()
        self.emoji_tab = self.create_emoji_tab()
        self.unicode_tab = self.create_unicode_tab()
        self.css_tab = self.create_css_tab()
        self.matplotlib_tab = self.create_matplotlib_tab()

        self.tab_widget.addTab(self.image_tab, " 🖼️ 图片转图标 ")
        self.tab_widget.addTab(self.text_tab, " 🔤 文字转图标 ")
        self.tab_widget.addTab(self.svg_tab, " 🖍️ SVG转图标 ")
        self.tab_widget.addTab(self.emoji_tab, " 😊 Emoji转图标 ")
        self.tab_widget.addTab(self.unicode_tab, " ✨ Unicode转图标 ")
        self.tab_widget.addTab(self.css_tab, " 🎨 CSS转图标 ")
        self.tab_widget.addTab(self.matplotlib_tab, " 📊 图表转图标 ")

        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        main_layout.addWidget(self.tab_widget)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # 预览和保存区域
        self.setup_preview_section(main_layout)

    def setup_connections(self):
        """设置信号连接"""
        # 图片标签页连接
        self.brightness_slider.valueChanged.connect(self.update_brightness_label)
        self.contrast_slider.valueChanged.connect(self.update_contrast_label)
        self.saturation_slider.valueChanged.connect(self.update_saturation_label)
        self.alpha_slider.valueChanged.connect(self.update_alpha_label)

    def setup_status_bar(self):
        """设置状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("准备就绪")

    def setup_preview_section(self, parent_layout):
        """设置预览和保存区域"""
        group = QGroupBox("最终预览和保存")
        layout = QVBoxLayout(group)

        # 预览区域
        self.preview_widget = IconPreviewWidget()
        layout.addWidget(self.preview_widget)

        # 控制区域
        controls = QHBoxLayout()

        # 实时预览
        controls.addWidget(QLabel("实时预览:"))

        self.realtime_preview = QLabel()
        self.realtime_preview.setFixedSize(60, 60)
        self.realtime_preview.setStyleSheet("border: 1px solid gray;")
        self.realtime_preview.setAlignment(Qt.AlignCenter)
        controls.addWidget(self.realtime_preview)

        # 按钮
        self.save_btn = QPushButton("保存图标")
        self.save_btn.clicked.connect(self.save_icons)
        self.save_btn.setEnabled(False)
        controls.addWidget(self.save_btn)

        self.clear_btn = QPushButton("清除预览")
        self.clear_btn.clicked.connect(self.clear_preview)
        controls.addWidget(self.clear_btn)

        # 输出格式
        controls.addWidget(QLabel("输出格式:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["ICO (多尺寸)", "PNG", "JPG", "WebP"])
        controls.addWidget(self.format_combo)

        # 质量
        controls.addWidget(QLabel("质量:"))
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(95)
        controls.addWidget(self.quality_spin)

        # 尺寸显示
        self.sizes_label = QLabel("包含尺寸: 无")
        controls.addWidget(self.sizes_label)

        layout.addLayout(controls)
        parent_layout.addWidget(group)

    # 更新标签的方法
    def update_brightness_label(self):
        self.brightness_label.setText(f"{self.brightness_slider.value()/100:.1f}")
        self.schedule_preview_update()

    def update_contrast_label(self):
        self.contrast_label.setText(f"{self.contrast_slider.value()/100:.1f}")
        self.schedule_preview_update()

    def update_saturation_label(self):
        self.saturation_label.setText(f"{self.saturation_slider.value()/100:.1f}")
        self.schedule_preview_update()

    def update_alpha_label(self):
        self.alpha_label.setText(f"{self.alpha_slider.value()/100:.1f}")
        self.schedule_preview_update()

    def create_image_tab(self):
        """创建图片转图标标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 创建可滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # 图片选择
        file_group = QGroupBox("图片设置")
        file_layout = QHBoxLayout(file_group)

        self.image_path_edit = QLineEdit()
        file_layout.addWidget(self.image_path_edit)

        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.select_image)
        file_layout.addWidget(browse_btn)

        scroll_layout.addWidget(file_group)

        # 图片调整
        adjust_group = QGroupBox("图片调整")
        adjust_layout = QGridLayout(adjust_group)

        # 亮度
        adjust_layout.addWidget(QLabel("亮度:"), 0, 0)
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(10, 200)
        self.brightness_slider.setValue(100)
        adjust_layout.addWidget(self.brightness_slider, 0, 1)

        self.brightness_label = QLabel("1.0")
        adjust_layout.addWidget(self.brightness_label, 0, 2)

        # 对比度
        adjust_layout.addWidget(QLabel("对比度:"), 1, 0)
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setRange(10, 200)
        self.contrast_slider.setValue(100)
        adjust_layout.addWidget(self.contrast_slider, 1, 1)

        self.contrast_label = QLabel("1.0")
        adjust_layout.addWidget(self.contrast_label, 1, 2)

        # 饱和度
        adjust_layout.addWidget(QLabel("饱和度:"), 2, 0)
        self.saturation_slider = QSlider(Qt.Horizontal)
        self.saturation_slider.setRange(0, 200)
        self.saturation_slider.setValue(100)
        adjust_layout.addWidget(self.saturation_slider, 2, 1)

        self.saturation_label = QLabel("1.0")
        adjust_layout.addWidget(self.saturation_label, 2, 2)

        # 透明度
        adjust_layout.addWidget(QLabel("透明度:"), 3, 0)
        self.alpha_slider = QSlider(Qt.Horizontal)
        self.alpha_slider.setRange(0, 100)
        self.alpha_slider.setValue(100)
        adjust_layout.addWidget(self.alpha_slider, 3, 1)

        self.alpha_label = QLabel("1.0")
        adjust_layout.addWidget(self.alpha_label, 3, 2)

        # 效果
        adjust_layout.addWidget(QLabel("效果:"), 0, 3)
        self.effect_combo = QComboBox()
        effects = ["无", "模糊", "轮廓", "锐化", "浮雕", "边缘增强",
                  "平滑", "细节增强", "反色", "黑白", "棕褐色",
                  "油画", "像素化", "高斯模糊", "查找边缘"]
        self.effect_combo.addItems(effects)
        adjust_layout.addWidget(self.effect_combo, 0, 4)

        scroll_layout.addWidget(adjust_group)

        # 形状蒙版
        shape_group = QGroupBox("形状蒙版")
        shape_layout = QGridLayout(shape_group)

        shape_layout.addWidget(QLabel("形状:"), 0, 0)
        self.shape_combo = QComboBox()
        shapes = ["方形", "圆形", "圆角矩形", "星形", "心形", "三角形"]
        self.shape_combo.addItems(shapes)
        shape_layout.addWidget(self.shape_combo, 0, 1)

        shape_layout.addWidget(QLabel("圆角半径:"), 1, 0)
        self.radius_spin = QSpinBox()
        self.radius_spin.setRange(0, 100)
        self.radius_spin.setValue(20)
        shape_layout.addWidget(self.radius_spin, 1, 1)

        scroll_layout.addWidget(shape_group)

        # 尺寸设置
        size_group = QGroupBox("尺寸设置")
        size_layout = QGridLayout(size_group)

        size_layout.addWidget(QLabel("预设尺寸:"), 0, 0)
        self.preset_sizes_edit = QLineEdit("16,24,32,48,64,128,256")
        size_layout.addWidget(self.preset_sizes_edit, 0, 1)

        size_layout.addWidget(QLabel("自定义尺寸:"), 1, 0)
        self.custom_size_edit = QLineEdit()
        size_layout.addWidget(self.custom_size_edit, 1, 1)

        self.customize_check = QCheckBox("单独定制尺寸")
        self.customize_check.toggled.connect(self.on_customize_toggled)
        size_layout.addWidget(self.customize_check, 2, 0, 1, 2)

        scroll_layout.addWidget(size_group)

        # 生成按钮
        self.image_generate_btn = QPushButton("生成预览")
        self.image_generate_btn.clicked.connect(self.start_image_preview)
        scroll_layout.addWidget(self.image_generate_btn)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)

        layout.addWidget(scroll)
        return tab

    def create_text_tab(self):
        """创建文字转图标标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # 文字输入
        text_group = QGroupBox("文字内容")
        text_layout = QVBoxLayout(text_group)
        self.text_edit = QLineEdit()
        self.text_edit.setText("文本")
        text_layout.addWidget(self.text_edit)
        scroll_layout.addWidget(text_group)

        # 字体设置
        font_group = QGroupBox("字体设置")
        font_layout = QGridLayout(font_group)

        font_layout.addWidget(QLabel("字体:"), 0, 0)
        self.font_combo = QComboBox()
        self.font_combo.setEditable(True)
        self.font_combo.addItems(["微软雅黑", "Arial", "Times New Roman", "Courier New"])
        font_layout.addWidget(self.font_combo, 0, 1)

        font_layout.addWidget(QLabel("大小:"), 0, 2)
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 300)
        self.font_size_spin.setValue(100)
        font_layout.addWidget(self.font_size_spin, 0, 3)

        font_layout.addWidget(QLabel("样式:"), 1, 0)
        self.style_combo = QComboBox()
        self.style_combo.addItems(["normal", "bold", "italic", "bold italic"])
        font_layout.addWidget(self.style_combo, 1, 1)

        font_layout.addWidget(QLabel("文字颜色:"), 1, 2)
        self.text_color_btn = ColorButton(QColor(0, 0, 0))
        font_layout.addWidget(self.text_color_btn, 1, 3)

        scroll_layout.addWidget(font_group)

        # 背景设置
        bg_group = QGroupBox("背景设置")
        bg_layout = QGridLayout(bg_group)

        bg_layout.addWidget(QLabel("背景类型:"), 0, 0)
        self.bg_type_combo = QComboBox()
        self.bg_type_combo.addItems(["纯色", "渐变", "透明"])
        self.bg_type_combo.currentTextChanged.connect(self.on_bg_type_changed)
        bg_layout.addWidget(self.bg_type_combo, 0, 1)

        bg_layout.addWidget(QLabel("背景颜色:"), 0, 2)
        self.bg_color_btn = ColorButton(QColor(255, 255, 255))
        bg_layout.addWidget(self.bg_color_btn, 0, 3)

        # 渐变控件
        self.gradient_label = QLabel("渐变方向:")
        bg_layout.addWidget(self.gradient_label, 1, 0)

        self.gradient_combo = QComboBox()
        self.gradient_combo.addItems(["水平", "垂直", "对角"])
        bg_layout.addWidget(self.gradient_combo, 1, 1)

        self.bg_color2_label = QLabel("第二颜色:")
        bg_layout.addWidget(self.bg_color2_label, 1, 2)

        self.bg_color2_btn = ColorButton(QColor(204, 204, 204))
        bg_layout.addWidget(self.bg_color2_btn, 1, 3)

        bg_layout.addWidget(QLabel("透明度:"), 2, 0)
        self.bg_alpha_slider = QSlider(Qt.Horizontal)
        self.bg_alpha_slider.setRange(0, 100)
        self.bg_alpha_slider.setValue(100)
        bg_layout.addWidget(self.bg_alpha_slider, 2, 1, 1, 3)

        self.on_bg_type_changed()  # 初始化渐变控件状态
        scroll_layout.addWidget(bg_group)

        # 形状蒙版设置
        shape_group = QGroupBox("形状蒙版")
        shape_layout = QGridLayout(shape_group)

        shape_layout.addWidget(QLabel("形状:"), 0, 0)
        self.text_shape_combo = QComboBox()
        shapes = ["方形", "圆形", "圆角矩形", "星形", "心形", "三角形"]
        self.text_shape_combo.addItems(shapes)
        shape_layout.addWidget(self.text_shape_combo, 0, 1)

        shape_layout.addWidget(QLabel("圆角半径:"), 1, 0)
        self.text_radius_spin = QSpinBox()
        self.text_radius_spin.setRange(0, 100)
        self.text_radius_spin.setValue(20)
        shape_layout.addWidget(self.text_radius_spin, 1, 1)

        scroll_layout.addWidget(shape_group)

        # 尺寸设置
        size_group = QGroupBox("图标尺寸设置")
        size_layout = QGridLayout(size_group)

        size_layout.addWidget(QLabel("预设尺寸:"), 0, 0)
        self.text_preset_sizes = QLineEdit("16,24,32,48,64,128,256")
        size_layout.addWidget(self.text_preset_sizes, 0, 1)

        size_layout.addWidget(QLabel("自定义尺寸:"), 1, 0)
        self.text_custom_size = QLineEdit()
        size_layout.addWidget(self.text_custom_size, 1, 1)

        scroll_layout.addWidget(size_group)

        # 生成按钮
        self.text_generate_btn = QPushButton("生成预览")
        self.text_generate_btn.clicked.connect(self.start_text_preview)
        scroll_layout.addWidget(self.text_generate_btn)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)

        layout.addWidget(scroll)
        return tab

    def create_svg_tab(self):
        """创建SVG转图标标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # SVG输入
        svg_group = QGroupBox("SVG代码")
        svg_layout = QVBoxLayout(svg_group)
        self.svg_text = QTextEdit()
        svg_layout.addWidget(self.svg_text)

        # 示例按钮
        example_layout = QHBoxLayout()
        example_btn1 = QPushButton("示例1: 圆形")
        example_btn1.clicked.connect(lambda: self.load_svg_example(1))
        example_layout.addWidget(example_btn1)

        example_btn2 = QPushButton("示例2: 矩形")
        example_btn2.clicked.connect(lambda: self.load_svg_example(2))
        example_layout.addWidget(example_btn2)

        example_btn3 = QPushButton("示例3: 星形")
        example_btn3.clicked.connect(lambda: self.load_svg_example(3))
        example_layout.addWidget(example_btn3)

        example_btn4 = QPushButton("示例4: 路径")
        example_btn4.clicked.connect(lambda: self.load_svg_example(4))
        example_layout.addWidget(example_btn4)

        svg_layout.addLayout(example_layout)
        layout.addWidget(svg_group)

        # 设置
        settings_group = QGroupBox("设置")
        settings_layout = QGridLayout(settings_group)

        settings_layout.addWidget(QLabel("预设尺寸:"), 0, 0)
        self.svg_preset_sizes = QLineEdit("16,24,32,48,64,128,256")
        settings_layout.addWidget(self.svg_preset_sizes, 0, 1)

        settings_layout.addWidget(QLabel("自定义尺寸:"), 1, 0)
        self.svg_custom_size = QLineEdit()
        settings_layout.addWidget(self.svg_custom_size, 1, 1)

        settings_layout.addWidget(QLabel("背景颜色:"), 0, 2)
        self.svg_bg_color_btn = ColorButton(QColor(255, 255, 255))
        settings_layout.addWidget(self.svg_bg_color_btn, 0, 3)

        settings_layout.addWidget(QLabel("透明度:"), 1, 2)
        self.svg_alpha_slider = QSlider(Qt.Horizontal)
        self.svg_alpha_slider.setRange(0, 100)
        self.svg_alpha_slider.setValue(100)
        settings_layout.addWidget(self.svg_alpha_slider, 1, 3)

        layout.addWidget(settings_group)

        # 生成按钮
        self.svg_generate_btn = QPushButton("生成预览")
        self.svg_generate_btn.clicked.connect(self.start_svg_preview)
        layout.addWidget(self.svg_generate_btn)

        return tab

    def create_emoji_tab(self):
        """创建Emoji转图标标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        if not EMOJI_SUPPORT:
            label = QLabel("需要安装emoji模块才能使用此功能\n请运行: pip install emoji")
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)
            return tab

        # Emoji选择
        emoji_group = QGroupBox("选择Emoji")
        emoji_layout = QVBoxLayout(emoji_group)

        # 分类按钮
        btn_layout = QHBoxLayout()
        categories = ["笑脸", "动物", "食物", "活动", "旅行", "物品", "符号", "旗帜"]
        for cat in categories:
            btn = QPushButton(cat)
            btn.clicked.connect(lambda checked, c=cat: self.show_emoji_palette(c))
            btn_layout.addWidget(btn)
        emoji_layout.addLayout(btn_layout)

        self.emoji_edit = QLineEdit()
        self.emoji_edit.setText("😊")
        emoji_layout.addWidget(self.emoji_edit)

        layout.addWidget(emoji_group)

        # 设置
        settings_group = QGroupBox("设置")
        settings_layout = QGridLayout(settings_group)

        settings_layout.addWidget(QLabel("预设尺寸:"), 0, 0)
        self.emoji_preset_sizes = QLineEdit("16,24,32,48,64,128,256")
        settings_layout.addWidget(self.emoji_preset_sizes, 0, 1)

        settings_layout.addWidget(QLabel("自定义尺寸:"), 1, 0)
        self.emoji_custom_size = QLineEdit()
        settings_layout.addWidget(self.emoji_custom_size, 1, 1)

        settings_layout.addWidget(QLabel("背景颜色:"), 0, 2)
        self.emoji_bg_color_btn = ColorButton(QColor(255, 255, 255))
        settings_layout.addWidget(self.emoji_bg_color_btn, 0, 3)

        settings_layout.addWidget(QLabel("透明度:"), 1, 2)
        self.emoji_alpha_slider = QSlider(Qt.Horizontal)
        self.emoji_alpha_slider.setRange(0, 100)
        self.emoji_alpha_slider.setValue(100)
        settings_layout.addWidget(self.emoji_alpha_slider, 1, 3)

        layout.addWidget(settings_group)

        # 生成按钮
        self.emoji_generate_btn = QPushButton("生成预览")
        self.emoji_generate_btn.clicked.connect(self.start_emoji_preview)
        layout.addWidget(self.emoji_generate_btn)

        return tab

    def create_unicode_tab(self):
        """创建Unicode符号转图标标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Unicode选择
        unicode_group = QGroupBox("选择Unicode符号")
        unicode_layout = QVBoxLayout(unicode_group)

        btn_layout = QHBoxLayout()
        categories = ["数学", "几何", "箭头", "货币", "标点", "其他"]
        for cat in categories:
            btn = QPushButton(cat)
            btn.clicked.connect(lambda checked, c=cat: self.show_unicode_palette(c))
            btn_layout.addWidget(btn)
        unicode_layout.addLayout(btn_layout)

        self.unicode_edit = QLineEdit()
        self.unicode_edit.setText("★")
        unicode_layout.addWidget(self.unicode_edit)

        layout.addWidget(unicode_group)

        # 字体设置
        font_group = QGroupBox("字体设置")
        font_layout = QGridLayout(font_group)

        font_layout.addWidget(QLabel("字体:"), 0, 0)
        self.unicode_font_combo = QComboBox()
        self.unicode_font_combo.setEditable(True)
        self.unicode_font_combo.addItems(["Arial Unicode MS", "Segoe UI Symbol", "Symbola", "Noto Sans"])
        font_layout.addWidget(self.unicode_font_combo, 0, 1)

        font_layout.addWidget(QLabel("大小:"), 0, 2)
        self.unicode_font_size = QSpinBox()
        self.unicode_font_size.setRange(8, 300)
        self.unicode_font_size.setValue(100)
        font_layout.addWidget(self.unicode_font_size, 0, 3)

        font_layout.addWidget(QLabel("颜色:"), 1, 0)
        self.unicode_color_btn = ColorButton(QColor(0, 0, 0))
        font_layout.addWidget(self.unicode_color_btn, 1, 1)

        layout.addWidget(font_group)

        # 设置
        settings_group = QGroupBox("设置")
        settings_layout = QGridLayout(settings_group)

        settings_layout.addWidget(QLabel("预设尺寸:"), 0, 0)
        self.unicode_preset_sizes = QLineEdit("16,24,32,48,64,128,256")
        settings_layout.addWidget(self.unicode_preset_sizes, 0, 1)

        settings_layout.addWidget(QLabel("自定义尺寸:"), 1, 0)
        self.unicode_custom_size = QLineEdit()
        settings_layout.addWidget(self.unicode_custom_size, 1, 1)

        settings_layout.addWidget(QLabel("背景颜色:"), 0, 2)
        self.unicode_bg_color_btn = ColorButton(QColor(255, 255, 255))
        settings_layout.addWidget(self.unicode_bg_color_btn, 0, 3)

        settings_layout.addWidget(QLabel("透明度:"), 1, 2)
        self.unicode_alpha_slider = QSlider(Qt.Horizontal)
        self.unicode_alpha_slider.setRange(0, 100)
        self.unicode_alpha_slider.setValue(100)
        settings_layout.addWidget(self.unicode_alpha_slider, 1, 3)

        layout.addWidget(settings_group)

        # 生成按钮
        self.unicode_generate_btn = QPushButton("生成预览")
        self.unicode_generate_btn.clicked.connect(self.start_unicode_preview)
        layout.addWidget(self.unicode_generate_btn)

        return tab

    def create_css_tab(self):
        """创建CSS样式转图标标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # CSS输入
        css_group = QGroupBox("CSS样式")
        css_layout = QVBoxLayout(css_group)
        self.css_text = QTextEdit()
        css_layout.addWidget(self.css_text)

        # 示例按钮
        example_layout = QHBoxLayout()
        example_btn1 = QPushButton("示例1: 圆形")
        example_btn1.clicked.connect(lambda: self.load_css_example(1))
        example_layout.addWidget(example_btn1)

        example_btn2 = QPushButton("示例2: 按钮")
        example_btn2.clicked.connect(lambda: self.load_css_example(2))
        example_layout.addWidget(example_btn2)

        example_btn3 = QPushButton("示例3: 渐变")
        example_btn3.clicked.connect(lambda: self.load_css_example(3))
        example_layout.addWidget(example_btn3)

        example_btn4 = QPushButton("示例4: 阴影")
        example_btn4.clicked.connect(lambda: self.load_css_example(4))
        example_layout.addWidget(example_btn4)

        css_layout.addLayout(example_layout)
        layout.addWidget(css_group)

        # 尺寸设置
        size_group = QGroupBox("图标尺寸设置")
        size_layout = QGridLayout(size_group)

        size_layout.addWidget(QLabel("预设尺寸:"), 0, 0)
        self.css_preset_sizes = QLineEdit("16,24,32,48,64,128,256")
        size_layout.addWidget(self.css_preset_sizes, 0, 1)

        size_layout.addWidget(QLabel("自定义尺寸:"), 1, 0)
        self.css_custom_size = QLineEdit()
        size_layout.addWidget(self.css_custom_size, 1, 1)

        layout.addWidget(size_group)

        # 生成按钮
        self.css_generate_btn = QPushButton("生成预览")
        self.css_generate_btn.clicked.connect(self.start_css_preview)
        layout.addWidget(self.css_generate_btn)

        return tab

    def create_matplotlib_tab(self):
        """创建Matplotlib图表转图标标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        if not MATPLOTLIB_SUPPORT:
            label = QLabel("需要安装matplotlib模块才能使用此功能\n请运行: pip install matplotlib")
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)
            return tab

        # 图表类型
        type_group = QGroupBox("图表类型")
        type_layout = QHBoxLayout(type_group)
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(["折线图", "柱状图", "饼图", "散点图", "雷达图", "面积图"])
        type_layout.addWidget(self.chart_type_combo)
        layout.addWidget(type_group)

        # 数据输入
        data_group = QGroupBox("图表数据")
        data_layout = QVBoxLayout(data_group)
        self.chart_data_text = QTextEdit()
        data_layout.addWidget(self.chart_data_text)

        # 示例按钮
        example_layout = QHBoxLayout()
        example_btn1 = QPushButton("示例1: 简单数据")
        example_btn1.clicked.connect(lambda: self.load_chart_example(1))
        example_layout.addWidget(example_btn1)

        example_btn2 = QPushButton("示例2: 多系列")
        example_btn2.clicked.connect(lambda: self.load_chart_example(2))
        example_layout.addWidget(example_btn2)

        example_btn3 = QPushButton("示例3: 随机数据")
        example_btn3.clicked.connect(lambda: self.load_chart_example(3))
        example_layout.addWidget(example_btn3)

        data_layout.addLayout(example_layout)
        layout.addWidget(data_group)

        # 样式设置
        style_group = QGroupBox("图表样式")
        style_layout = QGridLayout(style_group)

        style_layout.addWidget(QLabel("背景颜色:"), 0, 0)
        self.chart_bg_color_btn = ColorButton(QColor(255, 255, 255))
        style_layout.addWidget(self.chart_bg_color_btn, 0, 1)

        style_layout.addWidget(QLabel("透明度:"), 0, 2)
        self.chart_alpha_slider = QSlider(Qt.Horizontal)
        self.chart_alpha_slider.setRange(0, 100)
        self.chart_alpha_slider.setValue(100)
        style_layout.addWidget(self.chart_alpha_slider, 0, 3)

        layout.addWidget(style_group)

        # 尺寸设置
        size_group = QGroupBox("图标尺寸设置")
        size_layout = QGridLayout(size_group)

        size_layout.addWidget(QLabel("预设尺寸:"), 0, 0)
        self.chart_preset_sizes = QLineEdit("16,24,32,48,64,128,256")
        size_layout.addWidget(self.chart_preset_sizes, 0, 1)

        size_layout.addWidget(QLabel("自定义尺寸:"), 1, 0)
        self.chart_custom_size = QLineEdit()
        size_layout.addWidget(self.chart_custom_size, 1, 1)

        layout.addWidget(size_group)

        # 生成按钮
        self.chart_generate_btn = QPushButton("生成预览")
        self.chart_generate_btn.clicked.connect(self.start_matplotlib_preview)
        layout.addWidget(self.chart_generate_btn)

        return tab

    # 事件处理方法
    def on_tab_changed(self, index):
        """标签页切换时更新实时预览"""
        self.schedule_preview_update()

    def schedule_preview_update(self):
        """调度实时预览更新"""
        if self.preview_timer.isActive():
            self.preview_timer.stop()
        self.preview_timer.start()

    def on_bg_type_changed(self):
        """背景类型变化时更新控件状态"""
        is_gradient = self.bg_type_combo.currentText() == "渐变"
        self.gradient_label.setVisible(is_gradient)
        self.gradient_combo.setVisible(is_gradient)
        self.bg_color2_label.setVisible(is_gradient)
        self.bg_color2_btn.setVisible(is_gradient)

    def on_customize_toggled(self, checked):
        """单独定制尺寸切换"""
        if checked:
            sizes = self.parse_sizes(
                self.preset_sizes_edit.text(),
                self.custom_size_edit.text()
            )
            if sizes:
                dialog = SizeSettingsDialog(sizes, self)
                if dialog.exec() == QDialog.Accepted:
                    self.size_settings = dialog.get_settings()

    # 工具方法
    def parse_sizes(self, preset, custom):
        """解析尺寸字符串"""
        sizes = set()

        # 预设尺寸
        if preset and preset.strip():
            for size in preset.split(','):
                try:
                    size = int(size.strip())
                    if 8 <= size <= 512:
                        sizes.add(size)
                except ValueError:
                    continue

        # 自定义尺寸
        if custom and custom.strip():
            for size in custom.split(','):
                try:
                    size = int(size.strip())
                    if 8 <= size <= 512:
                        sizes.add(size)
                except ValueError:
                    continue

        return sorted(list(sizes))

    def get_current_tab_index(self):
        """获取当前标签页索引"""
        return self.tab_widget.currentIndex()

    def get_current_generate_button(self):
        """获取当前标签页的生成按钮"""
        index = self.get_current_tab_index()
        buttons = [
            self.image_generate_btn,
            self.text_generate_btn,
            self.svg_generate_btn,
            self.emoji_generate_btn,
            self.unicode_generate_btn,
            self.css_generate_btn,
            self.chart_generate_btn
        ]
        return buttons[index] if index < len(buttons) else None

    def disable_current_button(self):
        """禁用当前生成按钮"""
        btn = self.get_current_generate_button()
        if btn:
            btn.setEnabled(False)

    def enable_current_button(self):
        """启用当前生成按钮"""
        btn = self.get_current_generate_button()
        if btn:
            btn.setEnabled(True)

    # 文件操作
    def select_image(self):
        """选择图片文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择图片",
            os.path.expanduser("~"),
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif);;所有文件 (*.*)"
        )
        if file_path:
            self.image_path_edit.setText(file_path)
            self.schedule_preview_update()

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
        self.svg_text.setText(examples.get(num, ""))
        self.schedule_preview_update()

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
        self.css_text.setText(examples.get(num, ""))
        self.schedule_preview_update()

    def load_chart_example(self, num):
        """加载图表示例"""
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
        self.chart_data_text.setText(examples.get(num, ""))
        self.schedule_preview_update()

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

        dialog = QDialog(self)
        dialog.setWindowTitle(f"选择 {category} Emoji")

        layout = QGridLayout(dialog)

        emoji_list = emoji_map.get(category, [])
        for i, emoji_char in enumerate(emoji_list):
            btn = QPushButton(emoji_char)
            btn.setFont(QFont("Segoe UI Emoji", 16))
            btn.clicked.connect(lambda checked, e=emoji_char: self.select_emoji(e, dialog))
            layout.addWidget(btn, i // 5, i % 5)

        dialog.exec()

    def select_emoji(self, emoji_char, dialog):
        """选择Emoji"""
        self.emoji_edit.setText(emoji_char)
        dialog.accept()
        self.schedule_preview_update()

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

        dialog = QDialog(self)
        dialog.setWindowTitle(f"选择 {category} Unicode符号")

        layout = QGridLayout(dialog)

        unicode_list = unicode_map.get(category, [])
        for i, unicode_char in enumerate(unicode_list):
            btn = QPushButton(unicode_char)
            btn.setFont(QFont("Arial Unicode MS", 16))
            btn.clicked.connect(lambda checked, u=unicode_char: self.select_unicode(u, dialog))
            layout.addWidget(btn, i // 5, i % 5)

        dialog.exec()

    def select_unicode(self, unicode_char, dialog):
        """选择Unicode符号"""
        self.unicode_edit.setText(unicode_char)
        dialog.accept()
        self.schedule_preview_update()

    # 预览生成方法
    def start_image_preview(self):
        """开始图片预览"""
        if not self.image_path_edit.text() or not os.path.isfile(self.image_path_edit.text()):
            QMessageBox.critical(self, "错误", "请选择有效的图片文件")
            return

        sizes = self.parse_sizes(
            self.preset_sizes_edit.text(),
            self.custom_size_edit.text()
        )
        if not sizes:
            QMessageBox.critical(self, "错误", "请输入有效的尺寸")
            return

        params = {
            'sizes': sizes,
            'image_path': self.image_path_edit.text(),
            'brightness': self.brightness_slider.value() / 100.0,
            'contrast': self.contrast_slider.value() / 100.0,
            'saturation': self.saturation_slider.value() / 100.0,
            'alpha': self.alpha_slider.value() / 100.0,
            'effect': self.effect_combo.currentText(),
            'shape': self.shape_combo.currentText(),
            'radius': self.radius_spin.value(),
            'customize_sizes': self.customize_check.isChecked(),
            'size_settings': self.size_settings
        }

        self.start_worker('image', params)

    def start_text_preview(self):
        """开始文字预览"""
        if not self.text_edit.text():
            QMessageBox.critical(self, "错误", "请输入文字内容")
            return

        sizes = self.parse_sizes(
            self.text_preset_sizes.text(),
            self.text_custom_size.text()
        )
        if not sizes:
            QMessageBox.critical(self, "错误", "请输入有效的尺寸")
            return

        params = {
            'sizes': sizes,
            'text': self.text_edit.text(),
            'font_family': self.font_combo.currentText(),
            'font_size': self.font_size_spin.value(),
            'font_style': self.style_combo.currentText(),
            'text_color': self.text_color_btn.get_color().name(),
            'bg_type': self.bg_type_combo.currentText(),
            'bg_color': self.bg_color_btn.get_color().name(),
            'bg_color2': self.bg_color2_btn.get_color().name(),
            'bg_alpha': self.bg_alpha_slider.value() / 100.0,
            'gradient_dir': self.gradient_combo.currentText(),
            'shape': self.text_shape_combo.currentText(),
            'radius': self.text_radius_spin.value()
        }

        self.start_worker('text', params)

    def start_svg_preview(self):
        """开始SVG预览"""
        svg_code = self.svg_text.toPlainText().strip()
        if not svg_code:
            QMessageBox.critical(self, "错误", "请输入SVG代码")
            return

        sizes = self.parse_sizes(
            self.svg_preset_sizes.text(),
            self.svg_custom_size.text()
        )
        if not sizes:
            QMessageBox.critical(self, "错误", "请输入有效的尺寸")
            return

        params = {
            'sizes': sizes,
            'svg_code': svg_code,
            'bg_color': self.svg_bg_color_btn.get_color().name(),
            'alpha': self.svg_alpha_slider.value() / 100.0
        }

        self.start_worker('svg', params)

    def start_emoji_preview(self):
        """开始Emoji预览"""
        emoji_char = self.emoji_edit.text()
        if not emoji_char:
            QMessageBox.critical(self, "错误", "请选择Emoji")
            return

        sizes = self.parse_sizes(
            self.emoji_preset_sizes.text(),
            self.emoji_custom_size.text()
        )
        if not sizes:
            QMessageBox.critical(self, "错误", "请输入有效的尺寸")
            return

        params = {
            'sizes': sizes,
            'emoji': emoji_char,
            'bg_color': self.emoji_bg_color_btn.get_color().name(),
            'alpha': self.emoji_alpha_slider.value() / 100.0
        }

        self.start_worker('emoji', params)

    def start_unicode_preview(self):
        """开始Unicode预览"""
        unicode_char = self.unicode_edit.text()
        if not unicode_char:
            QMessageBox.critical(self, "错误", "请选择Unicode符号")
            return

        sizes = self.parse_sizes(
            self.unicode_preset_sizes.text(),
            self.unicode_custom_size.text()
        )
        if not sizes:
            QMessageBox.critical(self, "错误", "请输入有效的尺寸")
            return

        params = {
            'sizes': sizes,
            'unicode': unicode_char,
            'font_family': self.unicode_font_combo.currentText(),
            'font_color': self.unicode_color_btn.get_color().name(),
            'bg_color': self.unicode_bg_color_btn.get_color().name(),
            'alpha': self.unicode_alpha_slider.value() / 100.0
        }

        self.start_worker('unicode', params)

    def start_css_preview(self):
        """开始CSS预览"""
        css_code = self.css_text.toPlainText().strip()
        if not css_code:
            QMessageBox.critical(self, "错误", "请输入CSS样式")
            return

        sizes = self.parse_sizes(
            self.css_preset_sizes.text(),
            self.css_custom_size.text()
        )
        if not sizes:
            QMessageBox.critical(self, "错误", "请输入有效的尺寸")
            return

        params = {
            'sizes': sizes,
            'css_code': css_code
        }

        self.start_worker('css', params)

    def start_matplotlib_preview(self):
        """开始Matplotlib预览"""
        if not MATPLOTLIB_SUPPORT:
            QMessageBox.critical(self, "错误", "需要安装matplotlib模块才能使用此功能")
            return

        code = self.chart_data_text.toPlainText().strip()
        if not code:
            QMessageBox.critical(self, "错误", "请输入图表数据")
            return

        sizes = self.parse_sizes(
            self.chart_preset_sizes.text(),
            self.chart_custom_size.text()
        )
        if not sizes:
            QMessageBox.critical(self, "错误", "请输入有效的尺寸")
            return

        params = {
            'sizes': sizes,
            'code': code,
            'chart_type': self.chart_type_combo.currentText(),
            'bg_color': self.chart_bg_color_btn.get_color().name(),
            'alpha': self.chart_alpha_slider.value() / 100.0
        }

        self.start_worker('matplotlib', params)

    def start_worker(self, task_type, params):
        """启动工作线程"""
        # 如果已有工作线程在运行，先取消
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(1000)

        # 禁用当前生成按钮
        self.disable_current_button()
        self.save_btn.setEnabled(False)

        # 显示进度条
        self.progress_bar.setMaximum(len(params['sizes']))
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)

        # 创建并启动工作线程
        self.worker = IconGeneratorWorker(task_type, params)
        self.worker.progress_updated.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self.on_preview_finished)
        self.worker.error_occurred.connect(self.on_preview_error)
        self.worker.start()

        self.status_bar.showMessage(f"正在生成预览... ({len(params['sizes'])}个尺寸)")

    def on_preview_finished(self, icons):
        """预览完成"""
        self.current_icons = icons
        self.preview_widget.set_icons(icons)

        # 更新状态
        self.progress_bar.setVisible(False)
        self.save_btn.setEnabled(True)
        self.enable_current_button()

        sizes = [str(icon.width) for icon in icons]
        self.sizes_label.setText(f"包含尺寸: {', '.join(sizes)}")

        self.status_bar.showMessage("预览生成完成")

        # 更新实时预览
        self.update_realtime_preview()

    def on_preview_error(self, error_msg):
        """预览出错"""
        self.progress_bar.setVisible(False)
        self.enable_current_button()
        QMessageBox.critical(self, "错误", f"生成预览时出错:\n{error_msg}")
        self.status_bar.showMessage(f"错误: {error_msg}")

    def update_realtime_preview(self):
        """更新实时预览"""
        if self.preview_timer.isActive():
            self.preview_timer.stop()

        if self.current_icons:
            # 使用第一个图标
            icon = self.current_icons[0]
            self.display_preview_icon(icon)
        else:
            # 尝试生成小预览
            self.generate_realtime_preview()

    def generate_realtime_preview(self):
        """生成实时预览"""
        try:
            index = self.get_current_tab_index()
            img = None

            if index == 0:  # 图片
                if self.image_path_edit.text() and os.path.isfile(self.image_path_edit.text()):
                    img = Image.open(self.image_path_edit.text())
                    img.thumbnail((60, 60))
            elif index == 1:  # 文字
                if self.text_edit.text():
                    # 创建简单文字预览
                    img = Image.new("RGBA", (60, 60), (255, 255, 255, 255))
                    draw = ImageDraw.Draw(img)
                    try:
                        font = ImageFont.truetype("arial.ttf", 20)
                    except:
                        font = ImageFont.load_default()
                    text = self.text_edit.text()[:2]  # 只取前两个字符
                    try:
                        bbox = draw.textbbox((0, 0), text, font=font)
                        text_width = bbox[2] - bbox[0]
                        text_height = bbox[3] - bbox[1]
                    except AttributeError:
                        try:
                            text_width, text_height = draw.textsize(text, font=font)
                        except:
                            text_width, text_height = 30, 20
                    position = ((60 - text_width) // 2, (60 - text_height) // 2)
                    draw.text(position, text, fill="black", font=font)
            elif index == 2:  # SVG
                if self.svg_text.toPlainText().strip():
                    # 简单占位
                    img = Image.new("RGBA", (60, 60), (200, 200, 200, 255))
                    draw = ImageDraw.Draw(img)
                    draw.text((20, 20), "SVG", fill="black")
            elif index == 3:  # Emoji
                if self.emoji_edit.text():
                    img = Image.new("RGBA", (60, 60), (255, 255, 255, 255))
                    draw = ImageDraw.Draw(img)
                    try:
                        font = ImageFont.truetype("seguiemj.ttf", 40)
                    except:
                        font = ImageFont.load_default()
                    text = self.emoji_edit.text()[:1]
                    try:
                        bbox = draw.textbbox((0, 0), text, font=font)
                        text_width = bbox[2] - bbox[0]
                        text_height = bbox[3] - bbox[1]
                    except AttributeError:
                        try:
                            text_width, text_height = draw.textsize(text, font=font)
                        except:
                            text_width, text_height = 30, 30
                    position = ((60 - text_width) // 2, (60 - text_height) // 2)
                    draw.text(position, text, fill="black", font=font)
            elif index == 4:  # Unicode
                if self.unicode_edit.text():
                    img = Image.new("RGBA", (60, 60), (255, 255, 255, 255))
                    draw = ImageDraw.Draw(img)
                    try:
                        font = ImageFont.truetype("arial.ttf", 30)
                    except:
                        font = ImageFont.load_default()
                    text = self.unicode_edit.text()[:1]
                    try:
                        bbox = draw.textbbox((0, 0), text, font=font)
                        text_width = bbox[2] - bbox[0]
                        text_height = bbox[3] - bbox[1]
                    except AttributeError:
                        try:
                            text_width, text_height = draw.textsize(text, font=font)
                        except:
                            text_width, text_height = 20, 20
                    position = ((60 - text_width) // 2, (60 - text_height) // 2)
                    draw.text(position, text, fill="black", font=font)
            elif index == 5:  # CSS
                if self.css_text.toPlainText().strip():
                    img = Image.new("RGBA", (60, 60), (200, 200, 255, 255))
                    draw = ImageDraw.Draw(img)
                    draw.text((20, 20), "CSS", fill="black")
            elif index == 6:  # Matplotlib
                if self.chart_data_text.toPlainText().strip():
                    img = Image.new("RGBA", (60, 60), (200, 255, 200, 255))
                    draw = ImageDraw.Draw(img)
                    draw.text((15, 20), "Chart", fill="black")

            if img:
                self.display_preview_icon(img)

        except Exception as e:
            print(f"实时预览错误: {e}")

    def display_preview_icon(self, pil_image):
        """显示预览图标"""
        try:
            # 转换为QPixmap
            if pil_image.mode != 'RGBA':
                pil_image = pil_image.convert('RGBA')

            # 确保图像数据正确
            img_data = pil_image.tobytes()
            
            # 创建QImage
            qimage = QImage(img_data, pil_image.width, pil_image.height,
                           QImage.Format_RGBA8888)
            
            if qimage.isNull():
                print("创建的QImage为空")
                return
                
            pixmap = QPixmap.fromImage(qimage)

            # 缩放到合适大小
            pixmap = pixmap.scaled(60, 60, Qt.KeepAspectRatio,
                                  Qt.SmoothTransformation)

            self.realtime_preview.setPixmap(pixmap)
        except Exception as e:
            print(f"显示预览错误: {e}")

    def clear_preview(self):
        """清除预览"""
        self.current_icons = []
        self.preview_widget.clear()
        self.realtime_preview.clear()
        self.save_btn.setEnabled(False)
        self.sizes_label.setText("包含尺寸: 无")
        self.status_bar.showMessage("预览已清除")

    def save_icons(self):
        """保存图标"""
        if not self.current_icons:
            QMessageBox.critical(self, "错误", "没有可保存的图标")
            return

        format_map = {
            "ICO (多尺寸)": ("ico", ".ico"),
            "PNG": ("png", ".png"),
            "JPG": ("jpeg", ".jpg"),
            "WebP": ("webp", ".webp")
        }

        format_name = self.format_combo.currentText()
        if format_name not in format_map:
            QMessageBox.critical(self, "错误", "不支持的输出格式")
            return

        format_type, ext = format_map[format_name]
        quality = self.quality_spin.value()

        try:
            if format_type == "ico":
                # 保存ICO文件
                file_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "保存ICO文件",
                    os.path.expanduser("~"),
                    "ICO 文件 (*.ico);;所有文件 (*.*)"
                )
                if file_path:
                    if not file_path.lower().endswith('.ico'):
                        file_path += '.ico'
                    
                    # 确保所有图标都是RGBA模式且尺寸有效
                    icons = []
                    for img in self.current_icons:
                        if img.mode != 'RGBA':
                            img = img.convert('RGBA')
                        # ICO格式要求尺寸 <= 256x256
                        if img.width > 256 or img.height > 256:
                            img = img.resize((256, 256), Image.Resampling.LANCZOS)
                        icons.append(img)
                    
                    # 保存ICO
                    icons[0].save(
                        file_path,
                        format="ICO",
                        sizes=[(icon.width, icon.height) for icon in icons],
                        append_images=icons[1:],
                        quality=quality
                    )
                    self.status_bar.showMessage(f"ICO文件已保存: {file_path}")

            else:
                # 询问保存方式
                reply = QMessageBox.question(
                    self,
                    "保存选项",
                    "是否将所有尺寸保存为单独文件？\n点击'是'保存多个文件，'否'只保存最大尺寸",
                    QMessageBox.Yes | QMessageBox.No
                )

                if reply == QMessageBox.Yes:
                    # 保存多个文件
                    folder = QFileDialog.getExistingDirectory(
                        self,
                        "选择保存多文件的文件夹",
                        os.path.expanduser("~")
                    )
                    if folder:
                        base_name, ok = QInputDialog.getText(
                            self,
                            "输入文件名",
                            "请输入文件名前缀:"
                        )
                        if ok and base_name:
                            for img in self.current_icons:
                                # 处理图像模式转换
                                save_img = img.copy()
                                if format_type == "jpeg":
                                    if save_img.mode in ('RGBA', 'LA'):
                                        # 创建白色背景
                                        background = Image.new('RGB', save_img.size, (255, 255, 255))
                                        if save_img.mode == 'RGBA':
                                            background.paste(save_img, mask=save_img.split()[3])
                                        else:
                                            background.paste(save_img)
                                        save_img = background
                                    elif save_img.mode != 'RGB':
                                        save_img = save_img.convert('RGB')
                                elif format_type == "png" and save_img.mode not in ('RGB', 'RGBA'):
                                    save_img = save_img.convert('RGBA')
                                elif format_type == "webp":
                                    if save_img.mode not in ('RGB', 'RGBA'):
                                        save_img = save_img.convert('RGBA')

                                filename = f"{base_name}_{save_img.width}x{save_img.height}{ext}"
                                file_path = os.path.join(folder, filename)

                                save_params = {
                                    'format': format_type.upper(),
                                    'quality': quality
                                }
                                if format_type == "png":
                                    save_params['compress_level'] = 6

                                save_img.save(file_path, **save_params)

                            self.status_bar.showMessage(
                                f"已保存 {len(self.current_icons)} 个文件到: {folder}"
                            )

                else:
                    # 只保存最大尺寸
                    file_path, _ = QFileDialog.getSaveFileName(
                        self,
                        f"保存{format_name}文件",
                        os.path.expanduser("~"),
                        f"{format_name} 文件 (*{ext});;所有文件 (*.*)"
                    )
                    if file_path:
                        if not file_path.lower().endswith(ext):
                            file_path += ext
                        largest = max(self.current_icons, key=lambda x: x.width)

                        # 处理图像模式转换
                        save_img = largest.copy()
                        if format_type == "jpeg":
                            if save_img.mode in ('RGBA', 'LA'):
                                # 创建白色背景
                                background = Image.new('RGB', save_img.size, (255, 255, 255))
                                if save_img.mode == 'RGBA':
                                    background.paste(save_img, mask=save_img.split()[3])
                                else:
                                    background.paste(save_img)
                                save_img = background
                            elif save_img.mode != 'RGB':
                                save_img = save_img.convert('RGB')
                        elif save_img.mode not in ('RGB', 'RGBA'):
                            save_img = save_img.convert('RGBA')

                        save_params = {
                            'format': format_type.upper(),
                            'quality': quality
                        }
                        if format_type == "png":
                            save_params['compress_level'] = 6

                        save_img.save(file_path, **save_params)
                        self.status_bar.showMessage(
                            f"{format_name}文件已保存: {file_path}"
                        )

        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存过程中发生错误:\n{str(e)}")
            print(f"DEBUG - 保存错误详情: {traceback.format_exc()}")

    def show_help(self):
        """显示帮助信息"""
        help_text = """高级图标生成工具 使用说明 v{}

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
   - 选择形状蒙版 (圆形/圆角矩形/星形/心形等)
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
- ICO格式限制尺寸最大为256x256
- JPG格式不支持透明背景，会自动添加白色背景
""".format(__version__)

        QMessageBox.information(self, "帮助", help_text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AdvancedIconGenerator()
    if getattr(window, '_start_maximized', False):
        window.showMaximized()  # 恢复最大化状态
    else:
        window.show()
    sys.exit(app.exec())