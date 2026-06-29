# liuyao-engine

> 确定性**六爻**装卦/断法引擎 · _Deterministic I Ching (Liù Yáo) hexagram engine_
> **by [Yaomancy](https://yaomancy.com)** · Apache-2.0

[![CI](https://github.com/yaomancy/liuyao-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/yaomancy/liuyao-engine/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-green.svg)](LICENSE)

把"起卦时刻"和"六爻"换算成一份**结构化卦盘事实**：干支四柱 → 装卦（纳甲 / 六亲 / 六神 / 世应 / 伏神）→ 旺衰骨架 → 用神。**纯规则、零网络、可逐项回归验证。**

法度：装卦遵《卜筮正宗》、断法遵《增删卜易》；神煞不进核心逻辑；不混派。引擎只负责一切"硬事实"，不含任何 AI 解读。

---

## English quick start

`liuyao-engine` is a **deterministic engine for Liù Yáo (六爻) / coin-oracle I Ching divination**. Given a cast and a timestamp it returns a fully assembled, machine-readable hexagram chart — Heavenly-Stem/Earthly-Branch four pillars, najia stem-branch attribution, six-relations, six-spirits, self/other lines, hidden lines, and wàng-shuāi (strength) — as plain Python data. **No AI, no network, no I/O.** Its lookup tables are cross-validated against [`najia`](https://github.com/bopo/najia) and [`yigram-najia-rules`](https://github.com/AdrienSterling/yigram-najia-rules); the calendar is double-checked against `sxtwl` + `lunar-python`. Classical terms stay in Chinese (with pinyin) — see the glossary; interpretive meanings are intentionally not translated.

## 安装 / Install

```bash
pip install git+https://github.com/yaomancy/liuyao-engine
```

依赖：仅 `sxtwl`（历法）。Python ≥ 3.11。

## 30 秒上手 / Killer example

```python
from liuyao import toss, compute_four_pillars, cast_chart, build_reading

cast = toss()                                    # 摇一卦：六爻，每爻三枚 CSPRNG 铜钱
fp   = compute_four_pillars(2026, 6, 29, 14, 30) # 起卦时刻 → 干支四柱（含旬空）
chart = cast_chart(cast.bits, fp.day.gan)        # 装盘：纳甲/六亲/世应/伏神

print(fp)            # 丙午 甲午 甲戌 辛未（旬空：申酉）
print(cast.bits, cast.moving)   # 011010 {4: '老阴', 5: '老阳', 6: '老阴'}

# 一步到位：完整结构化卦盘（契约见 cases/hexagram-json-contract.md）
reading = build_reading(
    category="财运", text="近期求财如何",
    bits=cast.bits, moving=cast.moving, four_pillars=fp,
)
print(reading.keys())
# dict_keys(['question','castTime','palace','卦象关系','primary','changed','yongShen','assessment'])
```

公共 API：`toss` · `compute_four_pillars` · `cast_chart` · `build_reading`（外加 `CastResult` / `FourPillars` / `HexagramChart` 等数据类）。

## 为什么可信 / Why trust the numbers

命理类代码最稀缺的是"算得对"的证明。本引擎的查表与排盘：

- **与两个独立 MIT 实现交叉核验一致**：[`najia`](https://github.com/bopo/najia)（程序化排盘，主差分预言机）+ [`yigram-najia-rules`](https://github.com/AdrienSterling/yigram-najia-rules)（机器可读规则表）——纳甲 / 六亲 / 六神 / 世应 / 旬空 / 宫五行 / 地支五行逐项吻合。
- **历法 `sxtwl` + `lunar-python` 双库交叉验证**：节气交节、子时换日、跨时区起卦均有单测覆盖。
- **`tests/test_differential.py`** 对 najia 做大规模 (卦 + 时间) 差分比对，随 CI 跑通。

```bash
pip install -e ".[dev]"
pytest          # 含对 najia 的差分校验
```

想看它跑在真实产品里？→ **[yaomancy.com](https://yaomancy.com)**

## 设计取舍 / Design rationale

代码证明「算得对」，但**为什么这么设计**同样重要：为什么神煞不进核心、为什么用 najia 做差分预言机、历法为什么双库交叉、真太阳时为什么后置——背后是一条主线：**凡进核心，必可被独立交叉验证**。

完整的领域判断与工程决策见 **[`docs/DESIGN.md`](docs/DESIGN.md)**。

## 仓库结构

```
liuyao/        引擎包（11 模块：calendar/cast/hexagram/relations/analysis/reading/…）
tests/         引擎测试 + test_differential（对 najia 交叉验证）
cases/         锚点卦例：hexagram-json-contract.md（卦盘 JSON 契约）/ regression-cases-draft.md
data/          审计参考：真值表 yigram-najia-tables.json、术语 liuyao-glossary.json、ctext 公有领域古籍全文
LICENSE NOTICE licenses/    Apache-2.0 + 第三方/古籍署名
```

## 术语 / Terminology

领域术语保留中文原文 + 拼音（便于检索），不英译其含义。完整释义见 [`data/liuyao-glossary.json`](data/liuyao-glossary.json)。例：

| 中文 | 拼音 | 检索用英文（指针，非释义） |
|---|---|---|
| 纳甲 | nàjiǎ | stem-branch attribution |
| 六亲 | liùqīn | six relations |
| 世应 | shì / yìng | self / other line |
| 伏神 | fúshén | hidden line |
| 旺衰 | wàng-shuāi | line strength (by month qi) |
| 旬空 | xúnkōng | void / empty branches |

> 六十四卦的「中文 · 拼音 · 通用英文名（标注 Wilhelm/Baynes 译本）」对照表，见 glossary 的 `六十四卦` 段（持续完善）。

## 许可与署名 / License & attribution

Apache-2.0（版权 © 2026 Jincheng Xie）。第三方与古籍底本署名见 [`NOTICE`](NOTICE) 与 [`licenses/`](licenses/)：

- 交叉验证参考 **najia** (MIT) · **yigram-najia-rules** (MIT)；`data/yigram-najia-tables.json` 派生自后者。
- 历法 **sxtwl** (MIT) · **lunar-python** (MIT)。
- 古籍《卜筮正宗》《增删卜易》为公有领域（ctext.org 提取）；现代校评/整理本不含于本库。

---

_装卦遵《卜筮正宗》· 断法遵《增删卜易》· 神煞不进核心 · 不混派 — by Yaomancy · [yaomancy.com](https://yaomancy.com)_
