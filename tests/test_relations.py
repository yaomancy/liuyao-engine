"""断法关系：反吟伏吟 / 六合动合 / 入墓化墓随鬼入墓 / 绝。

只锁查表事实，不断吉凶。用神五行的墓、绝按水土同宫（长生在申）。
"""
from typing import get_type_hints

from liuyao.calendar import ZHI
from liuyao.hexagram import cast_chart
from liuyao.relations import (
    GuaLayerRelations,
    LineRelation,
    YongRelations,
    gua_relations,
    line_relations,
    yong_relations,
)


def _flip(bits: str, movers: set[int]) -> str:
    return "".join(
        str(1 - int(ch)) if (i + 1) in movers else ch for i, ch in enumerate(bits)
    )


def _z(name: str) -> int:
    return ZHI.index(name)


# ── 卦层 / 逐爻：伏吟、反吟、六合、动合 ─────────────────────
def test_fuyin_inner_and_outer_when_qian_moves_to_zhen():
    """乾↔震纳甲全同：动二三与五上，内外卦皆伏吟，水火三合且含动。"""
    bits = "111111"
    movers = {2, 3, 5, 6}
    primary = cast_chart(bits, 0)
    bian = cast_chart(_flip(bits, movers), 0)
    assert bian.name == "震为雷"

    gua = gua_relations(primary, bian, movers)
    assert gua["伏吟"] == "内卦+外卦"
    assert gua["反吟"] == "无"
    assert gua["六合"] is False
    assert gua["三合"] == [
        {"五行": "水", "成局": "全", "含动": True},
        {"五行": "火", "成局": "全", "含动": True},
    ]
    assert set(gua) == set(get_type_hints(GuaLayerRelations))

    lines = line_relations(primary, bian, movers, _z("丑"), _z("子"))
    for pos in (2, 3, 5, 6):
        assert lines[pos] == {"伏吟": True}
        assert set(lines[pos]) <= set(get_type_hints(LineRelation))
    # 初爻子与日辰丑六合，初爻未动，故只有日合
    assert lines[1]["合"] == ["日合"]


def test_fanyin_inner_then_both_palaces():
    """巽宫地支与对宫相冲：天风姤动二三为内卦反吟；风地观内外齐动为内+外。"""
    bits = "011111"  # 天风姤
    movers = {2, 3}
    primary = cast_chart(bits, 0)
    bian = cast_chart(_flip(bits, movers), 0)
    assert gua_relations(primary, bian, movers)["反吟"] == "内卦"
    lines = line_relations(primary, bian, movers, _z("子"), _z("寅"))
    assert lines[2]["反吟"] is True and lines[3]["反吟"] is True
    assert "伏吟" not in lines[2]

    guan = "000011"  # 风地观
    both = {2, 3, 5, 6}
    g = gua_relations(cast_chart(guan, 0), cast_chart(_flip(guan, both), 0), both)
    assert g["反吟"] == "内卦+外卦"
    assert g["伏吟"] == "无"


def test_liuhe_gua_and_donghe_with_day_month():
    """天地否为六合卦；初未、四午相合。日辰月建皆午时，初爻日合且月合。"""
    bits = "000111"
    movers = {1, 4}
    primary = cast_chart(bits, 0)
    assert primary.name == "天地否"
    bian = cast_chart(_flip(bits, movers), 0)

    gua = gua_relations(primary, None, set())
    assert gua["六合"] is True and gua["反吟"] == "无" and gua["伏吟"] == "无"

    lines = line_relations(primary, bian, movers, _z("午"), _z("午"))
    assert lines[1] == {"动合": True, "合": ["日合", "月合"]}
    assert lines[4] == {"动合": True}


def test_static_qian_sanhe_without_moving():
    primary = cast_chart("111111", 0)
    gua = gua_relations(primary, None, set())
    assert gua["三合"] == [
        {"五行": "水", "成局": "全", "含动": False},
        {"五行": "火", "成局": "全", "含动": False},
    ]


# ── 用神：入墓 / 化墓 / 随鬼入墓 / 绝 ───────────────────────
def test_yong_relations_empty_without_position_or_wuxing():
    primary = cast_chart("111111", 0)
    assert yong_relations(primary, None, None, "木", set(), _z("未"), _z("申")) == {}
    assert yong_relations(primary, None, 2, "", set(), _z("未"), _z("申")) == {}
    assert yong_relations(primary, None, 2, "气", set(), _z("未"), _z("申")) == {}


def test_ri_mu_and_jue_on_day_and_month():
    """乾二爻妻财寅木：日辰未为日墓，月建申为绝。"""
    primary = cast_chart("111111", 0)
    rel = yong_relations(primary, None, 2, "木", set(), _z("未"), _z("申"))
    assert rel == {
        "入墓": {"type": "日"},
        "绝": True,
        "长生态": {"日": "墓", "月": "绝"},
    }
    assert set(rel) <= set(get_type_hints(YongRelations))


def test_jue_on_day_only_and_changsheng_sides():
    primary = cast_chart("111111", 0)
    # 日辰申是木之绝，不是墓
    assert yong_relations(primary, None, 2, "木", set(), _z("申"), _z("子")) == {
        "绝": True, "长生态": {"日": "绝"},
    }
    # 月建卯是木之帝旺；日辰子无要点
    assert yong_relations(primary, None, 2, "木", set(), _z("子"), _z("卯")) == {
        "长生态": {"月": "帝旺"},
    }
    assert yong_relations(primary, None, 2, "木", set(), _z("子"), _z("寅")) == {}


def test_dong_mu_suigui_and_plain_dong_mu():
    """泽火革上爻未土官鬼，是初爻卯木的墓库 → 动墓且随鬼入墓。"""
    ge = cast_chart("101110", 0)
    assert ge.name == "泽火革"
    assert ge.yaos[5].zhi == "未" and ge.yaos[5].liuqin == "官鬼"
    rel = yong_relations(ge, None, 1, "木", {6}, _z("子"), _z("寅"))
    assert rel == {"入墓": {"type": "动"}, "随鬼入墓": True}

    # 用神自己也动，但变出的地支不是墓库：只记动墓，不记化墓
    both = {1, 6}
    bian = cast_chart(_flip("101110", both), 0)
    assert bian.yaos[0].zhi != "未"
    rel = yong_relations(ge, bian, 1, "木", both, _z("子"), _z("寅"))
    assert rel == {"入墓": {"type": "动"}, "随鬼入墓": True}

    # 乾四爻午火，上爻戌土父母是火之墓，但六亲不是官鬼
    qian = cast_chart("111111", 0)
    rel = yong_relations(qian, None, 4, "火", {6}, _z("子"), _z("丑"))
    assert rel == {"入墓": {"type": "动"}}
    assert "随鬼入墓" not in rel


def test_ri_dong_combines_in_order():
    """日辰与动爻同为墓库时，type 按日→动拼接。"""
    ge = cast_chart("101110", 0)
    rel = yong_relations(ge, None, 1, "木", {6}, _z("未"), _z("子"))
    assert rel == {
        "入墓": {"type": "日动"},
        "随鬼入墓": True,
        "长生态": {"日": "墓"},
    }


def test_hua_mu_suigui_and_plain_hua_mu():
    """离为火上爻巳火动化戌：戌是火之墓，变爻官鬼 → 化墓且随鬼入墓。"""
    bits = "101101"
    movers = {6}
    primary = cast_chart(bits, 0)
    bian = cast_chart(_flip(bits, movers), 0)
    assert bian.name == "雷火丰"
    assert bian.yaos[5].zhi == "戌" and bian.yaos[5].liuqin == "官鬼"
    rel = yong_relations(primary, bian, 6, "火", movers, _z("子"), _z("丑"))
    assert rel == {"入墓": {"type": "化"}, "随鬼入墓": True}

    # 日辰也是墓库：日、化按顺序拼接
    rel = yong_relations(primary, bian, 6, "火", movers, _z("戌"), _z("子"))
    assert rel["入墓"] == {"type": "日化"}
    assert rel["随鬼入墓"] is True
    assert rel["长生态"] == {"日": "墓"}

    # 火地晋上爻动化戌，变爻是妻财，不是官鬼
    jin_bits = "000101"
    jin = cast_chart(jin_bits, 0)
    jin_bian = cast_chart(_flip(jin_bits, {6}), 0)
    assert jin_bian.yaos[5].zhi == "戌" and jin_bian.yaos[5].liuqin == "妻财"
    rel = yong_relations(jin, jin_bian, 6, "火", {6}, _z("子"), _z("丑"))
    assert rel == {"入墓": {"type": "化"}}


def test_dong_hua_without_suigui():
    """天风姤三爻酉金，动初爻丑土（金之墓）并自化丑，途径为动化，六亲非官鬼。"""
    bits = "011111"
    movers = {1, 3}
    primary = cast_chart(bits, 0)
    bian = cast_chart(_flip(bits, movers), 0)
    assert bian.name == "天泽履"
    assert primary.yaos[0].zhi == "丑" and bian.yaos[2].zhi == "丑"
    rel = yong_relations(primary, bian, 3, "金", movers, _z("子"), _z("午"))
    assert rel == {"入墓": {"type": "动化"}}


def test_moving_yong_that_does_not_transform_into_tomb():
    """乾二爻寅木动化丑，丑不是木之墓，动爻里也没有未 → 无入墓。"""
    bits = "111111"
    movers = {2}
    primary = cast_chart(bits, 0)
    bian = cast_chart(_flip(bits, movers), 0)
    assert bian.yaos[1].zhi == "丑"
    assert yong_relations(primary, bian, 2, "木", movers, _z("子"), _z("寅")) == {}
