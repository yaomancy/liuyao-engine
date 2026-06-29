"""历法层：把"起卦时刻"换算成四柱干支 + 旬空（引擎地基）。

法度要点（见 design D5）：
- 月建按**节气**分月（非农历月）：sxtwl 的 getMonthGZ 本身即节气月柱。
- **子时换日**：23:00 起算次日日柱（子初换日，术数主流惯例），非 00:00。
- 起卦时刻用设备本地时间；真太阳时校正后置。
- 日柱算错一天则旺衰/旬空全错——故此层是引擎正确性的根基。

依赖 sxtwl（寿星天文历）做天文级干支/节气计算；lunar-python 作交叉验证（见 tests）。
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass

import sxtwl

GAN = "甲乙丙丁戊己庚辛壬癸"   # 十天干 index 0-9
ZHI = "子丑寅卯辰巳午未申酉戌亥"  # 十二地支 index 0-11


@dataclass(frozen=True)
class GanZhi:
    """一柱干支。gan/zhi 为索引，便于引擎做生克计算。"""

    gan: int  # 天干 0-9
    zhi: int  # 地支 0-11

    def __str__(self) -> str:
        return f"{GAN[self.gan]}{ZHI[self.zhi]}"


@dataclass(frozen=True)
class FourPillars:
    """年/月/日/时 四柱 + 旬空。"""

    year: GanZhi
    month: GanZhi
    day: GanZhi
    hour: GanZhi
    xunkong: tuple[int, int]  # 当旬两个空亡地支（索引）

    @property
    def month_branch(self) -> int:
        """月建（月支索引）——旺衰之"令"。"""
        return self.month.zhi

    def __str__(self) -> str:
        kong = f"{ZHI[self.xunkong[0]]}{ZHI[self.xunkong[1]]}"
        return f"{self.year} {self.month} {self.day} {self.hour}（旬空：{kong}）"


def _hour_branch_index(hour: int) -> int:
    """时辰地支索引。子时 23:00–01:00 → 子(0)。

    23、0 点皆为子；1–2 丑；…；11–12 午。公式：((hour+1)//2) % 12。
    """
    return ((hour + 1) // 2) % 12


def _hour_gan_index(day_gan: int, hour_branch: int) -> int:
    """五鼠遁起时干：时干 = (日干 % 5 * 2 + 时支) % 10。

    甲己起甲子、乙庚起丙子、丙辛起戊子、丁壬起庚子、戊癸起壬子。
    注意：子时换日后，day_gan 应为"换日后"的日干。
    """
    return (day_gan % 5 * 2 + hour_branch) % 10


def _to_jd(year: int, month: int, day: int, hour: int, minute: int) -> float:
    """把本地时刻转为儒略日（与 sxtwl 的节气 JD 同一坐标，可直接比较）。"""
    t = sxtwl.Time()
    t.Y, t.M, t.D, t.h, t.m, t.s = year, month, day, hour, minute, 0
    return sxtwl.toJD(t)


def _xunkong(day: GanZhi) -> tuple[int, int]:
    """旬空（空亡）两支。

    旬首甲所在地支 z0 = (日支 - 日干) % 12；空亡 = z0 前两位（z0-2, z0-1）。
    例：庚寅日 g=6,z=2 → z0=(2-6)%12=8(申)=甲申旬 → 空 午(6)未(7)。
    """
    z0 = (day.zhi - day.gan) % 12
    return ((z0 - 2) % 12, (z0 - 1) % 12)


_SXTWL_REF_OFFSET = 480  # sxtwl 节气/干支参照系 = 东经120°北京时（UTC+8），实证见 fix-overseas-casttime-tz


def ganzhi_from_str(s: str) -> GanZhi:
    """解析一柱干支字符串（如 "辛巳"）为 GanZhi 索引。"""
    s = s.strip()
    if len(s) != 2 or s[0] not in GAN or s[1] not in ZHI:
        raise ValueError(f"非法干支：{s!r}（应为 天干+地支，如 辛巳）")
    return GanZhi(GAN.index(s[0]), ZHI.index(s[1]))


def four_pillars_from_ganzhi(year: str, month: str, day: str,
                             hour: str | None = None) -> FourPillars:
    """直接按干支建四柱（用于古籍卦例：原书以"某月某日"干支记，非阳历）。

    旬空由日柱按法度推得（_xunkong）；时柱缺省按日干五鼠遁起子时。
    年/月柱直接取给定干支（古例的月建即题面所书，无需反推节气）。
    """
    day_p = ganzhi_from_str(day)
    if hour:
        hour_p = ganzhi_from_str(hour)
    else:
        hour_p = GanZhi(_hour_gan_index(day_p.gan, 0), 0)  # 缺省子时
    return FourPillars(
        year=ganzhi_from_str(year), month=ganzhi_from_str(month),
        day=day_p, hour=hour_p, xunkong=_xunkong(day_p),
    )


def compute_four_pillars(
    year: int, month: int, day: int, hour: int, minute: int = 0,
    tz_offset_minutes: int = _SXTWL_REF_OFFSET,
) -> FourPillars:
    """由起卦的本地时刻 + 时区偏移计算四柱干支 + 旬空。

    tz_offset_minutes：本地相对 UTC 的偏移（本地 = UTC + offset；东八区 +480、
        纽约冬季 -300）。缺省 +480 等价于"按北京时间处理"，与既往行为一致。

    法度（见 fix-overseas-casttime-tz/design）：
    - 日柱/时柱取**求测人当地墙钟**（"当时当地"）：子时换日 hour>=23 按次日，
      时柱用换日后日干起五鼠遁，时支恒为子。
    - 年/月柱交节是**全球绝对事件**：把本地时刻整体换算为等效北京民用时刻
      （含日期）后再判交节，使任意时区下同一绝对瞬间得到相同年/月柱。
    """
    if not (0 <= hour <= 23):
        raise ValueError(f"hour 必须在 0–23，收到 {hour}")

    # 日柱/时柱：当地墙钟 + 子时换日（23:00 起算次日，子初换日）——不随时区换算
    eff = datetime.date(year, month, day)
    if hour >= 23:
        eff += datetime.timedelta(days=1)
    day_obj = sxtwl.fromSolar(eff.year, eff.month, eff.day)
    d_gz = day_obj.getDayGZ()
    day_pillar = GanZhi(d_gz.tg, d_gz.dz)
    hb = _hour_branch_index(hour)
    hour_pillar = GanZhi(_hour_gan_index(day_pillar.gan, hb), hb)

    # 年/月柱：先把本地时刻整体换算为等效北京民用时刻（sxtwl 参照系=北京），
    # 再按"交节精确时刻"判定。海外用户的节气挂在北京日期上，故须含日期一起归位，
    # 否则用本地日期查不到当天的交节（漏判）。东八区位移为 0，等价现状。
    bj = datetime.datetime(year, month, day, hour, minute) + datetime.timedelta(
        minutes=_SXTWL_REF_OFFSET - tz_offset_minutes
    )
    civil = sxtwl.fromSolar(bj.year, bj.month, bj.day)
    ym_day = civil
    if civil.hasJieQi() and civil.getJieQi() % 2 == 1:
        if _to_jd(bj.year, bj.month, bj.day, bj.hour, bj.minute) < civil.getJieQiJD():
            prev = bj.date() - datetime.timedelta(days=1)
            ym_day = sxtwl.fromSolar(prev.year, prev.month, prev.day)
    y_gz, m_gz = ym_day.getYearGZ(), ym_day.getMonthGZ()

    return FourPillars(
        year=GanZhi(y_gz.tg, y_gz.dz),
        month=GanZhi(m_gz.tg, m_gz.dz),
        day=day_pillar,
        hour=hour_pillar,
        xunkong=_xunkong(day_pillar),
    )
