"""
今日页（今日摄入）
- 今日汇总卡片
- 记录列表（时间倒序）
- 编辑/删除记录
"""

from datetime import date
import copy
from kivy.metrics import dp
from kivy.clock import Clock

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDFlatButton, MDIconButton, MDRaisedButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.snackbar import MDSnackbar

from models.nutrients import (
    BASIC_NUTRIENTS, BASIC_NUTRIENT_UNITS,
    nutrients_to_display_dict,
)


class TodayScreen(MDScreen):
    """今日页 — 今日摄入"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'today'
        self._dialog = None
        self._build_ui()

    def _build_ui(self):
        root = MDBoxLayout(orientation='vertical')

        self.top_bar = MDTopAppBar(
            title="今日摄入",
            right_action_items=[["refresh", self._on_refresh]],
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

        # ── 今日汇总卡片 ──
        self.summary_card = MDCard(
            orientation='vertical',
            padding=dp(16),
            spacing=dp(8),
            size_hint_y=None,
            height=dp(160),
            elevation=2,
        )
        self.summary_title = MDLabel(
            text=f"今日汇总 · {date.today().strftime('%Y-%m-%d')}",
            font_style="H5",
            size_hint_y=None,
            height=dp(32),
        )
        self.summary_card.add_widget(self.summary_title)

        self.summary_content = MDLabel(
            text="今日暂无摄入",
            theme_text_color="Hint",
            size_hint_y=None,
            height=dp(100),
        )
        self.summary_card.add_widget(self.summary_content)
        self.content_area.add_widget(self.summary_card)

        # ── 记录列表 ──
        self.records_label = MDLabel(
            text="今日记录",
            font_style="H5",
            size_hint_y=None,
            height=dp(36),
        )
        self.content_area.add_widget(self.records_label)

        self.records_container = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            size_hint_y=None,
            adaptive_height=True,
        )

        self.empty_label = MDLabel(
            text="今日暂无记录",
            halign="center",
            theme_text_color="Hint",
            size_hint_y=None,
            height=dp(60),
        )
        self.records_container.add_widget(self.empty_label)
        self.content_area.add_widget(self.records_container)

        scroll.add_widget(self.content_area)
        root.add_widget(scroll)
        self.add_widget(root)

        Clock.schedule_once(lambda dt: self._refresh(), 0.1)

    # ── 刷新 ──────────────────────────────────────────────

    def on_enter(self, *args):
        """进入页面时自动刷新。"""
        self._refresh()

    def _on_refresh(self, instance=None):
        self._refresh()
        MDSnackbar(MDLabel(text="已刷新")).open()

    def _refresh(self):
        """刷新今日数据和记录列表。"""
        app = MDApp.get_running_app()
        summary = app.record_manager.get_today_summary()

        # 更新汇总卡片
        if summary['has_data']:
            total = summary['total_nutrients']
            lines = []
            for key in BASIC_NUTRIENTS:
                val = total.get(key, 0)
                unit = BASIC_NUTRIENT_UNITS.get(key, '')
                lines.append(f"{key}：{val} {unit}")
            self.summary_content.text = '\n'.join(lines)
        else:
            self.summary_content.text = "今日暂无摄入"

        # 更新记录列表
        self.records_container.clear_widgets()
        records = summary['records']

        if not records:
            self.records_container.add_widget(self.empty_label)
            return

        # 时间倒序
        for rec in reversed(records):
            card = self._build_record_card(rec)
            self.records_container.add_widget(card)

    def _build_record_card(self, record: dict):
        """构建单条记录卡片。"""
        ts = record.get('timestamp', '')[:16]  # yyyy-MM-dd HH:mm
        time_str = ts[-5:] if len(ts) >= 16 else ts  # HH:mm

        entries = record.get('entries', [])
        entry_texts = []
        total_energy = 0
        for entry in entries:
            fn = entry.get('food_name', '')
            g = entry.get('grams', 0)
            n = entry.get('nutrients', {})
            e = n.get('能量', 0)
            total_energy += e
            entry_texts.append(f"{fn} × {g}g")

        card = MDCard(
            orientation='vertical',
            padding=dp(12),
            spacing=dp(4),
            size_hint_y=None,
            adaptive_height=True,
            elevation=1,
        )

        # 标题行
        header_row = MDBoxLayout(
            size_hint_y=None,
            height=dp(32),
        )
        time_label = MDLabel(text=time_str, font_style="Subtitle1", size_hint_x=0.4)
        energy_label = MDLabel(text=f"{total_energy:.0f} 大卡", size_hint_x=0.25)
        header_row.add_widget(time_label)
        header_row.add_widget(energy_label)

        # 编辑/删除按钮
        edit_btn = MDIconButton(
            icon="pencil",
            on_release=lambda x, r=record: self._on_edit_record(r),
        )
        del_btn = MDIconButton(
            icon="delete",
            on_release=lambda x, r=record: self._on_delete_record(r),
        )
        header_row.add_widget(edit_btn)
        header_row.add_widget(del_btn)

        card.add_widget(header_row)

        # 条目详情
        entry_text = '\n'.join(entry_texts)
        entry_label = MDLabel(
            text=entry_text,
            theme_text_color="Secondary",
            size_hint_y=None,
            adaptive_height=True,
        )
        card.add_widget(entry_label)

        # 备注
        note = record.get('note', '')
        if note:
            note_label = MDLabel(
                text=f"备注：{note}",
                theme_text_color="Hint",
                size_hint_y=None,
                adaptive_height=True,
            )
            card.add_widget(note_label)

        return card

    # ── 编辑记录 ─────────────────────────────────────────

    def _on_edit_record(self, record: dict):
        """编辑记录弹窗。"""
        self._editing_record = copy.deepcopy(record)

        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            size_hint_y=None,
            adaptive_height=True,
        )

        # 时间戳（只读）
        ts = record.get('timestamp', '')
        ts_label = MDLabel(
            text=f"时间：{ts[:16]}",
            font_style="Subtitle2",
            size_hint_y=None,
            height=dp(28),
        )
        content.add_widget(ts_label)

        # 各条目编辑区域
        self._edit_entries_container = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            size_hint_y=None,
            adaptive_height=True,
        )
        content.add_widget(self._edit_entries_container)

        # 渲染条目
        self._render_edit_entries()

        self._dialog = MDDialog(
            title="编辑记录",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="取消", on_release=lambda x: self._close_dialog()),
                MDRaisedButton(text="保存", on_release=lambda x: self._on_save_edit_record()),
            ],
        )
        self._dialog.open()

    def _render_edit_entries(self):
        """渲染编辑弹窗中的条目。"""
        self._edit_entries_container.clear_widgets()
        self._edit_fields = []

        for i, entry in enumerate(self._editing_record.get('entries', [])):
            card = MDCard(
                orientation='vertical',
                padding=dp(8),
                spacing=dp(4),
                size_hint_y=None,
                adaptive_height=True,
                elevation=1,
            )

            fn = entry.get('food_name', '')
            name_label = MDLabel(
                text=f"食物：{fn}",
                font_style="Subtitle2",
                size_hint_y=None,
                height=dp(24),
            )
            card.add_widget(name_label)

            info_row = MDBoxLayout(
                spacing=dp(8),
                size_hint_y=None,
                height=dp(48),
            )

            grams_field = MDTextField(
                text=str(entry.get('grams', 0)),
                hint_text="克数",
                mode="line",
                size_hint_x=0.4,
                input_filter="float",
            )

            mn = entry.get('method_name', '生')
            method_label = MDLabel(
                text=f"方式：{mn}",
                size_hint_x=0.35,
                font_style="Body2",
            )

            del_btn = MDIconButton(
                icon="close",
                on_release=lambda x, idx=i: self._on_delete_entry_in_edit(idx),
            )

            info_row.add_widget(grams_field)
            info_row.add_widget(method_label)
            info_row.add_widget(del_btn)

            card.add_widget(info_row)
            self._edit_entries_container.add_widget(card)

            self._edit_fields.append({
                'grams_field': grams_field,
                'entry': entry,
            })

    def _on_delete_entry_in_edit(self, index: int):
        """在编辑中删除某个条目。"""
        if len(self._editing_record['entries']) <= 1:
            self._toast("记录至少需要一个条目")
            return
        del self._editing_record['entries'][index]
        self._render_edit_entries()

    def _on_save_edit_record(self):
        """保存编辑后的记录。"""
        app = MDApp.get_running_app()

        new_entries = []
        for field_data in self._edit_fields:
            entry = field_data['entry']
            grams_text = field_data['grams_field'].text

            try:
                grams = float(grams_text or 0)
            except ValueError:
                self._toast("克数请输入有效数字")
                return

            if grams <= 0:
                self._toast("克数必须大于0")
                return

            food_nutrients = app.food_manager.get_food_method_nutrients(
                entry.get('food_name', ''),
                entry.get('method_name', '生'),
            )

            if food_nutrients:
                from models.nutrients import calculate_entry_nutrients
                nutrients = calculate_entry_nutrients(food_nutrients, grams)
            else:
                nutrients = entry.get('nutrients', {})

            new_entries.append({
                'food_name': entry['food_name'],
                'method_name': entry.get('method_name', '生'),
                'grams': grams,
                'nutrients': nutrients,
            })

        ok, msg = app.record_manager.update_record_entries(
            self._editing_record['record_id'],
            new_entries,
        )

        self._close_dialog()
        self._refresh()
        self._toast(msg)

    # ── 删除记录 ─────────────────────────────────────────

    def _on_delete_record(self, record: dict):
        """确认删除弹窗。"""
        rid = record.get('record_id', '')
        self._dialog = MDDialog(
            title="确认删除",
            text=f"确定要删除这条记录吗？此操作不可撤销。",
            buttons=[
                MDFlatButton(text="取消", on_release=lambda x: self._close_dialog()),
                MDFlatButton(text="删除", on_release=lambda x: self._confirm_delete(rid)),
            ],
        )
        self._dialog.open()

    def _confirm_delete(self, record_id: str):
        """确认删除记录。"""
        app = MDApp.get_running_app()
        ok, msg = app.record_manager.delete_record(record_id)
        self._close_dialog()
        self._refresh()
        self._toast(msg)

    # ── 辅助 ──────────────────────────────────────────────

    def _close_dialog(self):
        if self._dialog:
            self._dialog.dismiss()
            self._dialog = None

    def _toast(self, text: str):
        MDSnackbar(MDLabel(text=text)).open()
