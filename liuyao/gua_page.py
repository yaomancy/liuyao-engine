"""卦页事实组装（卦库长青页的「硬事实」来源）。

宪法：卦页一切卦理硬事实只取自确定性引擎与经典查表，绝不由 AI 自算/杜撰。
本模块把 `cast_chart` + `_PALACE_TABLE` + `GUAXIANG` 的结果汇成卦页所需结构。

day-干说明：纳甲(gan/zhi)、五行、六亲、世应均为卦象固有，不随日变；唯六神依日干而变，
故卦页**从略六神**，只用固定示例日干（甲）跑一次排盘以取固有字段，并以 `chart_basis`
标注「排盘示例」语义，避免被误读为给访客起卦。
"""
from __future__ import annotations

from .guaxiang import get_xiangyi
from .hexagram import (
    GUA64,
    PALACE_WUXING,
    TRIGRAM_NAME,
    _PALACE_TABLE,
    cast_chart,
)
from .gua_slug import bits_to_slug

# 八宫陈列次序（与 guaxiang.py 分组一致）与卦型次序（京房八宫卦序）
_PALACE_ORDER = ["乾", "坎", "艮", "震", "巽", "离", "坤", "兑"]
_TYPE_ORDER = {"本宫": 0, "一世": 1, "二世": 2, "三世": 3,
               "四世": 4, "五世": 5, "游魂": 6, "归魂": 7}

# 固定示例日干（甲=0）：仅用于跑排盘取卦象固有字段；六神不上卦页。
_EXAMPLE_DAY_GAN = 0
_CHART_BASIS = "排盘示例：纳甲/六亲/世应为卦象固有（不随日变），六神依日干而变故本页从略"


def gua_page_facts(bits: str) -> dict:
    """组装一卦的卦页事实。未知 bits 抛 KeyError（由调用方转 404）。"""
    if bits not in GUA64:
        raise KeyError(bits)
    chart = cast_chart(bits, _EXAMPLE_DAY_GAN)
    yaos = [
        {
            "position": y.position,           # 1-6 初→上
            "yin_yang": y.yin_yang,           # 阳/阴
            "najia": y.najia,                 # 干支（卦象固有）
            "wuxing": y.wuxing,               # 爻五行
            "liuqin": y.liuqin,               # 六亲（以宫五行为我）
            "shiying": y.shiying,             # 世/应/None
        }
        for y in chart.yaos
    ]
    return {
        "bits": bits,
        "slug": bits_to_slug(bits),
        "name": chart.name,
        "palace": chart.palace,
        "palace_wuxing": chart.palace_wuxing,
        "gua_type": chart.gua_type,
        "shi_pos": chart.shi_pos,
        "shi_liuqin": chart.yaos[chart.shi_pos - 1].liuqin,  # 世爻六亲（持世诀挂载用）
        "ying_pos": chart.ying_pos,
        "lower_trigram": TRIGRAM_NAME[bits[:3]],
        "upper_trigram": TRIGRAM_NAME[bits[3:]],
        "yaos": yaos,                          # 初→上
        "xiangyi": get_xiangyi(chart.name),    # 缺则 ""（不杜撰）
        "chart_basis": _CHART_BASIS,           # 「排盘示例」语义标注
    }


def gua_index_items() -> list[tuple[str, str, list[dict]]]:
    """卦库索引数据：按八宫分组，每组 (宫名, 宫五行, [{name, slug, gua_type}])。

    组内按京房八宫卦序（本宫→一世…→归魂）排列。纯查表，不算卦理。
    """
    groups: dict[str, list[dict]] = {p: [] for p in _PALACE_ORDER}
    for bits, name in GUA64.items():
        palace, gua_type, _ = _PALACE_TABLE[bits]
        groups[palace].append(
            {"name": name, "slug": bits_to_slug(bits), "gua_type": gua_type, "bits": bits}
        )
    for p in groups:
        groups[p].sort(key=lambda d: _TYPE_ORDER[d["gua_type"]])
    return [(p, PALACE_WUXING[p], groups[p]) for p in _PALACE_ORDER]


def _resolve(bits: str) -> dict:
    return {"bits": bits, "name": GUA64[bits], "slug": bits_to_slug(bits)}


def gua_relations(bits: str) -> dict:
    """卦际关系（纯位运算派生的硬事实，不算卦理、不触碰 GUA64/排盘）：
      错卦＝六爻全反；综卦＝整卦倒置 bits[::-1]；交卦＝上下经卦互换 bits[3:]+bits[:3]；
      一爻动邻卦＝逐位翻 1 位得 6 个之卦。
    综/交存在自反卦（各 8）：自反时返回 None（调用方据此显「自覆/自身」说明而非自链）。
    返回值的 错/综/交 为 {bits,name,slug}|None，邻为 [{pos,bits,name,slug}]×6。
    未知 bits 抛 KeyError。"""
    if bits not in GUA64:
        raise KeyError(bits)
    cuo = "".join("1" if c == "0" else "0" for c in bits)   # 错：全位取反
    zong = bits[::-1]                                        # 综：整卦倒置
    jiao = bits[3:] + bits[:3]                               # 交：上下经卦互换
    lin = []
    for i in range(6):                                       # 邻：逐位翻一位
        nb = bits[:i] + ("1" if bits[i] == "0" else "0") + bits[i + 1:]
        lin.append({"pos": i + 1, **_resolve(nb)})
    return {
        "错": _resolve(cuo),                                 # 恒存在（错无自反）
        "综": None if zong == bits else _resolve(zong),      # 自综 → None
        "交": None if jiao == bits else _resolve(jiao),      # 八纯卦自身 → None
        "邻": lin,
    }
