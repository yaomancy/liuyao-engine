"""卦象象意测试：64 卦全覆盖、体例合规、入卦象事实、不下绝对吉凶。"""
from liuyao.guaxiang import GUAXIANG, get_xiangyi
from liuyao.hexagram import GUA64


def test_covers_all_64():
    """象意键集 == 64 卦名集，无缺无多。"""
    assert set(GUAXIANG.keys()) == set(GUA64.values())


def test_lengths_reasonable():
    for name, xy in GUAXIANG.items():
        assert 8 <= len(xy) <= 30, f"{name} 象意长度异常: {xy}"


def test_no_absolute_or_fatalistic_wording():
    """与'不下绝对吉凶'一致：象意不含绝对化/宿命/恐吓词。"""
    bad = ("必然", "一定会", "绝对", "注定", "必死", "必败", "无法改变")
    for name, xy in GUAXIANG.items():
        hit = [b for b in bad if b in xy]
        assert not hit, f"{name} 含绝对化措辞 {hit}: {xy}"


def test_get_xiangyi_unknown_returns_empty():
    assert get_xiangyi("乾为天")
    assert get_xiangyi("不存在卦") == ""


def test_reading_includes_xiangyi():
    """卦象事实(reading)中含本卦象意。"""
    from liuyao.calendar import FourPillars, GanZhi
    from liuyao.reading import build_reading

    fp = FourPillars(year=GanZhi(2, 6), month=GanZhi(2, 8),
                     day=GanZhi(6, 2), hour=GanZhi(0, 0), xunkong=(6, 7))
    r = build_reading(category="财运", text="x", bits="111111",
                      moving={}, four_pillars=fp)
    assert r["primary"]["象意"] == GUAXIANG["乾为天"]
