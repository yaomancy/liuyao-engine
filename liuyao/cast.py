"""起卦/成卦：三钱六掷成本卦 + 变卦（design D3）。

原则：交互（陀螺仪/长按蓄力）只提供熵与仪式感；每枚铜钱的最终结果由
**CSPRNG**（secrets）产出，保证四象分布 1/8:3/8:3/8:1/8 的统计公平，
且不可被传感器信号操纵。

铜钱约定：背=1、字=0。成爻遵《卜筮正宗》「以钱代蓍法」：一背为单(少阳·阳)、
**两背由来拆**(少阴·阴)、三背为重(老阳·动)、纯字为交(老阴·动)。故阴阳由背数奇偶定
（奇背=阳、偶背=阴），非"背越多越阳"。
"""
from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass


@dataclass(frozen=True)
class CastResult:
    bits: str                       # 本卦 6 位二进制，自下而上（初→上）
    moving: dict[int, str]          # {爻位(1-6): '老阳'|'老阴'}
    tosses: tuple[tuple[int, int, int], ...]  # 每爻三枚铜钱(背=1/字=0)，初→上

    @property
    def changed_bits(self) -> str | None:
        """变卦：翻转所有动爻位；无动爻则 None。"""
        if not self.moving:
            return None
        return "".join(
            str(1 - int(c)) if (i + 1) in self.moving else c
            for i, c in enumerate(self.bits)
        )


def yao_from_coins(coins: tuple[int, int, int]) -> tuple[str, str | None]:
    """三枚铜钱(背=1) → (阴阳位 '1'/'0', 动爻类型或 None)。遵《卜筮正宗》单拆重交：

    3背=重=老阳(动·阳变阴) 1/8 ｜ 1背=单=少阳(阳) 3/8 ｜
    2背=拆=少阴(阴) 3/8 ｜ 0背(纯字)=交=老阴(动·阴变阳) 1/8。
    （阴阳按背数奇偶：奇背为阳、偶背为阴；非"背越多越阳"。）
    """
    bei = sum(coins)
    if bei == 3:
        return ("1", "老阳")     # 重 三背 阳动
    if bei == 2:
        return ("0", None)       # 拆 两背 少阴(阴) —「两背由来拆」
    if bei == 1:
        return ("1", None)       # 单 一背 少阳(阳)
    return ("0", "老阴")         # 交 纯字 阴动


def lines_from_tosses(
    tosses: tuple[tuple[int, int, int], ...],
) -> tuple[str, dict[int, str]]:
    """由六次投掷结果（初→上）确定性地成本卦 + 动爻。"""
    if len(tosses) != 6:
        raise ValueError(f"需恰好六掷，收到 {len(tosses)}")
    bits = ""
    moving: dict[int, str] = {}
    for i, coins in enumerate(tosses):
        bit, mv = yao_from_coins(coins)
        bits += bit
        if mv:
            moving[i + 1] = mv
    return bits, moving


def _csprng_coin(entropy: bytes) -> int:
    """一枚铜钱：CSPRNG 产出 0/1。交互熵被混入但不改变均匀性。"""
    fresh = secrets.token_bytes(16)          # os CSPRNG，均匀且主导
    if entropy:
        fresh = hashlib.sha256(entropy + fresh).digest()  # 混熵；输出仍均匀
    return fresh[0] & 1


def toss_line(entropy: bytes | None = None) -> tuple[tuple[int, int, int], str, str | None]:
    """摇一爻：三枚 CSPRNG 铜钱 → (coins, 阴阳位 '1'/'0', 动爻类型或 None)。

    逐爻起卦（/cast_line）专用：与 toss() 同一随机源、同一分布，仅一次产一爻。
    交互熵混入但不决定结果（最终由 CSPRNG 保证 1/8:3/8:3/8:1/8 公平）。
    """
    ent = entropy or b""
    coins = tuple(_csprng_coin(ent) for _ in range(3))
    bit, mv = yao_from_coins(coins)
    return coins, bit, mv


def toss(entropy: bytes | None = None) -> CastResult:
    """摇一卦：六爻、每爻三枚 CSPRNG 铜钱。

    entropy: 来自交互（陀螺仪运动/蓄力时长等）的熵，仅作仪式与混入，
             不决定结果（最终由 CSPRNG 保证公平）。
    """
    ent = entropy or b""
    tosses = tuple(
        tuple(_csprng_coin(ent) for _ in range(3)) for _ in range(6)
    )
    bits, moving = lines_from_tosses(tosses)
    return CastResult(bits=bits, moving=moving, tosses=tosses)
