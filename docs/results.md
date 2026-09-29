# Measured performance

## Execution watchdog and desktop-era benchmarks — 29 September 2026

The new execution watchdog uses a fixed baseline of 40 executed-order observations
and scores 50 later observations without fitting on them. Ten test observations
contain deliberately injected volume and price spikes; labels are used only for
evaluation. Seed 42, Python 3.14.7, scikit-learn 1.9.1 on this Windows machine:

| Test outcome | Count |
| --- | ---: |
| Detected injected spikes | 10 |
| Missed injected spikes | 0 |
| False alarms on normal observations | 7 |
| Correct normal observations | 33 |

Precision is **58.8%**, recall is **100%** on this synthetic holdout only. Normal
transitions after spikes can also be flagged. This is not real-market fraud
accuracy, causal attribution, or a price forecast. Reproduce using
`python scripts/evaluate_watchdog.py --seed 42`; version and platform metadata are
in [watchdog-evaluation.json](../benchmarks/watchdog-evaluation.json).

Fresh matching, deep-book, and cancellation workloads at 100, 1,000, and 5,000
commands, each repeated three times per engine, are preserved separately in
[desktop-comparison.csv](../benchmarks/desktop-comparison.csv). Generation and full
indexed/linear outcome verification precede timing. No memory tracing was run
for this set. Earlier CSVs and their tables below are unchanged. Measurements
are machine-specific and include whole staged workloads, not individual-operation
latency guarantees.

## Indexed versus list price books — 28 September 2026

Measured with Python 3.14.7 on Windows 11, seed 42, one stock, three timed runs per engine and workload, and separate memory passes. Both engines share the full matching loop and analytics; only price-level indexing differs. Complete final outcomes were checked before timing. All 54 timing rows are retained in [`benchmarks/comparison.csv`](../benchmarks/comparison.csv).

| Workload | Commands | Indexed median commands/s | List median commands/s | Indexed / list speed ratio |
| --- | ---: | ---: | ---: | ---: |
| Mixed orders | 1,000 | 106,581 | 138,171 | 0.77× |
| Mixed orders | 5,000 | 110,889 | 136,018 | 0.82× |
| Mixed orders | 10,000 | 106,660 | 134,663 | 0.79× |
| Deep book | 1,000 | 86,378 | 45,139 | 1.91× |
| Deep book | 5,000 | 79,833 | 10,841 | 7.36× |
| Deep book | 10,000 | 73,122 | 5,495 | 13.31× |
| Cancellation | 1,000 | 132,029 | 61,292 | 2.15× |
| Cancellation | 5,000 | 105,868 | 14,503 | 7.30× |
| Cancellation | 10,000 | 103,368 | 7,773 | 13.30× |

The deep and cancellation workloads reach 5,000 active price levels at the 10,000-command size. Indexed throughput decreases modestly as the book grows, while repeated list scans become much more expensive. The mixed workload has just eleven possible prices, so list scanning has lower constant overhead. These results support using the advanced structures when price-book size grows; they do not imply that the indexed engine wins on every workload.

| Workload at 10,000 commands | Indexed peak traced memory | List peak traced memory | Trades per run |
| --- | ---: | ---: | ---: |
| Mixed orders | 3.53 MiB | 3.41 MiB | 8,104 |
| Deep book | 5.28 MiB | 3.84 MiB | 5,000 |
| Cancellation | 5.18 MiB | 3.84 MiB | 0 |

The extra heap, AVL nodes, and price hash table use additional memory. Throughput here counts every successful placement and cancellation command; in the staged workloads, half the commands build liquidity before the other half drains or cancels it. It is not a measurement of individual cancellation latency. See [evaluation method](evaluation.md) for exact workload definitions and reproduction commands.

## Custom hash tables and linear rebuilds — 28 September 2026

The current implementation uses custom separate-chaining hash tables for order IDs and price levels, bottom-up heap construction, and linear Fenwick capacity rebuilding. Measured with Python 3.14.7 on Windows 11, using the same seed 42, five-symbol workload and three repetitions per size described below. Raw results are in [`benchmarks/custom-structures.csv`](../benchmarks/custom-structures.csv).

| Orders | Median orders/s | Trades | Peak traced memory |
| ---: | ---: | ---: | ---: |
| 1,000 | 105,793 | 764 | 0.49 MiB |
| 10,000 | 107,278 | 8,049 | 3.63 MiB |
| 100,000 | 103,497 | 81,137 | 33.26 MiB |

The third 100,000-order timing was an outlier at 14,377 orders/s; the other two were 103,497 and 105,137 orders/s. All repetitions remain in the CSV. The matching results are identical to the earlier baseline (764, 8,049, and 81,137 trades). A Python implementation of a hash table adds overhead compared with Python's built-in dictionary; these measurements demonstrate the current educational implementation's throughput rather than a speedup over that earlier version. The runs were taken on different days, so they do not isolate the effect of any one change.

## Earlier baseline — 24 September 2026

Recorded on 24 September 2026 with Python 3.14.7 on Windows 11, using an Intel Core i7-14650HX (16 cores, 24 logical processors) and approximately 16 GB RAM. The workload used seed 42, five symbols, limit prices from ₹95 to ₹105, quantities from 1 to 100, and equal-probability buy/sell sides. Each size was timed three times. The full measurements are in [`benchmarks/baseline.csv`](../benchmarks/baseline.csv).

| Orders | Median orders/s | Trades | Peak traced memory |
| ---: | ---: | ---: | ---: |
| 1,000 | 117,944 | 764 | 0.47 MiB |
| 10,000 | 119,501 | 8,049 | 3.51 MiB |
| 100,000 | 116,861 | 81,137 | 32.21 MiB |

The third 100,000-order timing was an outlier at 28,174 orders/s; the other two were 116,861 and 117,139 orders/s. The table reports the median and the CSV retains all repetitions. Timing excludes workload generation and the separate memory-tracing passes. Python garbage collection was disabled during each timed loop, then restored. These are throughput measurements for this synthetic workload, not exchange latency guarantees.

The roughly linear increase in traced memory reflects the growing trade history and active orders. See [evaluation method](evaluation.md) for commands and interpretation.
