"""
摄入记录管理模块
- 加载/保存 records_db.json
- 增删改查摄入记录
- 按日期过滤、每日汇总
"""

import json
import os
import copy
import uuid
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple

from models.nutrients import (
    scale_nutrients, sum_nutrient_dicts, make_empty_nutrients,
    BASIC_NUTRIENTS, BASIC_NUTRIENT_UNITS
)


def _short_uuid() -> str:
    """生成8位短UUID。"""
    return uuid.uuid4().hex[:8]


def _now_str() -> str:
    """返回当前时间戳字符串 yyyy-MM-dd HH:mm:ss。"""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def _parse_date(ts: str) -> str:
    """从时间戳中提取日期 yyyy-MM-dd。"""
    if not ts or len(ts) < 10:
        return ''
    return ts[:10]


class RecordManager:
    """摄入记录管理器"""

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

        self.data_dir = data_dir
        self.db_path = os.path.join(data_dir, 'records_db.json')
        self._records: List[Dict] = []
        self.load()

    # ── 持久化 ────────────────────────────────────────────

    def load(self) -> bool:
        """从文件加载记录。"""
        try:
            if os.path.exists(self.db_path):
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, list):
                    self._records = data
                    return True
            self._records = []
            return False
        except (json.JSONDecodeError, IOError, OSError):
            self._records = []
            return False

    def save(self) -> bool:
        """保存记录到文件。"""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self._records, f, ensure_ascii=False, indent=2)
            return True
        except (IOError, OSError):
            return False

    # ── 查询 ──────────────────────────────────────────────

    @property
    def records(self) -> List[Dict]:
        return copy.deepcopy(self._records)

    def get_records_by_date(self, target_date: str) -> List[Dict]:
        """获取指定日期的所有记录（时间正序）。"""
        result = []
        for r in self._records:
            if _parse_date(r.get('timestamp', '')) == target_date:
                result.append(copy.deepcopy(r))
        # 按时间正序
        result.sort(key=lambda x: x.get('timestamp', ''))
        return result

    def get_records_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """获取日期范围内的记录。"""
        result = []
        for r in self._records:
            d = _parse_date(r.get('timestamp', ''))
            if start_date <= d <= end_date:
                result.append(copy.deepcopy(r))
        result.sort(key=lambda x: x.get('timestamp', ''))
        return result

    def get_record_by_id(self, record_id: str) -> Optional[Dict]:
        """按 record_id 查找。"""
        for r in self._records:
            if r.get('record_id') == record_id:
                return copy.deepcopy(r)
        return None

    def get_all_dates(self) -> List[str]:
        """返回有记录的所有日期列表（倒序）。"""
        dates = set()
        for r in self._records:
            d = _parse_date(r.get('timestamp', ''))
            if d:
                dates.add(d)
        return sorted(list(dates), reverse=True)

    def get_date_counts(self) -> Dict[str, int]:
        """返回每个日期的记录数。"""
        counts = {}
        for r in self._records:
            d = _parse_date(r.get('timestamp', ''))
            if d:
                counts[d] = counts.get(d, 0) + 1
        return counts

    # ── 每日汇总 ──────────────────────────────────────────

    def get_daily_summary(self, target_date: str) -> Dict:
        """
        获取指定日期的每日汇总。
        返回:
        {
            'date': 'yyyy-MM-dd',
            'records': [...],           # 该日所有记录
            'total_nutrients': {...},   # 合并后的营养总和
            'has_data': True/False
        }
        """
        records = self.get_records_by_date(target_date)
        if not records:
            return {
                'date': target_date,
                'records': [],
                'total_nutrients': make_empty_nutrients(),
                'has_data': False,
            }

        # 合并所有记录的 entries 营养
        all_entry_nutrients = []
        for rec in records:
            for entry in rec.get('entries', []):
                n = entry.get('nutrients', None)
                if n:
                    all_entry_nutrients.append(n)

        total = sum_nutrient_dicts(all_entry_nutrients)
        return {
            'date': target_date,
            'records': records,
            'total_nutrients': total,
            'has_data': True,
        }

    def get_range_summaries(self, start_date: str, end_date: str) -> List[Dict]:
        """
        获取日期范围内每日的汇总列表。
        按日期倒序。
        """
        dates_in_range = set()
        current = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()

        while current <= end:
            dates_in_range.add(current.strftime('%Y-%m-%d'))
            current += timedelta(days=1)

        summaries = []
        for d in sorted(dates_in_range, reverse=True):
            summary = self.get_daily_summary(d)
            summaries.append(summary)

        return summaries

    # ── 增 ────────────────────────────────────────────────

    def add_record(self, entries: List[Dict], note: str = '') -> Tuple[bool, str, Optional[str]]:
        """
        添加一条摄入记录。
        entries: [{'food_name': ..., 'method_name': ..., 'grams': ..., 'nutrients': ...}, ...]
        返回 (成功, 消息, record_id)
        """
        if not entries:
            return False, "没有摄入条目", None

        record = {
            'record_id': _short_uuid(),
            'timestamp': _now_str(),
            'entries': copy.deepcopy(entries),
            'note': note.strip() if note else '',
        }

        self._records.append(record)
        self.save()
        return True, "已提交到今日", record['record_id']

    # ── 删 ────────────────────────────────────────────────

    def delete_record(self, record_id: str) -> Tuple[bool, str]:
        """删除指定记录。"""
        for i, r in enumerate(self._records):
            if r.get('record_id') == record_id:
                del self._records[i]
                self.save()
                return True, "记录已删除"
        return False, "记录不存在"

    # ── 改 ────────────────────────────────────────────────

    def update_record_entries(self, record_id: str, entries: List[Dict], note: str = None) -> Tuple[bool, str]:
        """更新记录的条目和备注。"""
        for r in self._records:
            if r.get('record_id') == record_id:
                if not entries:
                    return False, "记录至少需要一个条目"
                r['entries'] = copy.deepcopy(entries)
                if note is not None:
                    r['note'] = note.strip()
                self.save()
                return True, "记录已更新"
        return False, "记录不存在"

    # ── 今日辅助 ──────────────────────────────────────────

    def get_today_records(self) -> List[Dict]:
        """获取今日的所有记录（时间倒序）。"""
        today = date.today().strftime('%Y-%m-%d')
        records = self.get_records_by_date(today)
        records.reverse()  # 倒序
        return records

    def get_today_summary(self) -> Dict:
        """获取今日汇总。"""
        today = date.today().strftime('%Y-%m-%d')
        return self.get_daily_summary(today)
