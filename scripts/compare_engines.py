"""Benchmark indexed price books against unsorted lists with identical rules."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import platform
import sys

from stock_engine.experiments import (
    ENGINE_TYPES, WORKLOAD_NAMES, compare_workload, generate_workload, measure_memory,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", default="1000,5000,10000", help="comma-separated command counts (at least 2)")
    parser.add_argument("--workloads", default=",".join(WORKLOAD_NAMES), help="mixed,deep,cancel (comma-separated)")
    parser.add_argument("--symbols", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--trace-memory", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("benchmarks/comparison.csv"))
    args = parser.parse_args()
    try:
        sizes = [int(value.strip()) for value in args.sizes.split(",")]
    except ValueError:
        parser.error("sizes must be comma-separated integers of at least 2")
    names = [value.strip() for value in args.workloads.split(",")]
    if any(size < 2 for size in sizes) or args.symbols < 1 or args.repeats < 1:
        parser.error("sizes must be at least 2; symbols and repeats must be positive")
    if any(name not in WORKLOAD_NAMES for name in names):
        parser.error("workloads must be selected from mixed,deep,cancel")
    if len(set(sizes)) != len(sizes) or len(set(names)) != len(names):
        parser.error("sizes and workloads must not contain duplicates")

    rows = []
    for name in names:
        for size in sizes:
            print(f"Verifying and timing workload={name} commands={size}", flush=True)
            measurements = compare_workload(name, size, args.seed, args.symbols, args.repeats)
            for row in measurements:
                row.update(platform=platform.platform(), python=sys.version.split()[0])
                print(f"  engine={row['engine']:7} repeat={row['repeat']} seconds={row['seconds']:.4f} "
                      f"throughput={row['commands_per_second']:,.0f}/s trades={row['trades']}", flush=True)
            rows.extend(measurements)

    # Complete every timing pass before tracing allocations.
    if args.trace_memory:
        for name in names:
            for size in sizes:
                commands = generate_workload(name, size, args.seed, args.symbols)
                for engine_name in ENGINE_TYPES:
                    memory = measure_memory(commands, engine_name)
                    for row in rows:
                        if (row["workload"], row["commands"], row["engine"]) == (name, size, engine_name):
                            row["peak_traced_mb"] = memory
                    print(f"Memory workload={name} commands={size} engine={engine_name} peak={memory:.2f} MiB", flush=True)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            formatted = dict(row, seconds=f"{row['seconds']:.6f}", commands_per_second=f"{row['commands_per_second']:.0f}",
                             peak_traced_mb="" if row["peak_traced_mb"] is None else f"{row['peak_traced_mb']:.2f}")
            writer.writerow(formatted)
    print(f"Saved {len(rows)} measurements to {args.output}")


if __name__ == "__main__":
    main()
