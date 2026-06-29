"""卦名 ↔ URL slug 纯查表（64 卦）。

仅一份静态映射：卦名拼音连字符化（无声调、小写），如「乾为天」→ qian-wei-tian。
slug 含关键词、利于 Google 理解与人读；简繁两域共用同一 slug（靠 hreflang 互链）。
本模块不触碰 GUA64 与排盘逻辑，只做名↔slug↔bits 的双向查表。
读法依占筮惯例（否=pi、屯=zhun、贲=bi、旅=lu、履=lu）。
"""
from __future__ import annotations

from .hexagram import GUA64

# 卦名 → slug（与 GUA64 的卦名一一对应；slug 全局唯一）
SLUG_BY_NAME: dict[str, str] = {
    "乾为天": "qian-wei-tian", "天风姤": "tian-feng-gou", "天山遁": "tian-shan-dun",
    "天地否": "tian-di-pi", "风地观": "feng-di-guan", "山地剥": "shan-di-bo",
    "火地晋": "huo-di-jin", "火天大有": "huo-tian-da-you",
    "兑为泽": "dui-wei-ze", "泽水困": "ze-shui-kun", "泽地萃": "ze-di-cui",
    "泽山咸": "ze-shan-xian", "水山蹇": "shui-shan-jian", "地山谦": "di-shan-qian",
    "雷山小过": "lei-shan-xiao-guo", "雷泽归妹": "lei-ze-gui-mei",
    "离为火": "li-wei-huo", "火山旅": "huo-shan-lu", "火风鼎": "huo-feng-ding",
    "火水未济": "huo-shui-wei-ji", "山水蒙": "shan-shui-meng", "风水涣": "feng-shui-huan",
    "天水讼": "tian-shui-song", "天火同人": "tian-huo-tong-ren",
    "震为雷": "zhen-wei-lei", "雷地豫": "lei-di-yu", "雷水解": "lei-shui-jie",
    "雷风恒": "lei-feng-heng", "地风升": "di-feng-sheng", "水风井": "shui-feng-jing",
    "泽风大过": "ze-feng-da-guo", "泽雷随": "ze-lei-sui",
    "巽为风": "xun-wei-feng", "风天小畜": "feng-tian-xiao-xu", "风火家人": "feng-huo-jia-ren",
    "风雷益": "feng-lei-yi", "天雷无妄": "tian-lei-wu-wang", "火雷噬嗑": "huo-lei-shi-ke",
    "山雷颐": "shan-lei-yi", "山风蛊": "shan-feng-gu",
    "坎为水": "kan-wei-shui", "水泽节": "shui-ze-jie", "水雷屯": "shui-lei-zhun",
    "水火既济": "shui-huo-ji-ji", "泽火革": "ze-huo-ge", "雷火丰": "lei-huo-feng",
    "地火明夷": "di-huo-ming-yi", "地水师": "di-shui-shi",
    "艮为山": "gen-wei-shan", "山火贲": "shan-huo-bi", "山天大畜": "shan-tian-da-xu",
    "山泽损": "shan-ze-sun", "火泽睽": "huo-ze-kui", "天泽履": "tian-ze-lu",
    "风泽中孚": "feng-ze-zhong-fu", "风山渐": "feng-shan-jian",
    "坤为地": "kun-wei-di", "地雷复": "di-lei-fu", "地泽临": "di-ze-lin",
    "地天泰": "di-tian-tai", "雷天大壮": "lei-tian-da-zhuang", "泽天夬": "ze-tian-guai",
    "水天需": "shui-tian-xu", "水地比": "shui-di-bi",
}

# bits（自下而上 6 位）↔ slug，便于路由与卦盘卦名直接取用
GUA_SLUG: dict[str, str] = {bits: SLUG_BY_NAME[name] for bits, name in GUA64.items()}
_SLUG_TO_BITS: dict[str, str] = {slug: bits for bits, slug in GUA_SLUG.items()}


def slug_to_bits(slug: str) -> str | None:
    """slug → 本卦 6 位二进制；未知 slug 返回 None。"""
    return _SLUG_TO_BITS.get((slug or "").strip().lower())


def bits_to_slug(bits: str) -> str | None:
    """本卦 6 位二进制 → slug；未知 bits 返回 None。"""
    return GUA_SLUG.get(bits)
