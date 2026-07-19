"""
历史页（历史记录与统计分析）
- 日历视图（有记录的日期标注）
- 日期范围选择（最近7天/15天/本月）
- 统计图表（折线图 + 扇形图）
"""

from datetime import date, datetime, timedelta
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.uix.image import Image as KivyImage
from kivy.core.image import Image as CoreImage

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRectangleFlatButton, MDFlatButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.snackbar import MDSnackbar

from models.nutrients import (
    BASIC_NUTRIENTS, BASIC_NUTRIENT_UNITS,
    nutrients_to_display_dict,
)
from ui.widgets.charts import ChartGenerator


class HistoryScreen(MDScreen):
    """历史页 — 历史记录与统计分析"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'history'
        self._chart_gen = ChartGenerator()
        self._selected_date = date.today().strftime('%Y-%m-%d')
        self._range_start = self._get_default_range()[0]
        self._range_end = self._get_default_range()[1]
        self._build_ui()

    def _get_default_range(self) -> tuple:
        """默认范围：最近7天。"""
        today = date.today()
        start = today - timedelta(days=6)
        return (start.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))

    # ── UI 构建 ───────────────────────────────────────────

    def _build_ui(self):
        root = MDBoxLayout(orientation='vertical')

        self.top_bar = MDTopAppBar(
            title="历史记录",
            elevation=2,
        )
        root.add_widget(self.top_bar)

        # 主内容（可滚动）
        scroll = MDScrollView()
        self.content_area = MDBoxLayout(
            orientation='vertical',
            padding=dp(16),
            spacing=dp(12),
            size_hint_y=None,
            adaptive_height=True,
        )

        # ── 日历视图（简单的月份网格） ──
        self._build_calendar_section()

        # ── 日期范围按钮 ──
        self._build_range_buttons()

        # ── 选中日期的记录 ──
        self.date_records_label = MDLabel(
            text="",
            font_style="Subtitle1",
            size_hint_y=None,
            adaptive_height=True,
        )
        self.content_area.add_widget(self.date_records_label)

        self.date_records_container = MDBoxLayout(
            orientation='vertical',
            spacing=dp(4),
            size_hint_y=None,
            adaptive_height=True,
        )
        self.content_area.add_widget(self.date_records_container)

        # ── 统计图表 ──
        self.charts_label = MDLabel(
            text="统计分析",
            font_style="H5",
            size_hint_y=None,
            height=dp(36),
        )
        self.content_area.add_widget(self.charts_label)

        self.charts_container = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            size_hint_y=None,
            adaptive_height=True,
        )
        self.content_area.add_widget(self.charts_container)

        # 空状态
        self.chart_placeholder = MDLabel(
            text="暂无足够数据生成图表",
            halign="center",
            theme_text_color="Hint",
            size_hint_y=None,
            height=dp(60),
        )
        self.charts_container.add_widget(self.chart_placeholder)

        scroll.add_widget(self.content_area)
        root.add_widget(scroll)
        self.add_widget(root)

        Clock.schedule_once(lambda dt: self._refresh_all(), 0.2)

    def _build_calendar_section(self):
        """构建简易日历区域。"""
        self.calendar_label = MDLabel(
            text="日历",
            font_style="H5",
            size_hint_y=None,
            height=dp(32),
        )
        self.content_area.add_widget(self.calendar_label)

        # 月份导航
        nav_row = MDBoxLayout(
            size_hint_y=None,
            height=dp(48),
            spacing=dp(8),
        )

        self.prev_month_btn = MDIconButton(
            icon="chevron-left",
            on_release=self._on_prev_month,
        )
        self.month_label = MDLabel(
            text="",
            halign="center",
            font_style="Subtitle1",
        )
        self.next_month_btn = MDIconButton(
            icon="chevron-right",
            on_release=self._on_next_month,
        )

        nav_row.add_widget(self.prev_month_btn)
        nav_row.add_widget(self.month_label)
        nav_row.add_widget(self.next_month_btn)
        self.content_area.add_widget(nav_row)

        # 日期网格
        self.calendar_grid = MDBoxLayout(
            orientation='vertical',
            spacing=dp(2),
            size_hint_y=None,
            adaptive_height=True,
        )
        self.content_area.add_widget(self.calendar_grid)

        # 初始化月份
        self._calendar_year = date.today().year
        self._calendar_month = date.today().month

    def _build_range_buttons(self):
        """构建时间范围选择按钮。"""
        range_row = MDBoxLayout(
            spacing=dp(8),
            size_hint_y=None,
            height=dp(48),
        )

        btn_7 = MDRectangleFlatButton(text="最近7天", on_release=lambda x: self._set_range(7))
        btn_15 = MDRectangleFlatButton(text="最近15天", on_release=lambda x: self._set_range(15))
        btn_month = MDRectangleFlatButton(text="本月", on_release=lambda x: self._set_range_month())

        range_row.add_widget(btn_7)
        range_row.add_widget(btn_15)
        range_row.add_widget(btn_month)
        self.content_area.add_widget(range_row)

    # ── 日历逻辑 ──────────────────────────────────────────

    def _on_prev_month(self, instance):
        if self._calendar_month == 1:
            self._calendar_year -= 1
            self._calendar_month = 12
        else:
            self._calendar_month -= 1
        self._render_calendar()

    def _on_next_month(self, instance):
        if self._calendar_month == 12:
            self._calendar_year += 1
            self._calendar_month = 1
        else:
            self._calendar_month += 1
        self._render_calendar()

    def _render_calendar(self):
        """渲染当月日历网格。"""
        self.month_label.text = f"{self._calendar_year}年 {self._calendar_month}月"

        self.calendar_grid.clear_widgets()

        # 获取有记录的日期集合
        app = MDApp.get_running_app()
        date_counts = app.record_manager.get_date_counts()

        # 当月第一天
        first_day = date(self._calendar_year, self._calendar_month, 1)
        # 当月天数
        if self._calendar_month == 12:
            next_month = date(self._calendar_year + 1, 1, 1)
        else:
            next_month = date(self._calendar_year, self._calendar_month + 1, 1)
        days_in_month = (next_month - first_day).days

        # 第一天是星期几（0=Monday, 6=Sunday）
        start_weekday = first_day.weekday()

        # 星期头
        weekdays_cn = ['一', '二', '三', '四', '五', '六', '日']
        header_row = MDBoxLayout(
            spacing=dp(1),
            size_hint_y=None,
            height=dp(24),
        )
        for wd in weekdays_cn:
            lbl = MDLabel(text=wd, halign="center", font_style="Caption", size_hint_x=1 / 7)
            header_row.add_widget(lbl)
        self.calendar_grid.add_widget(header_row)

        # 构建格子
        day = 1
        for week in range(6):  # 最多6行
            row = MDBoxLayout(spacing=dp(2), size_hint_y=None, height=dp(32))
            for wd in range(7):
                if (week == 0 and wd < start_weekday) or day > days_in_month:
                    # 空白格子
                    row.add_widget(MDLabel(text="", size_hint_x=1 / 7))
                else:
                    date_str = f"{self._calendar_year:04d}-{self._calendar_month:02d}-{day:02d}"
                    has_record = date_str in date_counts

                    if has_record:
                        # 有记录的日期用绿色圆点标记
                        btn = MDFlatButton(
                            text=str(day),
                            md_bg_color=(0.3, 0.8, 0.3, 0.3),
                            on_release=lambda x, d=date_str: self._on_date_click(d),
                            size_hint_x=1 / 7,
                        )
                    else:
                        btn = MDFlatButton(
                            text=str(day),
                            on_release=lambda x, d=date_str: self._on_date_click(d),
                            size_hint_x=1 / 7,
                        )

                    if date_str == self._selected_date:
                        btn.md_bg_color = (0.3, 0.6, 0.3, 0.5)

                    row.add_widget(btn)
                    day += 1
            self.calendar_grid.add_widget(row)
            if day > days_in_month:
                break

    def _on_date_click(self, date_str: str):
        """点击日历上的某一天。"""
        self._selected_date = date_str
        self._show_date_records(date_str)
        self._render_calendar()

    def _show_date_records(self, date_str: str):
        """显示选中日期的记录。"""
        app = MDApp.get_running_app()
        summary = app.record_manager.get_daily_summary(date_str)

        self.date_records_label.text = f"{date_str} 摄入详情"

        self.date_records_container.clear_widgets()

        if not summary['has_data']:
            self.date_records_container.add_widget(
                MDLabel(text="该日无记录", theme_text_color="Hint", size_hint_y=None, height=dp(40))
            )
            return

        for rec in summary['records']:
            ts = rec.get('timestamp', '')[:16]
            entries = rec.get('entries', [])
            texts = []
            for e in entries:
                texts.append(f"  {e.get('food_name','')} × {e.get('grams',0)}g")

            line = f"[{ts}]  " + '，'.join(texts)
            lbl = MDLabel(
                text=line,
                font_style="Body2",
                size_hint_y=None,
                adaptive_height=True,
            )
            self.date_records_container.add_widget(lbl)

    # ── 范围选择 ──────────────────────────────────────────

    def _set_range(self, days: int):
        """设置最近N天范围。"""
        end = date.today()
        start = end - timedelta(days=days - 1)
        self._range_start = start.strftime('%Y-%m-%d')
        self._range_end = end.strftime('%Y-%m-%d')
        self._render_charts()

    def _set_range_month(self):
        """设置本月范围。"""
        today = date.today()
        start = today.replace(day=1)
        self._range_start = start.strftime('%Y-%m-%d')
        self._range_end = today.strftime('%Y-%m-%d')
        self._render_charts()

    # ── 图表渲染 ──────────────────────────────────────────

    def _refresh_all(self):
        """初始刷新。"""
        self._render_calendar()
        self._render_charts()

    def _render_charts(self):
        """渲染统计图表。"""
        app = MDApp.get_running_app()
        summaries = app.record_manager.get_range_summaries(self._range_start, self._range_end)

        self.charts_container.clear_widgets()

        # 筛选有数据的日期
        data_days = [s for s in summaries if s['has_data']]
        if not data_days:
            self.charts_container.add_widget(self.chart_placeholder)
            return

        # 生成图表
        try:
            # 折线图：每日能量趋势
            energy_chart_img = self._chart_gen.create_line_chart(
                data_days,
                '能量',
                f'每日能量趋势 ({self._range_start} ~ {self._range_end})',
            )
            if energy_chart_img:
                self.charts_container.add_widget(energy_chart_img)

            # 折线图：每日蛋白质趋势
            protein_chart_img = self._chart_gen.create_line_chart(
                data_days,
                '蛋白质',
                f'每日蛋白质趋势 ({self._range_start} ~ {self._range_end})',
            )
            if protein_chart_img:
                self.charts_container.add_widget(protein_chart_img)

            # 扇形图：各食物能量占比
            pie_energy_img = self._chart_gen.create_pie_chart(
                data_days,
                '能量',
                f'各食物能量占比 ({self._range_start} ~ {self._range_end})',
            )
            if pie_energy_img:
                self.charts_container.add_widget(pie_energy_img)

            # 扇形图：各食物蛋白质占比
            pie_protein_img = self._chart_gen.create_pie_chart(
                data_days,
                '蛋白质',
                f'各食物蛋白质占比 ({self._range_start} ~ {self._range_end})',
            )
            if pie_protein_img:
                self.charts_container.add_widget(pie_protein_img)

        except Exception as e:
            self.charts_container.add_widget(
                MDLabel(text=f"图表生成失败：{str(e)}", theme_text_color="Error", size_hint_y=None, height=dp(40))
            )

    def on_enter(self, *args):
        """进入页面时刷新。"""
        self._render_calendar()
        self._render_charts()
