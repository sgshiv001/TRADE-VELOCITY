"""Run with: streamlit run dashboard.py"""

from dataclasses import asdict
from uuid import uuid4

import pandas as pd
import streamlit as st

from stock_engine import MatchingEngine

st.set_page_config(page_title="Stock Matching Engine", layout="wide")
st.title("Stock Market Order Matching Engine")
st.caption("Live, in-memory simulation with price-time priority")

if "engine" not in st.session_state:
    st.session_state.engine = MatchingEngine()
if "event" not in st.session_state:
    st.session_state.event = ""
engine: MatchingEngine = st.session_state.engine

with st.sidebar:
    st.header("New order")
    with st.form("new_order"):
        symbol = st.text_input("Stock symbol", value="ACME").upper().strip()
        side = st.selectbox("Side", ["BUY", "SELL"])
        order_type = st.selectbox("Order type", ["LIMIT", "MARKET"])
        quantity = st.number_input("Shares", min_value=1, value=100, step=1)
        price = st.text_input("Limit price (₹)", value="105.00", disabled=order_type == "MARKET")
        submitted = st.form_submit_button("Place order", width="stretch")
    if submitted:
        try:
            order_id = uuid4().hex[:8].upper()
            result = engine.place_order(order_id, symbol, side, int(quantity), price if order_type == "LIMIT" else None)
            st.session_state.event = f"{order_id}: filled {result.filled}, open {result.remaining if result.resting else 0}, trades {len(result.trades)}"
        except ValueError as exc:
            st.session_state.event = f"Error: {exc}"

    st.header("Cancel order")
    with st.form("cancel_order"):
        cancel_id = st.text_input("Order ID")
        canceled = st.form_submit_button("Cancel", width="stretch")
    if canceled:
        st.session_state.event = f"Canceled {cancel_id}" if engine.cancel_order(cancel_id.strip()) else f"No active order: {cancel_id}"

    st.header("Modify order")
    with st.form("modify_order"):
        modify_id = st.text_input("Active order ID")
        new_quantity = st.number_input("New open shares", min_value=1, value=100, step=1)
        new_price = st.text_input("New limit price (₹)", value="105.00")
        modified = st.form_submit_button("Replace order", width="stretch")
    if modified:
        try:
            result = engine.modify_order(modify_id.strip(), int(new_quantity), new_price)
            st.session_state.event = f"Replaced {modify_id}: filled {result.filled}, open {result.remaining if result.resting else 0}"
        except (KeyError, ValueError) as exc:
            st.session_state.event = f"Error: {exc}"

if st.session_state.event:
    st.info(st.session_state.event)

selected_symbol = st.text_input("View stock", value="ACME").upper().strip()
book = engine.order_book(selected_symbol)
stats = engine.symbol_stats(selected_symbol)
top = st.columns(4)
top[0].metric("Last price", f"₹{stats['last']}" if stats["last"] else "—")
top[1].metric("Traded volume", stats["volume"])
top[2].metric("Trades", stats["trades"])
top[3].metric("VWAP", f"₹{stats['vwap']}" if stats["vwap"] else "—")

left, right = st.columns(2)
with left:
    st.subheader("Buy book")
    st.dataframe(book["bids"], width="stretch", hide_index=True)
with right:
    st.subheader("Sell book")
    st.dataframe(book["asks"], width="stretch", hide_index=True)

st.subheader("Recent trades")
recent_trades = engine.trades(selected_symbol, 50)
st.dataframe([asdict(trade) for trade in reversed(recent_trades)], width="stretch", hide_index=True)
if recent_trades:
    st.subheader("Trade price history")
    prices = pd.DataFrame({"Trade ID": [trade.trade_id for trade in recent_trades], "Price (₹)": [float(trade.price) for trade in recent_trades]})
    st.line_chart(prices.set_index("Trade ID"))
st.subheader("Top traded stocks")
st.dataframe(engine.top_traded_stocks(), width="stretch", hide_index=True)

with st.expander("Performance benchmark"):
    benchmark_orders = st.number_input("Generated orders", min_value=100, max_value=100_000, value=10_000, step=100)
    if st.button("Run benchmark"):
        import random
        import time

        bench_engine = MatchingEngine()
        rng = random.Random(42)
        started = time.perf_counter()
        for index in range(int(benchmark_orders)):
            bench_engine.place_order(
                f"BENCH{index}", "TEST", "BUY" if rng.randrange(2) else "SELL",
                rng.randrange(1, 101), f"{rng.randrange(95, 106)}.00",
            )
        elapsed = time.perf_counter() - started
        st.metric("Orders per second", f"{benchmark_orders / elapsed:,.0f}")
        st.caption(f"{benchmark_orders:,} generated orders, {len(bench_engine.trades()):,} trades, {elapsed:.3f} seconds")
