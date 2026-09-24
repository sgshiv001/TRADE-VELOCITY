# High-Performance Stock Market Order Matching Engine

An in-memory stock exchange simulation built around explicit data structures. It matches orders by **best price, then arrival time** and executes each trade at the resting order's price. This is an educational DSA project, not a production exchange.

## Quick start

Requires Python 3.10 or newer.

```powershell
python -m pip install -e ".[test,dashboard]"
python -m stock_engine.cli demo
python -m pytest
python -m streamlit run dashboard.py
```

For a terminal throughput run:

```powershell
python -m stock_engine.cli benchmark --orders 100000 --seed 42
python -m stock_engine.cli simulate --orders 10000 --workers 4 --seed 42
```

The benchmark uses a fixed random seed. Report the machine, Python version, order count, and measured orders per second when comparing results. The concurrent simulation submits orders from several threads; the engine lock gives each order a valid sequence, though thread scheduling can change the particular matches between runs.

## Trading rules

- A buy limit order trades with the lowest ask at or below its limit; a sell limit order trades with the highest bid at or above its limit.
- Orders at one price execute in arrival order. A partially filled resting order keeps its place.
- A market order takes available liquidity and any unfilled remainder expires.
- Limit order remainders rest on the book. Cancel removes an active order. Modify replaces its **open** quantity and limit price, and loses its old time priority.
- Order IDs are unique for the life of the engine, except that modifying an active order preserves its ID.
- Symbols are independent; the engine serializes operations with a lock so a concurrent simulation has a valid total order.
- All quantities are positive integers, and prices are positive rupee amounts with at most two decimal places.

## Data structures and complexity

Let `P` be active price levels, `O` active orders, and `T` trades for a symbol.

| Operation | Structure | Typical cost |
| --- | --- | --- |
| Best bid / ask | Custom max / min binary heap | `O(1)` peek; stale entries may take extra pops |
| Price-time priority | Doubly linked FIFO queue per price | `O(1)` append / head / remove |
| Cancel by ID | Hash map to order and queue node | `O(1)` lookup and unlink, plus `O(log P)` if the price level empties |
| Ordered market depth | Custom AVL tree | `O(log P + k)` for first `k` levels |
| Add or remove a price level | AVL tree and binary heap | `O(log P)`; occasional heap rebuild |
| Trade history / ID lookup | Dynamic array and binary search | `O(1)` append, `O(log T)` search |
| Volume over a trade range | Appendable Fenwick tree | `O(log T)` query; append amortized `O(log T)` |
| Top traded stocks | Binary heap over per-symbol totals | `O(S log S + n log S)` for `S` symbols and top `n` |
| Current price statistics | Incremental per-symbol totals | `O(1)` read |

Matching an order also costs work proportional to the price levels and resting orders it consumes. The heap discards invalidated entries lazily and periodically compacts them when cancellations leave too many stale entries.

## Python API

```python
from stock_engine import MatchingEngine

engine = MatchingEngine()
engine.place_order("S1", "ACME", "SELL", 150, "105.00")
result = engine.place_order("B1", "ACME", "BUY", 100, "106.00")
print(result.trades[0])  # 100 shares at ₹105.00
print(engine.order_book("ACME"))
print(engine.symbol_stats("ACME"))
```

Pass `price=None` for a market order. Use `cancel_order(id)`, `modify_order(id, new_open_quantity, new_price)`, `trades(symbol)`, `trade_by_id(id)`, `traded_volume(symbol, start, end)`, and `top_traded_stocks()` for the other features.

## Scope

The project is a single-process simulation. It does not connect to a broker, persist orders, handle auction sessions, apply fees, or implement risk checks. Its purpose is to make matching and DSA complexity observable and testable.
