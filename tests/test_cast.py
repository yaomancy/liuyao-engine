"""起卦/成卦测试：四象映射 / 成本卦 / 变卦 / CSPRNG 分布 / 交互熵 / 端到端。"""
from collections import Counter

from liuyao.calendar import FourPillars, GanZhi
from liuyao.cast import (
    CastResult,
    lines_from_tosses,
    toss,
    yao_from_coins,
)
from liuyao.reading import build_reading


# ── 8.1/8.2 四象映射（《卜筮正宗》单拆重交：一背单·两背拆·三背重·纯字交）──
def test_yao_from_coins():
    assert yao_from_coins((1, 1, 1)) == ("1", "老阳")  # 三背 重 老阳动
    assert yao_from_coins((1, 1, 0)) == ("0", None)    # 两背 拆 少阴(阴)
    assert yao_from_coins((1, 0, 0)) == ("1", None)    # 一背 单 少阳(阳)
    assert yao_from_coins((0, 0, 0)) == ("0", "老阴")  # 纯字 交 老阴动


# ── 8.2 三钱六掷成本卦（自下而上）──────────────────────────
def test_lines_from_tosses_qian():
    """六爻皆一背(单·少阳) → 乾为天，无动爻。"""
    bits, moving = lines_from_tosses(tuple([(1, 0, 0)] * 6))
    assert bits == "111111"
    assert moving == {}


def test_lines_from_tosses_order():
    """第一掷=初爻，第六掷=上爻（自下而上）。"""
    # 初爻老阴(纯字 0,0,0)，其余一背少阳
    tosses = ((0, 0, 0),) + tuple([(1, 0, 0)] * 5)
    bits, moving = lines_from_tosses(tosses)
    assert bits[0] == "0"          # 初爻为阴
    assert moving == {1: "老阴"}   # 初爻动


# ── 8.3 变卦 ────────────────────────────────────────────
def test_changed_bits_all_moving():
    """乾为天六爻皆老阳(动) → 变坤为地。"""
    r = CastResult(bits="111111",
                   moving={i: "老阳" for i in range(1, 7)},
                   tosses=tuple([(1, 1, 1)] * 6))
    assert r.changed_bits == "000000"


def test_no_moving_no_changed():
    r = CastResult(bits="111111", moving={}, tosses=tuple([(1, 0, 0)] * 6))
    assert r.changed_bits is None


# ── 8.1 CSPRNG 四象分布 ~ 1/8:3/8:3/8:1/8 ─────────────────
def test_csprng_distribution():
    n = 3000
    counts = Counter()
    for _ in range(n):
        for coins in toss().tosses:
            counts[sum(coins)] += 1
    total = n * 6
    # 3背=老阳1/8, 2背=少阴3/8, 1背=少阳3/8, 0背=老阴1/8（背数分布，与单拆重交映射无关）
    assert abs(counts[3] / total - 0.125) < 0.02
    assert abs(counts[2] / total - 0.375) < 0.02
    assert abs(counts[1] / total - 0.375) < 0.02
    assert abs(counts[0] / total - 0.125) < 0.02


# ── 8.4 交互熵：被接受、混入，但仍产出合法卦 ──────────────────
def test_entropy_accepted():
    r = toss(entropy=b"gyroscope-motion-and-charge-time-bytes")
    assert len(r.bits) == 6 and all(c in "01" for c in r.bits)
    assert all(1 <= p <= 6 for p in r.moving)


# ── 端到端：起卦 → 装卦 → 契约 ──────────────────────────────
def test_end_to_end_cast_to_reading():
    fp = FourPillars(year=GanZhi(2, 6), month=GanZhi(2, 8),
                     day=GanZhi(6, 2), hour=GanZhi(0, 0), xunkong=(6, 7))
    r = toss(entropy=b"seed")
    reading = build_reading(category="财运", text="测试", bits=r.bits,
                            moving=r.moving, four_pillars=fp)
    assert reading["primary"]["name"]  # 排出了卦名
    assert (reading["changed"] is None) == (not r.moving)  # 动则有变卦
