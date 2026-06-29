# 卦象 JSON 契约（HexagramReading）

> 引擎输出的**唯一接口契约**（供下游渲染与回归测试使用）。
> 原则：引擎只输出**事实标记**，不含吉凶结论；下游只能在这些事实上综合（事实锁定）。

---

## 一、枚举值（约定固定取值）

| 枚举 | 取值 |
|---|---|
| `yinYang` 阴阳 | `"yang"` 阳 ｜ `"yin"` 阴 |
| `moving` 动爻类型 | `null` 静 ｜ `"老阳"`(重·阳变阴) ｜ `"老阴"`(交·阴变阳) |
| `wuXing` 五行 | `"金"` ｜ `"木"` ｜ `"水"` ｜ `"火"` ｜ `"土"` |
| `liuQin` 六亲 | `"父母"` ｜ `"兄弟"` ｜ `"子孙"` ｜ `"妻财"` ｜ `"官鬼"` |
| `liuShen` 六神 | `"青龙"` ｜ `"朱雀"` ｜ `"勾陈"` ｜ `"螣蛇"` ｜ `"白虎"` ｜ `"玄武"` |
| `gua` 八卦 | `"乾"` ｜ `"坎"` ｜ `"艮"` ｜ `"震"` ｜ `"巽"` ｜ `"离"` ｜ `"坤"` ｜ `"兑"` |
| `palaceType` 卦型 | `"本宫"` ｜ `"一世"` ｜ `"二世"` ｜ `"三世"` ｜ `"四世"` ｜ `"五世"` ｜ `"游魂"` ｜ `"归魂"` |
| `shiYing` 世应 | `null` ｜ `"世"` ｜ `"应"` |
| `wangShuai` 旺衰档 | `"旺"` ｜ `"相"` ｜ `"休"` ｜ `"囚"` ｜ `"死"` |
| `feiFu` 飞伏生克 | `"飞来生伏"` ｜ `"飞来克伏"` ｜ `"伏来生飞"` ｜ `"伏来克飞"` ｜ `"飞伏比和"` |
| `huiTou` 回头生克 | `null` ｜ `"回头生"` ｜ `"回头克"` ｜ `"化进"` ｜ `"化退"` ｜ `"化空"` |
| `category` 问题类别 | `"事业"` ｜ `"姻缘"` ｜ `"财运"` ｜ `"健康"` ｜ `"出行"` ｜ `"失物"`（可扩展） |

爻位 `position`：整数 `1..6`，自下而上（1=初爻，6=上爻）。

---

## 二、结构定义

```jsonc
HexagramReading {
  "question": {
    "category": category,        // 立问类别（决定用神六亲）
    "text": string               // 所测之事原文
  },

  "castTime": {
    "localTime": string,         // ISO8601，用户设备本地时间
    "ganZhi": {                  // 四柱干支（子时23:00换日、月建按节气）
      "年": string, "月": string, "日": string, "时": string
    },
    "月建": string,              // 月支（旺衰所凭）
    "日辰": string,              // 日干支（旺衰/旬空所凭）
    "旬空": [string, string]     // 当旬两个空亡地支
  },

  "palace": {
    "gua": gua,                  // 所属卦宫
    "wuXing": wuXing,            // 宫五行（六亲之"我"）
    "type": palaceType           // 本宫/一世…/游魂/归魂
  },

  "primary": {                   // 本卦
    "上卦": gua, "下卦": gua,
    "name": string,             // 卦名，如 "乾为天"
    "lines": [Line, Line, Line, Line, Line, Line]   // 索引0=初爻 … 索引5=上爻
  },

  "changed": Hexagram | null,    // 变卦；无动爻时为 null。结构同 primary（lines 重新装卦）

  "yongShen": {
    "liuQin": liuQin,            // 用神六亲（由 category 映射）
    "positions": [int],         // 用神所在爻位（可能多个）
    "chosen": int | null,       // 最终选定的用神爻位（两现时按优先级取一；伏藏时为 null）
    "两现": boolean,
    "伏藏": boolean              // true 时见对应 Line.伏神
  },

  "assessment": {               // 力量评估骨架——全为事实标记，无吉凶结论
    "用神": ForceEntry,
    "原神": ForceEntry,         // 生用神之六亲
    "忌神": ForceEntry          // 克用神之六亲
  }
}

Line {
  "position": int,             // 1..6
  "yinYang": yinYang,
  "moving": moving,            // null / 老阳 / 老阴
  "纳甲": { "干": string, "支": string },
  "wuXing": wuXing,            // 该爻地支五行
  "liuQin": liuQin,
  "liuShen": liuShen,
  "shiYing": shiYing,          // 世/应/null
  "伏神": {                    // 仅当该爻下伏神时存在
    "干": string, "支": string,
    "liuQin": liuQin, "wuXing": wuXing,
    "feiFu": feiFu             // 飞伏生克
  } | null,
  "flags": {
    "旬空": boolean,
    "月破": boolean,
    "日冲": boolean
  }
}

ForceEntry {
  "liuQin": liuQin,
  "position": int | null,      // 所评估之爻；伏藏时可为 null
  "wangShuai": wangShuai,      // 在月建下的旺相休囚死
  "得令": boolean,             // 得月建之气
  "得日": boolean,             // 得日辰生扶
  "被日冲": boolean,
  "旬空": boolean,
  "月破": boolean,
  "发动": boolean,
  "huiTou": huiTou             // 发动时的化进/化退/回头生克/化空
}
```

---

## 三、实例（以「例 1 乾为天」填充，节选）

> 起卦：申月 庚寅日，问财运，静卦。用神＝妻财（财运）。

```jsonc
{
  "question": { "category": "财运", "text": "近期投资能否获利" },
  "castTime": {
    "localTime": "2026-08-12T10:30:00+08:00",
    "ganZhi": { "年": "丙午", "月": "丙申", "日": "庚寅", "时": "辛巳" },
    "月建": "申", "日辰": "庚寅", "旬空": ["午", "未"]
  },
  "palace": { "gua": "乾", "wuXing": "金", "type": "本宫" },
  "primary": {
    "上卦": "乾", "下卦": "乾", "name": "乾为天",
    "lines": [
      { "position": 1, "yinYang": "yang", "moving": null,
        "纳甲": {"干":"甲","支":"子"}, "wuXing":"水", "liuQin":"子孙",
        "liuShen":"白虎", "shiYing":"世", "伏神": null,
        "flags": {"旬空": false, "月破": false, "日冲": false} },
      { "position": 2, "yinYang": "yang", "moving": null,
        "纳甲": {"干":"甲","支":"寅"}, "wuXing":"木", "liuQin":"妻财",
        "liuShen":"玄武", "shiYing": null, "伏神": null,
        "flags": {"旬空": false, "月破": true, "日冲": false} },
      { "position": 3, "yinYang": "yang", "moving": null,
        "纳甲": {"干":"甲","支":"辰"}, "wuXing":"土", "liuQin":"父母",
        "liuShen":"青龙", "shiYing":"应", "伏神": null,
        "flags": {"旬空": false, "月破": false, "日冲": false} },
      { "position": 4, "yinYang": "yang", "moving": null,
        "纳甲": {"干":"壬","支":"午"}, "wuXing":"火", "liuQin":"官鬼",
        "liuShen":"朱雀", "shiYing": null, "伏神": null,
        "flags": {"旬空": true, "月破": false, "日冲": false} },
      { "position": 5, "yinYang": "yang", "moving": null,
        "纳甲": {"干":"壬","支":"申"}, "wuXing":"金", "liuQin":"兄弟",
        "liuShen":"勾陈", "shiYing": null, "伏神": null,
        "flags": {"旬空": false, "月破": false, "日冲": false} },
      { "position": 6, "yinYang": "yang", "moving": null,
        "纳甲": {"干":"壬","支":"戌"}, "wuXing":"土", "liuQin":"父母",
        "liuShen":"螣蛇", "shiYing": null, "伏神": null,
        "flags": {"旬空": false, "月破": false, "日冲": false} }
    ]
  },
  "changed": null,
  "yongShen": { "liuQin": "妻财", "positions": [2], "chosen": 2, "两现": false, "伏藏": false },
  "assessment": {
    "用神": { "liuQin":"妻财", "position":2, "wangShuai":"死",
              "得令":false, "得日":true, "被日冲":false,
              "旬空":false, "月破":true, "发动":false, "huiTou": null },
    "原神": { "liuQin":"子孙", "position":1, "wangShuai":"相",
              "得令":true, "得日":false, "被日冲":false,
              "旬空":false, "月破":false, "发动":false, "huiTou": null },
    "忌神": { "liuQin":"兄弟", "position":5, "wangShuai":"旺",
              "得令":true, "得日":false, "被日冲":true,
              "旬空":false, "月破":false, "发动":false, "huiTou": null }
  }
}
```

> 注：以上 assessment 旺衰已由引擎按"月令旺相休囚死"算出并经测试核验：申(金)月 → 用神妻财木**死**、原神子孙水**相**、忌神兄弟金**旺**；用神逢月破(申冲寅)、得日(日辰寅木同我)；忌神被日冲(日辰寅冲申)。（初版示例曾误标为"囚/死"，已修正。）引擎只给到这一层事实，是否"不利"由解读层综合判断。

---

## 四、设计要点回顾

- **assessment 也结构化**：把旺衰/空破/回头生克做成枚举字段，AI 只能在既定事实上推理，无法"重新理解"卦理（事实锁定的技术保证）。
- **原神/忌神随用神而定**：原神＝生用神之六亲、忌神＝克用神之六亲，引擎据用神五行自动定位。
- **变卦 lines 重新装卦**：变卦是一个完整的卦，其纳甲/六亲按变卦本身重排；动爻的"回头生克"记录在本卦该爻的 assessment.huiTou。
- **前端可纯渲染**：primary.lines + changed 即可画出完整卦盘，无需任何额外计算。
