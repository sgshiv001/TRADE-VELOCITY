"""A small terminal demonstration and repeatable throughput benchmark."""

import argparse
import random
import time
from concurrent.futures import ThreadPoolExecutor

from .engine import MatchingEngine


def demo() -> None:
    engine = MatchingEngine()
    engine.place_order("S1", "ACME", "SELL", 150, "105.00")
    engine.place_order("S2", "ACME", "SELL", 100, "106.00")
    result = engine.place_order("B1", "ACME", "BUY", 100, "106.00")
    for trade in result.trades:
        print(f"Trade #{trade.trade_id}: {trade.quantity} {trade.symbol} @ INR {trade.price} ({trade.buy_order_id} / {trade.sell_order_id})")
    print("Book:", engine.order_book("ACME"))
    print("Stats:", engine.symbol_stats("ACME"))


def benchmark(count: int, seed: int) -> None:
    if count <= 0:
        raise ValueError("count must be positive")
    rng = random.Random(seed)
    engine = MatchingEngine()
    start = time.perf_counter()
    for index in range(count):
        side = "BUY" if rng.randrange(2) else "SELL"
        price = f"{rng.randrange(95, 106)}.00"
        engine.place_order(f"O{index}", "ACME", side, rng.randrange(1, 101), price)
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Stock order matching engine")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("demo", help="run a small matching example")
    bench = subcommands.add_parser("benchmark", help="measure order insertion and matching")
    bench.add_argument("--orders", type=int, default=100_000)
    bench.add_argument("--seed", type=int, default=42)
    simulation = subcommands.add_parser("simulate", help="submit orders from several threads")
    simulation.add_argument("--orders", type=int, default=10_000)
    simulation.add_argument("--workers", type=int, default=4)
    simulation.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.command == "demo":
        demo()
    elif args.command == "benchmark":
        benchmark(args.orders, args.seed)
    else:
        simulate(args.orders, args.workers, args.seed)


if __name__ == "__main__":
    main()
