"""
图表生成模块
使用 matplotlib 生成图表，返回 Kivy Image widget
当 matplotlib 不可用时（如 Android APK 不含 matplotlib），
所有方法返回 None 且不崩溃。
"""

import io
import os
from collections import defaultdict
from typing import List, Dict, Optional

from kivy.uix.image import Image as KivyImage
from kivy.core.image import Image as CoreImage

# ── 尝试导入 matplotlib（可能不存在） ──────────────────

_MATPLOTLIB_AVAILABLE = False
plt = None
np_module = None

try:
    os.environ['MPLBACKEND'] = 'AGG'
    import matplotlib
    matplotlib.use('AGG')
    import matplotlib.pyplot as _plt
    from matplotlib import font_manager as _fm
    import numpy as _np
    plt = _plt
    np_module = _np
    _MATPLOTLIB_AVAILABLE = True

    # 中文字体配置
    _CANDIDATE_FONTS = [
        '/system/fonts/DroidSansFallback.ttf',
        '/system/fonts/NotoSansCJK-Regular.ttc',
        '/system/fonts/NotoSansSC-Regular.otf',
        'C:/Windows/Fonts/simhei.ttf',
        'C:/Windows/Fonts/msyh.ttc',
        '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
    ]
    _CHINESE_FONT = None
    for fp in _CANDIDATE_FONTS:
        if os.path.exists(fp):
            _CHINESE_FONT = fp
            break
    if _CHINESE_FONT:
        matplotlib.rcParams['font.family'] = 'sans-serif'
        _fm.fontManager.addfont(_CHINESE_FONT)
        matplotlib.rcParams['font.sans-serif'] = [os.path.basename(_CHINESE_FONT).rsplit('.', 1)[0]]
    else:
        matplotlib.rcParams['font.family'] = 'sans-serif'
    matplotlib.rcParams['axes.unicode_minus'] = False
except ImportError:
    pass

# ── 颜色方案 ─────────────────────────────────────────────

PRIMARY_COLOR = '#4CAF50'
SECONDARY_COLOR = '#81C784'
PIE_COLORS = ['#4CAF50', '#81C784', '#A5D6A7', '#C8E6C9', '#388E3C',
              '#2E7D32', '#66BB6A', '#43A047', '#1B5E20', '#E8F5E9']


class ChartGenerator:
    """图表生成器。matplotlib 不可用时所有方法返回 None。"""

    def __init__(self, width: int = 320, height: int = 240, dpi: int = 80):
        self.width = width
        self.height = height
        self.dpi = dpi

    def create_line_chart(self, daily_summaries: List[Dict], nutrient_name: str,
                          title: str = '') -> Optional[KivyImage]:
        """创建折线图。matplotlib 不可用时返回 None。"""
        if not _MATPLOTLIB_AVAILABLE:
            return None

        dates = []
        values = []
        for summary in reversed(daily_summaries):
            if summary['has_data']:
                dates.append(summary['date'][-5:])
                values.append(summary['total_nutrients'].get(nutrient_name, 0))
            else:
                dates.append(summary['date'][-5:])
                values.append(0)
        if not dates:
            return None

        fig, ax = plt.subplots(figsize=(self.width / self.dpi, self.height / self.dpi), dpi=self.dpi)
        ax.plot(dates, values, marker='o', color=PRIMARY_COLOR, linewidth=2, markersize=4)
        ax.fill_between(range(len(values)), values, alpha=0.2, color=SECONDARY_COLOR)
        ax.set_title(title, fontsize=11, color='#333333')
        ax.set_xlabel('日期', fontsize=9)
        ax.set_ylabel(nutrient_name, fontsize=9)
        ax.grid(True, linestyle='--', alpha=0.5)
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right', fontsize=8)
        fig.tight_layout()
        return self._fig_to_kivy_image(fig)

    def create_pie_chart(self, daily_summaries: List[Dict], nutrient_name: str,
                         title: str = '') -> Optional[KivyImage]:
        """创建扇形图。matplotlib 不可用时返回 None。"""
        if not _MATPLOTLIB_AVAILABLE:
            return None

        food_totals = defaultdict(float)
        for summary in daily_summaries:
            if not summary['has_data']:
                continue
            for rec in summary['records']:
                for entry in rec.get('entries', []):
                    fn = entry.get('food_name', '未知')
                    val = entry.get('nutrients', {}).get(nutrient_name, 0)
                    food_totals[fn] += val

        food_totals = {k: round(v, 1) for k, v in food_totals.items() if v > 0}
        if not food_totals:
            return None

        labels = list(food_totals.keys())
        sizes = list(food_totals.values())
        fig, ax = plt.subplots(figsize=(self.width / self.dpi, self.height / self.dpi), dpi=self.dpi)
        colors = PIE_COLORS[:len(labels)]
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors, textprops={'fontsize': 8})
        ax.set_title(title, fontsize=11, color='#333333')
        fig.tight_layout()
        return self._fig_to_kivy_image(fig)

    def _fig_to_kivy_image(self, fig) -> Optional[KivyImage]:
        """将 matplotlib Figure 转为 Kivy Image widget。"""
        try:
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=self.dpi, bbox_inches='tight')
            buf.seek(0)
            plt.close(fig)
            data = buf.read()
            buf.close()
            core_img = CoreImage(io.BytesIO(data), ext='png')
            img = KivyImage(texture=core_img.texture)
            img.size_hint_x = 1
            img.size_hint_y = None
            img.height = self.height
            return img
        except Exception as e:
            print(f"Chart generation error: {e}")
            try:
                plt.close(fig)
            except Exception:
                pass
            return None
