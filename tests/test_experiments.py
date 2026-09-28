import gc
import tracemalloc

import pytest

from stock_engine import MatchingEngine
from stock_engine.experiments import (
    Command, LinearMatchingEngine, compare_workload, execute, generate_workload,
    measure, measure_memory, verify_workload,
)


@pytest.mark.parametrize("name", ["mixed", "deep", "cancel"])
@pytest.mark.parametrize("count,symbols", [(2, 1), (33, 5), (300, 1)])
def test_comparison_workloads_are_deterministic_and_engines_agree(name, count, symbols):
    commands = generate_workload(name, count, seed=7, symbols=symbols)
    assert commands == generate_workload(name, count, seed=7, symbols=symbols)
    assert len(commands) == count
    trades, active = verify_workload(commands)
    if name == "deep":
        assert trades == count // 2
        assert active == 0
    elif name == "cancel":
        assert trades == 0
        assert active == count % 2


@pytest.mark.parametrize("engine_type", [MatchingEngine, LinearMatchingEngine])
def test_comparison_book_retains_fifo_and_resting_execution_prices(engine_type):
    engine = engine_type()
    engine.place_order("S1", "AAA", "SELL", 7, "100.00")
    engine.place_order("S2", "AAA", "SELL", 5, "100.00")
    engine.place_order("S3", "AAA", "SELL", 10, "101.00")
    result = engine.place_order("B1", "AAA", "BUY", 10, "102.00")
    assert [(trade.sell_order_id, trade.quantity, str(trade.price)) for trade in result.trades] == [
        ("S1", 7, "100.00"), ("S2", 3, "100.00"),
    ]
    assert engine.order_book("AAA")["asks"] == [
        {"price": "100.00", "quantity": 2, "orders": 1},
        {"price": "101.00", "quantity": 10, "orders": 1},
    ]


def test_comparison_records_each_engine_repeat_and_correct_outcome():
    rows = compare_workload("deep", 20, symbols=2, repeats=2)
    assert [(row["repeat"], row["engine"]) for row in rows] == [
        (1, "indexed"), (1, "linear"), (2, "linear"), (2, "indexed"),
    ]
    for row in rows:
        assert row["trades"] == 10
        assert row["open_orders"] == 0
        assert row["commands_per_second"] == 20 / row["seconds"]
        assert row["peak_traced_mb"] is None


def test_timing_and_tracing_restore_state_after_failed_command():
    invalid = [Command("place", ("BAD", "AAA", "BUY", 0, "100.00"))]
    enabled = gc.isenabled()
    with pytest.raises(ValueError):
        measure(invalid, "indexed")
    assert gc.isenabled() == enabled
    with pytest.raises(ValueError):
        measure_memory(invalid, "indexed")
    assert not tracemalloc.is_tracing()
    gc.disable()
    try:
        measure(generate_workload("mixed", 10), "linear")
        assert not gc.isenabled()
    finally:
        if enabled:
            gc.enable()


@pytest.mark.parametrize("args", [("unknown", 10, 42, 1), ("deep", 1, 42, 1), ("mixed", True, 42, 1), ("cancel", 20, 42, 0)])
def test_workload_rejects_invalid_parameters(args):
    with pytest.raises(ValueError):
        generate_workload(*args)


def test_unknown_command_is_rejected():
    with pytest.raises(ValueError, match="unknown benchmark operation"):
        execute(MatchingEngine(), [Command("unknown", ())])
