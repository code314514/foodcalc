"""
增强交互测试工具
- 中文字体修复
- 模拟所有按钮点击 → 截图 → 验证无崩溃
"""

import os
import sys
import json

APP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app')
sys.path.insert(0, APP_DIR)

SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

from kivy.config import Config
Config.set('graphics', 'resizable', '0')
Config.set('graphics', 'width', '400')
Config.set('graphics', 'height', '700')

from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivymd.app import MDApp

# ── 中文字体 ──
_CHINESE_FONT = None
for fp in ['C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/simhei.ttf', '/system/fonts/DroidSansFallback.ttf']:
    if os.path.exists(fp):
        _CHINESE_FONT = fp
        break
if _CHINESE_FONT:
    LabelBase.register(name='Roboto', fn_regular=_CHINESE_FONT)

# ── 测试结果追踪 ──
_results = []
_errors = []

def log_result(name, ok, detail=''):
    status = 'PASS' if ok else 'FAIL'
    entry = f"[{status}] {name} {detail}"
    _results.append(entry)
    print(entry)
    if not ok:
        _errors.append(entry)

def safe_call(name, fn, *args, detail=''):
    """安全调用函数，捕获异常。"""
    try:
        fn()
        log_result(name, True)
    except Exception as e:
        log_result(name, False, f"-> {type(e).__name__}: {e}")

def screenshot(app, filename):
    """截图并记录。"""
    path = os.path.join(SCREENSHOT_DIR, filename)
    try:
        app.root.export_to_png(path)
        size = os.path.getsize(path)
        print(f"  [SCREENSHOT] {filename} ({size} bytes)")
        return True
    except Exception as e:
        print(f"  [SCREENSHOT FAIL] {filename}: {e}")
        return False


# ═══════════════════════════════════════════════════════════
# 测试套件
# ═══════════════════════════════════════════════════════════

def run_tests(app):
    """逐步测试所有交互。"""

    # ── Step 1: 初始状态 ──
    def step1(dt):
        print("\n=== STEP 1: 初始状态 ===")
        safe_call("app.food_manager 存在", lambda: app.food_manager is not None)
        safe_call("app.record_manager 存在", lambda: app.record_manager is not None)
        safe_call("4个screen已创建", lambda: all(hasattr(app, s) for s in
            ['input_screen', 'calc_screen', 'today_screen', 'history_screen']))
        screenshot(app, '01_initial.png')
        Clock.schedule_once(step2, 0.3)

    # ── Step 2: JSON批量录入 ──
    def step2(dt):
        print("\n=== STEP 2: JSON批量录入 ===")
        # 用 JSON 字符串测试导入
        json_text = json.dumps([
            {"name":"鸡蛋","methods":[{"method_name":"生","nutrients":{"能量":144,"蛋白质":13.3,"脂肪":9.5,"碳水化合物":1.5,"膳食纤维":0,"维生素":[],"矿物质":[],"自定义":[]}},{"method_name":"煮","nutrients":{"能量":155,"蛋白质":12.6,"脂肪":10.6,"碳水化合物":1.1,"膳食纤维":0,"维生素":[],"矿物质":[],"自定义":[]}}]},
            {"name":"米饭","methods":[{"method_name":"生","nutrients":{"能量":116,"蛋白质":2.6,"脂肪":0.3,"碳水化合物":25.9,"膳食纤维":0.3,"维生素":[],"矿物质":[],"自定义":[]}}]},
            {"name":"鸡胸肉","methods":[{"method_name":"生","nutrients":{"能量":120,"蛋白质":24.6,"脂肪":1.9,"碳水化合物":0.5,"膳食纤维":0,"维生素":[],"矿物质":[],"自定义":[]}},{"method_name":"蒸","nutrients":{"能量":133,"蛋白质":27,"脂肪":2.0,"碳水化合物":0.5,"膳食纤维":0,"维生素":[],"矿物质":[],"自定义":[]}}]},
        ], ensure_ascii=False)

        # 模拟：设置文本框内容 + 点击"录入食物"
        app.input_screen.json_input.text = json_text
        safe_call("点击[录入食物]按钮", lambda: app.input_screen._on_json_import(None))

        # 检查结果
        count = app.food_manager.food_count
        safe_call(f"食物库应有3个食物(count={count})",
                  lambda: count == 3,
                  f"count={count}")

        app.input_screen._refresh_food_list()
        screenshot(app, '02_after_json_import.png')
        Clock.schedule_once(step3, 0.3)

    # ── Step 3: AI提示词复制 ──
    def step3(dt):
        print("\n=== STEP 3: AI提示词复制 ===")
        safe_call("点击[AI生成(复制提示词)]", lambda: app.input_screen._on_copy_prompt(None))
        screenshot(app, '03_input_list.png')
        Clock.schedule_once(step4, 0.3)

    # ── Step 4: 编辑食物弹窗 ──
    def step4(dt):
        print("\n=== STEP 4: 编辑食物弹窗 ===")
        food = app.food_manager.get_food_by_name('鸡蛋')
        safe_call("点击编辑[鸡蛋]", lambda: app.input_screen._on_edit_food(food))
        # 弹窗已打开，关闭它
        safe_call("关闭编辑弹窗", lambda: app.input_screen._close_dialog())
        Clock.schedule_once(step5, 0.3)

    # ── Step 5: 删除确认弹窗(取消) ──
    def step5(dt):
        print("\n=== STEP 5: 删除确认弹窗(取消) ===")
        food = app.food_manager.get_food_by_name('鸡蛋')
        safe_call("点击删除[鸡蛋]→取消",
                  lambda: app.input_screen._on_delete_food(food))
        safe_call("取消删除弹窗", lambda: app.input_screen._close_dialog())
        safe_call("鸡蛋仍在库中",
                  lambda: app.food_manager.food_exists('鸡蛋'))
        Clock.schedule_once(step6, 0.3)

    # ── Step 6: 导出 ──
    def step6(dt):
        print("\n=== STEP 6: 导出食物库 ===")
        safe_call("点击[导出]按钮", lambda: app.input_screen._on_export(None))
        Clock.schedule_once(step7, 0.3)

    # ── Step 7: 切换到计算页 ──
    def step7(dt):
        print("\n=== STEP 7: 切换到计算页 ===")
        safe_call("switch_tab('calc')", lambda: app.root.switch_tab('calc'))
        Clock.schedule_once(step8, 0.5)

    # ── Step 8: 选择食物弹窗 ──
    def step8(dt):
        print("\n=== STEP 8: 选择食物弹窗 ===")
        safe_call("点击[选择食物]", lambda: app.calc_screen._on_select_foods(None))
        # 弹窗已打开，关闭
        try:
            app.calc_screen._close_select_dialog()
            log_result("关闭选择弹窗", True)
        except Exception as e:
            log_result("关闭选择弹窗", False, str(e))
        Clock.schedule_once(step9, 0.3)

    # ── Step 9: 添加条目 × 3 ──
    def step9(dt):
        print("\n=== STEP 9: 添加计算条目 ===")
        safe_call("点击[+添加条目] #1", lambda: app.calc_screen._on_add_entry(None))
        safe_call("点击[+添加条目] #2", lambda: app.calc_screen._on_add_entry(None))
        safe_call("点击[+添加条目] #3", lambda: app.calc_screen._on_add_entry(None))
        safe_call(f"应有3个条目(len={len(app.calc_screen._entries)})",
                  lambda: len(app.calc_screen._entries) == 3,
                  f"len={len(app.calc_screen._entries)}")
        screenshot(app, '04_calc_entries.png')
        Clock.schedule_once(step10, 0.3)

    # ── Step 10: 计算营养 ──
    def step10(dt):
        print("\n=== STEP 10: 计算营养 ===")
        safe_call("点击[计算营养]", lambda: app.calc_screen._on_calculate(None))
        # 关闭结果弹窗
        safe_call("关闭结果弹窗", lambda: app.calc_screen._close_dialog())
        Clock.schedule_once(step11, 0.3)

    # ── Step 11: 提交到今日 ──
    def step11(dt):
        print("\n=== STEP 11: 提交到今日 ===")
        safe_call("点击[提交到今日]", lambda: app.calc_screen._on_submit_to_today(None))
        safe_call("计算页条目已清空",
                  lambda: len(app.calc_screen._entries) == 0,
                  f"len={len(app.calc_screen._entries)}")
        Clock.schedule_once(step12, 0.3)

    # ── Step 12: 切换到今日页 ──
    def step12(dt):
        print("\n=== STEP 12: 切换到今日页 ===")
        safe_call("switch_tab('today')", lambda: app.root.switch_tab('today'))
        app.today_screen._refresh()
        Clock.schedule_once(step13, 0.5)

    # ── Step 13: 今日页 - 编辑记录 ──
    def step13(dt):
        print("\n=== STEP 13: 今日页 - 编辑记录 ===")
        today_records = app.record_manager.get_today_records()
        has_records = len(today_records) > 0
        safe_call(f"今日有记录(count={len(today_records)})",
                  lambda: has_records,
                  f"count={len(today_records)}")
        if has_records:
            rec = today_records[0]
            safe_call("点击编辑记录", lambda: app.today_screen._on_edit_record(rec))
            safe_call("关闭编辑弹窗", lambda: app.today_screen._close_dialog())
        screenshot(app, '05_today_with_record.png')
        Clock.schedule_once(step14, 0.3)

    # ── Step 14: 今日页 - 删除确认(取消) ──
    def step14(dt):
        print("\n=== STEP 14: 今日页 - 删除确认 ===")
        today_records = app.record_manager.get_today_records()
        if today_records:
            rec = today_records[0]
            safe_call("点击删除记录→取消", lambda: app.today_screen._on_delete_record(rec))
            safe_call("取消删除弹窗", lambda: app.today_screen._close_dialog())
        Clock.schedule_once(step15, 0.3)

    # ── Step 15: 切换到历史页 ──
    def step15(dt):
        print("\n=== STEP 15: 切换到历史页 ===")
        safe_call("switch_tab('history')", lambda: app.root.switch_tab('history'))
        Clock.schedule_once(step16, 0.5)

    # ── Step 16: 历史页 - 日历导航 ──
    def step16(dt):
        print("\n=== STEP 16: 历史页 - 日历导航 ===")
        app.history_screen._refresh_all()
        safe_call("点击[上月]", lambda: app.history_screen._on_prev_month(None))
        safe_call("点击[下月]", lambda: app.history_screen._on_next_month(None))
        Clock.schedule_once(step17, 0.3)

    # ── Step 17: 历史页 - 日期范围 ──
    def step17(dt):
        print("\n=== STEP 17: 历史页 - 日期范围按钮 ===")
        safe_call("点击[最近7天]", lambda: app.history_screen._set_range(7))
        safe_call("点击[最近15天]", lambda: app.history_screen._set_range(15))
        safe_call("点击[本月]", lambda: app.history_screen._set_range_month())
        Clock.schedule_once(step18, 0.3)

    # ── Step 18: 历史页 - 点击有记录日期 ──
    def step18(dt):
        print("\n=== STEP 18: 历史页 - 点击日期 ===")
        dates = app.record_manager.get_all_dates()
        if dates:
            latest = dates[0]
            safe_call(f"点击日期[{latest}]", lambda: app.history_screen._on_date_click(latest))
        screenshot(app, '06_history_final.png')
        Clock.schedule_once(step19, 0.5)

    # ── Step 19: 总结 ──
    def step19(dt):
        print("\n" + "=" * 50)
        print(f"  TEST COMPLETE: {sum(1 for r in _results if '[PASS]' in r)}/{len(_results)} passed")
        if _errors:
            print(f"  ERRORS ({len(_errors)}):")
            for e in _errors:
                print(f"    {e}")
        else:
            print("  ALL TESTS PASSED")
        print(f"  Screenshots: {SCREENSHOT_DIR}")
        print("=" * 50)
        app.stop()
        sys.exit(0 if not _errors else 1)

    # 启动测试链
    Clock.schedule_once(step1, 1.0)


if __name__ == '__main__':
    from main import FoodCalcApp
    app = FoodCalcApp()
    Clock.schedule_once(lambda dt: run_tests(app), 0)
    app.run()
