"""诸爻持世诀数据与挂载映射单测（§1.4）。"""
from liuyao.chizhi import CHIZHI_JUE, CHIZHI_SOURCE, chizhi_for
from liuyao.gua_page import gua_page_facts
from liuyao.hexagram import GUA64, cast_chart

_SIX = {"父母", "子孙", "官鬼", "妻财", "兄弟"}


def test_exactly_five_verses_keyed_by_liuqin():
    assert set(CHIZHI_JUE) == _SIX
    assert len(CHIZHI_JUE) == 5
    assert "诸爻持世诀" in CHIZHI_SOURCE


def test_corrected_chars_present_no_errata():
    blob = "".join(CHIZHI_JUE.values())
    # 校改后的正字在
    assert "子孙持世事无忧" in CHIZHI_JUE["子孙"]
    assert "朱雀并临" in CHIZHI_JUE["兄弟"]
    assert "父母相生身有寿" in CHIZHI_JUE["兄弟"]
    # 底本讹字不得残留
    for bad in ("子身持世", "朱雀井临", "夬母"):
        assert bad not in blob


def test_chizhi_for_known_and_unknown():
    assert chizhi_for("父母").startswith("父母持世主身劳")
    assert chizhi_for("无此六亲") == ""   # 未知不杜撰


def test_every_hexagram_maps_to_a_verse_consistent_with_engine():
    for bits in GUA64:
        facts = gua_page_facts(bits)
        chart = cast_chart(bits, 0)
        # facts 暴露的世爻六亲与引擎一致
        assert facts["shi_liuqin"] == chart.yaos[chart.shi_pos - 1].liuqin
        # 该六亲必能挂到 5 段之一
        assert facts["shi_liuqin"] in _SIX
        assert chizhi_for(facts["shi_liuqin"]) in CHIZHI_JUE.values()


def test_qian_is_fumu_chizhi():
    f = gua_page_facts("111111")  # 乾为天
    assert f["shi_pos"] == 6 and f["shi_liuqin"] == "父母"
