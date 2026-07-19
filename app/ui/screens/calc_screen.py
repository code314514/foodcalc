"""
计算页（营养计算）
- 选择食物
- 计算条目列表（食物名、烹饪方式、克数）
- 计算营养并显示结果/图表
- 提交到今日
"""

import copy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.clock import Clock

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton, MDRectangleFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.snackbar import MDSnackbar
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.list import OneLineAvatarIconListItem

from models.nutrients import (
    calculate_entry_nutrients, sum_nutrient_dicts,
    BASIC_NUTRIENTS, BASIC_NUTRIENT_UNITS,
    nutrients_to_display_dict,
)


class CalcScreen(MDScreen):
    """计算页 — 营养计算"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'calc'
        self._entries = []  # [{'food_name': ..., 'method_name': ..., 'grams': ..., 'nutrients': ...}, ...]
        self._dialog = None
        self._build_ui()

    # ── UI 构建 ───────────────────────────────────────────

    def _build_ui(self):
        root = MDBoxLayout(orientation='vertical')

        self.top_bar = MDTopAppBar(
            title="营养计算",
            elevation=2,
        )
        root.add_widget(self.top_bar)

        # 主内容
        scroll = MDScrollView()
        self.content_area = MDBoxLayout(
            orientation='vertical',
            padding=dp(16),
            spacing=dp(12),
            size_hint_y=None,
            adaptive_height=True,
        )

        # ── 选择食物按钮 ──
        btn_select = MDRaisedButton(
            text="选择食物",
            on_release=self._on_select_foods,
            size_hint_x=1,
        )
        self.content_area.add_widget(btn_select)

        # ── 条目列表容器 ──
        self.entries_label = MDLabel(
            text="计算条目",
            font_style="H5",
            size_hint_y=None,
            height=dp(36),
        )
        self.content_area.add_widget(self.entries_label)

        self.entries_container = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            size_hint_y=None,
            adaptive_height=True,
        )
        self.content_area.add_widget(self.entries_container)

        # 添加按钮
        btn_add = MDRectangleFlatButton(
            text="+ 添加条目",
            on_release=self._on_add_entry,
            size_hint_x=1,
        )
        self.content_area.add_widget(btn_add)

        # ── 操作按钮 ──
        btn_row = MDBoxLayout(spacing=dp(8), adaptive_height=True)
        btn_calc = MDRaisedButton(text="计算营养", on_release=self._on_calculate)
        btn_submit = MDRaisedButton(text="提交到今日", on_release=self._on_submit_to_today)
        btn_row.add_widget(btn_calc)
        btn_row.add_widget(btn_submit)
        self.content_area.add_widget(btn_row)

        # 空提示
        self.empty_label = MDLabel(
            text="请先选择食物并添加条目",
            halign="center",
            theme_text_color="Hint",
            size_hint_y=None,
            height=dp(60),
        )

        scroll.add_widget(self.content_area)
        root.add_widget(scroll)
        self.add_widget(root)

        Clock.schedule_once(lambda dt: self._check_empty(), 0.1)

    def _check_empty(self):
        """检查是否有条目，无则显示提示。"""
        if not self._entries:
            if self.empty_label.parent is None:
                self.entries_container.add_widget(self.empty_label)

    # ── 选择食物弹窗 ─────────────────────────────────────

    def _on_select_foods(self, instance):
        """打开食物多选弹窗（搜索 + Checkbox 多选）。"""
        app = MDApp.get_running_app()
        foods = app.food_manager.foods

        if not foods:
            self._toast("食物库为空，请先在录入页添加食物")
            return

        # 记录选中状态
        self._selected_foods = set()

        # 构建内容
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            size_hint_y=None,
            adaptive_height=True,
        )

        # 搜索框
        search_field = MDTextField(
            hint_text="搜索食物…",
            mode="line",
            size_hint_y=None,
            height=dp(48),
        )
        content.add_widget(search_field)

        # 食物列表容器
        list_container = MDBoxLayout(
            orientation='vertical',
            spacing=dp(2),
            size_hint_y=None,
            adaptive_height=True,
        )
        content.add_widget(list_container)

        # 构建食物列表
        def build_food_list(filter_text=''):
            list_container.clear_widgets()
            filter_lower = filter_text.strip().lower()
            for food in foods:
                if filter_lower and filter_lower not in food['name'].lower():
                    continue

                item = MDBoxLayout(
                    size_hint_y=None,
                    height=dp(40),
                    spacing=dp(4),
                )

                checkbox = MDCheckbox(
                    size_hint_x=None,
                    width=dp(40),
                    active=food['name'] in self._selected_foods,
                )
                checkbox.bind(active=lambda cb, v, fn=food['name']: self._toggle_select(fn, v))

                label = MDLabel(
                    text=food['name'],
                    size_hint_x=1,
                    font_style="Body2",
                )

                item.add_widget(checkbox)
                item.add_widget(label)
                list_container.add_widget(item)

        build_food_list()

        search_field.bind(text=lambda instance, value: build_food_list(value))

        self._select_dialog = MDDialog(
            title="选择食物",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="取消", on_release=lambda x: self._close_select_dialog()),
                MDRaisedButton(text="确定", on_release=lambda x: self._confirm_select()),
            ],
        )
        self._select_dialog.open()

    def _toggle_select(self, food_name: str, active: bool):
        """切换食物选中状态。"""
        if active:
            self._selected_foods.add(food_name)
        else:
            self._selected_foods.discard(food_name)

    def _close_select_dialog(self):
        if self._select_dialog:
            self._select_dialog.dismiss()
            self._select_dialog = None

    def _confirm_select(self):
        """确认选择，添加选中食物为计算条目。"""
        self._close_select_dialog()

        if not self._selected_foods:
            self._toast("请至少选择一个食物")
            return

        app = MDApp.get_running_app()
        added = 0
        for food_name in self._selected_foods:
            food = app.food_manager.get_food_by_name(food_name)
            if not food:
                continue

            methods = [m['method_name'] for m in food.get('methods', [])]
            method = methods[0] if methods else '生'
            grams = 100.0

            nutrients = app.food_manager.get_food_method_nutrients(food_name, method)
            if nutrients:
                scaled = calculate_entry_nutrients(nutrients, grams)
            else:
                from models.nutrients import make_empty_nutrients
                scaled = make_empty_nutrients()

            self._entries.append({
                'food_name': food_name,
                'method_name': method,
                'grams': grams,
                'nutrients': scaled,
                'orig_nutrients': nutrients,
            })
            added += 1

        self._refresh_entries()
        self._toast(f"已添加 {added} 个食物")

    # ── 添加条目 ─────────────────────────────────────────

    def _on_add_entry(self, instance):
        """添加计算条目。"""
        app = MDApp.get_running_app()
        foods = app.food_manager.foods

        if not foods:
            self._toast("食物库为空")
            return

        # 默认选择第一个食物
        food = foods[0]
        methods = [m['method_name'] for m in food.get('methods', [])]
        method = methods[0] if methods else '生'
        grams = 100.0

        # 计算营养成分
        nutrients = app.food_manager.get_food_method_nutrients(food['name'], method)
        if nutrients:
            scaled = calculate_entry_nutrients(nutrients, grams)
        else:
            from models.nutrients import make_empty_nutrients
            scaled = make_empty_nutrients()

        entry = {
            'food_name': food['name'],
            'method_name': method,
            'grams': grams,
            'nutrients': scaled,
            'orig_nutrients': nutrients,  # 保留原始（每100g），用于修改克数时重新计算
        }

        self._entries.append(entry)
        self._refresh_entries()

    def _refresh_entries(self):
        """刷新条目列表显示。"""
        self.entries_container.clear_widgets()

        if self.empty_label.parent:
            self.empty_label.parent.remove_widget(self.empty_label)

        if not self._entries:
            self.entries_container.add_widget(self.empty_label)
            return

        for i, entry in enumerate(self._entries):
            card = self._build_entry_card(i, entry)
            self.entries_container.add_widget(card)

    def _build_entry_card(self, index: int, entry: dict):
        """构建单条目卡片。"""
        card = MDCard(
            orientation='vertical',
            padding=dp(8),
            spacing=dp(4),
            size_hint_y=None,
            height=dp(100),
            elevation=1,
        )

        # 食物名
        name_label = MDLabel(
            text=entry['food_name'],
            font_style="Subtitle1",
            size_hint_y=None,
            height=dp(24),
        )

        # 克数和烹饪方式行
        info_row = MDBoxLayout(
            spacing=dp(8),
            size_hint_y=None,
            height=dp(48),
        )

        grams_input = MDTextField(
            text=str(entry['grams']),
            hint_text="克数",
            mode="line",
            size_hint_x=0.4,
            input_filter="float",
        )

        method_label = MDLabel(
            text=f"方式：{entry['method_name']}",
            size_hint_x=0.4,
        )

        # 删除按钮
        del_btn = MDIconButton(
            icon="close",
            on_release=lambda x, idx=index: self._on_remove_entry(idx),
        )

        info_row.add_widget(grams_input)
        info_row.add_widget(method_label)
        info_row.add_widget(del_btn)

        card.add_widget(name_label)
        card.add_widget(info_row)

        return card

    def _on_remove_entry(self, index: int):
        """删除条目。"""
        if 0 <= index < len(self._entries):
            del self._entries[index]
            self._refresh_entries()

    # ── 计算营养 ─────────────────────────────────────────

    def _on_calculate(self, instance):
        """计算所有条目的营养总和并弹窗展示。"""
        if not self._entries:
            self._toast("请先添加计算条目")
            return

        # 验证克数
        for entry in self._entries:
            if entry.get('grams', 0) <= 0:
                self._toast("克数必须大于0")
                return

        # 合并所有条目的营养
        all_nutrients = [entry['nutrients'] for entry in self._entries]
        total = sum_nutrient_dicts(all_nutrients)

        # 弹窗显示结果
        self._show_result_dialog(total)

    def _show_result_dialog(self, total: dict):
        """显示计算结果弹窗。"""
        display = nutrients_to_display_dict(total)

        # 构建显示文本
        lines = ["【营养计算结果】", ""]
        for key in BASIC_NUTRIENTS:
            lines.append(f"{key}：{display.get(key, '0')}")

        text = '\n'.join(lines)

        self._dialog = MDDialog(
            title="营养计算结果",
            text=text,
            buttons=[
                MDFlatButton(text="关闭", on_release=lambda x: self._close_dialog()),
            ],
        )
        self._dialog.open()

    # ── 提交到今日 ───────────────────────────────────────

    def _on_submit_to_today(self, instance):
        """提交计算条目到今日记录。"""
        if not self._entries:
            self._toast("请先添加计算条目")
            return

        app = MDApp.get_running_app()
        entries_to_save = []
        for entry in self._entries:
            if entry.get('grams', 0) <= 0:
                self._toast("克数必须大于0")
                return
            entries_to_save.append({
                'food_name': entry['food_name'],
                'method_name': entry['method_name'],
                'grams': entry['grams'],
                'nutrients': entry['nutrients'],
            })

        ok, msg, record_id = app.record_manager.add_record(entries_to_save)
        if ok:
            self._entries.clear()
            self._refresh_entries()
            self._toast(f"{msg}，是否跳转到今日页？")
        else:
            self._toast(msg)

    # ── 辅助 ──────────────────────────────────────────────

    def _close_dialog(self):
        if self._dialog:
            self._dialog.dismiss()
            self._dialog = None

    def _toast(self, text: str):
        MDSnackbar(MDLabel(text=text)).open()
