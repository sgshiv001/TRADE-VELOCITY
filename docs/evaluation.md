# Testing and performance evaluation

## Correctness

Run:

```powershell
python -m pytest -q
```

The suite checks resting-price execution, price-time priority, partial fills, market-order expiry, cancellation, modification, multiple symbols, statistics, range-volume queries, AVL deletion, Fenwick growth, input rejection, scenario replay, and concurrent share conservation. A seeded 500-order test compares every trade and order-book snapshot with a simpler list-based reference matcher.

The bundled scenario can be replayed with:

```powershell
python -m stock_engine.cli run scenarios/demo.json
```

Expected summary: nine commands, four trades; ACME has 190 executed shares and TECH has 40.

## Throughput experiment

Install the package first, then run:

```powershell
python scripts/benchmark.py --sizes 1000,10000,100000 --repeats 3 --seed 42 --symbols 5 --trace-memory
```

The script writes `benchmarks/results.csv` with elapsed time, orders per second, trade count, platform, Python version, and peak memory traced during matching. It creates each workload before timing, collects garbage from the previous run outside the timed section, and disables Python garbage collection during the timed section to measure the matching loop consistently. Real applications can still experience GC pauses. When `--trace-memory` is set, **all throughput runs finish before memory tracing starts**. A separate traced pass per size provides the memory estimate without distorting the recorded timings. The lighter CLI benchmark runs only one size and no memory pass:

```powershell
python -m stock_engine.cli benchmark --orders 100000 --seed 42
```

For a fair comparison, keep the same machine, Python version, seed, symbol count, and workload definition. Run several repetitions and report the median. The timing includes validation, insertion, matching, and trade/statistics updates; it excludes workload generation and CSV writing. This is an in-memory Python simulation, so its results are not exchange-grade latency claims.

## Suggested report figures

1. Plot orders per second against order count from `benchmarks/results.csv`.
2. Plot peak traced memory against order count.
3. Compare `benchmark` and `simulate` commands for one and four workers; explain that the engine lock preserves correctness, while Python thread scheduling and lock contention can change throughput.
4. Use the dashboard's market-depth and execution-price charts to explain one replayed scenario.

## Limitations and extensions

The current engine has no durable live log, broker connectivity, account balances, risk limits, exchange auctions, order routing, or transaction fees. Scenario JSON is for reproducible demonstrations and experiments. Future extensions can add time-in-force rules, persistence, a service API, and external market-data feeds while keeping the matching core isolated.
