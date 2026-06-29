"""断法关系层（engine-fadu-extend）：反吟伏吟 / 生旺墓绝 / 合化。

全部为五行·地支·纳甲的确定关系（查表），只标事实、不下吉凶；神煞/刑害不入此层。
十二长生锁定【水土同宫·长生在申】（六爻主流，与《增删卜易》断法一致）。
"""
from __future__ import annotations

from .calendar import ZHI

_Z = {c: i for i, c in enumerate(ZHI)}   # 地支 → 索引


def _i(zhi: str) -> int:
    return _Z[zhi]


def chong(idx: int) -> int:
    """相冲：相隔六位。"""
    return (idx + 6) % 12


# ── 六合 / 三合 ───────────────────────────────────────────
_LIUHE_PAIRS = {(0, 1), (2, 11), (3, 10), (4, 9), (5, 8), (6, 7)}  # 子丑寅亥卯戌辰酉巳申午未
_LIUHE = _LIUHE_PAIRS | {(b, a) for a, b in _LIUHE_PAIRS}


def is_liuhe(a: int, b: int) -> bool:
    return (a, b) in _LIUHE


# 三合局：五行 → (三支集合, 中神)
_SANHE = {
    "水": ({8, 0, 4}, 0),    # 申子辰，中神子
    "木": ({11, 3, 7}, 3),   # 亥卯未，中神卯
    "火": ({2, 6, 10}, 6),   # 寅午戌，中神午
    "金": ({5, 9, 1}, 9),    # 巳酉丑，中神酉
}

# 十二长生四要点：五行 → {长生, 帝旺, 墓, 绝} 地支索引（水土同宫）
_CHANGSHENG = {
    "木": {"长生": 11, "帝旺": 3, "墓": 7, "绝": 8},
    "火": {"长生": 2, "帝旺": 6, "墓": 10, "绝": 11},
    "金": {"长生": 5, "帝旺": 9, "墓": 1, "绝": 2},
    "水": {"长生": 8, "帝旺": 0, "墓": 4, "绝": 5},
    "土": {"长生": 8, "帝旺": 0, "墓": 4, "绝": 5},
}


def changsheng_state(wuxing: str, zhi_idx: int) -> str | None:
    """该五行在该地支的要点态：长生/帝旺/墓/绝，否则 None。"""
    for state, idx in _CHANGSHENG.get(wuxing, {}).items():
        if idx == zhi_idx:
            return state
    return None


def mu_branch(wuxing: str) -> int | None:
    return _CHANGSHENG.get(wuxing, {}).get("墓")


def jue_branch(wuxing: str) -> int | None:
    return _CHANGSHENG.get(wuxing, {}).get("绝")


# ── 反吟伏吟 / 合：逐爻 ───────────────────────────────────
def line_relations(primary, bian, moving_set: set[int],
                   day_zhi: int, month_branch: int) -> dict[int, dict]:
    """每爻关系：反吟/伏吟（动爻 本↔变）+ 合（逢日/月合、动爻相合）。返回 {pos: {...}}。"""
    out: dict[int, dict] = {}
    movers = sorted(moving_set)
    for y in primary.yaos:
        p = y.position
        zi = _i(y.zhi)
        rel: dict = {}
        # 反吟伏吟（仅动爻，需变卦）
        if bian is not None and p in moving_set:
            bz = _i(bian.yaos[p - 1].zhi)
            if bz == zi:
                rel["伏吟"] = True
            elif bz == chong(zi):
                rel["反吟"] = True
        # 合：逢日/月
        he = []
        if is_liuhe(zi, day_zhi):
            he.append("日合")
        if is_liuhe(zi, month_branch):
            he.append("月合")
        if he:
            rel["合"] = he
        # 动爻相合
        if p in moving_set:
            for q in movers:
                if q != p and is_liuhe(zi, _i(primary.yaos[q - 1].zhi)):
                    rel["动合"] = True
                    break
        if rel:
            out[p] = rel
    return out


# ── 反吟伏吟 / 合化：卦层 ─────────────────────────────────
def gua_relations(primary, bian, moving_set: set[int]) -> dict:
    """卦层：反吟/伏吟（内外卦三爻皆动且整体同支/相冲）+ 六合卦 + 三合局。"""
    res: dict = {"反吟": "无", "伏吟": "无", "六合": False, "三合": []}
    # 反吟伏吟：内卦(1-3)/外卦(4-6)——该宫【凡动之爻】皆同支=卦伏吟、皆相冲=卦反吟
    # （乾↔震互化纳甲地支全同，仅动 2 爻亦成立，故按"动爻是否一致"判，不强求三爻皆动）
    if bian is not None:
        for name, ps in (("内卦", (1, 2, 3)), ("外卦", (4, 5, 6))):
            movers = [p for p in ps if p in moving_set]
            if not movers:
                continue
            同 = all(_i(primary.yaos[p - 1].zhi) == _i(bian.yaos[p - 1].zhi) for p in movers)
            冲 = all(_i(bian.yaos[p - 1].zhi) == chong(_i(primary.yaos[p - 1].zhi)) for p in movers)
            if 同:
                res["伏吟"] = name if res["伏吟"] == "无" else res["伏吟"] + "+" + name
            elif 冲:
                res["反吟"] = name if res["反吟"] == "无" else res["反吟"] + "+" + name
    # 六合卦：初四/二五/三六 三组对应爻皆六合
    zis = [_i(y.zhi) for y in primary.yaos]   # index 0..5 = 初..上
    if all(is_liuhe(zis[i], zis[i + 3]) for i in range(3)):
        res["六合"] = True
    # 三合局：六爻地支集合（标含动否）
    present = set(zis)
    move_zhi = {_i(primary.yaos[p - 1].zhi) for p in moving_set}
    for wx, (trio, zhong) in _SANHE.items():
        have = trio & present
        if len(have) == 3:
            res["三合"].append({"五行": wx, "成局": "全",
                               "含动": bool(trio & move_zhi)})
        elif len(have) == 2 and zhong in have:
            res["三合"].append({"五行": wx, "成局": "半",
                               "含动": bool(trio & move_zhi)})
    return res


# ── 用神：入墓 / 随鬼入墓 / 绝 / 长生态 ───────────────────
def yong_relations(primary, bian, yong_pos: int | None, yong_wx: str,
                   moving_set: set[int], day_zhi: int, month_branch: int) -> dict:
    """用神生旺墓绝相关事实。yong_pos 为 None（伏藏）时返回空。"""
    if yong_pos is None or not yong_wx:
        return {}
    rel: dict = {}
    mu = mu_branch(yong_wx)
    jue = jue_branch(yong_wx)
    # 入墓：日墓 / 动墓 / 化墓
    types = []
    sui_gui = False
    if mu is not None:
        if day_zhi == mu:
            types.append("日")
        for p in moving_set:                       # 动墓：某动爻地支为用神墓库
            if _i(primary.yaos[p - 1].zhi) == mu:
                types.append("动")
                if primary.yaos[p - 1].liuqin == "官鬼":
                    sui_gui = True
                break
        if bian is not None and yong_pos in moving_set:   # 化墓：用神动化墓
            bz = _i(bian.yaos[yong_pos - 1].zhi)
            if bz == mu:
                types.append("化")
                if bian.yaos[yong_pos - 1].liuqin == "官鬼":
                    sui_gui = True
    if types:
        rel["入墓"] = {"type": "".join(dict.fromkeys(types))}
        if sui_gui:
            rel["随鬼入墓"] = True
    # 绝（对日辰或月建）
    if jue is not None and (day_zhi == jue or month_branch == jue):
        rel["绝"] = True
    # 长生态（要点）：对日、对月
    state = {"日": changsheng_state(yong_wx, day_zhi),
             "月": changsheng_state(yong_wx, month_branch)}
    if state["日"] or state["月"]:
        rel["长生态"] = {k: v for k, v in state.items() if v}
    return rel
