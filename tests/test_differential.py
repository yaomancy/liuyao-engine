"""差分校验（Tasks 7.3/7.4）：随机抽样大量卦，本引擎 vs najia(独立 MIT 实现) 逐项比对。

隔离历法：用 najia 算出的日干喂本引擎（六神对齐），故此处纯比对**装卦逻辑**
（卦名/卦宫/纳甲/六亲/六神/世应）。历法(date→干支)另由 test_calendar 对 lunar-python 验证。

najia 编码：每爻 1少阳/2少阴/3老阳/4老阴（初→上）；mark=p%2，动爻=p>2。
"""
import random

import pytest

from liuyao.hexagram import GAN, cast_chart

najia_mod = pytest.importorskip("najia.najia")
from najia.najia import Najia  # noqa: E402
from najia.utils import get_najia  # noqa: E402

_DATES = [
    "2026-08-12 10:00:00", "2024-02-04 18:00:00", "2000-01-01 09:00:00",
    "1987-06-15 16:00:00", "2026-12-22 11:00:00", "2025-03-21 08:00:00",
]


def _najia_chart(params, date):
    return Najia(0).compile(params=params, date=date).data


def test_differential_vs_najia():
    """200 个随机卦 × 随机日期，逐项与 najia 一致。"""
    rng = random.Random(20260616)  # 固定种子，可复现
    mismatches = []

    for _ in range(200):
        params = [rng.choice([1, 2, 3, 4]) for _ in range(6)]
        date = rng.choice(_DATES)
        d = _najia_chart(params, date)
        bits = d["mark"]

        # 用 najia 的日干喂本引擎 → 隔离历法，纯比装卦
        day_gan = GAN.index(d["lunar"]["gz"]["day"][0])
        chart = cast_chart(bits, day_gan)

        checks = {
            "卦名": (chart.name, d["name"]),
            "卦宫": (chart.palace, d["gong"]),
            "纳甲": ([y.najia for y in chart.yaos], list(get_najia(bits))),
            "六亲": ([y.liuqin for y in chart.yaos], list(d["qin6"])),
            "六神": ([y.liushen for y in chart.yaos], list(d["god6"])),
            "世": (chart.shi_pos, d["shiy"][0]),
            "应": (chart.ying_pos, d["shiy"][1]),
        }
        for field, (mine, theirs) in checks.items():
            if mine != theirs:
                mismatches.append(f"{bits} {field}: 本={mine} najia={theirs}")

    assert not mismatches, "差分不一致：\n" + "\n".join(mismatches[:20])
