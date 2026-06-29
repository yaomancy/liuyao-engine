# 贡献指南 / Contributing

感谢关注 `liuyao-engine`。本库是一个**确定性**装卦/断法引擎，正确性是第一要务。

## 跑测试 / Run tests

```bash
pip install -e ".[dev]"   # sxtwl + pytest + lunar-python + najia
pytest -q                 # 全套，含对 najia 的差分校验
```

## 红线 / Hard rules

1. **改动引擎逻辑必须过锚点卦例与差分校验**：任何触及装卦 / 纳甲 / 六亲 / 世应 / 伏神 / 旺衰 / 历法的改动，`tests/test_differential.py`（对 najia 交叉验证）与 `cases/`（锚点卦例）必须全绿。算错即回退。
2. **法度不可动摇**：装卦遵《卜筮正宗》、断法遵《增删卜易》；**神煞不进核心逻辑**；**不混派**（不引入梅花/奇门等他派规则）。
3. **引擎只产硬事实**：纯规则、可逐项验证；不引入随机性（起卦的 CSPRNG 除外）、不引入网络/IO、不做 AI 解读。
4. **历法以双库为准**：历法相关改动需与 `sxtwl` + `lunar-python` 交叉验证一致（含节气交节、子时换日、跨时区）。

## 差分校验口径 / Differential oracle

以 [`najia`](https://github.com/bopo/najia) 为主预言机做大规模 (卦 + 时间) 比对；以 [`yigram-najia-rules`](https://github.com/AdrienSterling/yigram-najia-rules) 的规则表作第二静态参照。两者均为独立 MIT 实现。

## 提 PR / Pull requests

- 保持改动小而聚焦；附测试。
- 描述清楚改了哪条法度依据（引《卜筮正宗》/《增删卜易》原文或卷章）。
- 古典术语保留中文原文（可加拼音）；不英译释义。
