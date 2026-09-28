"""Interactive exchange simulator. Run: python -m streamlit run dashboard.py"""

from __future__ import annotations

import random
import time
from pathlib import Path
from uuid import uuid4

import pandas as pd
import streamlit as st

from stock_engine import ExchangeSession, MatchingEngine
from stock_engine.experiments import compare_workload


st.set_page_config(page_title="Order Matching Engine", page_icon="📈", layout="wide")

if "exchange" not in st.session_state:
    st.session_state.exchange = ExchangeSession()
if "notice" not in st.session_state:
    st.session_state.notice = None


def notice(message: str, error: bool = False) -> None:
    st.session_state.notice = (message, error)


def trade_table(trades) -> pd.DataFrame:
    columns = ["Trade ID", "Time (UTC)", "Symbol", "Price (₹)", "Shares", "Buy order", "Sell order"]
    return pd.DataFrame([
        {
            "Trade ID": trade.trade_id,
            "Time (UTC)": trade.timestamp.isoformat(timespec="seconds"),
            "Symbol": trade.symbol,
            "Price (₹)": str(trade.price),
            "Shares": trade.quantity,
            "Buy order": trade.buy_order_id,
            "Sell order": trade.sell_order_id,
        }
        for trade in trades
    ], columns=columns)


def comparison_summary(rows: pd.DataFrame) -> pd.DataFrame:
    summary = rows.groupby(["commands", "engine"])["commands_per_second"].median().unstack()
    summary["Indexed / list speed ratio"] = summary["indexed"] / summary["linear"]
    return summary.rename(columns={"indexed": "Heap + AVL + hash", "linear": "Unsorted list"})


with st.sidebar:
    st.header("Session")
    if st.button("Load example market", width="stretch"):
        st.session_state.exchange = ExchangeSession.from_file(Path(__file__).parent / "scenarios" / "demo.json")
        notice("Example scenario loaded: ACME and TECH.")
    if st.button("Start new session", width="stretch"):
        st.session_state.exchange = ExchangeSession()
        notice("New empty session started.")

    uploaded = st.file_uploader("Import scenario JSON", type="json")
    if st.button("Import scenario", disabled=uploaded is None, width="stretch"):
        try:
            st.session_state.exchange = ExchangeSession.from_json(uploaded.getvalue().decode("utf-8"))
            notice(f"Imported {len(st.session_state.exchange.events)} events.")
        except (UnicodeDecodeError, ValueError) as exc:
            notice(f"Import failed: {exc}", error=True)

exchange: ExchangeSession = st.session_state.exchange
engine = exchange.engine

st.title("Stock Market Order Matching Engine")
st.caption("Price-time priority • Multiple stocks • Replayable scenarios • DSA experiments")
if st.session_state.notice:
    message, is_error = st.session_state.notice
    (st.error if is_error else st.success)(message)

trade_tab, book_tab, analytics_tab, experiments_tab, session_tab = st.tabs(
    ["Trade", "Order book", "Analytics", "Experiments", "Session & export"]
)

with trade_tab:
    st.subheader("Place an order")
    # Form widgets only rerun on submission. Keep this selector outside the
    # form so the price field updates immediately when the order type changes.
    order_type = st.selectbox("Order type", ["LIMIT", "MARKET"])
    with st.form("place_order", clear_on_submit=False):
        top = st.columns(3)
        order_id = top[0].text_input("Order ID (optional)", placeholder="Auto-generated if blank")
        symbol = top[1].text_input("Stock symbol", value="ACME").strip().upper()
        side = top[2].selectbox("Side", ["BUY", "SELL"])
        bottom = st.columns(2)
        quantity = bottom[0].number_input("Shares", min_value=1, max_value=10_000_000, value=100, step=1)
        price = bottom[1].text_input("Limit price (₹)", value="105.00", disabled=order_type == "MARKET")
        submitted = st.form_submit_button("Place order", width="stretch")
    if submitted:
        try:
            order_id = order_id.strip() or f"O-{uuid4().hex[:10].upper()}"
            result = exchange.place_order(order_id, symbol, side, int(quantity), price if order_type == "LIMIT" else None)
            status = "resting" if result.resting else "closed"
            notice(f"{order_id}: {result.filled} shares filled, {result.remaining} unfilled, {status}; {len(result.trades)} trade(s).")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))

    st.subheader("Open orders")
    active = engine.active_orders()
    st.dataframe(pd.DataFrame(active), width="stretch", hide_index=True)

    if active:
        labels = {order["order_id"]: f"{order['order_id']} · {order['symbol']} {order['side']} {order['remaining']} @ ₹{order['price']}" for order in active}
        cancel_col, modify_col = st.columns(2)
        with cancel_col:
            st.markdown("**Cancel**")
            with st.form("cancel_order"):
                cancel_id = st.selectbox("Order to cancel", list(labels), format_func=labels.get)
                canceled = st.form_submit_button("Cancel order")
            if canceled:
                if exchange.cancel_order(cancel_id):
                    notice(f"Canceled {cancel_id}.")
                    st.rerun()
                else:
                    st.error("That order is no longer open.")
        with modify_col:
            st.markdown("**Replace**")
            with st.form("modify_order"):
                modify_id = st.selectbox("Order to replace", list(labels), format_func=labels.get)
                new_quantity = st.number_input("New open shares", min_value=1, max_value=10_000_000, value=100, step=1)
                new_price = st.text_input("New limit price (₹)", value="105.00")
                modified = st.form_submit_button("Replace order")
            if modified:
                try:
                    result = exchange.modify_order(modify_id, int(new_quantity), new_price)
                    notice(f"Replaced {modify_id}: {result.filled} filled, {result.remaining} unfilled. Time priority reset.")
                    st.rerun()
                except (KeyError, ValueError) as exc:
                    st.error(str(exc))
    else:
        st.info("No open orders yet. Place a limit order or load the example market.")

with book_tab:
    symbols = engine.symbols() or ["ACME"]
    selected_symbol = st.selectbox("Stock", symbols, key="book_symbol")
    depth = st.slider("Price levels", min_value=1, max_value=50, value=10)
    book = engine.order_book(selected_symbol, depth)
    bid_col, ask_col = st.columns(2)
    with bid_col:
        st.subheader("Bids · highest first")
        st.dataframe(pd.DataFrame(book["bids"]), width="stretch", hide_index=True)
    with ask_col:
        st.subheader("Asks · lowest first")
        st.dataframe(pd.DataFrame(book["asks"]), width="stretch", hide_index=True)
    depth_rows = [
        {"Price": float(row["price"]), "Bid shares": row["quantity"], "Ask shares": 0}
        for row in book["bids"]
    ] + [
        {"Price": float(row["price"]), "Bid shares": 0, "Ask shares": row["quantity"]}
        for row in book["asks"]
    ]
    if depth_rows:
        st.subheader("Market depth")
        st.bar_chart(pd.DataFrame(depth_rows).groupby("Price").sum().sort_index())
    else:
        st.info("No resting orders for this stock.")

with analytics_tab:
    symbols = engine.symbols() or ["ACME"]
    selected_symbol = st.selectbox("Stock", symbols, key="analytics_symbol")
    stats = engine.symbol_stats(selected_symbol)
    metrics = st.columns(4)
    metrics[0].metric("Last price", f"₹{stats['last']}" if stats["last"] else "—")
    metrics[1].metric("Volume", f"{stats['volume']:,}")
    metrics[2].metric("Trades", f"{stats['trades']:,}")
    metrics[3].metric("VWAP", f"₹{stats['vwap']}" if stats["vwap"] else "—")
    if stats["trades"]:
        st.caption(f"Open ₹{stats['open']} · High ₹{stats['high']} · Low ₹{stats['low']}")
    trades = engine.trades(selected_symbol)
    if trades:
        chart_data = pd.DataFrame({
            "Trade ID": [trade.trade_id for trade in trades],
            "Price (₹)": [float(trade.price) for trade in trades],
            "Shares": [trade.quantity for trade in trades],
        }).set_index("Trade ID")
        st.subheader("Execution price")
        st.line_chart(chart_data[["Price (₹)"]])
        st.subheader("Shares per trade")
        st.bar_chart(chart_data[["Shares"]].tail(50))
        st.subheader("Volume over a trade range")
        st.caption("Trade positions are zero-based; the end position is excluded. This query uses the Fenwick tree.")
        range_cols = st.columns(2)
        range_start = range_cols[0].number_input("Start position", min_value=0, max_value=len(trades) - 1, value=0)
        range_end = range_cols[1].number_input("End position", min_value=int(range_start) + 1, max_value=len(trades), value=len(trades))
        st.metric("Shares in range", engine.traded_volume(selected_symbol, int(range_start), int(range_end)))
    st.subheader("Recent trades")
    st.dataframe(trade_table(reversed(engine.trades(selected_symbol, 100))), width="stretch", hide_index=True)
    if engine.trades():
        st.subheader("Find trade by ID")
        lookup_id = st.number_input("Trade ID", min_value=1, max_value=len(engine.trades()), value=1)
        found = engine.trade_by_id(int(lookup_id))
        st.dataframe(trade_table([found] if found else []), width="stretch", hide_index=True)
    st.subheader("Most traded stocks")
    st.dataframe(pd.DataFrame(engine.top_traded_stocks(10)), width="stretch", hide_index=True)

with experiments_tab:
    baseline_path = Path(__file__).parent / "benchmarks" / "custom-structures.csv"
    if baseline_path.exists():
        st.subheader("Recorded scaling measurements")
        baseline = pd.read_csv(baseline_path)
        summary = baseline.groupby("orders", as_index=False).agg(
            median_orders_per_second=("orders_per_second", "median"),
            peak_traced_mb=("peak_traced_mb", "first"),
        )
        st.line_chart(summary.set_index("orders")[["median_orders_per_second"]])
        st.dataframe(summary, width="stretch", hide_index=True)
        st.caption("Custom data structures · Median of three runs per size. See docs/results.md for the method and all results.")

    st.subheader("Compare price-level data structures")
    st.write("Both engines use the same matching rules, FIFO queues, order-ID lookup, and statistics. "
             "This experiment compares heap, AVL, and hash price indexes with an unsorted list of price levels.")
    workload_labels = {
        "mixed": "Mixed orders · eleven possible prices per stock",
        "deep": "Deep order book · build levels, then execute market buys",
        "cancel": "Cancellation · build levels, then remove orders",
    }
    comparison_path = Path(__file__).parent / "benchmarks" / "comparison.csv"
    if comparison_path.exists():
        recorded = pd.read_csv(comparison_path)
        recorded_names = [name for name in workload_labels if name in set(recorded["workload"])]
        recorded_workload = st.selectbox("Recorded comparison workload", recorded_names, format_func=workload_labels.get)
        recorded_summary = comparison_summary(recorded[recorded["workload"] == recorded_workload])
        st.line_chart(recorded_summary[["Heap + AVL + hash", "Unsorted list"]], y_label="Commands per second")
        st.dataframe(recorded_summary, width="stretch")
        st.caption("Median of three runs. A speed ratio above 1 means the indexed engine is faster. "
                   "Every workload's trades, open orders, depth, statistics, and volume agree before timing begins.")

    comparison_cols = st.columns(2)
    comparison_workload = comparison_cols[0].selectbox("Comparison workload", list(workload_labels), format_func=workload_labels.get)
    comparison_count = comparison_cols[1].number_input("Comparison commands", min_value=100, max_value=10_000, value=1000, step=100)
    st.caption("This runs in separate engines and preserves your trading session. Seed 42 · one stock · three runs per engine.")
    if st.button("Run comparison"):
        with st.spinner("Checking matching results and measuring both engines…"):
            st.session_state.comparison_results = compare_workload(comparison_workload, int(comparison_count))
    if "comparison_results" in st.session_state:
        live_results = pd.DataFrame(st.session_state.comparison_results)
        st.write(f"Last comparison: {live_results.iloc[0]['workload']} · {int(live_results.iloc[0]['commands']):,} commands")
        st.dataframe(comparison_summary(live_results), width="stretch")
        st.download_button("Download comparison CSV", live_results.to_csv(index=False), file_name="engine-comparison.csv", mime="text/csv")

    st.subheader("Generate market activity")
    st.write("Add deterministic random orders to this session to explore matching and depth. The generated commands are included in the exported scenario.")
    gen_cols = st.columns(2)
    generated_count = gen_cols[0].number_input("Orders to generate", min_value=1, max_value=10_000, value=500, step=100)
    generated_seed = gen_cols[1].number_input("Random seed", min_value=0, max_value=2_147_483_647, value=42, step=1)
    if st.button("Generate orders"):
        rng = random.Random(int(generated_seed))
        batch_id = uuid4().hex[:8].upper()
        for index in range(int(generated_count)):
            generated_symbol = rng.choice(["ACME", "TECH", "BANK"])
            generated_side = "BUY" if rng.randrange(2) else "SELL"
            generated_price = f"{rng.randrange(95, 106)}.00" if generated_symbol == "ACME" else (
                f"{rng.randrange(190, 211)}.00" if generated_symbol == "TECH" else f"{rng.randrange(70, 91)}.00"
            )
            exchange.place_order(f"SIM-{batch_id}-{index}", generated_symbol, generated_side, rng.randrange(1, 101), generated_price)
        notice(f"Generated {generated_count:,} orders with seed {generated_seed}.")
        st.rerun()

    st.divider()
    st.subheader("Isolated throughput benchmark")
    st.write("This uses a separate engine, so it does not change your session. Compare runs on the same machine and Python version.")
    benchmark_count = st.number_input("Benchmark orders", min_value=100, max_value=100_000, value=10_000, step=100)
    if st.button("Run benchmark"):
        rng = random.Random(42)
        bench_engine = MatchingEngine()
        orders = [
            (f"BENCH{index}", "TEST", "BUY" if rng.randrange(2) else "SELL",
             rng.randrange(1, 101), f"{rng.randrange(95, 106)}.00")
            for index in range(int(benchmark_count))
        ]
        started = time.perf_counter()
        for order in orders:
            bench_engine.place_order(*order)
        elapsed = time.perf_counter() - started
        st.metric("Orders / second", f"{benchmark_count / elapsed:,.0f}")
        st.caption(f"{benchmark_count:,} orders · {len(bench_engine.trades()):,} trades · {elapsed:.3f} seconds")

with session_tab:
    st.subheader("Session history")
    st.caption("The simulation stays in this browser session. Download the JSON scenario to replay it later.")
    st.metric("Recorded commands", len(exchange.events))
    st.dataframe(pd.DataFrame(exchange.events), width="stretch", hide_index=True)
    st.download_button("Download scenario JSON", exchange.to_json(), file_name="exchange-scenario.json", mime="application/json")
    trade_csv = trade_table(engine.trades()).to_csv(index=False)
    st.download_button("Download trades CSV", trade_csv, file_name="trades.csv", mime="text/csv")
