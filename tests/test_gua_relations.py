"""卦际关系确定性派生单测（§1.2）。"""
from liuyao.gua_page import gua_relations
from liuyao.gua_slug import bits_to_slug
from liuyao.hexagram import GUA64

_SELF_ZONG = {"乾为天", "坤为地", "坎为水", "离为火", "山雷颐", "泽风大过", "风泽中孚", "雷山小过"}


def test_cuo_is_full_flip_and_never_self():
    for bits in GUA64:
        r = gua_relations(bits)
        cuo = r["错"]["bits"]
        assert cuo == "".join("1" if c == "0" else "0" for c in bits)
        assert cuo != bits                       # 错卦无自反
        assert r["错"]["name"] == GUA64[cuo]


def test_zong_reverse_and_exactly_8_self():
    self_cnt = 0
    for bits in GUA64:
        r = gua_relations(bits)
        if r["综"] is None:
            assert bits[::-1] == bits            # 仅自反时为 None
            self_cnt += 1
        else:
            assert r["综"]["bits"] == bits[::-1]
    assert self_cnt == 8
    assert {GUA64[b] for b in GUA64 if b[::-1] == b} == _SELF_ZONG


def test_jiao_swap_and_exactly_8_self():
    self_cnt = 0
    for bits in GUA64:
        r = gua_relations(bits)
        if r["交"] is None:
            assert bits[3:] + bits[:3] == bits
            self_cnt += 1
        else:
            assert r["交"]["bits"] == bits[3:] + bits[:3]
    assert self_cnt == 8                          # 八纯卦


def test_neighbors_six_distinct_with_yao_pos():
    for bits in GUA64:
        lin = gua_relations(bits)["邻"]
        assert len(lin) == 6
        assert [n["pos"] for n in lin] == [1, 2, 3, 4, 5, 6]
        for n in lin:
            assert n["bits"] != bits              # 一爻动必变
            assert sum(a != b for a, b in zip(n["bits"], bits)) == 1  # 恰差一爻


def test_all_derived_in_gua64_and_have_slug():
    for bits in GUA64:
        r = gua_relations(bits)
        derived = [r["错"]] + [r["综"], r["交"]] + r["邻"]
        for d in derived:
            if d is None:
                continue
            assert d["bits"] in GUA64
            assert bits_to_slug(d["bits"]) == d["slug"] and d["slug"]


def test_symmetric_relations_are_mutual():
    # 错/综/交/邻 数学对称 → A 的该关系是 B，则 B 的同类关系含 A
    for bits in GUA64:
        r = gua_relations(bits)
        assert gua_relations(r["错"]["bits"])["错"]["bits"] == bits
        if r["综"]:
            assert gua_relations(r["综"]["bits"])["综"]["bits"] == bits
        if r["交"]:
            assert gua_relations(r["交"]["bits"])["交"]["bits"] == bits
        for n in r["邻"]:
            back = {x["bits"] for x in gua_relations(n["bits"])["邻"]}
            assert bits in back


def test_known_example_shui_lei_zhun():
    r = gua_relations("100010")  # 水雷屯
    assert r["错"]["name"] == "火风鼎"
    assert r["综"]["name"] == "山水蒙"
    assert r["交"]["name"] == "雷水解"


def test_unknown_bits_raises():
    import pytest
    with pytest.raises(KeyError):
        gua_relations("999999")
