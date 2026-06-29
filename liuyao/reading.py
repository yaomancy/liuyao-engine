"""卦象组装层：按 hexagram-json-contract.md 把排盘结果组装成结构化卦象 dict。

这是引擎输出的唯一接口契约（供下游渲染与回归测试使用）。
输入：立问 + 本卦(6位二进制) + 动爻 + 四柱；输出：契约 dict（纯事实，无吉凶结论）。
"""
from __future__ import annotations

from .analysis import (
    CATEGORY_TO_YONGSHEN,
    ForceEntry,
    feifu,
    force_entry,
    fushen_force,
    is_known_category,
    select_yongshen,
    yao_flags,
)
from .calendar import GAN, ZHI, FourPillars
from .guaxiang import get_xiangyi
from .gua_slug import bits_to_slug
from .hexagram import (
    HexagramChart,
    _KE,
    _SHENG,
    _liuqin,
    cast_chart,
)
from .relations import (
    gua_relations,
    line_relations,
    yong_relations,
)


def _bian_bits(bits: str, moving: set[int]) -> str:
    """变卦：翻转所有动爻位（position 1-6 → 索引 0-5）。"""
    return "".join(
        str(1 - int(c)) if (i + 1) in moving else c for i, c in enumerate(bits)
    )


def _yuan_ji_chou_liuqin(yongshen_wx: str, palace_wx: str) -> tuple[str, str, str]:
    """由用神五行推原神/忌神/仇神六亲。

    原神=生用神者；忌神=克用神者；仇神=生忌神者（亦克原神，对用神不利的"帮凶"）。
    """
    yuan_wx = next(k for k, v in _SHENG.items() if v == yongshen_wx)  # 生用神
    ji_wx = next(k for k, v in _KE.items() if v == yongshen_wx)       # 克用神
    chou_wx = next(k for k, v in _SHENG.items() if v == ji_wx)        # 生忌神
    return (_liuqin(yuan_wx, palace_wx), _liuqin(ji_wx, palace_wx),
            _liuqin(chou_wx, palace_wx))


def _first_pos(chart: HexagramChart, liuqin: str) -> int | None:
    ps = chart.liuqin_positions(liuqin)
    return ps[0] if ps else None


def _entry_dict(e: ForceEntry) -> dict:
    return {
        "liuQin": e.liuqin, "position": e.position, "wangShuai": e.wangshuai,
        "得令": e.de_ling, "得日": e.de_ri, "月破": e.yuepo,
        "旬空": e.xunkong, "日冲": e.richong, "发动": e.fadong,
        "暗动": e.andong, "huiTou": e.huitou,
    }


def build_reading(
    *,
    category: str,
    text: str,
    bits: str,
    moving: dict[int, str],
    four_pillars: FourPillars,
) -> dict:
    """组装结构化卦象 dict（契约见 hexagram-json-contract.md）。

    moving: {爻位(1-6): '老阳'|'老阴'}；其余爻为静。
    """
    if not is_known_category(category):
        raise ValueError(f"未知问题类别: {category}")

    day_gan = four_pillars.day.gan
    month_branch = four_pillars.month.zhi
    day_zhi = four_pillars.day.zhi
    xunkong = four_pillars.xunkong
    moving_set = set(moving)

    primary = cast_chart(bits, day_gan)
    bian = cast_chart(_bian_bits(bits, moving_set), day_gan) if moving_set else None

    flags = {f.position: f for f in
             yao_flags(primary, month_branch, day_zhi, xunkong)}

    ys = select_yongshen(primary, category, month_branch, day_zhi,
                         xunkong, moving_set, day_gan)

    def mk_entry(liuqin, pos):
        return force_entry(primary, pos, liuqin, month_branch, day_zhi,
                           xunkong, moving_set, bian)

    # 用神上卦时给出 用神/原神/忌神 力量评估；伏藏时据飞伏 + 伏神旺衰填充（engine-feifu）
    yong_pos = ys["chosen"]
    fushen_pos = ys.get("fushen", {}).get("position") if ys["伏藏"] else None
    feifu_rel = None       # 飞伏生克（伏藏时算；供 Line.伏神.feiFu 与 assessment.用神）
    assessment = {}
    if yong_pos is not None:
        yong_wx = primary.yaos[yong_pos - 1].wuxing
        yuan_lq, ji_lq, chou_lq = _yuan_ji_chou_liuqin(yong_wx, primary.palace_wuxing)
        assessment = {
            "用神": _entry_dict(mk_entry(ys["liuqin"], yong_pos)),
            "原神": _entry_dict(mk_entry(yuan_lq, _first_pos(primary, yuan_lq))),
            "忌神": _entry_dict(mk_entry(ji_lq, _first_pos(primary, ji_lq))),
            "仇神": _entry_dict(mk_entry(chou_lq, _first_pos(primary, chou_lq))),
        }
    elif ys["伏藏"] and ys.get("fushen"):
        # 伏藏：飞神=本卦同位可见爻；飞伏生克 + 伏神旺衰（事实，不下"能否出伏"结论）
        fs = ys["fushen"]
        fei_wx = primary.yaos[fs["position"] - 1].wuxing
        feifu_rel = feifu(fei_wx, fs["wuxing"])
        # position 置 None：用神伏藏、不在可见卦面（position 恒指"该六亲所在可见爻"）；
        # 飞神爻位另存 伏神位，仅供展示，不污染 position 语义。
        fu_entry = _entry_dict(
            fushen_force(fs["wuxing"], fs["zhi"], ys["liuqin"], None,
                         month_branch, day_zhi, xunkong))
        fu_entry["feiFu"] = feifu_rel
        fu_entry["伏藏"] = True
        fu_entry["伏神位"] = fs["position"]
        yuan_lq, ji_lq, chou_lq = _yuan_ji_chou_liuqin(fs["wuxing"], primary.palace_wuxing)
        assessment = {
            "用神": fu_entry,
            "原神": _entry_dict(mk_entry(yuan_lq, _first_pos(primary, yuan_lq))),
            "忌神": _entry_dict(mk_entry(ji_lq, _first_pos(primary, ji_lq))),
            "仇神": _entry_dict(mk_entry(chou_lq, _first_pos(primary, chou_lq))),
        }

    # 断法关系（engine-fadu-extend）：反吟伏吟 / 合（逐爻）+ 卦层 / 用神生旺墓绝
    rel_by_pos = line_relations(primary, bian, moving_set, day_zhi, month_branch)
    gua_rel = gua_relations(primary, bian, moving_set)
    yong_rel = {}
    if yong_pos is not None:
        yong_rel = yong_relations(primary, bian, yong_pos,
                                  primary.yaos[yong_pos - 1].wuxing,
                                  moving_set, day_zhi, month_branch)
        if yong_rel and assessment.get("用神"):
            assessment["用神"]["relations"] = yong_rel  # 入墓/随鬼/绝/长生态（纯增）

    def line_dict(y, flag, relations):
        d = {
            "position": y.position,
            "yinYang": "yang" if y.yin_yang == "阳" else "yin",
            "moving": moving.get(y.position),
            "纳甲": {"干": y.gan, "支": y.zhi},
            "wuXing": y.wuxing,
            "liuQin": y.liuqin,
            "liuShen": y.liushen,
            "shiYing": {"世": "世", "应": "应"}.get(y.shiying),
            "flags": {"旬空": flag.xunkong, "月破": flag.yuepo, "日冲": flag.richong},
            "relations": relations,    # 反吟/伏吟/合/动合（变了即视为事实，纯增）
        }
        if fushen_pos == y.position and ys.get("fushen"):
            d["伏神"] = {"najia": ys["fushen"]["najia"], "liuQin": ys["liuqin"],
                         "feiFu": feifu_rel}      # 飞伏生克（engine-feifu，契约既有字段）
        else:
            d["伏神"] = None
        return d

    def chart_dict(c: HexagramChart, with_relations: bool):
        rels = rel_by_pos if with_relations else {}
        return {
            "上卦": c.bits[3:], "下卦": c.bits[:3], "name": c.name,
            "slug": bits_to_slug(c.bits),  # 卦盘卦名链到 /gua/{slug} 详解（单一来源）
            "象意": get_xiangyi(c.name),
            "lines": [line_dict(y, flags[y.position], rels.get(y.position, {}))
                      for y in c.yaos],
        }

    return {
        "question": {"category": category, "text": text},
        "castTime": {
            "ganZhi": {"年": str(four_pillars.year), "月": str(four_pillars.month),
                       "日": str(four_pillars.day), "时": str(four_pillars.hour)},
            "月建": ZHI[month_branch], "日辰": str(four_pillars.day),
            "旬空": [ZHI[xunkong[0]], ZHI[xunkong[1]]],
        },
        "palace": {"gua": primary.palace, "wuXing": primary.palace_wuxing,
                   "type": primary.gua_type},
        "卦象关系": gua_rel,                     # 反吟/伏吟/六合卦/三合局（顶层·纯增）
        "primary": chart_dict(primary, True),
        "changed": chart_dict(bian, False) if bian else None,
        "yongShen": {"liuQin": ys["liuqin"], "positions": ys["positions"],
                     "chosen": ys["chosen"], "两现": ys["两现"], "伏藏": ys["伏藏"],
                     "应爻为纲": ys.get("应爻为纲", False)},
        "assessment": assessment,
    }
