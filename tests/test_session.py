import json
from datetime import datetime, timezone
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


def test_bundled_order_lifecycle_fixture():
    session = ExchangeSession.from_file(Path(__file__).resolve().parents[1] / "scenarios" / "order-lifecycle.json")
    assert len(session.events) == 9
    assert session.engine.symbol_stats("ACME")["volume"] == 190
    assert session.engine.symbol_stats("TECH")["volume"] == 40


def test_recorded_execution_times_are_preserved_including_amendment():
    session = ExchangeSession()
    moment = datetime(2026,9,30,12,0,tzinfo=timezone.utc)
    session.place_order("S","AAA","SELL",5,"100",timestamp=moment)
    session.place_order("B","AAA","BUY",3,"99",timestamp=moment)
    session.modify_order("B",3,"100",timestamp=moment)
    restored = ExchangeSession.from_dict(session.to_dict())
    assert restored.engine.trades() == session.engine.trades()
    assert restored.observations == session.observations
    assert restored.engine.trades()[0].timestamp == moment


def test_legacy_execution_time_is_unknown_not_replay_time():
    payload = {"version":1,"events":[{"type":"place","order_id":identifier,"symbol":"AAA","side":side,"quantity":1,"price":"100"} for identifier,side in [("S","SELL"),("B","BUY")]]}
    restored = ExchangeSession.from_dict(payload)
    assert restored.engine.trades()[0].timestamp is None
    assert ExchangeSession.from_dict(restored.to_dict()).engine.trades() == restored.engine.trades()


@pytest.mark.parametrize("timestamp",["invalid","2026-09-30T12:00:00",123])
def test_invalid_saved_timestamps_are_rejected(timestamp):
    payload = {"version":2,"events":[{"type":"place","order_id":"A","symbol":"AAA","side":"BUY","quantity":1,"price":"100","timestamp":timestamp}]}
    with pytest.raises(ValueError,match="invalid event 1"):
        ExchangeSession.from_dict(payload)
