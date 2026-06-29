"""装卦引擎：给定本卦六爻 + 起卦日干，排出完整卦盘。

确定性核心（design D4）。每一步都是查表 + 固定规则，可逐项回归验证。
卦的二进制表示：6 字符串，自下而上（索引0=初爻），1=阳 0=阴；
下卦=前 3 位（初二三），上卦=后 3 位（四五上）。

真值表已与 najia(MIT) + yigram-najia-rules(MIT) 交叉核验一致
（见 reference/classics/SOURCES.md）。
"""
from __future__ import annotations

from dataclasses import dataclass

# ── 八卦（三爻，自下而上的二进制）──────────────────────────
TRIGRAM_NAME = {
    "111": "乾", "110": "兑", "101": "离", "100": "震",
    "011": "巽", "010": "坎", "001": "艮", "000": "坤",
}
TRIGRAM_BITS = {v: k for k, v in TRIGRAM_NAME.items()}

# 八宫五行（宫=六亲之"我"）
PALACE_WUXING = {
    "乾": "金", "兑": "金", "离": "火", "震": "木",
    "巽": "木", "坎": "水", "艮": "土", "坤": "土",
}

# 纳甲：每卦作内卦(下)用 inner，作外卦(上)用 outer；地支按初→上三位
NAJIA = {
    "乾": ("甲", "子寅辰", "壬", "午申戌"),
    "坎": ("戊", "寅辰午", "戊", "申戌子"),
    "艮": ("丙", "辰午申", "丙", "戌子寅"),
    "震": ("庚", "子寅辰", "庚", "午申戌"),
    "巽": ("辛", "丑亥酉", "辛", "未巳卯"),
    "离": ("己", "卯丑亥", "己", "酉未巳"),
    "坤": ("乙", "未巳卯", "癸", "丑亥酉"),
    "兑": ("丁", "巳卯丑", "丁", "亥酉未"),
}

ZHI_WUXING = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
    "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水",
}

SHEN6 = ("青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武")
GAN = "甲乙丙丁戊己庚辛壬癸"

# 五行生克
_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
_KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

# 卦名（64 卦，键为自下而上 6 位二进制；与 najia 交叉核验一致）
GUA64 = {
    "111111": "乾为天", "011111": "天风姤", "001111": "天山遁", "000111": "天地否",
    "000011": "风地观", "000001": "山地剥", "000101": "火地晋", "111101": "火天大有",
    "110110": "兑为泽", "010110": "泽水困", "000110": "泽地萃", "001110": "泽山咸",
    "001010": "水山蹇", "001000": "地山谦", "001100": "雷山小过", "110100": "雷泽归妹",
    "101101": "离为火", "001101": "火山旅", "011101": "火风鼎", "010101": "火水未济",
    "010001": "山水蒙", "010011": "风水涣", "010111": "天水讼", "101111": "天火同人",
    "100100": "震为雷", "000100": "雷地豫", "010100": "雷水解", "011100": "雷风恒",
    "011000": "地风升", "011010": "水风井", "011110": "泽风大过", "100110": "泽雷随",
    "011011": "巽为风", "111011": "风天小畜", "101011": "风火家人", "100011": "风雷益",
    "100111": "天雷无妄", "100101": "火雷噬嗑", "100001": "山雷颐", "011001": "山风蛊",
    "010010": "坎为水", "110010": "水泽节", "100010": "水雷屯", "101010": "水火既济",
    "101110": "泽火革", "101100": "雷火丰", "101000": "地火明夷", "010000": "地水师",
    "001001": "艮为山", "101001": "山火贲", "111001": "山天大畜", "110001": "山泽损",
    "110101": "火泽睽", "110111": "天泽履", "110011": "风泽中孚", "001011": "风山渐",
    "000000": "坤为地", "100000": "地雷复", "110000": "地泽临", "111000": "地天泰",
    "111100": "雷天大壮", "111110": "泽天夬", "111010": "水天需", "000010": "水地比",
}

# 八宫生成：本宫(纯卦相叠)经固定"翻爻集"生成 8 卦，并定卦型与世位
_FLIP_SEQ = [
    (frozenset(), 6, "本宫"),
    (frozenset({0}), 1, "一世"),
    (frozenset({0, 1}), 2, "二世"),
    (frozenset({0, 1, 2}), 3, "三世"),
    (frozenset({0, 1, 2, 3}), 4, "四世"),
    (frozenset({0, 1, 2, 3, 4}), 5, "五世"),
    (frozenset({0, 1, 2, 4}), 4, "游魂"),
    (frozenset({4}), 3, "归魂"),
]


def _build_palace_table() -> dict[str, tuple[str, str, int]]:
    """生成 64 卦 → (卦宫, 卦型, 世位1-6)。"""
    table: dict[str, tuple[str, str, int]] = {}
    for palace in TRIGRAM_NAME.values():
        base = TRIGRAM_BITS[palace] + TRIGRAM_BITS[palace]  # 下+上，纯卦相叠
        for flips, shi, gua_type in _FLIP_SEQ:
            bits = "".join(
                str(1 - int(c)) if i in flips else c for i, c in enumerate(base)
            )
            table[bits] = (palace, gua_type, shi)
    return table


_PALACE_TABLE = _build_palace_table()


def _liuqin(yao_wx: str, palace_wx: str) -> str:
    """六亲：以宫五行为"我"，按生克定。"""
    if yao_wx == palace_wx:
        return "兄弟"
    if _SHENG[yao_wx] == palace_wx:
        return "父母"  # 爻生我
    if _SHENG[palace_wx] == yao_wx:
        return "子孙"  # 我生爻
    if _KE[yao_wx] == palace_wx:
        return "官鬼"  # 爻克我
    return "妻财"      # 我克爻


def _liushen_start(day_gan: int) -> int:
    """日干起六神的起始索引（甲乙青龙…壬癸玄武）。"""
    return {0: 0, 1: 0, 2: 1, 3: 1, 4: 2, 5: 3, 6: 4, 7: 4, 8: 5, 9: 5}[day_gan]


def _ying_pos(shi: int) -> int:
    """应爻位：与世爻隔三位。"""
    return shi + 3 if shi <= 3 else shi - 3


@dataclass(frozen=True)
class Yao:
    position: int    # 1-6 初→上
    yin_yang: str    # 阳/阴
    gan: str
    zhi: str
    wuxing: str
    liuqin: str
    liushen: str
    shiying: str | None  # 世/应/None

    @property
    def najia(self) -> str:
        return f"{self.gan}{self.zhi}"


@dataclass(frozen=True)
class HexagramChart:
    bits: str
    name: str
    palace: str
    palace_wuxing: str
    gua_type: str
    shi_pos: int
    ying_pos: int
    yaos: tuple[Yao, ...]  # 初→上

    def liuqin_positions(self, liuqin: str) -> list[int]:
        return [y.position for y in self.yaos if y.liuqin == liuqin]


def cast_chart(bits: str, day_gan: int) -> HexagramChart:
    """装卦：给定本卦 6 位二进制(自下而上) + 起卦日干索引，排出完整卦盘。"""
    if len(bits) != 6 or any(c not in "01" for c in bits):
        raise ValueError(f"bits 必须是 6 位 0/1，收到 {bits!r}")

    lower, upper = bits[:3], bits[3:]
    palace, gua_type, shi = _PALACE_TABLE[bits]
    palace_wx = PALACE_WUXING[palace]

    in_gan, in_zhi, _, _ = NAJIA[TRIGRAM_NAME[lower]]
    _, _, out_gan, out_zhi = NAJIA[TRIGRAM_NAME[upper]]
    gans = [in_gan, in_gan, in_gan, out_gan, out_gan, out_gan]
    zhis = list(in_zhi) + list(out_zhi)

    shen_start = _liushen_start(day_gan)
    ying = _ying_pos(shi)

    yaos = []
    for i in range(6):
        zhi = zhis[i]
        wx = ZHI_WUXING[zhi]
        shiying = "世" if i + 1 == shi else ("应" if i + 1 == ying else None)
        yaos.append(
            Yao(
                position=i + 1,
                yin_yang="阳" if bits[i] == "1" else "阴",
                gan=gans[i],
                zhi=zhi,
                wuxing=wx,
                liuqin=_liuqin(wx, palace_wx),
                liushen=SHEN6[(shen_start + i) % 6],
                shiying=shiying,
            )
        )

    return HexagramChart(
        bits=bits,
        name=GUA64[bits],
        palace=palace,
        palace_wuxing=palace_wx,
        gua_type=gua_type,
        shi_pos=shi,
        ying_pos=ying,
        yaos=tuple(yaos),
    )


def find_fushen(chart: HexagramChart, liuqin: str, day_gan: int) -> Yao | None:
    """伏神：若本卦缺某六亲，从本宫首卦(纯卦相叠)取该六亲爻为伏神。

    返回的 Yao.position 对齐到本卦同位爻(飞神)，gan/zhi 为伏神干支。
    """
    if chart.liuqin_positions(liuqin):
        return None  # 该六亲已上卦，无需伏神
    base_bits = TRIGRAM_BITS[chart.palace] + TRIGRAM_BITS[chart.palace]
    base = cast_chart(base_bits, day_gan)
    for y in base.yaos:
        if y.liuqin == liuqin:
            return y  # 其 position 即所伏的飞神爻位
    return None
