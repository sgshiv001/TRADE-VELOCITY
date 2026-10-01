"""Persistent exchange sessions and command replay."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .engine import CURRENT_TIME, MatchingEngine
from .models import OrderResult, Side


class ExchangeSession:
    """Record successful user commands and replay them into a fresh engine."""

    VERSION = 2

    def __init__(self):
        self.engine = MatchingEngine()
        self.events: list[dict[str, Any]] = []
        # Derived from successful commands; replay reconstructs this telemetry.
        self.observations: list[dict[str, Any]] = []

    def _observe(self, result: OrderResult, symbol: str, quantity: int, book: dict) -> None:
        if not result.trades:
            return
        symbol = symbol.upper()
        previous = next((row for row in reversed(self.observations) if row["symbol"] == symbol), None)
        volume = sum(trade.quantity for trade in result.trades)
        price = float(sum(trade.price * trade.quantity for trade in result.trades) / volume)
        bids = sum(level["quantity"] for level in book["bids"])
        asks = sum(level["quantity"] for level in book["asks"])
        self.observations.append({
            "symbol": symbol, "event": len(self.events), "order_id": result.order_id,
            "trade_ids": [trade.trade_id for trade in result.trades],
            "timestamp": result.trades[-1].timestamp.isoformat() if result.trades[-1].timestamp else None,
            "price": price, "quantity": volume,
            "price_change_pct": (price / previous["price"] - 1) * 100 if previous else 0.0,
            "execution_count": len(result.trades), "submitted_quantity": quantity,
            "bid_depth": bids, "ask_depth": asks,
            "depth_imbalance": (bids - asks) / max(1, bids + asks),
        })

    def place_order(self, order_id: str, symbol: str, side: Side | str, quantity: int, price: str | int | None = None, *, timestamp=CURRENT_TIME) -> OrderResult:
        timestamp = datetime.now(timezone.utc) if timestamp is CURRENT_TIME else timestamp
        book = self.engine.order_book(symbol, 30)
        result = self.engine.place_order(order_id, symbol, side, quantity, price, timestamp=timestamp)
        self.events.append({
            "type": "place", "order_id": order_id, "symbol": symbol.upper(),
            "side": Side(side.upper() if isinstance(side, str) else side).value,
            "quantity": quantity, "price": str(price) if price is not None else None,
            "timestamp": timestamp.isoformat() if timestamp else None,
        })
        self._observe(result, symbol, quantity, book)
        return result

    def cancel_order(self, order_id: str) -> bool:
        canceled = self.engine.cancel_order(order_id)
        if canceled:
            self.events.append({"type": "cancel", "order_id": order_id})
        return canceled

    def modify_order(self, order_id: str, quantity: int, price: str | int, *, timestamp=CURRENT_TIME) -> OrderResult:
        timestamp = datetime.now(timezone.utc) if timestamp is CURRENT_TIME else timestamp
        order = next((order for order in self.engine.active_orders() if order["order_id"] == order_id), None)
        book = self.engine.order_book(order["symbol"], 30) if order else None
        result = self.engine.modify_order(order_id, quantity, price, timestamp=timestamp)
        self.events.append({"type": "modify", "order_id": order_id, "quantity": quantity, "price": str(price), "timestamp": timestamp.isoformat() if timestamp else None})
        if book:
            self._observe(result, book["symbol"], quantity, book)
        return result

    def to_dict(self) -> dict[str, Any]:
        return {"version": self.VERSION, "events": [event.copy() for event in self.events]}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2) + "\n"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExchangeSession:
        if not isinstance(data, dict) or data.get("version") not in (1, cls.VERSION) or not isinstance(data.get("events"), list):
            raise ValueError("session must contain version 1 or 2 and an events list")
        session = cls()
        for index, event in enumerate(data["events"], 1):
            if not isinstance(event, dict):
                raise ValueError(f"event {index} must be an object")
            kind = event.get("type")
            try:
                timestamp = None
                if kind in ("place", "modify"):
                    if data["version"] == cls.VERSION and "timestamp" not in event:
                        raise ValueError("timestamp is required in version 2")
                    if event.get("timestamp") is not None:
                        timestamp = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
                        if timestamp.tzinfo is None:
                            raise ValueError("timestamp must include a timezone")
                        timestamp = timestamp.astimezone(timezone.utc)
                if kind == "place":
                    session.place_order(event["order_id"], event["symbol"], event["side"], event["quantity"], event.get("price"), timestamp=timestamp)
                elif kind == "cancel":
                    if not session.cancel_order(event["order_id"]):
                        raise ValueError("order is not active")
                elif kind == "modify":
                    session.modify_order(event["order_id"], event["quantity"], event["price"], timestamp=timestamp)
                else:
                    raise ValueError(f"unknown event type: {kind}")
            except (AttributeError, KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"invalid event {index}: {exc}") from exc
        return session

    @classmethod
    def from_json(cls, text: str) -> ExchangeSession:
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid scenario JSON: {exc.msg}") from exc
        return cls.from_dict(data)

    @classmethod
    def from_file(cls, path: str | Path) -> ExchangeSession:
        return cls.from_json(Path(path).read_text(encoding="utf-8"))

    def save(self, path: str | Path) -> None:
        Path(path).write_text(self.to_json(), encoding="utf-8")
