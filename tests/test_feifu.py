"""engine-feifu 校验：飞伏生克 + 伏神旺衰。

- 单测 feifu() 五种关系。
- 差分校验：以 najia(MIT) 的 hide(伏神) + 飞神为预言机，逐项比对本引擎的伏神纳甲与飞伏生克。
- 伏神旺衰：复用已被 najia 核验的 wangshuai()。
- 锚点：地山谦·财运 伏藏（丁卯木 / 伏来生飞），稳定回归。
"""
import pytest

from liuyao.analysis import feifu, wangshuai
from liuyao.calendar import four_pillars_from_ganzhi
from liuyao.hexagram import cast_chart
from liuyao.reading import build_reading

najia_mod = pytest.importorskip("najia.najia")
from najia.najia import Najia  # noqa: E402

_FP = four_pillars_from_ganzhi(year="丙午", month="丙申", day="庚寅", hour="辛巳")
# 月支 申=金，供伏神旺衰核验
_MONTH_WX = "金"


def test_feifu_five_relations():
    # feifu(fei_wx, fu_wx)：第一参为飞神、第二参为伏神
    assert feifu("金", "水") == "飞来生伏"   # 飞金 生 伏水
    assert feifu("金", "木") == "飞来克伏"   # 飞金 克 伏木
    assert feifu("火", "木") == "伏来生飞"   # 伏木 生 飞火
    assert feifu("土", "木") == "伏来克飞"   # 伏木 克 飞土
    assert feifu("金", "金") == "飞伏比和"


def _najia_hide(bits):
    """同一本卦喂 najia，取其 hide(伏神) 数据。bits 自下而上；params 初→上 少阳1/少阴2。"""
    params = [1 if c == "1" else 2 for c in bits]
    d = Najia(1).compile(params=params, date="2026-3-7 21:00:00").data
    return d


def test_feifu_differential_vs_najia():
    """遍历本卦：凡 财运(妻财)伏藏者，伏神纳甲与飞伏生克须与 najia 一致。"""
    checked = 0
    for n in range(64):
        bits = format(n, "06b")
        chart = cast_chart(bits, _FP.day.gan)
        if chart.liuqin_positions("妻财"):
            continue  # 妻财上卦，非伏藏
        rd = build_reading(category="财运", text="差分", bits=bits,
                           moving={}, four_pillars=_FP)
        fu_line = next((y for y in rd["primary"]["lines"] if y["伏神"]), None)
        if not fu_line:
            continue
        eng = fu_line["伏神"]            # {najia, liuQin, feiFu}

        d = _najia_hide(bits)
        hide = d.get("hide") or {}
        # najia hide 中妻财所在 seat（0-based 爻序，初→上）
        seats = [i for i, q in enumerate(hide.get("qin6", [])) if q == "妻财"]
        assert seats, (bits, "najia hide 无妻财")
        seat = seats[0]
        nj_fu = hide["qinx"][seat]        # 如 "丁卯木"
        nj_fu_gz, nj_fu_wx = nj_fu[:2], nj_fu[2]
        fei_wx = d["qinx"][seat][2]       # 本卦该位（飞神）五行
        expected = feifu(fei_wx, nj_fu_wx)

        assert eng["najia"] == nj_fu_gz, (bits, eng["najia"], nj_fu_gz)
        assert eng["feiFu"] == expected, (bits, eng["feiFu"], expected, fei_wx, nj_fu_wx)

        # 伏神旺衰 = wangshuai(伏神五行, 月令五行)，与 assessment 一致
        a = rd["assessment"]["用神"]
        assert a["wangShuai"] == wangshuai(nj_fu_wx, _MONTH_WX), (bits, a["wangShuai"])
        assert a["position"] is None and a["伏藏"] is True   # 用神不在可见卦面
        checked += 1
    assert checked >= 5, f"伏藏样本过少({checked})"


def test_anchor_dishan_qian_caiyun():
    """锚点：地山谦(001000)·财运 → 妻财伏藏，伏神丁卯(木)，飞神丙午(火)，木生火=伏来生飞。"""
    rd = build_reading(category="财运", text="锚点", bits="001000",
                       moving={}, four_pillars=_FP)
    fu = next(y["伏神"] for y in rd["primary"]["lines"] if y["伏神"])
    assert fu["liuQin"] == "妻财"
    assert fu["najia"] == "丁卯"
    assert fu["feiFu"] == "伏来生飞"
    a = rd["assessment"]["用神"]
    assert a["feiFu"] == "伏来生飞" and a["伏藏"] is True and a["伏神位"] == 2
