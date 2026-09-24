# High-Performance Stock Market Order Matching Engine

A complete, in-memory mini stock exchange for studying advanced data structures and algorithms. It accepts buy and sell orders, applies **price-time priority**, executes trades, and shows the market through a Streamlit dashboard. The matching core is independent of the UI, with reproducible scenarios, tests, and benchmarking tools.

> Educational simulation. It does not connect to a live exchange or place real trades.

## What it does

- **Trading:** buy and sell limit orders, market orders, partial fills, cancellation, and modification.
- **Order book:** multiple stocks, best bid and ask, FIFO at each price, and ordered market depth.
- **Analytics:** trade history, OHLC prices, VWAP, executed volume, volume-range queries, and most traded stocks.
- **Experiments:** deterministic generated orders, concurrent submission simulation, and throughput and memory benchmarks.
- **Reproducibility:** export a session to JSON, import it later, and download trades as CSV.

## Quick start

Requires Python 3.10 or newer. From the project folder:

```powershell
python -m pip install -e ".[dashboard,test]"
python -m pytest -q
python -m streamlit run dashboard.py
```

In the dashboard, click **Load example market** to see a ready-made two-stock scenario. Place orders in the **Trade** tab, inspect depth in **Order book**, view statistics in **Analytics**, generate data in **Experiments**, and export the session in **Session & export**.

## Terminal commands

```powershell
python -m stock_engine.cli demo
python -m stock_engine.cli run scenarios/demo.json
python -m stock_engine.cli benchmark --orders 100000 --seed 42
python -m stock_engine.cli simulate --orders 10000 --workers 4 --seed 42
python scripts/benchmark.py --sizes 1000,10000,100000 --repeats 3 --trace-memory
```

The last command writes a CSV to `benchmarks/results.csv`. See the [measured baseline](docs/results.md) and [performance evaluation](docs/evaluation.md) for results, methodology, and interpretation.

## Python API

```python
from stock_engine import MatchingEngine

engine = MatchingEngine()
engine.place_order("S1", "ACME", "SELL", 150, "105.00")
result = engine.place_order("B1", "ACME", "BUY", 100, "106.00")

assert result.trades[0].quantity == 100
assert str(result.trades[0].price) == "105.00"  # resting order's price
print(engine.order_book("ACME"))
print(engine.symbol_stats("ACME"))
```

Use `price=None` for a market order. Other methods include `cancel_order`, `modify_order`, `active_orders`, `trades`, `trade_by_id`, `traded_volume`, and `top_traded_stocks`. `modify_order(id, quantity, price)` replaces the order's **open** quantity and loses its previous time priority.

To record and replay a session:

```python
from stock_engine import ExchangeSession

session = ExchangeSession()
session.place_order("S1", "ACME", "SELL", 20, "100.00")
session.save("my-scenario.json")
restored = ExchangeSession.from_file("my-scenario.json")
```

## Data structures

| Purpose | Implementation |
| --- | --- |
| Best bid and ask | Custom max and min binary heaps |
| Orders at the same price | Doubly linked FIFO queues |
| Find or cancel an order | Order-ID hash map |
| Sorted price levels and market depth | Custom AVL trees |
| Volume over a trade range | Appendable Fenwick trees |
| Trade history and search | Dynamic array and binary search |
| Most traded stocks | Binary heap over symbol totals |

The core structures are implemented in [`src/stock_engine/structures.py`](src/stock_engine/structures.py). See [architecture and complexity](docs/architecture.md) for the matching algorithm, invariants, and operation costs.

## Project layout

```text
dashboard.py                 Streamlit interface
src/stock_engine/engine.py   Matching and order books
src/stock_engine/structures.py  Heaps, linked queues, AVL, Fenwick
src/stock_engine/session.py  JSON scenario recording and replay
src/stock_engine/cli.py      Demo, replay, benchmark, concurrency
scenarios/demo.json          Example two-stock market
scripts/benchmark.py         Repeatable CSV performance experiment
tests/                       Correctness and replay tests
docs/                        Design and evaluation notes
.github/workflows/tests.yml  Cross-platform CI
```

## Trading rules and scope

Each trade executes at the resting order's price. An unfilled limit-order remainder rests on the book; an unfilled market-order remainder expires. Partially filled resting orders keep their position. Order IDs are unique for one engine session, except that modification preserves the ID. Prices are positive rupee amounts with at most two decimal places; quantities are positive integers.

The engine protects each command with a lock. A concurrent run has a valid total order, although its exact matching sequence can vary with thread scheduling. Session JSON records successful commands for replay; trade timestamps are generated again during replay. The application does not provide durable live storage, broker connectivity, or financial risk controls.
