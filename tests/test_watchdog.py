import pytest

from stock_engine.session import ExchangeSession
from stock_engine.watchdog import classroom_demo, report, simulate


def test_warmup_and_actual_execution_features():
    session = ExchangeSession()
    session.place_order("S", "ACME", "SELL", 30, "100")
    assert session.observations == []
    session.place_order("B", "ACME", "BUY", 20, "100")
    row = session.observations[0]
    assert row["quantity"] == 20
    assert row["ask_depth"] == 30
    assert row["trade_ids"] == [1]
    assert report(session)["status"] == "warming_up"
    restored = ExchangeSession.from_dict(session.to_dict())
    assert restored.observations[0]["quantity"] == 20


def test_demo_holdout_metrics_and_reproducibility():
    session, demo = classroom_demo()
    _, again = classroom_demo()
    evaluation = demo["evaluation"]
    assert len(session.engine.trades()) == 90
    assert evaluation["heldout"] == 50
    assert evaluation["training"] == 40
    assert evaluation["true_positives"] + evaluation["false_negatives"] == 10
    assert evaluation["false_positives"] + evaluation["true_negatives"] == 40
    assert evaluation["true_positives"] > 0
    assert evaluation == again["evaluation"]
    assert report(session)["scored"] == 50
    # Replay rebuilds features from commands; imported fake telemetry is ignored.
    payload = session.to_dict()
    payload["observations"] = [{"quantity": 999}]
    assert report(ExchangeSession.from_dict(payload))["flagged"] == demo["watchdog"]["flagged"]


@pytest.mark.parametrize("scenario", ["normal", "bull", "bear", "volatile", "low_liquidity", "high_liquidity"])
def test_simulator_executes_real_orders(scenario):
    session = ExchangeSession()
    result = simulate(session, 100, scenario, "ACME", 42, 50, 10)
    assert len(session.events) == result["commands"] == 100
    assert result["trades"] == len(session.engine.trades())
    assert result["seconds"] > 0
    assert result["filled_shares"] == sum(trade.quantity for trade in session.engine.trades())
