"""状态与旺衰骨架 + 用神选取（design D1/D6；引擎只输出事实标记，不下吉凶结论）。

- 旬空/月破/日冲：按四柱给每爻打事实标记
- 旺相休囚死：用神/原神/忌神在月令下的状态
- 回头生克 / 化进退：动爻与其变爻的关系
- 用神选取：类别→六亲映射、两现优先级、伏藏取伏神
"""
from __future__ import annotations

from dataclasses import dataclass

from .calendar import ZHI
from .hexagram import (
    HexagramChart,
    Yao,
    _KE,
    _SHENG,
    ZHI_WUXING,
    cast_chart,
    find_fushen,
)

# ── 五行旺相休囚死（以月令为基准）──────────────────────────
def wangshuai(yao_wx: str, month_wx: str) -> str:
    if yao_wx == month_wx:
        return "旺"
    if _SHENG[month_wx] == yao_wx:
        return "相"  # 令生爻
    if _SHENG[yao_wx] == month_wx:
        return "休"  # 爻生令
    if _KE[yao_wx] == month_wx:
        return "囚"  # 爻克令
    return "死"      # 令克爻


def _chong(zhi_index: int) -> int:
    """地支相冲：相隔六位。"""
    return (zhi_index + 6) % 12


# ── 问题类别 → 用神六亲（MVP 简化映射，见 design D6）────────────
CATEGORY_TO_YONGSHEN = {
    # 既有 6 类
    "事业": "官鬼", "姻缘": "官鬼", "财运": "妻财",
    "健康": "官鬼", "出行": "父母", "失物": "妻财",
    # 扩展（依《卜筮正宗·用神章》取用，见 expand-question-types/design D1）
    "考试": "官鬼",   # 功名应试：官鬼为主用神（父母为文书/成绩之辅，交解读层综合）
    "求子": "子孙",   # 子孙即子嗣之用神
    "官非": "官鬼",   # 词讼官非：官鬼为官府/对头，看世应
    "搬迁": "父母",   # 宅舍田宅以父母爻为用神
    "合作": "妻财",   # 求利交易以妻财为用神（应为对方，交解读层）
    "寻物": "妻财",   # 同失物，财物为用神
}

# 应爻为纲的类别（无固定六亲映射）：方案占判既定方案、谋望求事——以应爻为用神之纲
# （应代表所谋之事/彼方），见 expand-question-types/design D2。
YING_AS_YONGSHEN = {"方案占", "谋望"}


def is_known_category(category: str) -> bool:
    return category in CATEGORY_TO_YONGSHEN or category in YING_AS_YONGSHEN


@dataclass(frozen=True)
class YaoFlags:
    position: int
    xunkong: bool
    yuepo: bool
    richong: bool


def yao_flags(chart: HexagramChart, month_branch: int, day_zhi: int,
              xunkong: tuple[int, int]) -> list[YaoFlags]:
    """给每爻打 旬空/月破/日冲 事实标记。"""
    po = _chong(month_branch)   # 月破之支
    chong = _chong(day_zhi)     # 日冲之支
    out = []
    for y in chart.yaos:
        zi = ZHI.index(y.zhi)
        out.append(
            YaoFlags(
                position=y.position,
                xunkong=zi in xunkong,
                yuepo=zi == po,
                richong=zi == chong,
            )
        )
    return out


@dataclass(frozen=True)
class ForceEntry:
    liuqin: str
    position: int | None
    wangshuai: str
    de_ling: bool      # 得令（旺/相）
    de_ri: bool        # 得日辰生扶
    yuepo: bool
    xunkong: bool
    richong: bool
    fadong: bool       # 发动
    huitou: str | None  # 回头生/回头克/化进/化退/None
    andong: bool       # 暗动（静爻被日辰冲）


def _huitou(ben_wx: str, ben_zhi: int, bian_wx: str, bian_zhi: int) -> str | None:
    """动爻与变爻的关系：同五行论化进/化退，异五行论回头生克。"""
    if ben_wx == bian_wx:
        # 同五行：地支递进为进神、递退为退神
        return "化进" if (bian_zhi - ben_zhi) % 12 in (1, 2) else "化退"
    if _SHENG[bian_wx] == ben_wx:
        return "回头生"
    if _KE[bian_wx] == ben_wx:
        return "回头克"
    return None


def force_entry(
    chart: HexagramChart,
    position: int | None,
    liuqin: str,
    month_branch: int,
    day_zhi: int,
    xunkong: tuple[int, int],
    moving: set[int],
    bian_chart: HexagramChart | None,
) -> ForceEntry:
    """对某六亲所在爻输出结构化力量评估（纯事实标记）。"""
    if position is None:
        return ForceEntry(liuqin, None, "—", False, False, False, False,
                          False, False, None, False)
    y = chart.yaos[position - 1]
    zi = ZHI.index(y.zhi)
    month_wx = _branch_wx(month_branch)
    day_wx = _branch_wx(day_zhi)
    ws = wangshuai(y.wuxing, month_wx)
    de_ri = day_wx == y.wuxing or _SHENG[day_wx] == y.wuxing

    huitou = None
    fadong = position in moving
    if fadong and bian_chart is not None:
        by = bian_chart.yaos[position - 1]
        huitou = _huitou(y.wuxing, zi, by.wuxing, ZHI.index(by.zhi))

    return ForceEntry(
        liuqin=liuqin,
        position=position,
        wangshuai=ws,
        de_ling=ws in ("旺", "相"),
        de_ri=de_ri,
        yuepo=zi == _chong(month_branch),
        xunkong=zi in xunkong,
        richong=zi == _chong(day_zhi),
        fadong=fadong,
        huitou=huitou,
        andong=(zi == _chong(day_zhi)) and not fadong,  # 暗动：日冲静爻
    )


def feifu(fei_wx: str, fu_wx: str) -> str:
    """飞伏生克（engine-feifu）：飞神五行 ⊗ 伏神五行 → 契约五枚举。纯五行关系，不含吉凶。"""
    if fei_wx == fu_wx:
        return "飞伏比和"
    if _SHENG[fei_wx] == fu_wx:
        return "飞来生伏"
    if _KE[fei_wx] == fu_wx:
        return "飞来克伏"
    if _SHENG[fu_wx] == fei_wx:
        return "伏来生飞"
    if _KE[fu_wx] == fei_wx:
        return "伏来克飞"
    return "飞伏比和"


def fushen_force(fu_wx: str, fu_zhi: str, liuqin: str, position: int,
                 month_branch: int, day_zhi: int,
                 xunkong: tuple[int, int]) -> ForceEntry:
    """伏神力量事实（engine-feifu）：旺衰按月令、得日/旬空/月破/日冲同既有算法。
    伏神不上卦面，不计发动/回头/暗动（fadong/huitou/andong 恒为否）。"""
    zi = ZHI.index(fu_zhi)
    month_wx = _branch_wx(month_branch)
    day_wx = _branch_wx(day_zhi)
    ws = wangshuai(fu_wx, month_wx)
    de_ri = day_wx == fu_wx or _SHENG[day_wx] == fu_wx
    return ForceEntry(
        liuqin=liuqin, position=position, wangshuai=ws,
        de_ling=ws in ("旺", "相"), de_ri=de_ri,
        yuepo=zi == _chong(month_branch), xunkong=zi in xunkong,
        richong=zi == _chong(day_zhi),
        fadong=False, huitou=None, andong=False,
    )


def _branch_wx(zhi_index: int) -> str:
    return ZHI_WUXING[ZHI[zhi_index]]


# ── 用神选取 ────────────────────────────────────────────
def select_yongshen(
    chart: HexagramChart,
    category: str,
    month_branch: int,
    day_zhi: int,
    xunkong: tuple[int, int],
    moving: set[int],
    day_gan: int,
) -> dict:
    """返回 {liuqin, positions, chosen, 两现, 伏藏, fushen?, 应爻为纲?}。"""
    # 方案占/谋望：以应爻为用神之纲（应代表所谋之事/彼方）。应爻恒上卦，无伏藏。
    if category in YING_AS_YONGSHEN:
        yp = next((y.position for y in chart.yaos if y.shiying == "应"), None)
        ying = chart.yaos[yp - 1]
        return {"liuqin": ying.liuqin, "positions": [yp], "chosen": yp,
                "两现": False, "伏藏": False, "应爻为纲": True}

    liuqin = CATEGORY_TO_YONGSHEN[category]
    positions = chart.liuqin_positions(liuqin)

    if not positions:  # 伏藏
        fu = find_fushen(chart, liuqin, day_gan)
        return {
            "liuqin": liuqin, "positions": [], "chosen": None,
            "两现": False, "伏藏": True,
            "fushen": {"position": fu.position, "najia": fu.najia,
                       "wuxing": fu.wuxing, "zhi": fu.zhi} if fu else None,
        }

    if len(positions) == 1:
        return {"liuqin": liuqin, "positions": positions, "chosen": positions[0],
                "两现": False, "伏藏": False}

    chosen = _resolve_liang_xian(chart, positions, month_branch, day_zhi,
                                 xunkong, moving)
    return {"liuqin": liuqin, "positions": positions, "chosen": chosen,
            "两现": True, "伏藏": False}


def _resolve_liang_xian(chart, positions, month_branch, day_zhi, xunkong, moving):
    """两现取一优先级：①动 ②空破 ③临世应 ④得月日生扶 ⑤近世爻。"""
    po = _chong(month_branch)
    chong = _chong(day_zhi)
    month_wx = _branch_wx(month_branch)
    day_wx = _branch_wx(day_zhi)

    def rank(pos: int) -> tuple:
        y = chart.yaos[pos - 1]
        zi = ZHI.index(y.zhi)
        moving_f = pos in moving
        kongpo = (zi in xunkong) or (zi == po)
        shiying = y.shiying is not None
        ws = wangshuai(y.wuxing, month_wx)
        de = ws in ("旺", "相") or day_wx == y.wuxing or _SHENG[day_wx] == y.wuxing
        dist = abs(pos - chart.shi_pos)
        # 优先级越靠前权重越高；最后用"近世爻"(dist 越小越好)
        return (moving_f, kongpo, shiying, de, -dist)

    return max(positions, key=rank)
