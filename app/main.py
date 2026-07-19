"""
食物营养计算 APP — 主入口
基于 Kivy + KivyMD 实现 Material Design 3 界面
"""

import os
import sys

# 确保 app 目录在路径中
APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

# Kivy 配置（必须在导入 kivy 之前设置）
from kivy.config import Config
Config.set('graphics', 'resizable', '0')
Config.set('graphics', 'width', '360')
Config.set('graphics', 'height', '640')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window
from kivy.core.text import LabelBase

# ── 中文字体注册（必须在任何 Widget 创建之前） ──
_CHINESE_FONT_PATH = None
_CANDIDATE_FONTS = [
    'C:/Windows/Fonts/msyh.ttc',      # Microsoft YaHei (最佳显示效果)
    'C:/Windows/Fonts/simhei.ttf',    # SimHei 黑体
    'C:/Windows/Fonts/simsun.ttc',    # SimSun 宋体
    'C:/Windows/Fonts/msyhbd.ttc',    # Microsoft YaHei Bold
    '/system/fonts/DroidSansFallback.ttf',        # Android
    '/system/fonts/NotoSansCJK-Regular.ttc',       # Android
    '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',  # Linux
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',     # Linux
]

for fp in _CANDIDATE_FONTS:
    if os.path.exists(fp):
        _CHINESE_FONT_PATH = fp
        break

if _CHINESE_FONT_PATH:
    # 用中文字体替换 Kivy 的默认字体 Roboto
    # KivyMD 使用 Roboto 作为基础字体，替换后所有 MDLabel 自动支持中文
    LabelBase.register(name='Roboto', fn_regular=_CHINESE_FONT_PATH)
    print(f"[FONT] Registered default font with: {_CHINESE_FONT_PATH}")

# KivyMD
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.toolbar import MDTopAppBar

# 数据模型
from models.food import FoodManager
from models.record import RecordManager

# 页面（稍后实现）
from ui.screens.input_screen import InputScreen
from ui.screens.calc_screen import CalcScreen
from ui.screens.today_screen import TodayScreen
from ui.screens.history_screen import HistoryScreen


class FoodCalcApp(MDApp):
    """食物营养计算 APP"""

    def build(self):
        # ── MD3 主题配置 ──
        self.theme_cls.primary_palette = "Green"
        self.theme_cls.primary_hue = "500"  # #4CAF50
        self.theme_cls.theme_style = "Light"
        self.theme_cls.material_style = "M3"

        # ── 初始化数据管理器 ──
        # 数据目录：Android 用 user_data_dir，桌面用相对路径
        try:
            from kivy.utils import platform
            if platform == 'android':
                from android.storage import app_storage_path
                data_dir = app_storage_path()
            else:
                data_dir = os.path.join(APP_DIR, '..', 'data')
        except Exception:
            data_dir = os.path.join(APP_DIR, '..', 'data')

        os.makedirs(data_dir, exist_ok=True)
        self.food_manager = FoodManager(data_dir=data_dir)
        self.record_manager = RecordManager(data_dir=data_dir)

        # ── 底部导航 ──
        bottom_nav = MDBottomNavigation(
            panel_color=self.theme_cls.primary_color,
        )

        # 录入页
        self.input_screen = InputScreen()
        nav_input = MDBottomNavigationItem(
            name='input',
            text='录入',
            icon='database-plus',
        )
        nav_input.add_widget(self.input_screen)
        bottom_nav.add_widget(nav_input)

        # 计算页
        self.calc_screen = CalcScreen()
        nav_calc = MDBottomNavigationItem(
            name='calc',
            text='计算',
            icon='calculator',
        )
        nav_calc.add_widget(self.calc_screen)
        bottom_nav.add_widget(nav_calc)

        # 今日页
        self.today_screen = TodayScreen()
        nav_today = MDBottomNavigationItem(
            name='today',
            text='今日',
            icon='calendar-today',
        )
        nav_today.add_widget(self.today_screen)
        bottom_nav.add_widget(nav_today)

        # 历史页
        self.history_screen = HistoryScreen()
        nav_history = MDBottomNavigationItem(
            name='history',
            text='历史',
            icon='chart-line',
        )
        nav_history.add_widget(self.history_screen)
        bottom_nav.add_widget(nav_history)

        return bottom_nav

    def switch_to_tab(self, tab_name: str):
        """切换到指定标签页。"""
        root = self.root
        if isinstance(root, MDBottomNavigation):
            root.switch_tab(tab_name)

    def show_snackbar(self, text: str):
        """显示 Snackbar 提示。"""
        from kivymd.uix.snackbar import MDSnackbar
        MDSnackbar(MDLabel(text=text)).open()


if __name__ == '__main__':
    FoodCalcApp().run()
