# Project demonstration guide

## Start the application

```powershell
python -m pip install -e ".[dashboard,test]"
python -m streamlit run dashboard.py
```

Introduce the project as an in-memory exchange that enforces price-time priority. The matching core runs independently of Streamlit, and its custom structures are demonstrated through correctness tests and controlled benchmarks.

## Demonstrate the order lifecycle

Click **Start new session**. In the **Trade** tab, use stock symbol `ACME` and submit the following commands in order. Enter the explicit order IDs so the trade history is easy to follow.

| Step | Command | Expected result |
| --- | --- | --- |
| 1 | Sell limit `S1`: 150 shares at ₹105 | Rests on the sell book |
| 2 | Sell limit `S2`: 100 shares at ₹106 | Rests behind the better ₹105 ask |
| 3 | Buy limit `B1`: 100 shares at ₹106 | Executes 100 at the resting price ₹105; `S1` has 50 left |
| 4 | Buy limit `B2`: 80 shares at ₹105 | Executes the remaining 50 from `S1`; 30 buy shares rest at ₹105 |
| 5 | Sell limit `S3`: 20 shares at ₹105 | Executes 20 against `B2`; `B2` has 10 left |
| 6 | Replace `B2`: 25 open shares at ₹104 | Replaces the open quantity and resets time priority |
| 7 | Cancel `B2` | Removes it from the open orders and book |
| 8 | Buy market `M1`: 120 shares | Executes 100 from `S2` at ₹106; unfilled 20 expire |

After step 8, the book is empty, there are four trades, and ACME executed volume is 270 shares. Use **Analytics** to inspect history, execution prices, volume ranges, and statistics. Download the scenario in **Session & export**, import it, and show that the book and trade details reproduce (timestamps regenerate).

To show FIFO explicitly, start another session, place two sell orders at the same price with different IDs, and submit a market buy large enough to finish the first and partially fill the second. The first arrival must execute first. Replacing an order at the same price moves it behind earlier resting orders.

## Explain the structures

Open `src/stock_engine/structures.py` and `docs/architecture.md`:

- Min/max heaps select the best price; generation tokens make stale heap entries safe after cancellation and price recreation.
- A doubly linked queue preserves FIFO and supports direct node removal.
- The custom hash table resolves collisions with chains and resizes to control load.
- The AVL tree provides balanced insertion, deletion, and ordered market depth.
- The Fenwick tree computes trade-range volumes without scanning the whole history.
- Dynamic arrays retain trades; binary search locates a trade ID.

Explain that cancellation removes the queue node immediately. Lazy deletion applies to the price heap entry. A partially filled maker retains its queue position. A replacement uses the new open quantity and arrival sequence.

## Demonstrate the performance tradeoff

In **Experiments**, choose each recorded comparison workload. At 10,000 commands, the indexed book is about 13.3 times faster for the deep and cancellation workloads; the list book is faster when there are only eleven possible prices. Show the memory figures in `docs/results.md` as part of that tradeoff.

Run a fresh comparison and point out that it leaves the trading session unchanged. The comparison shares matching rules and analytics across both engines, so it measures the price-level indexing choice. An independent reference matcher in the tests checks algorithm correctness separately.

To reproduce all measurements:

```powershell
python scripts/compare_engines.py --sizes 1000,5000,10000 --workloads mixed,deep,cancel --repeats 3 --trace-memory
python -m pytest -q
python -m stock_engine.cli simulate --orders 10000 --workers 4 --seed 42
```

Discuss expected/amortized hash costs, stale-entry cleanup, Fenwick update costs during each trade, and memory retained for history and used IDs. The engine lock makes concurrent submission safe but serializes matching; thread count is not a promise of parallel matching speedup.

## Bound the project clearly

This project studies matching and data structures. It does not implement broker connectivity, accounts, risk limits, durable exchange storage, or exchange-grade latency guarantees. Those can be future extensions while keeping the matching core isolated.
