"""装卦引擎单测：以 5 个锚点卦例（reference/classics/regression-cases-draft.md）
逐爻断言 纳甲/五行/六亲/六神/世应，并验证伏神。

真值已与 najia + yigram 交叉核验；此处锚点为引擎"标准答案"。
"""
from liuyao.hexagram import GAN, cast_chart, find_fushen

# 每个锚点：bits、日干、以及 初→上 六爻的 (六亲, 纳甲, 五行, 六神, 世/应)
ANCHORS = {
    "乾为天": {
        "bits": "111111", "gan": "庚", "palace": "乾", "type": "本宫",
        "yaos": [
            ("子孙", "甲子", "水", "白虎", None),
            ("妻财", "甲寅", "木", "玄武", None),
            ("父母", "甲辰", "土", "青龙", "应"),  # 本宫：应在三爻
            ("官鬼", "壬午", "火", "朱雀", None),
            ("兄弟", "壬申", "金", "勾陈", None),
            ("父母", "壬戌", "土", "螣蛇", "世"),  # 本宫：世在上爻
        ],
    },
    "天风姤": {
        "bits": "011111", "gan": "甲", "palace": "乾", "type": "一世",
        "yaos": [
            ("父母", "辛丑", "土", "青龙", "世"),
            ("子孙", "辛亥", "水", "朱雀", None),
            ("兄弟", "辛酉", "金", "勾陈", None),
            ("官鬼", "壬午", "火", "螣蛇", "应"),
            ("兄弟", "壬申", "金", "白虎", None),
            ("父母", "壬戌", "土", "玄武", None),
        ],
        "fushen": ("妻财", "甲寅"),  # 缺妻财 → 取乾宫首卦二爻甲寅
    },
    "火地晋": {
        "bits": "000101", "gan": "戊", "palace": "乾", "type": "游魂",
        "yaos": [
            ("父母", "乙未", "土", "勾陈", "应"),
            ("官鬼", "乙巳", "火", "螣蛇", None),
            ("妻财", "乙卯", "木", "白虎", None),
            ("兄弟", "己酉", "金", "玄武", "世"),
            ("父母", "己未", "土", "青龙", None),
            ("官鬼", "己巳", "火", "朱雀", None),
        ],
        "fushen": ("子孙", "甲子"),  # 缺子孙 → 取乾宫首卦初爻甲子
    },
    "火天大有": {
        "bits": "111101", "gan": "甲", "palace": "乾", "type": "归魂",
        "yaos": [
            ("子孙", "甲子", "水", "青龙", None),
            ("妻财", "甲寅", "木", "朱雀", None),
            ("父母", "甲辰", "土", "勾陈", "世"),
            ("兄弟", "己酉", "金", "螣蛇", None),
            ("父母", "己未", "土", "白虎", None),
            ("官鬼", "己巳", "火", "玄武", "应"),
        ],
    },
    "坎为水": {
        "bits": "010010", "gan": "壬", "palace": "坎", "type": "本宫",
        "yaos": [
            ("子孙", "戊寅", "木", "玄武", None),
            ("官鬼", "戊辰", "土", "青龙", None),
            ("妻财", "戊午", "火", "朱雀", "应"),
            ("父母", "戊申", "金", "勾陈", None),
            ("官鬼", "戊戌", "土", "螣蛇", None),
            ("兄弟", "戊子", "水", "白虎", "世"),
        ],
    },
}


def _assert_anchor(name: str, data: dict):
    chart = cast_chart(data["bits"], GAN.index(data["gan"]))
    assert chart.name == name
    assert chart.palace == data["palace"]
    assert chart.gua_type == data["type"]
    for i, (lq, najia, wx, ls, sy) in enumerate(data["yaos"]):
        y = chart.yaos[i]
        ctx = f"{name} 第{i + 1}爻"
        assert y.liuqin == lq, f"{ctx} 六亲: {y.liuqin}!={lq}"
        assert y.najia == najia, f"{ctx} 纳甲: {y.najia}!={najia}"
        assert y.wuxing == wx, f"{ctx} 五行: {y.wuxing}!={wx}"
        assert y.liushen == ls, f"{ctx} 六神: {y.liushen}!={ls}"
        assert y.shiying == sy, f"{ctx} 世应: {y.shiying}!={sy}"


def test_anchor_qianweitian():
    _assert_anchor("乾为天", ANCHORS["乾为天"])


def test_anchor_tianfenggou():
    _assert_anchor("天风姤", ANCHORS["天风姤"])


def test_anchor_huodijin():
    _assert_anchor("火地晋", ANCHORS["火地晋"])


def test_anchor_huotiandayou():
    _assert_anchor("火天大有", ANCHORS["火天大有"])


def test_anchor_kanweishui():
    _assert_anchor("坎为水", ANCHORS["坎为水"])


def test_fushen_feilaisheng():
    """天风姤缺妻财 → 伏神取乾宫首卦二爻甲寅(妻财)，伏于本卦二爻。"""
    chart = cast_chart("011111", GAN.index("甲"))
    fu = find_fushen(chart, "妻财", GAN.index("甲"))
    assert fu is not None
    assert fu.liuqin == "妻财"
    assert fu.najia == "甲寅"
    assert fu.position == 2  # 伏于本卦二爻(飞神辛亥)


def test_fushen_feilaike():
    """火地晋缺子孙 → 伏神取乾宫首卦初爻甲子(子孙)，伏于本卦初爻。"""
    chart = cast_chart("000101", GAN.index("戊"))
    fu = find_fushen(chart, "子孙", GAN.index("戊"))
    assert fu is not None
    assert fu.najia == "甲子"
    assert fu.position == 1


def test_palace_table_complete():
    """八宫生成应恰好覆盖 64 卦，无重复。"""
    from liuyao.hexagram import _PALACE_TABLE

    assert len(_PALACE_TABLE) == 64
