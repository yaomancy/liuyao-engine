"""liuyao —— 确定性六爻装卦/断法引擎。

历法（干支四柱）→ 装卦（纳甲/六亲/世应/伏神）→ 旺衰骨架 → 结构化卦盘。
纯规则、零网络、可逐项回归验证；与 najia + yigram-najia-rules 交叉核验一致。

法度：装卦遵《卜筮正宗》、断法遵《增删卜易》，神煞不进核心，不混派。

常用入口：
    from liuyao import toss, compute_four_pillars, cast_chart, build_reading

    cast = toss()                                  # 摇一卦（六爻·CSPRNG）
    fp = compute_four_pillars(2026, 6, 29, 14, 30) # 起卦时刻 → 四柱干支
    chart = cast_chart(cast.bits, fp.day.gan)      # 装盘
    reading = build_reading(category="求财", text="...",
                            bits=cast.bits, moving=cast.moving,
                            four_pillars=fp)        # 完整结构化卦盘
"""
from __future__ import annotations

from .cast import CastResult, toss, toss_line, yao_from_coins, lines_from_tosses
from .calendar import (
    GanZhi,
    FourPillars,
    compute_four_pillars,
    four_pillars_from_ganzhi,
    ganzhi_from_str,
)
from .hexagram import Yao, HexagramChart, cast_chart, find_fushen, GUA64
from .reading import build_reading

__version__ = "0.1.0"

__all__ = [
    # 起卦
    "toss",
    "toss_line",
    "yao_from_coins",
    "lines_from_tosses",
    "CastResult",
    # 历法 / 四柱
    "compute_four_pillars",
    "four_pillars_from_ganzhi",
    "ganzhi_from_str",
    "FourPillars",
    "GanZhi",
    # 装卦
    "cast_chart",
    "find_fushen",
    "HexagramChart",
    "Yao",
    "GUA64",
    # 完整卦盘
    "build_reading",
    "__version__",
]
