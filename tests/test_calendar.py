"""历法层单测：四柱 / 节气月建 / 子时换日 / 旬空 / 交叉验证。

干支真值以 sxtwl + lunar-python 双实现交叉印证为准（见 reference/classics/SOURCES.md）。
"""
from liuyao.calendar import (
    GAN,
    ZHI,
    FourPillars,
    GanZhi,
    compute_four_pillars,
)


def _s(gz: GanZhi) -> str:
    return f"{GAN[gz.gan]}{ZHI[gz.zhi]}"


# ── 2.1 四柱基线 ─────────────────────────────────────────
def test_four_pillars_baseline():
    """2026-08-12 10:30 → 丙午 丙申 戊午 丁巳（sxtwl/lunar 已交叉确认）。"""
    fp = compute_four_pillars(2026, 8, 12, 10, 30)
    assert _s(fp.year) == "丙午"
    assert _s(fp.month) == "丙申"
    assert _s(fp.day) == "戊午"
    assert _s(fp.hour) == "丁巳"


# ── 2.2 月建按节气（非农历月）──────────────────────────────
def test_month_branch_follows_jieqi():
    """立秋（约 8/7）前后月支应由未→申。"""
    before = compute_four_pillars(2026, 8, 6, 12)   # 立秋前
    after = compute_four_pillars(2026, 8, 12, 12)   # 立秋后
    assert ZHI[before.month_branch] == "未"
    assert ZHI[after.month_branch] == "申"


# ── 2.3 子时换日（23:00 起算次日）────────────────────────────
def test_zi_hour_day_change():
    """同一公历日 22:30 与 23:30 跨越子时界：日柱应进位。"""
    before_zi = compute_four_pillars(2026, 8, 12, 22, 30)  # 亥时，仍属当日
    after_zi = compute_four_pillars(2026, 8, 12, 23, 30)   # 子时，算次日

    assert _s(before_zi.day) == "戊午"   # 当日
    assert _s(before_zi.hour) == "癸亥"  # 戊日亥时

    assert _s(after_zi.day) == "己未"    # 次日(08-13)日柱
    assert _s(after_zi.hour) == "甲子"   # 换日后己日子时


def test_midnight_not_day_change():
    """00:30 属当日子时，日柱不应是前一日。"""
    fp = compute_four_pillars(2026, 8, 12, 0, 30)
    assert _s(fp.day) == "戊午"
    assert _s(fp.hour) == "壬子"  # 戊日子时（00:30 仍是当日，五鼠遁戊→壬子）


# ── 2.4 旬空 ────────────────────────────────────────────
def test_xunkong():
    """戊午日属甲寅旬 → 空子丑。"""
    fp = compute_four_pillars(2026, 8, 12, 10, 30)  # 戊午日
    kong = {ZHI[fp.xunkong[0]], ZHI[fp.xunkong[1]]}
    assert kong == {"子", "丑"}


def test_xunkong_gengyin_rule():
    """规则验证：庚寅日(g=庚,z=寅)属甲申旬 → 空午未。"""
    from liuyao.calendar import _xunkong

    gengyin = GanZhi(gan=GAN.index("庚"), zhi=ZHI.index("寅"))
    kong = {ZHI[i] for i in _xunkong(gengyin)}
    assert kong == {"午", "未"}


# ── 2.5 与 lunar-python 交叉验证 ──────────────────────────
def test_cross_validate_with_lunar_python():
    """sxtwl 计算的日柱/月柱，应与独立实现 lunar-python 一致。"""
    from lunar_python import Solar

    samples = [
        (2026, 8, 12, 10),
        (2024, 2, 4, 14),    # 立春附近
        (2000, 1, 1, 9),
        (1987, 6, 15, 16),
        (2026, 12, 22, 11),  # 冬至附近
    ]
    for y, m, d, h in samples:
        fp = compute_four_pillars(y, m, d, h)
        lunar = Solar.fromYmdHms(y, m, d, h, 0, 0).getLunar()
        assert _s(fp.day) == lunar.getDayInGanZhi(), f"日柱不一致 @ {y}-{m}-{d}"
        assert _s(fp.month) == lunar.getMonthInGanZhiExact(), f"月柱不一致 @ {y}-{m}-{d}"
        assert _s(fp.year) == lunar.getYearInGanZhiExact(), f"年柱不一致 @ {y}-{m}-{d}"


def test_jieqi_precise_boundary():
    """交节精确时刻换月/换年：2024 立春约 2/4 16:27。

    14:00（立春前）→ 丑月·癸卯年；18:00（立春后）→ 寅月·甲辰年。
    这是日粒度历法库会算错、而时刻级才正确的关键边界。
    """
    before = compute_four_pillars(2024, 2, 4, 14)
    after = compute_four_pillars(2024, 2, 4, 18)
    assert ZHI[before.month_branch] == "丑"
    assert _s(before.year) == "癸卯"
    assert ZHI[after.month_branch] == "寅"
    assert _s(after.year) == "甲辰"
