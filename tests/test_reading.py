"""组 4–6 测试：旺衰骨架 / 用神选取 / 卦象 JSON 契约组装。

旺衰按月令规则计算（修正了 06 契约示例中的占位错值）。
"""
from liuyao.analysis import (
    CATEGORY_TO_YONGSHEN,
    _huitou,
    _resolve_liang_xian,
    select_yongshen,
    wangshuai,
)
from liuyao.calendar import GAN, ZHI, FourPillars, GanZhi
from liuyao.hexagram import cast_chart
from liuyao.reading import build_reading


def _gz(s: str) -> GanZhi:
    return GanZhi(GAN.index(s[0]), ZHI.index(s[1]))


def _fp(month: str, day: str, kong: tuple[str, str]) -> FourPillars:
    """构造测试用四柱（年/时取占位，只用到月/日/旬空）。"""
    return FourPillars(
        year=_gz("丙午"), month=_gz(month), day=_gz(day), hour=_gz("甲子"),
        xunkong=(ZHI.index(kong[0]), ZHI.index(kong[1])),
    )


# ── 4.2 旺相休囚死（申月：金旺·水相·土休·火囚·木死）───────────
def test_wangshuai_in_shen_month():
    assert wangshuai("金", "金") == "旺"
    assert wangshuai("水", "金") == "相"
    assert wangshuai("土", "金") == "休"
    assert wangshuai("火", "金") == "囚"
    assert wangshuai("木", "金") == "死"


# ── 4.3 回头生克 ─────────────────────────────────────────
def test_huitou_kefan():
    """例2：辛酉(金) 动化 戊午(火)，火克金 → 回头克。"""
    assert _huitou("金", ZHI.index("酉"), "火", ZHI.index("午")) == "回头克"


def test_huitou_jinshen():
    """同五行递进 → 化进（寅化卯）。"""
    assert _huitou("木", ZHI.index("寅"), "木", ZHI.index("卯")) == "化进"
    assert _huitou("木", ZHI.index("卯"), "木", ZHI.index("寅")) == "化退"


# ── 5.1 用神类别映射 ─────────────────────────────────────
def test_category_mapping():
    assert CATEGORY_TO_YONGSHEN["财运"] == "妻财"
    assert CATEGORY_TO_YONGSHEN["事业"] == "官鬼"


# ── 5.2 两现优先级：动者优先 ──────────────────────────────
def test_liang_xian_prefers_moving():
    """天风姤 兄弟两现(三爻酉、五爻申)；三爻发动 → 取三爻。"""
    chart = cast_chart("011111", GAN.index("甲"))
    fp = _fp("丙子", "甲子", ("戌", "亥"))
    chosen = _resolve_liang_xian(
        chart, [3, 5], fp.month.zhi, fp.day.zhi, fp.xunkong, {3})
    assert chosen == 3


# ── 5.3 + 6：例1 乾为天 财运 完整组装 ──────────────────────
def test_build_reading_qian_caiyun():
    """申月庚寅日 问财运：用神妻财(寅,死,月破,得日)；原神子孙(相)；忌神兄弟(旺,日冲)。"""
    fp = _fp("丙申", "庚寅", ("午", "未"))
    r = build_reading(category="财运", text="近期投资", bits="111111",
                      moving={}, four_pillars=fp)

    assert r["palace"] == {"gua": "乾", "wuXing": "金", "type": "本宫"}
    assert r["yongShen"]["liuQin"] == "妻财"
    assert r["yongShen"]["chosen"] == 2
    assert r["yongShen"]["伏藏"] is False

    yong = r["assessment"]["用神"]
    assert yong["wangShuai"] == "死" and yong["月破"] is True and yong["得日"] is True
    assert r["assessment"]["原神"]["liuQin"] == "子孙"
    assert r["assessment"]["原神"]["wangShuai"] == "相"
    assert r["assessment"]["忌神"]["liuQin"] == "兄弟"
    assert r["assessment"]["忌神"]["wangShuai"] == "旺"
    assert r["assessment"]["忌神"]["日冲"] is True

    # 四爻壬午旬空、二爻甲寅月破
    line4 = r["primary"]["lines"][3]
    assert line4["flags"]["旬空"] is True
    assert r["primary"]["lines"][1]["flags"]["月破"] is True


# ── 仇神 + 暗动 ──────────────────
def test_choushen_in_assessment():
    """申月庚寅日 财运：用神妻财(木)→忌神兄弟(金)→仇神=生金者=父母(土)。"""
    fp = _fp("丙申", "庚寅", ("午", "未"))
    r = build_reading(category="财运", text="x", bits="111111",
                      moving={}, four_pillars=fp)
    assert r["assessment"]["仇神"]["liuQin"] == "父母"


def test_andong_jingyao_richong():
    """忌神兄弟申金 被日辰寅冲且为静爻 → 暗动；用神妻财不冲 → 非暗动。"""
    fp = _fp("丙申", "庚寅", ("午", "未"))
    r = build_reading(category="财运", text="x", bits="111111",
                      moving={}, four_pillars=fp)
    ji = r["assessment"]["忌神"]
    assert ji["日冲"] is True and ji["发动"] is False and ji["暗动"] is True
    assert r["assessment"]["用神"]["暗动"] is False


def test_andong_excludes_fadong():
    """规则：发动之爻不算暗动（andong = 日冲 且 非发动）。"""
    from liuyao.analysis import force_entry
    from liuyao.hexagram import cast_chart, GAN
    chart = cast_chart("111111", GAN.index("庚"))   # 乾为天
    # 五爻兄弟申，日辰寅(冲申)；令其发动 → 应为发动而非暗动
    e = force_entry(chart, 5, "兄弟", month_branch=8, day_zhi=2,
                    xunkong=(6, 7), moving={5}, bian_chart=None)
    assert e.richong is True and e.fadong is True and e.andong is False


# ── 5.3 + 6：例2 天风姤 三爻动 → 伏藏 + 变卦 ────────────────
def test_build_reading_gou_fushen_bian():
    """子月甲子日 问财运：天风姤缺妻财→伏藏(伏神甲寅)；三爻动→变天水讼。"""
    fp = _fp("丙子", "甲子", ("戌", "亥"))
    r = build_reading(category="财运", text="求财", bits="011111",
                      moving={3: "老阳"}, four_pillars=fp)

    assert r["yongShen"]["伏藏"] is True
    assert r["yongShen"]["positions"] == []
    assert r["changed"]["name"] == "天水讼"
    # 三爻动标记
    assert r["primary"]["lines"][2]["moving"] == "老阳"
    # 伏神挂在飞神二爻（辛亥）下
    line2 = r["primary"]["lines"][1]
    assert line2["伏神"] is not None and line2["伏神"]["najia"] == "甲寅"
