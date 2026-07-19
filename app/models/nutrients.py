"""
营养计算工具模块
- 营养成分模板
- 按克数折算营养
- 合并多条记录的营养总和
- 营养单位表
"""

import copy
from typing import Dict, List

# ── 营养成分固定单位表 ──────────────────────────────────

BASIC_NUTRIENTS = ['能量', '蛋白质', '脂肪', '碳水化合物', '膳食纤维']

BASIC_NUTRIENT_UNITS = {
    '能量': '大卡',
    '蛋白质': '克',
    '脂肪': '克',
    '碳水化合物': '克',
    '膳食纤维': '克',
}

VITAMIN_LIST = [
    {'name': '维生素A', 'unit': 'mcg'},
    {'name': '维生素B1', 'unit': 'mg'},
    {'name': '维生素B2', 'unit': 'mg'},
    {'name': '维生素B6', 'unit': 'mg'},
    {'name': '维生素B12', 'unit': 'mcg'},
    {'name': '维生素C', 'unit': 'mg'},
    {'name': '维生素D', 'unit': 'mcg'},
    {'name': '维生素E', 'unit': 'mg'},
    {'name': '维生素K', 'unit': 'mcg'},
]

MINERAL_LIST = [
    {'name': '钙', 'unit': 'mg'},
    {'name': '铁', 'unit': 'mg'},
    {'name': '锌', 'unit': 'mg'},
    {'name': '硒', 'unit': 'mcg'},
    {'name': '钠', 'unit': 'mg'},
    {'name': '钾', 'unit': 'mg'},
    {'name': '镁', 'unit': 'mg'},
    {'name': '磷', 'unit': 'mg'},
]

NUTRIENT_ORDER = BASIC_NUTRIENTS + [v['name'] for v in VITAMIN_LIST] + [m['name'] for m in MINERAL_LIST]


def make_empty_nutrients() -> Dict:
    """返回空营养成分模板（以 100g 为单位的默认值均为 0）。"""
    return {
        '能量': 0.0,
        '蛋白质': 0.0,
        '脂肪': 0.0,
        '碳水化合物': 0.0,
        '膳食纤维': 0.0,
        '维生素': [{'name': v['name'], 'value': 0.0, 'unit': v['unit']} for v in VITAMIN_LIST],
        '矿物质': [{'name': m['name'], 'value': 0.0, 'unit': m['unit']} for m in MINERAL_LIST],
        '自定义': [],
    }


# 别名，方便导入
NUTRIENT_TEMPLATE = make_empty_nutrients
EMPTY_NUTRIENTS = make_empty_nutrients


def make_vitamin_list() -> List[Dict]:
    """返回标准维生素列表（值均为 0）。"""
    return [{'name': v['name'], 'value': 0.0, 'unit': v['unit']} for v in VITAMIN_LIST]


def make_mineral_list() -> List[Dict]:
    """返回标准矿物质列表（值均为 0）。"""
    return [{'name': m['name'], 'value': 0.0, 'unit': m['unit']} for m in MINERAL_LIST]


# ── 营养计算函数 ────────────────────────────────────────

def scale_nutrients(nutrients: Dict, grams: float) -> Dict:
    """
    按克数折算一份营养成分。
    营养成分中存储的是每 100g 的数值，按 grams/100 比例折算。
    """
    if grams <= 0:
        return make_empty_nutrients()

    factor = grams / 100.0
    result = copy.deepcopy(nutrients)

    # 基础营养
    for key in BASIC_NUTRIENTS:
        if key in result:
            result[key] = round(result[key] * factor, 2)

    # 维生素
    if '维生素' in result:
        for vit in result['维生素']:
            vit['value'] = round(vit.get('value', 0) * factor, 2)

    # 矿物质
    if '矿物质' in result:
        for mineral in result['矿物质']:
            mineral['value'] = round(mineral.get('value', 0) * factor, 2)

    # 自定义
    if '自定义' in result:
        for custom in result['自定义']:
            custom['value'] = round(custom.get('value', 0) * factor, 2)

    return result


def calculate_entry_nutrients(food_nutrients: Dict, grams: float) -> Dict:
    """
    根据食物营养（每 100g）和克数，计算该份的实际营养。
    等同于 scale_nutrients，命名更语义化。
    """
    return scale_nutrients(food_nutrients, grams)


def sum_nutrient_dicts(nut_list: List[Dict]) -> Dict:
    """合并多个营养成分字典（加法）。"""
    result = make_empty_nutrients()

    for nutrients in nut_list:
        if nutrients is None:
            continue
        # 基础
        for key in BASIC_NUTRIENTS:
            result[key] = round(result.get(key, 0) + nutrients.get(key, 0), 2)

        # 维生素
        for vit in nutrients.get('维生素', []):
            existing = _find_by_name(result['维生素'], vit.get('name', ''))
            if existing:
                existing['value'] = round(existing.get('value', 0) + vit.get('value', 0), 2)

        # 矿物质
        for mineral in nutrients.get('矿物质', []):
            existing = _find_by_name(result['矿物质'], mineral.get('name', ''))
            if existing:
                existing['value'] = round(existing.get('value', 0) + mineral.get('value', 0), 2)

        # 自定义
        for custom in nutrients.get('自定义', []):
            existing = _find_by_name(result['自定义'], custom.get('name', ''))
            if existing:
                existing['value'] = round(existing.get('value', 0) + custom.get('value', 0), 2)
            else:
                result['自定义'].append(copy.deepcopy(custom))

    return result


def merge_nutrients(records_nutrients: List[Dict]) -> Dict:
    """
    合并多条记录的营养总和（别名，与 sum_nutrient_dicts 相同）。
    records_nutrients: 每条记录的营养字典列表。
    """
    return sum_nutrient_dicts(records_nutrients)


def _find_by_name(items: List[Dict], name: str) -> Dict:
    """在列表中按 name 字段查找。"""
    for item in items:
        if item.get('name') == name:
            return item
    return None


def get_nutrient_value(nutrients: Dict, category: str, name: str = None) -> float:
    """
    从营养成分中提取数值。
    category: 'basic' | 'vitamin' | 'mineral' | 'custom'
    """
    if category == 'basic':
        return nutrients.get(name, 0)
    elif category in ('vitamin', '维生素'):
        item = _find_by_name(nutrients.get('维生素', []), name)
        return item.get('value', 0) if item else 0
    elif category in ('mineral', '矿物质'):
        item = _find_by_name(nutrients.get('矿物质', []), name)
        return item.get('value', 0) if item else 0
    elif category == 'custom':
        item = _find_by_name(nutrients.get('自定义', []), name)
        return item.get('value', 0) if item else 0
    return 0


def nutrients_to_display_dict(nutrients: Dict) -> Dict[str, str]:
    """
    将营养成分转为可显示的字典型（带单位）。
    返回 { "能量": "500 大卡", "蛋白质": "30.5 克", ... }
    """
    display = {}

    for key in BASIC_NUTRIENTS:
        v = nutrients.get(key, 0)
        unit = BASIC_NUTRIENT_UNITS.get(key, '')
        display[key] = f"{v} {unit}" if unit else str(v)

    for vit in nutrients.get('维生素', []):
        display[vit['name']] = f"{vit.get('value', 0)} {vit.get('unit', '')}"

    for mineral in nutrients.get('矿物质', []):
        display[mineral['name']] = f"{mineral.get('value', 0)} {mineral.get('unit', '')}"

    for custom in nutrients.get('自定义', []):
        display[custom['name']] = f"{custom.get('value', 0)} {custom.get('unit', '')}"

    return display


def get_basic_summary(nutrients: Dict) -> str:
    """返回基础营养的简短摘要字符串。"""
    parts = []
    for key in BASIC_NUTRIENTS:
        v = nutrients.get(key, 0)
        if v > 0:
            unit = BASIC_NUTRIENT_UNITS.get(key, '')
            parts.append(f"{key}: {v}{unit}")
    return ', '.join(parts) if parts else '无数据'
