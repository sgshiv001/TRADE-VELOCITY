"""Controlled experiments comparing indexed and linear price-level books.

Both engines use the same matching rules, validation, FIFO queues, order-ID
lookup, locking, trade history, statistics, and Fenwick index. Only the
price-level implementation changes, so this comparison isolates that choice.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
import gc
import random
import time
import tracemalloc

from .engine import MatchingEngine, PriceLevel
from .models import Order
from .structures import LinkedQueue, QueueNode


class LinearBookSide:
    """Unsorted price-level list: scans for prices and sorts for market depth."""

    def __init__(self, is_buy: bool):
        self.is_buy = is_buy
        self.levels: list[PriceLevel] = []

    def best(self) -> PriceLevel | None:
        if not self.levels:
            return None
        choose = max if self.is_buy else min
        return choose(self.levels, key=lambda level: level.price)

    def add(self, order: Order) -> QueueNode[Order]:
        assert order.price is not None
        level = next((level for level in self.levels if level.price == order.price), None)
        if level is None:
            level = PriceLevel(order.price, 0, LinkedQueue())
            self.levels.append(level)
        level.quantity += order.remaining
        return level.orders.append(order)

    def remove(self, order: Order, node: QueueNode[Order]) -> None:
        level = next(level for level in self.levels if level.price == order.price)
        level.quantity -= order.remaining
        level.orders.remove(node)
        if not level.orders.length:
            self.levels.remove(level)

    def depth(self, limit: int) -> list[dict]:
        return [
            {"price": str(level.price), "quantity": level.quantity, "orders": level.orders.length}
            for level in sorted(self.levels, key=lambda level: level.price, reverse=self.is_buy)[:limit]
        ]


class LinearMatchingEngine(MatchingEngine):
    """Benchmark reference using the production matching loop with list books."""

    def __init__(self):
        super().__init__()
        self._books = defaultdict(lambda: (LinearBookSide(True), LinearBookSide(False)))


@dataclass(frozen=True, slots=True)
class Command:
    operation: str
    args: tuple


ENGINE_TYPES = {"indexed": MatchingEngine, "linear": LinearMatchingEngine}
WORKLOAD_NAMES = ("mixed", "deep", "cancel")


def generate_workload(name: str, count: int, seed: int = 42, symbols: int = 1) -> list[Command]:
    """Generate commands before timing, with reproducible arrival order.

    mixed: crossing limit orders within eleven prices per stock.
    deep: build distinct sell levels, then drain them with market buys.
    cancel: build distinct bid levels, then cancel in shuffled order.
    """
    if name not in WORKLOAD_NAMES:
        raise ValueError(f"unknown workload: {name}")
    if isinstance(count, bool) or not isinstance(count, int) or count < 2:
        raise ValueError("count must be an integer of at least 2")
    if isinstance(symbols, bool) or not isinstance(symbols, int) or symbols < 1:
        raise ValueError("symbols must be a positive integer")
    rng = random.Random(seed)
    if name == "mixed":
        return [Command("place", (
            f"O{index}", f"STOCK{rng.randrange(symbols)}", "BUY" if rng.randrange(2) else "SELL",
            rng.randrange(1, 101), f"{rng.randrange(95, 106)}.00",
        )) for index in range(count)]

    makers = count // 2
    commands = [Command("place", (
        f"M{index}", f"STOCK{index % symbols}", "SELL" if name == "deep" else "BUY", 10,
        str(Decimal(10000 + index) / 100),
    )) for index in range(makers)]
    rng.shuffle(commands)
    if name == "deep":
        commands.extend(Command("place", (f"T{index}", f"STOCK{index % symbols}", "BUY", 10, None))
                        for index in range(count - makers))
    else:
        ids = [f"M{index}" for index in range(makers)]
        rng.shuffle(ids)
        commands.extend(Command("cancel", (order_id,)) for order_id in ids)
        # An odd-sized workload ends with an extra successful place operation.
        if count % 2:
            commands.append(Command("place", ("TAIL", "STOCK0", "BUY", 10, "99.00")))
    return commands


def execute(engine: MatchingEngine, commands: list[Command]) -> None:
    for command in commands:
        if command.operation == "place":
            engine.place_order(*command.args)
        elif command.operation == "cancel":
            if not engine.cancel_order(*command.args):
                raise ValueError(f"benchmark cancellation failed: {command.args[0]}")
        else:
            raise ValueError(f"unknown benchmark operation: {command.operation}")


def _snapshot(engine: MatchingEngine, depth: int) -> dict:
    symbols = engine.symbols()
    return {
        "orders": engine.active_orders(),
        "books": [engine.order_book(symbol, depth) for symbol in symbols],
        "trades": [(trade.trade_id, trade.symbol, trade.price, trade.quantity, trade.buy_order_id, trade.sell_order_id)
                   for trade in engine.trades()],
        "statistics": [engine.symbol_stats(symbol) for symbol in symbols],
        "volumes": [engine.traded_volume(symbol) for symbol in symbols],
    }


def verify_workload(commands: list[Command]) -> tuple[int, int]:
    """Compare full outcomes outside timing; timestamps are intentionally excluded."""
    snapshots = []
    for engine_type in ENGINE_TYPES.values():
        engine = engine_type()
        execute(engine, commands)
        snapshots.append(_snapshot(engine, len(commands)))
    if snapshots[0] != snapshots[1]:
        raise RuntimeError("indexed and linear engine results disagree")
    return len(snapshots[0]["trades"]), len(snapshots[0]["orders"])


def measure(commands: list[Command], engine_name: str) -> tuple[float, int, int]:
    """Time only command processing; restore the caller's GC setting."""
    gc.collect()
    engine = ENGINE_TYPES[engine_name]()
    was_enabled = gc.isenabled()
    gc.disable()
    try:
        started = time.perf_counter()
        execute(engine, commands)
        elapsed = time.perf_counter() - started
    finally:
        if was_enabled:
            gc.enable()
    return elapsed, len(engine.trades()), len(engine.active_orders())


def measure_memory(commands: list[Command], engine_name: str) -> float:
    """Peak traced allocations during matching in a separate untimed pass."""
    if tracemalloc.is_tracing():
        raise RuntimeError("stop existing allocation tracing before measuring memory")
    gc.collect()
    engine = ENGINE_TYPES[engine_name]()
    tracemalloc.start()
    try:
        execute(engine, commands)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return peak / 1_048_576


def compare_workload(name: str, count: int, seed: int = 42, symbols: int = 1, repeats: int = 3) -> list[dict]:
    """Validate once, then alternate which engine is timed first per repetition."""
    if isinstance(repeats, bool) or not isinstance(repeats, int) or repeats < 1:
        raise ValueError("repeats must be a positive integer")
    commands = generate_workload(name, count, seed, symbols)
    expected = verify_workload(commands)
    rows = []
    for repeat in range(1, repeats + 1):
        names = list(ENGINE_TYPES)
        if repeat % 2 == 0:
            names.reverse()
        for engine_name in names:
            elapsed, trades, active = measure(commands, engine_name)
            if (trades, active) != expected:
                raise RuntimeError("timed engine outcome differs from verification")
            rows.append({
                "workload": name, "engine": engine_name, "commands": count, "symbols": symbols,
                "seed": seed, "repeat": repeat, "seconds": elapsed,
                "commands_per_second": count / elapsed, "trades": trades, "open_orders": active,
                "peak_traced_mb": None,
            })
    return rows
