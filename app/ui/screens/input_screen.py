"""
录入页（食物库管理）
- JSON 批量录入
- AI 提示词复制
- 食物列表
- 编辑/删除弹窗
- 导出与分享
"""

import json
import os
import copy
from kivy.app import App
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.metrics import dp
from kivy.clock import Clock

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.list import MDList, TwoLineAvatarIconListItem, ImageLeftWidget, IconRightWidget
from kivymd.uix.dialog import MDDialog
from kivymd.uix.snackbar import MDSnackbar
from kivymd.uix.card import MDCard
from kivymd.uix.widget import MDWidget


class InputScreen(MDScreen):
    """录入页 — 食物库管理"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'input'
        self._dialog = None
        self._build_ui()

    # ── UI 构建 ───────────────────────────────────────────

    def _build_ui(self):
        """构建录入页界面。"""
        # 根布局
        root = MDBoxLayout(orientation='vertical')

        # 顶部导航栏
        self.top_bar = MDTopAppBar(
            title="食物库管理",
            left_action_items=[["refresh", self._on_refresh]],
            right_action_items=[
                ["export-variant", self._on_export],
                ["share-variant", self._on_share],
            ],
            elevation=2,
        )
        root.add_widget(self.top_bar)

        # ── 主内容区（可滚动） ──
        scroll = MDScrollView()
        self.content_area = MDBoxLayout(
            orientation='vertical',
            padding=dp(16),
            spacing=dp(12),
            size_hint_y=None,
            adaptive_height=True,
        )

        # ── 1. JSON 录入区域 ──
        self._add_section_title("JSON 批量录入")

        self.json_input = MDTextField(
            hint_text='[{"name":"食物名","methods":[{"method_name":"烹饪方式","nutrients":{...}}]}]',
            multiline=True,
            mode="line",
            max_height=dp(150),
        )
        self.content_area.add_widget(self.json_input)

        btn_row = MDBoxLayout(
            spacing=dp(8),
            size_hint_y=None,
            height=dp(48),
            adaptive_width=True,
        )
        btn_submit = MDRaisedButton(text="录入食物", on_release=self._on_json_import)
        btn_ai = MDFlatButton(text="AI生成（复制提示词）", on_release=self._on_copy_prompt)
        btn_row.add_widget(btn_submit)
        btn_row.add_widget(btn_ai)
        self.content_area.add_widget(btn_row)

        # ── 2. 食物列表 ──
        self._add_section_title("食物列表")
        self.food_list = MDList(spacing=dp(4))
        self.content_area.add_widget(self.food_list)

        # 空状态提示
        self.empty_label = MDLabel(
            text="暂无食物数据，请先录入",
            halign="center",
            theme_text_color="Hint",
            size_hint_y=None,
            height=dp(60),
        )

        scroll.add_widget(self.content_area)
        root.add_widget(scroll)

        self.add_widget(root)

        # 初始化列表
        Clock.schedule_once(lambda dt: self._refresh_food_list(), 0.1)

    def _add_section_title(self, title: str):
        """添加分区标题。"""
        lbl = MDLabel(
            text=title,
            font_style="H5",
            size_hint_y=None,
            height=dp(36),
        )
        self.content_area.add_widget(lbl)

    # ── 食物列表刷新 ──────────────────────────────────────

    def _refresh_food_list(self, *args):
        """刷新食物列表。"""
        self.food_list.clear_widgets()
        app = MDApp.get_running_app()
        foods = app.food_manager.foods

        if not foods:
            if self.empty_label.parent is None:
                self.food_list.add_widget(self.empty_label)
            return

        if self.empty_label.parent:
            self.empty_label.parent.remove_widget(self.empty_label)

        for food in foods:
            method_names = [m['method_name'] for m in food.get('methods', [])]
            subtitle = ' · '.join(method_names)

            item = TwoLineAvatarIconListItem(
                text=food['name'],
                secondary_text=subtitle,
            )
            item.text = food['name']
            item.secondary_text = subtitle

            # 编辑按钮
            edit_btn = MDIconButton(icon="pencil", on_release=lambda x, f=food: self._on_edit_food(f))
            # 删除按钮
            del_btn = MDIconButton(icon="delete", on_release=lambda x, f=food: self._on_delete_food(f))

            # KivyMD TwoLineAvatarIconListItem 使用 right 属性的 widget
            # 或者使用 ImageRightWidget
            from kivy.uix.boxlayout import BoxLayout
            right_box = BoxLayout(orientation='horizontal', size_hint_x=None, width=dp(96))
            right_box.add_widget(edit_btn)
            right_box.add_widget(del_btn)

            # 尝试设置右侧图标
            try:
                item.add_widget(right_box)
            except Exception:
                pass

            self.food_list.add_widget(item)

    # ── JSON 导入 ─────────────────────────────────────────

    def _on_json_import(self, instance):
        """处理 JSON 批量导入。"""
        json_text = self.json_input.text.strip()
        if not json_text:
            self._toast("请输入 JSON 数据")
            return

        app = MDApp.get_running_app()
        success, skipped, messages = app.food_manager.import_from_json(json_text)

        if success == 0 and skipped == 0:
            self._toast(messages[0] if messages else "导入失败")
            return

        self._refresh_food_list()
        self.json_input.text = ""
        self._toast(f"成功 {success} 个，跳过 {skipped} 个")

    # ── AI 提示词复制 ────────────────────────────────────

    def _on_copy_prompt(self, instance):
        """复制 AI 提示词模板到剪贴板。"""
        prompt = self._get_ai_prompt()
        try:
            import pyperclip
            pyperclip.copy(prompt)
            self._toast("提示词已复制到剪贴板，请粘贴到 AI 工具中")
        except Exception:
            try:
                from kivy.core.clipboard import Clipboard
                Clipboard.copy(prompt)
                self._toast("提示词已复制到剪贴板")
            except Exception:
                self._toast("复制失败，请手动复制")

    def _get_ai_prompt(self) -> str:
        """返回 AI 提示词模板。"""
        return '''请帮我生成食物【XXX】在【未处理】和【指定烹饪方式，如：蒸、炒、烤】两种状态下的营养成分JSON数据。
要求：
1. 包含：能量（大卡）、蛋白质、脂肪、碳水化合物、膳食纤维（克）。
2. 维生素包括：维生素A、维生素B1、维生素B2、维生素B6、维生素B12、维生素C、维生素D、维生素E、维生素K。单位统一使用：维A、D、E、K用mcg（微克），B1、B2、B6用mg（毫克），B12用mcg，C用mg。
3. 矿物质包括：钙、铁、锌、硒、钠、钾、镁、磷。单位统一使用：mg（毫克），硒用mcg（微克）。
4. 请分别提供未经处理和指定烹饪方式处理后的营养数据。
5. 请严格按照以下JSON格式输出，不要有任何多余解释：
{
  "name": "食物名称",
  "methods": [
    {
      "method_name": "烹饪方式名称",
      "nutrients": {
        "能量": 数值,
        "蛋白质": 数值,
        "脂肪": 数值,
        "碳水化合物": 数值,
        "膳食纤维": 数值,
        "维生素": [
          {"name": "维生素A", "value": 数值, "unit": "mcg"},
          {"name": "维生素B1", "value": 数值, "unit": "mg"},
          {"name": "维生素B2", "value": 数值, "unit": "mg"},
          {"name": "维生素B6", "value": 数值, "unit": "mg"},
          {"name": "维生素B12", "value": 数值, "unit": "mcg"},
          {"name": "维生素C", "value": 数值, "unit": "mg"},
          {"name": "维生素D", "value": 数值, "unit": "mcg"},
          {"name": "维生素E", "value": 数值, "unit": "mg"},
          {"name": "维生素K", "value": 数值, "unit": "mcg"}
        ],
        "矿物质": [
          {"name": "钙", "value": 数值, "unit": "mg"},
          {"name": "铁", "value": 数值, "unit": "mg"},
          {"name": "锌", "value": 数值, "unit": "mg"},
          {"name": "硒", "value": 数值, "unit": "mcg"},
          {"name": "钠", "value": 数值, "unit": "mg"},
          {"name": "钾", "value": 数值, "unit": "mg"},
          {"name": "镁", "value": 数值, "unit": "mg"},
          {"name": "磷", "value": 数值, "unit": "mg"}
        ],
        "自定义": []
      }
    }
  ]
}'''

    # ── 编辑食物弹窗 ─────────────────────────────────────

    def _on_edit_food(self, food: dict):
        """打开编辑食物弹窗。"""
        self._editing_food = copy.deepcopy(food)
        self._editing_original_name = food['name']

        # 构建自定义内容
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            size_hint_y=None,
            adaptive_height=True,
        )

        # 食物名称
        self._edit_name_field = MDTextField(
            text=self._editing_food['name'],
            hint_text="食物名称",
            mode="line",
        )
        content.add_widget(self._edit_name_field)

        # 方法列表标签
        content.add_widget(MDLabel(
            text="烹饪方式",
            font_style="Subtitle1",
            size_hint_y=None,
            height=dp(28),
        ))

        # 方法容器
        self._edit_methods_container = MDBoxLayout(
            orientation='vertical',
            spacing=dp(4),
            size_hint_y=None,
            adaptive_height=True,
        )
        content.add_widget(self._edit_methods_container)

        # 添加方法按钮
        btn_add_method = MDFlatButton(
            text="+ 添加烹饪方式",
            on_release=lambda x: self._on_add_method_dialog(),
        )
        content.add_widget(btn_add_method)

        # 刷新方法列表
        self._refresh_edit_methods()

        self._dialog = MDDialog(
            title="编辑食物",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="取消", on_release=lambda x: self._close_dialog()),
                MDRaisedButton(text="保存", on_release=lambda x: self._on_save_edit()),
            ],
        )
        self._dialog.open()

    def _refresh_edit_methods(self):
        """刷新编辑弹窗中的方法列表。"""
        self._edit_methods_container.clear_widgets()

        for i, method in enumerate(self._editing_food.get('methods', [])):
            mn = method.get('method_name', '')
            nutrients = method.get('nutrients', {})
            energy = nutrients.get('能量', 0)
            protein = nutrients.get('蛋白质', 0)

            row = MDBoxLayout(
                size_hint_y=None,
                height=dp(40),
                spacing=dp(4),
            )

            label = MDLabel(
                text=f"{mn}  (能量{energy:.0f}大卡, 蛋白质{protein:.1f}g)",
                size_hint_x=0.65,
                font_style="Body2",
            )

            edit_btn = MDIconButton(
                icon="pencil",
                on_release=lambda x, idx=i: self._on_edit_method(idx),
            )
            del_btn = MDIconButton(
                icon="delete",
                on_release=lambda x, idx=i, name=mn: self._on_delete_method(idx, name),
            )

            row.add_widget(label)
            row.add_widget(edit_btn)
            row.add_widget(del_btn)
            self._edit_methods_container.add_widget(row)

    def _on_delete_method(self, index: int, method_name: str):
        """在编辑弹窗中删除烹饪方式。"""
        if method_name == '生':
            self._toast("「生」烹饪方式不可删除")
            return

        ok, msg = MDApp.get_running_app().food_manager.delete_method(
            self._editing_original_name, method_name
        )
        if ok:
            del self._editing_food['methods'][index]
            self._refresh_edit_methods()
        self._toast(msg)

    def _on_add_method_dialog(self):
        """添加烹饪方式弹窗。"""
        # 先关闭编辑弹窗
        if self._dialog:
            self._dialog.dismiss()

        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            padding=dp(8),
            size_hint_y=None,
            adaptive_height=True,
        )

        # 方式名称
        method_name_field = MDTextField(
            hint_text="烹饪方式名称（如：蒸、炒）",
            mode="line",
        )
        content.add_widget(method_name_field)

        # 基础营养
        content.add_widget(MDLabel(text="基础营养（每100g）", font_style="Subtitle2", size_hint_y=None, height=dp(24)))
        energy_field = MDTextField(hint_text="能量(大卡)", mode="outlined", input_filter="float")
        protein_field = MDTextField(hint_text="蛋白质(g)", mode="outlined", input_filter="float")
        fat_field = MDTextField(hint_text="脂肪(g)", mode="outlined", input_filter="float")
        carb_field = MDTextField(hint_text="碳水化合物(g)", mode="outlined", input_filter="float")
        fiber_field = MDTextField(hint_text="膳食纤维(g)", mode="outlined", input_filter="float")

        for fld in [energy_field, protein_field, fat_field, carb_field, fiber_field]:
            content.add_widget(fld)

        # 维生素和矿物质（简化：通过 JSON 文本输入）
        content.add_widget(MDLabel(text="维生素（JSON，可选）", font_style="Subtitle2", size_hint_y=None, height=dp(24)))
        vitamins_field = MDTextField(
            hint_text='[{"name":"维生素A","value":0,"unit":"mcg"},...]',
            multiline=True,
            mode="line",
            max_height=dp(80),
        )
        content.add_widget(vitamins_field)

        content.add_widget(MDLabel(text="矿物质（JSON，可选）", font_style="Subtitle2", size_hint_y=None, height=dp(24)))
        minerals_field = MDTextField(
            hint_text='[{"name":"钙","value":0,"unit":"mg"},...]',
            multiline=True,
            mode="line",
            max_height=dp(80),
        )
        content.add_widget(minerals_field)

        # 自定义（JSON，可选）
        content.add_widget(MDLabel(text="自定义成分（JSON，可选）", font_style="Subtitle2", size_hint_y=None, height=dp(24)))
        custom_field = MDTextField(
            hint_text='[{"name":"自定义","value":0,"unit":"单位"}]',
            multiline=True,
            mode="line",
            max_height=dp(60),
        )
        content.add_widget(custom_field)

        sub_dialog = MDDialog(
            title="添加烹饪方式",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="取消", on_release=lambda x: self._close_sub_and_reopen(sub_dialog)),
                MDRaisedButton(text="添加", on_release=lambda x: self._do_add_method(
                    sub_dialog, method_name_field, energy_field, protein_field,
                    fat_field, carb_field, fiber_field, vitamins_field,
                    minerals_field, custom_field
                )),
            ],
        )
        sub_dialog.open()

    def _close_sub_and_reopen(self, sub_dialog):
        """关闭子对话框并重新打开编辑弹窗。"""
        sub_dialog.dismiss()
        # 重新打开编辑弹窗
        self._on_edit_food(self._editing_food)

    def _do_add_method(self, sub_dialog, mn_field, energy_f, protein_f, fat_f,
                       carb_f, fiber_f, vit_f, min_f, custom_f):
        """执行添加烹饪方式。"""
        method_name = mn_field.text.strip()
        if not method_name:
            self._toast("请输入烹饪方式名称")
            return

        try:
            energy = float(energy_f.text or 0)
            protein = float(protein_f.text or 0)
            fat = float(fat_f.text or 0)
            carb = float(carb_f.text or 0)
            fiber = float(fiber_f.text or 0)
        except ValueError:
            self._toast("基础营养请输入有效数字")
            return

        # 解析维生素
        vitamins = []
        if vit_f.text.strip():
            try:
                vitamins = json.loads(vit_f.text)
            except json.JSONDecodeError:
                self._toast("维生素 JSON 格式错误")
                return

        # 解析矿物质
        minerals = []
        if min_f.text.strip():
            try:
                minerals = json.loads(min_f.text)
            except json.JSONDecodeError:
                self._toast("矿物质 JSON 格式错误")
                return

        # 解析自定义
        customs = []
        if custom_f.text.strip():
            try:
                customs = json.loads(custom_f.text)
            except json.JSONDecodeError:
                self._toast("自定义成分 JSON 格式错误")
                return

        nutrients = {
            '能量': energy,
            '蛋白质': protein,
            '脂肪': fat,
            '碳水化合物': carb,
            '膳食纤维': fiber,
            '维生素': vitamins,
            '矿物质': minerals,
            '自定义': customs,
        }

        method = {
            'method_name': method_name,
            'nutrients': nutrients,
        }

        ok, msg = MDApp.get_running_app().food_manager.add_method(
            self._editing_original_name, method
        )

        if ok:
            self._editing_food['methods'].append(method)

        sub_dialog.dismiss()
        self._toast(msg)
        # 重新打开编辑弹窗
        self._on_edit_food(self._editing_food)

    def _on_edit_method(self, index: int):
        """编辑某个烹饪方式的营养成分。"""
        method = self._editing_food['methods'][index]
        self._toast(f"编辑「{method['method_name']}」的营养数据（可通过 JSON 录入页面修改）")

    def _on_save_edit(self):
        """保存编辑。"""
        new_name = self._edit_name_field.text.strip()
        if not new_name:
            self._toast("食物名称不能为空")
            return

        self._editing_food['name'] = new_name

        app = MDApp.get_running_app()
        ok, msg = app.food_manager.update_food(self._editing_original_name, self._editing_food)
        self._close_dialog()
        self._refresh_food_list()
        self._toast(msg)

    # ── 删除食物 ─────────────────────────────────────────

    def _on_delete_food(self, food: dict):
        """确认删除食物弹窗。"""
        self._dialog = MDDialog(
            title="确认删除",
            text=f"确定要删除食物「{food['name']}」吗？此操作不可撤销。",
            buttons=[
                MDFlatButton(text="取消", on_release=lambda x: self._close_dialog()),
                MDFlatButton(text="删除", on_release=lambda x: self._confirm_delete_food(food)),
            ],
        )
        self._dialog.open()

    def _confirm_delete_food(self, food: dict):
        """确认删除。"""
        app = MDApp.get_running_app()
        ok, msg = app.food_manager.delete_food(food['name'])
        self._close_dialog()
        self._refresh_food_list()
        self._toast(msg)

    def _close_dialog(self):
        """关闭弹窗。"""
        if self._dialog:
            self._dialog.dismiss()
            self._dialog = None

    # ── 导出 ──────────────────────────────────────────────

    def _on_export(self, instance):
        """导出食物库。"""
        app = MDApp.get_running_app()
        ok, path = app.food_manager.export_to_file()
        if ok:
            self._toast(f"已导出到：{path}")
        else:
            self._toast(f"导出失败：{path}")

    # ── 分享 ──────────────────────────────────────────────

    def _on_share(self, instance):
        """分享食物库文件。"""
        app = MDApp.get_running_app()
        ok, path = app.food_manager.export_to_file()
        if not ok:
            self._toast(f"导出失败：{path}")
            return

        try:
            from plyer import share
            share.share_file(path, title="分享食物数据库")
        except Exception:
            try:
                from android.storage import primary_external_storage_path
                import shutil
                pub_path = os.path.join(primary_external_storage_path(), 'Download', os.path.basename(path))
                shutil.copy(path, pub_path)
                self._toast(f"已复制到下载目录：{pub_path}")
            except Exception:
                self._toast(f"文件已保存到：{path}")

    # ── 刷新 ──────────────────────────────────────────────

    def _on_refresh(self, instance):
        """刷新列表。"""
        self._refresh_food_list()
        self._toast("已刷新")

    # ── 辅助 ──────────────────────────────────────────────

    def _toast(self, text: str):
        """显示 Snackbar 提示。"""
        MDSnackbar(MDLabel(text=text)).open()
