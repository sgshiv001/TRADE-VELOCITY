import random
import numpy as np
import pytest
from stock_engine.session import ExchangeSession
from stock_engine.watchdog import BASELINE, FEATURES, CalibratedBaseline, ExecutionMonitor, Settings, report


def test_warmup_only_counts_executions():
    session = ExchangeSession()
    session.place_order("S", "RELIANCE", "SELL", 30, "100")
    assert session.observations == []
    session.place_order("B", "RELIANCE", "BUY", 20, "100")
    row = session.observations[0]
    assert row["quantity"] == 20 and row["ask_depth"] == 30
    assert row["trade_ids"] == [1]
    assert report(session)["status"] == "warming_up"
    assert ExchangeSession.from_dict(session.to_dict()).observations[0]["quantity"] == 20


def test_later_activity_does_not_change_baseline_or_old_scores():
    session = ExchangeSession()
    rng = random.Random(42)
    for index in range(65):
        quantity = rng.randrange(10, 50)
        price = f"{100 + rng.randrange(-2, 3) / 10:.2f}"
        session.place_order(f"S-{index}", "RELIANCE", "SELL", quantity, price)
        session.place_order(f"B-{index}", "RELIANCE", "BUY", quantity, price)
    before = report(session)
    assert before["baseline_size"] == 40 and before["scored"] == 25
    session.place_order("LATER-S", "RELIANCE", "SELL", 5000, "130")
    session.place_order("LATER-B", "RELIANCE", "BUY", 5000, "130")
    after = report(session)
    assert [row["score"] for row in after["timeline"][:-1]] == [row["score"] for row in before["timeline"]]
    assert after["timeline"][-1]["needs_review"]
    payload = session.to_dict()
    payload["observations"] = [{"quantity": 999}]
    assert report(ExchangeSession.from_dict(payload))["flagged"] == after["flagged"]


def matched(session, identifier, quantity, price):
    session.place_order(f"S-{identifier}","RELIANCE","SELL",quantity,price)
    session.place_order(f"B-{identifier}","RELIANCE","BUY",quantity,price)


def test_previously_missed_repeated_baseline_is_detected_by_explicit_guard():
    session = ExchangeSession()
    for index in range(45):
        matched(session,str(index),10+index%17,f"{100+(index%5-2)/10:.2f}")
    matched(session,"LARGE",5000,"130")
    result = report(session)
    last = result["timeline"][-1]
    assert last["needs_review"]
    assert "robust_guard" in last["detectors"]
    assert "price_change_pct" in last["reasons"]
    assert result["model_version"] == "execution-watchdog-v3"
    assert result["calibration"]["fit_observations"] == 24
    assert result["calibration"]["cutoff_observations"] == 16


def test_constant_baseline_has_no_tiny_change_alarm_but_detects_extremes():
    session = ExchangeSession()
    for index in range(BASELINE):
        matched(session,str(index),25,"100")
    matched(session,"TINY",26,"100.01")
    monitor = ExecutionMonitor()
    before = monitor.report(session.observations,"RELIANCE")
    assert before["timeline"][-1]["needs_review"] is False
    assert "Low-variation" in before["calibration"]["baseline_warning"]
    matched(session,"LARGE",5000,"130")
    after = monitor.report(session.observations,"RELIANCE")
    assert after["timeline"][-1]["needs_review"]
    assert after["timeline"][0] == before["timeline"][0]
    assert all(0 <= row["score"] <= 1 for row in after["timeline"])


def test_cutoff_observations_are_not_used_to_fit_forest_or_robust_statistics():
    rng = np.random.default_rng(42)
    matrix = np.abs(rng.normal(10,2,(BASELINE,len(FEATURES))))
    first = CalibratedBaseline(matrix)
    altered = matrix.copy()
    altered[24:] *= 100
    second = CalibratedBaseline(altered)
    np.testing.assert_array_equal(first.center,second.center)
    np.testing.assert_array_equal(first.scale,second.scale)
    np.testing.assert_array_equal(first.model.score_samples(matrix[:5]),second.model.score_samples(matrix[:5]))
    assert second.calibration_guard_max > first.calibration_guard_max


def test_unchanged_reports_reuse_model_and_return_independent_copies(monkeypatch):
    session = ExchangeSession()
    for index in range(41):
        matched(session,str(index),20+index%8,"100")
    monitor = ExecutionMonitor()
    first = monitor.report(session.observations,"RELIANCE")
    model = monitor.models["RELIANCE"][1]
    monkeypatch.setattr(model.model,"fit",lambda *args:pytest.fail("Baseline was refitted"))
    first["timeline"][0]["score"] = -100
    second = monitor.report(session.observations,"RELIANCE")
    assert second["timeline"][0]["score"] >= 0
    matched(session,"NEXT",20,"100")
    assert monitor.report(session.observations,"RELIANCE")["scored"] == 2


@pytest.mark.parametrize("settings", [{"forest_margin":float("nan")},{"guard_floor":0},{"guard_padding":-1},
                                      {"size_multiplier":float("inf")},{"forest_confirmation":-1}])
def test_invalid_calibration_parameters_are_rejected(settings):
    with pytest.raises(ValueError,match="invalid watchdog calibration"):
        Settings(**settings)


def test_high_volume_previous_miss_is_caught_by_raw_envelope():
    from stock_engine.calibration import workload
    rows,_ = workload("high_volume",2009)
    result = ExecutionMonitor().report(rows,"RELIANCE")
    last = result["timeline"][-1]
    assert last["price_change_pct"] == 0
    assert last["needs_review"]
    assert "size_envelope" in last["detectors"]
    assert last["max_count_ratio"] > result["calibration"]["size_multiplier"]
