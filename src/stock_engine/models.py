from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass(slots=True)
class Order:
    order_id: str
    symbol: str
    side: Side
    quantity: int
    remaining: int
    price: Decimal | None
    sequence: int


@dataclass(frozen=True, slots=True)
class Trade:
    trade_id: int
    symbol: str
    price: Decimal
    quantity: int
    buy_order_id: str
    sell_order_id: str
    timestamp: datetime | None = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True, slots=True)
class OrderResult:
    order_id: str
    filled: int
    remaining: int
    resting: bool
    trades: tuple[Trade, ...] = field(default_factory=tuple)
