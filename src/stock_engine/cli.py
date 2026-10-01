"""Engine workload measurements and command replay."""

import argparse
import random
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .engine import MatchingEngine
from .session import ExchangeSession


def benchmark(count: int, seed: int) -> None:
    if count <= 0:
        raise ValueError("count must be positive")
    rng = random.Random(seed)
    engine = MatchingEngine()
    orders = []
    for index in range(count):
        side = "BUY" if rng.randrange(2) else "SELL"
        price = f"{rng.randrange(95, 106)}.00"
        orders.append((f"O{index}", "ACME", side, rng.randrange(1, 101), price))
    start = time.perf_counter()
    for order in orders:
        engine.place_order(*order)
    elapsed = time.perf_counter() - start
    print(f"orders={count} trades={len(engine.trades())} seconds={elapsed:.4f} orders_per_second={count / elapsed:,.0f}")


def simulate(count: int, workers: int, seed: int) -> None:
    """Submit independent orders from workers; the engine lock serializes matching."""
    if count <= 0 or workers <= 0:
        raise ValueError("orders and workers must be positive")
    rng = random.Random(seed)
    orders = [
        (f"C{index}", "ACME", "BUY" if rng.randrange(2) else "SELL", rng.randrange(1, 101), f"{rng.randrange(95, 106)}.00")
        for index in range(count)
    ]
    engine = MatchingEngine()
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(lambda order: engine.place_order(*order), orders))
    elapsed = time.perf_counter() - started
    book = engine.order_book("ACME", depth=count)
    print(f"workers={workers} orders={count} trades={len(engine.trades())} open_levels={len(book['bids']) + len(book['asks'])} seconds={elapsed:.4f}")


def run_scenario(path: Path) -> None:
    session = ExchangeSession.from_file(path)
    print(f"scenario={path} events={len(session.events)} trades={len(session.engine.trades())}")
    for symbol in session.engine.symbols():
        print(f"{symbol}: {session.engine.symbol_stats(symbol)}")
        print(f"book: {session.engine.order_book(symbol)}")
    for trade in session.engine.trades():
        print(f"trade #{trade.trade_id}: {trade.symbol} {trade.quantity} @ INR {trade.price} ({trade.buy_order_id} / {trade.sell_order_id})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Stock order matching engine")
    subcommands = parser.add_subparsers(dest="command", required=True)
    bench = subcommands.add_parser("benchmark", help="measure order insertion and matching")
    bench.add_argument("--orders", type=int, default=100_000)
    bench.add_argument("--seed", type=int, default=42)
    simulation = subcommands.add_parser("simulate", help="submit orders from several threads")
    simulation.add_argument("--orders", type=int, default=10_000)
    simulation.add_argument("--workers", type=int, default=4)
    simulation.add_argument("--seed", type=int, default=42)
    scenario = subcommands.add_parser("run", help="replay a JSON scenario")
    scenario.add_argument("path", type=Path)
    args = parser.parse_args()
    if args.command == "benchmark":
        benchmark(args.orders, args.seed)
    elif args.command == "simulate":
        simulate(args.orders, args.workers, args.seed)
    else:
        run_scenario(args.path)


if __name__ == "__main__":
    main()
