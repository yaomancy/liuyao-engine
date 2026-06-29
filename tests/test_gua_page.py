"""卦页事实与 slug 映射单测（§1）。"""
from liuyao.guaxiang import GUAXIANG
from liuyao.gua_page import gua_page_facts
from liuyao.gua_slug import (
    GUA_SLUG,
    SLUG_BY_NAME,
    bits_to_slug,
    slug_to_bits,
)
from liuyao.hexagram import GUA64, cast_chart

_QIAN = "111111"  # 乾为天


# ── 1.3 slug 双向映射一致且唯一 ─────────────────────────────
def test_slug_covers_all_64_and_unique():
    assert len(GUA_SLUG) == 64
    assert set(GUA_SLUG) == set(GUA64)            # 覆盖全部 64 卦
    slugs = list(GUA_SLUG.values())
    assert len(set(slugs)) == 64                  # slug 全局唯一，无碰撞


def test_slug_roundtrip():
    for bits in GUA64:
        slug = bits_to_slug(bits)
        assert slug and slug_to_bits(slug) == bits  # bits→slug→bits 还原


def test_slug_name_alignment():
    # SLUG_BY_NAME 的键与 GUA64 的卦名集合一致
    assert set(SLUG_BY_NAME) == set(GUA64.values())


def test_unknown_slug_returns_none():
    assert slug_to_bits("not-a-real-gua") is None
    assert slug_to_bits("") is None
    assert bits_to_slug("999999") is None


def test_slug_is_url_safe():
    for slug in GUA_SLUG.values():
        assert slug == slug.lower()
        assert all(c.isalnum() or c == "-" for c in slug)


# ── 1.3 gua_page_facts 各字段与 cast_chart 逐一相符 ─────────
def test_facts_match_engine():
    bits = _QIAN
    facts = gua_page_facts(bits)
    chart = cast_chart(bits, 0)
    assert facts["name"] == chart.name == "乾为天"
    assert facts["palace"] == chart.palace
    assert facts["gua_type"] == chart.gua_type
    assert facts["shi_pos"] == chart.shi_pos
    assert facts["ying_pos"] == chart.ying_pos
    # 逐爻：阴阳/纳甲/六亲/世应与引擎一致
    for f, y in zip(facts["yaos"], chart.yaos):
        assert f["yin_yang"] == y.yin_yang
        assert f["najia"] == y.najia
        assert f["liuqin"] == y.liuqin
        assert f["shiying"] == y.shiying


def test_facts_all_64_buildable():
    for bits in GUA64:
        facts = gua_page_facts(bits)
        assert facts["slug"] == bits_to_slug(bits)
        assert len(facts["yaos"]) == 6


def test_facts_xiangyi_no_fabrication():
    # 有象意的卦如实取；缺象意时返回 ""，绝不编造
    for bits, name in GUA64.items():
        facts = gua_page_facts(bits)
        assert facts["xiangyi"] == GUAXIANG.get(name, "")


def test_facts_chart_basis_labeled():
    # 纳甲示例须带「排盘示例」语义标注，且不含六神字段
    facts = gua_page_facts(_QIAN)
    assert "排盘示例" in facts["chart_basis"]
    assert "liushen" not in facts["yaos"][0]


def test_unknown_bits_raises():
    import pytest
    with pytest.raises(KeyError):
        gua_page_facts("999999")
