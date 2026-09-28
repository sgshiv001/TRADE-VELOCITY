"""Long-only paper portfolio whose fills come from the matching engine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json

from .models import OrderResult, Side
from .session import ExchangeSession

CENT = Decimal("0.01")


def money(value) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("amount must be finite and positive") from exc
    if not parsed.is_finite() or parsed <= 0:
        raise ValueError("amount must be finite and positive")
    rounded = parsed.quantize(CENT)
    if rounded <= 0:
        raise ValueError("amount must be at least one paisa")
    return rounded


@dataclass
class Position:
    quantity: int = 0
    cost: Decimal = Decimal(0)

    @property
    def average_cost(self) -> Decimal:
        return self.cost / self.quantity if self.quantity else Decimal(0)


class PaperBroker:
    """Independent paper exchange: maker liquidity is simulated, cash is virtual."""

    def __init__(self, initial_cash=1_000_000):
        self.initial_cash = money(initial_cash)
        self.cash = self.initial_cash
        self.realized_pnl = Decimal(0)
        self.positions: dict[str, Position] = {}
        self.exchange = ExchangeSession()
        self.fills: list[dict] = []
        self.equity_history: list[dict] = []
        self.events: list[dict] = []
        self._next_id = 0

    def _id(self, prefix: str) -> str:
        self._next_id += 1
        return f"{prefix}-{self._next_id}"

    def seed_liquidity(self, symbol: str, reference_price, shares: int = 5000, spread=Decimal("0.001")) -> None:
        reference = money(reference_price)
        if not isinstance(shares, int) or isinstance(shares, bool) or shares <= 0:
            raise ValueError("liquidity shares must be a positive integer")
        spread = Decimal(str(spread))
        if not spread.is_finite() or spread < 0 or spread >= 1:
            raise ValueError("spread must be between zero (inclusive) and one")
        symbol, _, _ = self.exchange.engine._validate(symbol, Side.BUY, shares, reference)
        # This broker only submits market orders for users, so all open orders
        # are synthetic makers and may be replaced safely when quotes change.
        for order in self.exchange.engine.active_orders(symbol):
            self.exchange.cancel_order(order["order_id"])
        for level in range(3):
            gap = max(CENT, (reference * spread * (level + 1)).quantize(CENT))
            self.exchange.place_order(self._id("LP-B"), symbol, "BUY", shares, max(CENT, reference - gap))
            self.exchange.place_order(self._id("LP-S"), symbol, "SELL", shares, reference + gap)
        self.events.append({"type": "liquidity", "symbol": symbol, "price": str(reference),
                            "shares": shares, "spread": str(spread)})

    def place_market_order(self, symbol: str, side: Side | str, quantity: int, note: str = "Paper trade") -> OrderResult:
        symbol, side, _ = self.exchange.engine._validate(symbol, side, quantity, None)
        position = self.positions.get(symbol, Position())
        if side == Side.SELL and quantity > position.quantity:
            raise ValueError(f"only {position.quantity} shares are available to sell")
        book = self.exchange.engine.order_book(symbol, depth=len(self.exchange.engine.active_orders(symbol)))
        remaining = quantity
        estimate = Decimal(0)
        for level in book["asks"] if side == Side.BUY else book["bids"]:
            shares = min(remaining, level["quantity"])
            estimate += Decimal(level["price"]) * shares
            remaining -= shares
            if not remaining:
                break
        if remaining == quantity:
            raise ValueError("no paper liquidity available; refresh the paper order book")
        if side == Side.BUY and estimate > self.cash:
            raise ValueError("insufficient virtual cash for the available fills")
        result = self.exchange.place_order(self._id("PAPER"), symbol, side, quantity)
        position = self.positions.setdefault(symbol, Position())
        for trade in result.trades:
            amount = trade.price * trade.quantity
            realized = Decimal(0)
            if side == Side.BUY:
                self.cash -= amount
                position.cost += amount
                position.quantity += trade.quantity
            else:
                cost = position.average_cost * trade.quantity
                realized = amount - cost
                position.quantity -= trade.quantity
                position.cost -= cost
                if not position.quantity:
                    position.cost = Decimal(0)
                self.cash += amount
                self.realized_pnl += realized
            self.fills.append({
                "Time (UTC)": trade.timestamp.isoformat(), "Order": result.order_id, "Symbol": symbol,
                "Side": side.value, "Shares": trade.quantity, "Price (₹)": str(trade.price),
                "Realized P/L (₹)": str(realized.quantize(CENT)), "Note": note,
            })
        self.events.append({"type": "market", "symbol": symbol, "side": side.value, "quantity": quantity, "note": note})
        return result

    def valuation(self, marks: dict) -> dict:
        rows = []
        market_value = Decimal(0)
        cost_basis = Decimal(0)
        for symbol, position in self.positions.items():
            if not position.quantity:
                continue
            if symbol not in marks:
                raise ValueError(f"valuation price missing for {symbol}")
            mark = money(marks[symbol])
            value = mark * position.quantity
            pnl = value - position.cost
            market_value += value
            cost_basis += position.cost
            rows.append({"Symbol": symbol, "Shares": position.quantity, "Average cost (₹)": float(position.average_cost),
                         "Mark price (₹)": float(mark), "Cost basis (₹)": float(position.cost),
                         "Market value (₹)": float(value), "Unrealized P/L (₹)": float(pnl),
                         "Return %": float(pnl / position.cost * 100)})
        unrealized = market_value - cost_basis
        equity = self.cash + market_value
        return {"cash": self.cash, "market_value": market_value, "equity": equity, "realized_pnl": self.realized_pnl,
                "unrealized_pnl": unrealized, "total_pnl": equity - self.initial_cash, "holdings": rows}

    def record_equity(self, marks: dict) -> None:
        valuation = self.valuation(marks)
        self.equity_history.append({"Time": datetime.now(timezone.utc).isoformat(), "Equity (₹)": float(valuation["equity"]),
                                    "P/L (₹)": float(valuation["total_pnl"])})

    def to_dict(self) -> dict:
        return json.loads(json.dumps({"version": 1, "initial_cash": str(self.initial_cash),
                                      "events": self.events, "equity_history": self.equity_history}))

    @classmethod
    def from_dict(cls, data: dict) -> PaperBroker:
        if data.get("version") != 1 or not isinstance(data.get("events"), list):
            raise ValueError("invalid paper portfolio snapshot")
        broker = cls(data["initial_cash"])
        for event in data["events"]:
            if event["type"] == "liquidity":
                broker.seed_liquidity(event["symbol"], event["price"], event["shares"], event["spread"])
            elif event["type"] == "market":
                broker.place_market_order(event["symbol"], event["side"], event["quantity"], event["note"])
            else:
                raise ValueError("invalid paper portfolio event")
        broker.equity_history = data.get("equity_history", [])
        return broker
