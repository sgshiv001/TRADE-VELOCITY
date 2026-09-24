"""Repeatable scaling experiment for the matching engine.

Example: python scripts/benchmark.py --sizes 1000,10000,100000 --repeats 3
"""

from __future__ import annotations

import argparse
import csv
import gc
import platform
import random
import sys
import time
import tracemalloc
from pathlib import Path

from stock_engine import MatchingEngine


def workload(size: int, seed: int, symbols: int) -> list[tuple[str, str, str, int, str]]:
    rng = random.Random(seed)
    return [
        (
            f"O{index}",
            f"STOCK{rng.randrange(symbols)}",
            "BUY" if rng.randrange(2) else "SELL",
            rng.randrange(1, 101),
            f"{rng.randrange(95, 106)}.00",
        )
        for index in range(size)
    ]


def measure(orders: list[tuple[str, str, str, int, str]]) -> tuple[float, int]:
    # Reclaim the previous run's linked-queue nodes outside the timed section.
    gc.collect()
    engine = MatchingEngine()
    was_enabled = gc.isenabled()
    gc.disable()
    try:
        started = time.perf_counter()
        for order in orders:
            engine.place_order(*order)
        elapsed = time.perf_counter() - started
    finally:
        if was_enabled:
            gc.enable()
    return elapsed, len(engine.trades())


def measure_memory(orders: list[tuple[str, str, str, int, str]]) -> float:
    """Run a separate traced pass so allocation tracing does not skew timing."""
    gc.collect()
    engine = MatchingEngine()
    tracemalloc.start()
    for order in orders:
        engine.place_order(*order)
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak_bytes / 1_048_576


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure matching throughput and peak traced memory")
    parser.add_argument("--sizes", default="1000,10000,100000", help="comma-separated order counts")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--symbols", type=int, default=5)
    parser.add_argument("--trace-memory", action="store_true", help="run one separate memory-traced pass per size")
    parser.add_argument("--output", type=Path, default=Path("benchmarks/results.csv"))
    args = parser.parse_args()
    try:
        sizes = [int(value.strip()) for value in args.sizes.split(",")]
    except ValueError:
        parser.error("sizes must be comma-separated positive integers")
    if not sizes or any(size <= 0 for size in sizes) or args.repeats <= 0 or args.symbols <= 0:
        parser.error("sizes, repeats, and symbols must be positive")

    rows = []
    for size in sizes:
        orders = workload(size, args.seed, args.symbols)
        for repeat in range(1, args.repeats + 1):
            elapsed, trades = measure(orders)
            row = {
                "platform": platform.platform(),
                "python": sys.version.split()[0],
                "orders": size,
                "symbols": args.symbols,
                "seed": args.seed,
                "repeat": repeat,
                "seconds": f"{elapsed:.6f}",
                "orders_per_second": f"{size / elapsed:.0f}",
                "trades": trades,
                "peak_traced_mb": "",
            }
            rows.append(row)
            print(f"orders={size:>7} repeat={repeat} trades={trades:>7} seconds={elapsed:.3f} throughput={size / elapsed:,.0f}/s")

    # Allocation tracing can perturb subsequent runs even after it is stopped.
    # Finish all throughput runs first, then perform one traced pass per size.
    if args.trace_memory:
        for size in sizes:
            memory_mb = measure_memory(workload(size, args.seed, args.symbols))
            for row in rows:
                if row["orders"] == size:
                    row["peak_traced_mb"] = f"{memory_mb:.2f}"
            print(f"orders={size:>7} peak_traced_memory={memory_mb:.2f} MiB")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} measurements to {args.output}")


if __name__ == "__main__":
    main()
