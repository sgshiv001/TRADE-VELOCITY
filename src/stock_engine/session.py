"""Replayable exchange sessions for demos, experiments, and dashboard export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .engine import MatchingEngine
from .models import OrderResult, Side


class ExchangeSession:
    """Record successful user commands and replay them into a fresh engine."""

    VERSION = 1

    def __init__(self):
        self.engine = MatchingEngine()
        self.events: list[dict[str, Any]] = []

    def place_order(self, order_id: str, symbol: str, side: Side | str, quantity: int, price: str | int | None = None) -> OrderResult:
        result = self.engine.place_order(order_id, symbol, side, quantity, price)
        self.events.append({
            "type": "place", "order_id": order_id, "symbol": symbol.upper(),
            "side": Side(side.upper() if isinstance(side, str) else side).value,
            "quantity": quantity, "price": str(price) if price is not None else None,
        })
        return result

    def cancel_order(self, order_id: str) -> bool:
        canceled = self.engine.cancel_order(order_id)
        if canceled:
            self.events.append({"type": "cancel", "order_id": order_id})
        return canceled

    def modify_order(self, order_id: str, quantity: int, price: str | int) -> OrderResult:
        result = self.engine.modify_order(order_id, quantity, price)
        self.events.append({"type": "modify", "order_id": order_id, "quantity": quantity, "price": str(price)})
        return result

    def to_dict(self) -> dict[str, Any]:
        return {"version": self.VERSION, "events": [event.copy() for event in self.events]}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2) + "\n"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExchangeSession:
        if not isinstance(data, dict) or data.get("version") != cls.VERSION or not isinstance(data.get("events"), list):
            raise ValueError("scenario must contain version 1 and an events list")
        session = cls()
        for index, event in enumerate(data["events"], 1):
            if not isinstance(event, dict):
                raise ValueError(f"event {index} must be an object")
            kind = event.get("type")
            try:
                if kind == "place":
                    session.place_order(event["order_id"], event["symbol"], event["side"], event["quantity"], event.get("price"))
                elif kind == "cancel":
                    if not session.cancel_order(event["order_id"]):
                        raise ValueError("order is not active")
                elif kind == "modify":
                    session.modify_order(event["order_id"], event["quantity"], event["price"])
                else:
                    raise ValueError(f"unknown event type: {kind}")
            except (KeyError, TypeError, ValueError) as exc:
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
