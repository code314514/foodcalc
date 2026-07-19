"""
自动化截图测试工具
启动 APP → 延迟截图各页面 → 注入测试数据 → 再截图 → 退出
"""

import os
import sys
import json
import time

# 确保 app 目录在路径中
APP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app')
sys.path.insert(0, APP_DIR)

SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

from kivy.config import Config
Config.set('graphics', 'resizable', '0')
Config.set('graphics', 'width', '400')
Config.set('graphics', 'height', '700')

from kivy.clock import Clock
from kivy.core.window import Window
from kivymd.app import MDApp


# ── 测试数据 ────────────────────────────────────────────

SAMPLE_FOODS = [
    {
        "name": "鸡蛋",
        "methods": [
            {
                "method_name": "生",
                "nutrients": {
                    "能量": 144,
                    "蛋白质": 13.3,
                    "脂肪": 9.5,
                    "碳水化合物": 1.5,
                    "膳食纤维": 0,
                    "维生素": [
                        {"name": "维生素A", "value": 234, "unit": "mcg"},
                        {"name": "维生素B1", "value": 0.11, "unit": "mg"},
                        {"name": "维生素B2", "value": 0.27, "unit": "mg"},
                        {"name": "维生素B6", "value": 0.14, "unit": "mg"},
                        {"name": "维生素B12", "value": 1.3, "unit": "mcg"},
                        {"name": "维生素C", "value": 0, "unit": "mg"},
                        {"name": "维生素D", "value": 2.0, "unit": "mcg"},
                        {"name": "维生素E", "value": 1.84, "unit": "mg"},
                        {"name": "维生素K", "value": 0.3, "unit": "mcg"}
                    ],
                    "矿物质": [
                        {"name": "钙", "value": 56, "unit": "mg"},
                        {"name": "铁", "value": 2.5, "unit": "mg"},
                        {"name": "锌", "value": 1.3, "unit": "mg"},
                        {"name": "硒", "value": 31.7, "unit": "mcg"},
                        {"name": "钠", "value": 142, "unit": "mg"},
                        {"name": "钾", "value": 154, "unit": "mg"},
                        {"name": "镁", "value": 12, "unit": "mg"},
                        {"name": "磷", "value": 198, "unit": "mg"}
                    ],
                    "自定义": []
                }
            },
            {
                "method_name": "煮",
                "nutrients": {
                    "能量": 155,
                    "蛋白质": 12.6,
                    "脂肪": 10.6,
                    "碳水化合物": 1.1,
                    "膳食纤维": 0,
                    "维生素": [],
                    "矿物质": [],
                    "自定义": []
                }
            }
        ]
    },
    {
        "name": "米饭",
        "methods": [
            {
                "method_name": "生",
                "nutrients": {
                    "能量": 116,
                    "蛋白质": 2.6,
                    "脂肪": 0.3,
                    "碳水化合物": 25.9,
                    "膳食纤维": 0.3,
                    "维生素": [],
                    "矿物质": [],
                    "自定义": []
                }
            }
        ]
    },
    {
        "name": "鸡胸肉",
        "methods": [
            {
                "method_name": "生",
                "nutrients": {
                    "能量": 120,
                    "蛋白质": 24.6,
                    "脂肪": 1.9,
                    "碳水化合物": 0.5,
                    "膳食纤维": 0,
                    "维生素": [],
                    "矿物质": [],
                    "自定义": []
                }
            },
            {
                "method_name": "蒸",
                "nutrients": {
                    "能量": 133,
                    "蛋白质": 27.0,
                    "脂肪": 2.0,
                    "碳水化合物": 0.5,
                    "膳食纤维": 0,
                    "维生素": [],
                    "矿物质": [],
                    "自定义": []
                }
            }
        ]
    }
]


def run_tests(app):
    """测试流程：截图+交互。"""

    steps = []

    # ── Step 1: 等待 UI 渲染 ──
    def step1(dt):
        print("[TEST] Step 1: 截图 — 录入页（初始状态）")
        app.root.export_to_png(os.path.join(SCREENSHOT_DIR, '01_input_empty.png'))
        print("  -> 01_input_empty.png saved")

        # 注入测试食物数据
        fm = app.food_manager
        for food in SAMPLE_FOODS:
            ok, msg = fm.add_food(food)
            print(f"  -> 添加食物: {msg}")

        # 刷新录入页
        app.input_screen._refresh_food_list()
        Clock.schedule_once(step2, 0.3)

    # ── Step 2: 截图 — 录入页（有数据） ──
    def step2(dt):
        print("[TEST] Step 2: 截图 — 录入页（3个食物）")
        app.root.export_to_png(os.path.join(SCREENSHOT_DIR, '02_input_with_foods.png'))
        print("  -> 02_input_with_foods.png saved")

        # 切换到计算页
        app.root.switch_tab('calc')
        Clock.schedule_once(step3, 0.5)

    # ── Step 3: 截图 — 计算页 ──
    def step3(dt):
        print("[TEST] Step 3: 截图 — 计算页（空）")
        app.root.export_to_png(os.path.join(SCREENSHOT_DIR, '03_calc_empty.png'))
        print("  -> 03_calc_empty.png saved")

        # 添加计算条目
        from models.nutrients import calculate_entry_nutrients

        # 条目1: 鸡蛋 煮 100g
        nutrients1 = app.food_manager.get_food_method_nutrients('鸡蛋', '煮')
        app.calc_screen._entries = [{
            'food_name': '鸡蛋',
            'method_name': '煮',
            'grams': 100.0,
            'nutrients': calculate_entry_nutrients(nutrients1, 100),
            'orig_nutrients': nutrients1,
        }, {
            'food_name': '米饭',
            'method_name': '生',
            'grams': 200.0,
            'nutrients': calculate_entry_nutrients(
                app.food_manager.get_food_method_nutrients('米饭', '生'), 200),
            'orig_nutrients': app.food_manager.get_food_method_nutrients('米饭', '生'),
        }, {
            'food_name': '鸡胸肉',
            'method_name': '蒸',
            'grams': 150.0,
            'nutrients': calculate_entry_nutrients(
                app.food_manager.get_food_method_nutrients('鸡胸肉', '蒸'), 150),
            'orig_nutrients': app.food_manager.get_food_method_nutrients('鸡胸肉', '蒸'),
        }]
        app.calc_screen._refresh_entries()

        Clock.schedule_once(step4, 0.3)

    # ── Step 4: 截图 — 计算页（有条目） ──
    def step4(dt):
        print("[TEST] Step 4: 截图 — 计算页（3条目）")
        app.root.export_to_png(os.path.join(SCREENSHOT_DIR, '04_calc_with_entries.png'))
        print("  -> 04_calc_with_entries.png saved")

        # 提交到今日
        entries_to_save = [
            {'food_name': '鸡蛋', 'method_name': '煮', 'grams': 100,
             'nutrients': app.calc_screen._entries[0]['nutrients']},
            {'food_name': '米饭', 'method_name': '生', 'grams': 200,
             'nutrients': app.calc_screen._entries[1]['nutrients']},
            {'food_name': '鸡胸肉', 'method_name': '蒸', 'grams': 150,
             'nutrients': app.calc_screen._entries[2]['nutrients']},
        ]
        app.record_manager.add_record(entries_to_save, note="午餐")

        # 切换到今日页
        app.root.switch_tab('today')
        Clock.schedule_once(step5, 0.5)

    # ── Step 5: 截图 — 今日页 ──
    def step5(dt):
        print("[TEST] Step 5: 截图 — 今日页")
        app.today_screen._refresh()
        app.root.export_to_png(os.path.join(SCREENSHOT_DIR, '05_today.png'))
        print("  -> 05_today.png saved")

        # 切换到历史页
        app.root.switch_tab('history')
        Clock.schedule_once(step6, 0.5)

    # ── Step 6: 截图 — 历史页 ──
    def step6(dt):
        print("[TEST] Step 6: 截图 — 历史页")
        app.history_screen._refresh_all()
        app.root.export_to_png(os.path.join(SCREENSHOT_DIR, '06_history.png'))
        print("  -> 06_history.png saved")

        # 完成
        Clock.schedule_once(step7, 0.3)

    # ── Step 7: 完成 ──
    def step7(dt):
        print("[TEST] ✓ 所有截图完成，退出")
        print(f"  截图保存在: {SCREENSHOT_DIR}")
        app.stop()
        sys.exit(0)

    # 启动
    Clock.schedule_once(step1, 1.0)


if __name__ == '__main__':
    # 延迟导入 app，避免循环依赖
    from main import FoodCalcApp

    app = FoodCalcApp()
    # 在 build 完成后运行测试
    Clock.schedule_once(lambda dt: run_tests(app), 0)
    app.run()
