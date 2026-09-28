"""Verified TradeVelocity examples followed by the complete app.

Run from the repository root with::

    python demoapp.py

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


def run_engine_walkthrough() -> dict:
    """Show price priority, time priority, partial fill, and statistics."""

    heading("TRADEVELOCITY / LIVE CLASSROOM WALKTHROUGH")
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
    executions = [(trade.quantity, str(trade.price)) for trade in result.trades]
    if executions != [(50, "105.00"), (100, "106.00"), (100, "107.00")]:
        raise RuntimeError("Multi-price matching did not produce the expected trades.")
    if result.filled != 250 or result.remaining != 0:
        raise RuntimeError("Matched quantities did not conserve the incoming order.")
    vwap = engine.symbol_stats("ACME")["vwap"]
    if vwap != "106.20":
        raise RuntimeError("VWAP did not match the executed prices and quantities.")
    print("  [PASS] Price priority, matched quantities, and VWAP verified.")

    print("\n[4] Demonstrate a partial fill")
    engine.place_order("PARTIAL-SELL", "PARTIAL", "SELL", 150, "105.00")
    partial = engine.place_order("PARTIAL-BUY", "PARTIAL", "BUY", 100, "106.00")
    print(f"  Trade quantity: {partial.trades[0].quantity}")
    partial_remaining = engine.get_order("PARTIAL-SELL")["remaining"]
    print(f"  Seller remaining: {partial_remaining}")
    print("  This proves that the unfilled quantity remains on the book.")
    if partial.trades[0].quantity != 100 or partial_remaining != 50:
        raise RuntimeError("Partial-fill quantities were incorrect.")
    print("  [PASS] Partial-fill remainder verified.")

    print("\n[5] Demonstrate FIFO priority at the same price")
    fifo_engine = MatchingEngine()
    fifo_engine.place_order("FIRST-SELL", "FIFO", "SELL", 20, "100.00")
    fifo_engine.place_order("SECOND-SELL", "FIFO", "SELL", 30, "100.00")
    fifo_result = fifo_engine.place_order("FIFO-BUY", "FIFO", "BUY", 25, "100.00")
    fifo_executions = [(trade.sell_order_id, trade.quantity) for trade in fifo_result.trades]
    fifo_remaining = fifo_engine.get_order("SECOND-SELL")["remaining"]
    if fifo_executions != [("FIRST-SELL", 20), ("SECOND-SELL", 5)] or fifo_remaining != 25:
        raise RuntimeError("Same-price orders did not execute in FIFO order.")
    print("  FIRST-SELL fills 20 shares before SECOND-SELL fills 5 shares.")
    print(f"  SECOND-SELL remaining: {fifo_remaining}")
    print("  [PASS] Same-price time priority verified.")

    print("\n[6] Cancel the remaining partial order")
    cancelled = engine.cancel_order("PARTIAL-SELL")
    if not cancelled or engine.order_book("PARTIAL")["asks"]:
        raise RuntimeError("Cancellation did not remove the resting order.")
    print("  [PASS] Cancelled order removed from the order book.")

    print("\n[7] Data-structure story")
    print("  Hash Table  -> locate an order by order ID")
    print("  AVL Tree    -> keep price levels ordered")
    print("  FIFO Queue  -> preserve time priority at one price")
    print("  Min/Max Heap -> surface best ask and best bid")
    print("  Fenwick Tree -> support cumulative volume queries")
    print("\nALL ENGINE DEMO CHECKS PASSED")
    return {"matched_shares": result.filled, "executions": executions,
            "vwap": vwap, "partial_remaining": partial_remaining,
            "fifo_executions": fifo_executions, "fifo_remaining": fifo_remaining,
            "cancelled": cancelled}


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Demonstrate and launch TradeVelocity")
    parser.add_argument("--port", type=int, default=8000, help="local app port (default: 8000)")
    browser_options = parser.add_mutually_exclusive_group()
    browser_options.add_argument("--no-browser", action="store_true", help="do not open the app automatically")
    browser_options.add_argument("--browser", choices=("edge", "chrome", "firefox", "default"),
                                 help="choose a browser without the selection prompt")
    parser.add_argument("--terminal-only", action="store_true", help="run only the deterministic terminal walkthrough")
    parser.add_argument("--skip-build", action="store_true", help="reuse the frontend build")
    args = parser.parse_args(arguments)

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
    print("  4. Simulator    -> explain the illustrative counters; use CLI for real workloads")
    print("  5. AI Monitor   -> explain the feature pipeline and model status")
    print("  6. Benchmark    -> show measured results only")

    from app import main as launch_app

    arguments = ["--port", str(args.port)]
    if args.no_browser:
        arguments.append("--no-browser")
    elif args.browser:
        arguments.extend(["--browser", args.browser])
    if args.skip_build:
        arguments.append("--skip-build")
    return launch_app(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
