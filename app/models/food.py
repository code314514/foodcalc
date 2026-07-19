"""
食物数据库管理模块
- 加载/保存 food_db.json
- 增删改查食物
- JSON 批量导入
- 导出到文件
"""

import json
import os
import copy
from datetime import datetime
from typing import List, Dict, Optional, Tuple

from models.nutrients import NUTRIENT_TEMPLATE, EMPTY_NUTRIENTS, NUTRIENT_ORDER


class FoodManager:
    """食物数据库管理器"""

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

        self.data_dir = data_dir
        self.db_path = os.path.join(data_dir, 'food_db.json')
        self.exports_dir = os.path.join(data_dir, '..', 'exports')
        os.makedirs(self.exports_dir, exist_ok=True)

        self._foods: List[Dict] = []
        self.load()

    # ── 持久化 ────────────────────────────────────────────

    def load(self) -> bool:
        """从文件加载食物库。失败时重置为空列表。"""
        try:
            if os.path.exists(self.db_path):
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, list):
                    self._foods = data
                    return True
            self._foods = []
            return False
        except (json.JSONDecodeError, IOError, OSError):
            self._foods = []
            return False

    def save(self) -> bool:
        """保存食物库到文件。"""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self._foods, f, ensure_ascii=False, indent=2)
            return True
        except (IOError, OSError):
            return False

    # ── 查询 ──────────────────────────────────────────────

    @property
    def foods(self) -> List[Dict]:
        """返回食物列表的深拷贝，避免外部直接修改。"""
        return copy.deepcopy(self._foods)

    @property
    def food_count(self) -> int:
        return len(self._foods)

    def get_food_names(self) -> List[str]:
        """返回所有食物名称列表。"""
        return [f['name'] for f in self._foods]

    def get_food_by_name(self, name: str) -> Optional[Dict]:
        """按名称查找食物（精确匹配）。"""
        name = name.strip()
        for food in self._foods:
            if food['name'] == name:
                return copy.deepcopy(food)
        return None

    def food_exists(self, name: str) -> bool:
        """检查食物名是否已存在。"""
        name = name.strip()
        return any(f['name'] == name for f in self._foods)

    def get_food_methods(self, name: str) -> List[str]:
        """返回某个食物的所有烹饪方式名称列表。"""
        food = self._find_food(name)
        if food is None:
            return []
        return [m['method_name'] for m in food.get('methods', [])]

    def get_food_method_nutrients(self, food_name: str, method_name: str) -> Optional[Dict]:
        """获取某食物某烹饪方式的营养成分。"""
        food = self._find_food(food_name)
        if food is None:
            return None
        for method in food.get('methods', []):
            if method['method_name'] == method_name:
                return copy.deepcopy(method['nutrients'])
        return None

    # ── 内部查找（返回引用，慎重使用） ──────────────────

    def _find_food(self, name: str) -> Optional[Dict]:
        """在内部列表中以引用方式查找食物。"""
        name = name.strip()
        for food in self._foods:
            if food['name'] == name:
                return food
        return None

    def _find_food_index(self, name: str) -> int:
        """查找食物的索引。"""
        name = name.strip()
        for i, food in enumerate(self._foods):
            if food['name'] == name:
                return i
        return -1

    # ── 校验 ──────────────────────────────────────────────

    def validate_food(self, food: Dict) -> Tuple[bool, str]:
        """
        校验单个食物对象是否合法。
        返回 (是否有效, 错误信息)
        """
        if not isinstance(food, dict):
            return False, "食物数据格式错误：应为字典"

        name = food.get('name', '').strip()
        if not name:
            return False, "食物名称为空"

        methods = food.get('methods', [])
        if not isinstance(methods, list) or len(methods) == 0:
            return False, f"食物「{name}」缺少烹饪方式"

        method_names = []
        has_raw = False
        for method in methods:
            if not isinstance(method, dict):
                return False, f"食物「{name}」的烹饪方式格式错误"
            mn = method.get('method_name', '').strip()
            if not mn:
                return False, f"食物「{name}」的烹饪方式名称为空"
            if mn == '生':
                has_raw = True
            if mn in method_names:
                return False, f"食物「{name}」的烹饪方式「{mn}」重复"
            method_names.append(mn)

            # 校验 nutrients
            nutrients = method.get('nutrients', {})
            if not isinstance(nutrients, dict):
                return False, f"食物「{name}」的烹饪方式「{mn}」营养成分格式错误"

        if not has_raw:
            return False, f"食物「{name}」缺少「生」烹饪方式"

        return True, ""

    def validate_food_name(self, name: str, exclude_name: str = None) -> Tuple[bool, str]:
        """
        校验食物名称是否可用。
        exclude_name: 编辑时排除自身的旧名称。
        """
        name = name.strip()
        if not name:
            return False, "食物名称不能为空"
        if len(name) > 50:
            return False, "食物名称过长（最多50个字符）"
        # 检查重名
        for food in self._foods:
            if food['name'] == name:
                if exclude_name is None or food['name'] != exclude_name:
                    return False, f"食物「{name}」已存在"
        return True, ""

    # ── 增 ────────────────────────────────────────────────

    def add_food(self, food: Dict) -> Tuple[bool, str]:
        """添加单个食物。"""
        valid, msg = self.validate_food(food)
        if not valid:
            return False, msg

        name = food['name'].strip()
        if self.food_exists(name):
            return False, f"食物「{name}」已存在，跳过"

        # 清理：去除名称首尾空格
        cleaned = copy.deepcopy(food)
        cleaned['name'] = name
        for method in cleaned.get('methods', []):
            method['method_name'] = method.get('method_name', '').strip()
            # 补齐空字段
            n = method.get('nutrients', {})
            n.setdefault('能量', 0)
            n.setdefault('蛋白质', 0)
            n.setdefault('脂肪', 0)
            n.setdefault('碳水化合物', 0)
            n.setdefault('膳食纤维', 0)
            n.setdefault('维生素', [])
            n.setdefault('矿物质', [])
            n.setdefault('自定义', [])

        self._foods.append(cleaned)
        self.save()
        return True, f"食物「{name}」录入成功"

    def add_foods_batch(self, foods: List[Dict]) -> Tuple[int, int, List[str]]:
        """
        批量添加食物。
        返回 (成功数, 跳過数, 信息列表)
        """
        success = 0
        skipped = 0
        messages = []

        for food in foods:
            ok, msg = self.add_food(food)
            if ok:
                success += 1
            else:
                skipped += 1
            messages.append(msg)

        return success, skipped, messages

    def import_from_json(self, json_str: str) -> Tuple[int, int, List[str]]:
        """
        从 JSON 字符串批量导入食物。
        返回 (成功数, 跳過数, 信息列表)
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            return 0, 0, [f"JSON 解析失败：{str(e)}"]

        if isinstance(data, dict):
            data = [data]

        if not isinstance(data, list):
            return 0, 0, ["JSON 格式错误：应为数组或对象"]

        return self.add_foods_batch(data)

    # ── 删 ────────────────────────────────────────────────

    def delete_food(self, name: str) -> Tuple[bool, str]:
        """删除指定食物。"""
        idx = self._find_food_index(name)
        if idx < 0:
            return False, f"食物「{name}」不存在"
        del self._foods[idx]
        self.save()
        return True, f"食物「{name}」已删除"

    # ── 改 ────────────────────────────────────────────────

    def update_food_name(self, old_name: str, new_name: str) -> Tuple[bool, str]:
        """修改食物名称。"""
        food = self._find_food(old_name)
        if food is None:
            return False, f"食物「{old_name}」不存在"

        valid, msg = self.validate_food_name(new_name, exclude_name=old_name)
        if not valid:
            return False, msg

        food['name'] = new_name.strip()
        self.save()
        return True, f"食物名称已更新为「{new_name}」"

    def update_food(self, name: str, updated_food: Dict) -> Tuple[bool, str]:
        """
        整体更新食物（用于编辑弹窗保存）。
        旧名称 name，新数据 updated_food。
        """
        valid, msg = self.validate_food(updated_food)
        if not valid:
            return False, msg

        new_name = updated_food['name'].strip()

        # 如果改名了，检查重名
        if new_name != name:
            if self.food_exists(new_name):
                return False, f"食物「{new_name}」已存在"

        idx = self._find_food_index(name)
        if idx < 0:
            return False, f"食物「{name}」不存在"

        # 清理新数据
        cleaned = copy.deepcopy(updated_food)
        cleaned['name'] = new_name
        for method in cleaned.get('methods', []):
            method['method_name'] = method.get('method_name', '').strip()
            n = method.get('nutrients', {})
            n.setdefault('能量', 0)
            n.setdefault('蛋白质', 0)
            n.setdefault('脂肪', 0)
            n.setdefault('碳水化合物', 0)
            n.setdefault('膳食纤维', 0)
            n.setdefault('维生素', [])
            n.setdefault('矿物质', [])
            n.setdefault('自定义', [])

        self._foods[idx] = cleaned
        self.save()
        return True, f"食物「{new_name}」已更新"

    def add_method(self, food_name: str, method: Dict) -> Tuple[bool, str]:
        """为食物添加烹饪方式。"""
        food = self._find_food(food_name)
        if food is None:
            return False, f"食物「{food_name}」不存在"

        mn = method.get('method_name', '').strip()
        if not mn:
            return False, "烹饪方式名称不能为空"

        existing = [m['method_name'] for m in food.get('methods', [])]
        if mn in existing:
            return False, f"烹饪方式「{mn}」已存在"

        nutrients = method.get('nutrients', {})
        nutrients.setdefault('能量', 0)
        nutrients.setdefault('蛋白质', 0)
        nutrients.setdefault('脂肪', 0)
        nutrients.setdefault('碳水化合物', 0)
        nutrients.setdefault('膳食纤维', 0)
        nutrients.setdefault('维生素', [])
        nutrients.setdefault('矿物质', [])
        nutrients.setdefault('自定义', [])

        food['methods'].append({
            'method_name': mn,
            'nutrients': nutrients
        })
        self.save()
        return True, f"烹饪方式「{mn}」已添加"

    def delete_method(self, food_name: str, method_name: str) -> Tuple[bool, str]:
        """删除食物的某个烹饪方式。「生」不可删除。"""
        if method_name == '生':
            return False, "「生」烹饪方式不可删除"

        food = self._find_food(food_name)
        if food is None:
            return False, f"食物「{food_name}」不存在"

        for i, method in enumerate(food.get('methods', [])):
            if method['method_name'] == method_name:
                del food['methods'][i]
                self.save()
                return True, f"烹饪方式「{method_name}」已删除"

        return False, f"烹饪方式「{method_name}」不存在"

    # ── 导出 ──────────────────────────────────────────────

    def export_to_file(self) -> Tuple[bool, str]:
        """导出食物库到文件，返回 (成功, 文件路径或错误信息)。"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'food_db_export_{timestamp}.json'
            filepath = os.path.join(self.exports_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self._foods, f, ensure_ascii=False, indent=2)

            return True, filepath
        except (IOError, OSError) as e:
            return False, str(e)
