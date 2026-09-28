# Testing and performance evaluation

## Correctness

Run:

```powershell
python -m pytest -q
```

The suite checks resting-price execution, price-time priority, partial fills, market-order expiry, cancellation, modification, multiple symbols, statistics, range-volume queries, input rejection, scenario replay, and concurrent share conservation. Structure tests force hash collisions through growth and shrinkage, compare randomized hash-table operations with a dictionary, verify both heap directions, check FIFO links, inspect AVL balance after every mutation, and check Fenwick capacity boundaries. A seeded 500-order test compares every trade and order-book snapshot with a simpler list-based reference matcher. A second independent reference test checks 1,200 mixed placement, cancellation, and replacement commands, including open-order state, depth, trade history, and volume after every command. Cancellation churn also checks heap compaction and safe price-level recreation on both sides.

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

## Controlled price-book comparison

Run:

```powershell
python scripts/compare_engines.py --sizes 1000,5000,10000 --workloads mixed,deep,cancel --symbols 1 --seed 42 --repeats 3 --trace-memory
```

The output is `benchmarks/comparison.csv`. Both engines share validation, matching, FIFO queues, order-ID lookup, statistics, Fenwick updates, and locking. The indexed engine uses heap, AVL, and hash price indexes; the reference engine scans an unsorted price-level list. This comparison measures the price-level indexing choice, not the speed difference between two entirely separate exchanges.

| Workload | Definition | What it exposes |
| --- | --- | --- |
| `mixed` | Equal-probability buys and sells, quantities 1–100, limit prices ₹95–₹105 | Constant overhead with few prices and frequent matches |
| `deep` | First half: shuffled sell orders of ten shares at distinct one-paise prices starting at ₹100. Second half: market buys of ten shares | Growth and drainage of a large price book |
| `cancel` | First half: shuffled buy orders of ten shares at distinct prices. Second half: shuffled cancellations | Price-level deletion and lazy-heap compaction |

For one stock, the staged workloads reach `floor(commands / 2)` distinct levels before draining or cancellation. For multiple stocks, levels are distributed round-robin. An odd deep workload has one final market order whose excess expires; an odd cancellation workload ends with an extra ten-share limit buy at ₹99, so every workload has exactly the requested command count.

Before timing each workload and size, the harness compares complete final trades, open orders, depth, statistics, and total volume, excluding regenerated timestamps. It alternates which engine runs first on successive repetitions, collects garbage outside each timed run, disables GC during processing, and restores the previous setting afterward. Each timed run's trade and open-order counts must match the verified counts. Every timing completes before the optional separate memory passes begin. CSV rows retain every repetition, parameters, Python version, platform, elapsed time, throughput, and peak traced allocations during matching. Engine construction, workload generation, verification, and output formatting are outside the timed section.

Compare medians within the same workload and size. An indexed/list throughput ratio above one favors the indexed engine. Include the small-price result and memory costs when discussing the benefit of advanced structures. The **Experiments** dashboard tab charts these measurements and runs a fresh one-stock, seed-42 comparison in separate engines.

## Suggested report figures

1. Plot orders per second against order count from `benchmarks/results.csv`.
2. Plot peak traced memory against order count.
3. Run `simulate` for one and four workers; explain that the engine lock preserves correctness, while Python thread scheduling and lock contention can change throughput. Keep the workload identical and do not compare it directly with the multi-symbol CSV experiment.
4. Use the dashboard's market-depth and execution-price charts to explain one replayed scenario.

## Limitations and extensions

The current engine has no durable live log, broker connectivity, account balances, risk limits, exchange auctions, order routing, or transaction fees. Scenario JSON is for reproducible demonstrations and experiments. Future extensions can add time-in-force rules, persistence, a service API, and external market-data feeds while keeping the matching core isolated.
