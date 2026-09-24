import json
from pathlib import Path

import pytest

from stock_engine import ExchangeSession


def test_export_and_replay_preserve_book_and_trades():
    session = ExchangeSession()
    session.place_order("S1", "AAA", "SELL", 10, "100.00")
    session.place_order("B1", "AAA", "BUY", 4, "101.00")
    session.place_order("B2", "AAA", "BUY", 8, "99.00")
    session.modify_order("B2", 5, "100.00")
    session.cancel_order("S1")

    restored = ExchangeSession.from_json(session.to_json())

    assert restored.to_dict() == session.to_dict()
    assert restored.engine.order_book("AAA") == session.engine.order_book("AAA")
    assert restored.engine.symbol_stats("AAA") == session.engine.symbol_stats("AAA")
    assert [(trade.price, trade.quantity) for trade in restored.engine.trades()] == [
        (trade.price, trade.quantity) for trade in session.engine.trades()
    ]


def test_invalid_scenario_gives_event_number():
    scenario = {"version": 1, "events": [
        {"type": "place", "order_id": "A", "symbol": "AAA", "side": "BUY", "quantity": 5, "price": "10.00"},
        {"type": "cancel", "order_id": "missing"},
    ]}
    with pytest.raises(ValueError, match="invalid event 2"):
        ExchangeSession.from_json(json.dumps(scenario))


def test_bundled_demo_scenario():
    session = ExchangeSession.from_file(Path(__file__).resolve().parents[1] / "scenarios" / "demo.json")
    assert len(session.events) == 9
    assert session.engine.symbol_stats("ACME")["volume"] == 190
    assert session.engine.symbol_stats("TECH")["volume"] == 40
