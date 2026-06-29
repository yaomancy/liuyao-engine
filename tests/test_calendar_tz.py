"""海外起卦时区差分回归（fix-overseas-casttime-tz）。

铁律：年/月柱交节是全球绝对事件——同一绝对瞬间，无论提交方在哪个时区，
得到的年/月柱 MUST 相同；日/时柱按当地墙钟，不随时区换算改变。
锚点：2026 立春 = 北京 2026-02-04 04:01:51（spike 实证，sxtwl 参照系=北京 UTC+8）。
"""
import datetime

from liuyao.calendar import GAN, ZHI, GanZhi, compute_four_pillars

BEIJING = 480      # 东八区偏移（本地=UTC+offset）
NY_WINTER = -300   # 纽约冬季 EST=UTC-5


def _s(gz: GanZhi) -> str:
    return f"{GAN[gz.gan]}{ZHI[gz.zhi]}"


# 立春 2026 北京时刻；同一绝对瞬间纽约钟表 = 北京 - 13h
_LICHUN_BJ = datetime.datetime(2026, 2, 4, 4, 1)
_LICHUN_NY = _LICHUN_BJ - datetime.timedelta(hours=13)


def _mb(dt, off):
    fp = compute_four_pillars(dt.year, dt.month, dt.day, dt.hour, dt.minute, off)
    return fp


# ── 同一绝对瞬间：北京 vs 海外，年/月柱必须一致 ──────────────
def test_same_instant_same_year_month_after_jieqi():
    """立春后 30min：北京与纽约(同一绝对瞬间)月建均为寅、年柱均为丙午。"""
    d = datetime.timedelta(minutes=30)
    bj = _mb(_LICHUN_BJ + d, BEIJING)
    ny = _mb(_LICHUN_NY + d, NY_WINTER)
    assert ZHI[bj.month_branch] == "寅" and ZHI[ny.month_branch] == "寅"
    assert _s(bj.year) == _s(ny.year) == "丙午"


def test_same_instant_same_year_month_before_jieqi():
    """立春前 30min：北京与纽约月建均为丑、年柱均为乙巳。"""
    d = datetime.timedelta(minutes=30)
    bj = _mb(_LICHUN_BJ - d, BEIJING)
    ny = _mb(_LICHUN_NY - d, NY_WINTER)
    assert ZHI[bj.month_branch] == "丑" and ZHI[ny.month_branch] == "丑"
    assert _s(bj.year) == _s(ny.year) == "乙巳"


def test_overseas_crosses_jieqi_like_beijing():
    """海外用户交节前后月建翻转，且与北京同步（修复前纽约会滞后错判）。"""
    d = datetime.timedelta(minutes=30)
    ny_before = _mb(_LICHUN_NY - d, NY_WINTER)
    ny_after = _mb(_LICHUN_NY + d, NY_WINTER)
    assert ZHI[ny_before.month_branch] == "丑"
    assert ZHI[ny_after.month_branch] == "寅"        # 关键：不再滞后为丑
    assert ny_before.month_branch != ny_after.month_branch


# ── 日/时柱按当地墙钟，不随时区改变 ──────────────────────────
def test_local_day_hour_invariant_to_tz():
    """当地 09:00 起卦：无论时区偏移，时支恒为巳、日柱恒为当地民用日。"""
    bj = compute_four_pillars(2026, 8, 12, 9, 0, BEIJING)
    ny = compute_four_pillars(2026, 8, 12, 9, 0, NY_WINTER)
    assert ZHI[bj.hour.zhi] == "巳" and ZHI[ny.hour.zhi] == "巳"
    assert _s(bj.day) == _s(ny.day)   # 日柱取当地民用日，不被时区换算改写


# ── 向后兼容：缺省 offset 等价显式 480、等价既往行为 ──────────
def test_default_offset_equivalent_to_beijing():
    """缺省 tz_offset 应等价显式 +480，且与既往(无参数)行为一致。"""
    samples = [(2026, 8, 12, 10, 30), (2024, 2, 4, 14, 0),
               (2024, 2, 4, 18, 0), (2026, 12, 22, 11, 0)]
    for y, m, d, h, mi in samples:
        default = compute_four_pillars(y, m, d, h, mi)
        explicit = compute_four_pillars(y, m, d, h, mi, 480)
        assert str(default) == str(explicit), f"缺省≠显式480 @ {y}-{m}-{d}"
