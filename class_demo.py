"""Trade Velocity classroom demo launcher.

Run from the repository root with::

    python class_demo.py

The script first prints a deterministic order-matching walkthrough and then
starts the live local app (or reuses an app already running on the port). It is
intended for a classroom presentation, not for production trading.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from stock_engine import MatchingEngine  # noqa: E402


def heading(text: str) -> None:
    print("\n" + "=" * 72)
    print(text)
    print("=" * 72)


def run_engine_walkthrough() -> None:
    """Show price priority, time priority, partial fill, and statistics."""

    heading("TRADE VELOCITY / LIVE CLASSROOM WALKTHROUGH")
    print("Educational simulation - deterministic matching engine - virtual orders")

    engine = MatchingEngine()

    print("\n[1] Build the sell-side liquidity")
    for order_id, quantity, price in (
        ("SELL-105", 50, "105.00"),
        ("SELL-106", 100, "106.00"),
        ("SELL-107-A", 100, "107.00"),
    ):
        engine.place_order(order_id, "ACME", "SELL", quantity, price)
        print(f"  {order_id}: SELL {quantity} ACME @ INR {price}")

    print("\n[2] Submit BUY-250 @ INR 107.00")
    result = engine.place_order("BUY-250", "ACME", "BUY", 250, "107.00")
    for trade in result.trades:
        print(
            f"  TRADE #{trade.trade_id}: {trade.quantity} shares @ "
            f"INR {trade.price} ({trade.buy_order_id} <-> {trade.sell_order_id})"
        )

    print("\n[3] Verify the matching result")
    print(f"  Filled: {result.filled} shares")
    print(f"  Remaining: {result.remaining} shares")
    print("  Why this order matched: lowest compatible ask first, then FIFO.")
    print(f"  ACME order book: {engine.order_book('ACME')}")
    print(f"  ACME statistics: {engine.symbol_stats('ACME')}")

    print("\n[4] Demonstrate a partial fill")
    engine.place_order("PARTIAL-SELL", "PARTIAL", "SELL", 150, "105.00")
    partial = engine.place_order("PARTIAL-BUY", "PARTIAL", "BUY", 100, "106.00")
    print(f"  Trade quantity: {partial.trades[0].quantity}")
    print(f"  Seller remaining: {engine.get_order('PARTIAL-SELL')['remaining']}")
    print("  This proves that the unfilled quantity remains on the book.")

    print("\n[5] Data-structure story")
    print("  Hash Table  -> locate an order by order ID")
    print("  AVL Tree    -> keep price levels ordered")
    print("  FIFO Queue  -> preserve time priority at one price")
    print("  Min/Max Heap -> surface best ask and best bid")
    print("  Fenwick Tree -> support cumulative volume queries")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Trade Velocity classroom demonstration")
    parser.add_argument("--port", type=int, default=8000, help="local app port (default: 8000)")
    parser.add_argument("--no-browser", action="store_true", help="do not open the app automatically")
    parser.add_argument("--terminal-only", action="store_true", help="run only the deterministic terminal walkthrough")
    parser.add_argument("--skip-build", action="store_true", help="reuse the frontend build")
    args = parser.parse_args()

    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")

    run_engine_walkthrough()
    if args.terminal_only:
        heading("TERMINAL DEMO COMPLETE")
        return 0

    print("\nPresentation flow:")
    print("  1. Engine       -> explain the order-to-trade pipeline")
    print("  2. Order Book   -> click a price level to show FIFO priority")
    print("  3. DSA Lab      -> demonstrate Heap, AVL, Hash, Queue, Fenwick")
    print("  4. Simulator    -> start a clearly labelled synthetic workload")
    print("  5. AI Monitor   -> explain the feature pipeline and model status")
    print("  6. Benchmark    -> show measured results only")

    from app import main as launch_app

    arguments = ["--port", str(args.port)]
    if args.no_browser:
        arguments.append("--no-browser")
    if args.skip_build:
        arguments.append("--skip-build")
    return launch_app(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
