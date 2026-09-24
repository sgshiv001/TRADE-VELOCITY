# Measured baseline

Recorded on 24 September 2026 with Python 3.14.7 on Windows 11, using an Intel Core i7-14650HX (16 cores, 24 logical processors) and approximately 16 GB RAM. The workload used seed 42, five symbols, limit prices from ₹95 to ₹105, quantities from 1 to 100, and equal-probability buy/sell sides. Each size was timed three times. The full measurements are in [`benchmarks/baseline.csv`](../benchmarks/baseline.csv).

| Orders | Median orders/s | Trades | Peak traced memory |
| ---: | ---: | ---: | ---: |
| 1,000 | 117,944 | 764 | 0.47 MiB |
| 10,000 | 119,501 | 8,049 | 3.51 MiB |
| 100,000 | 116,861 | 81,137 | 32.21 MiB |

The third 100,000-order timing was an outlier at 28,174 orders/s; the other two were 116,861 and 117,139 orders/s. The table reports the median and the CSV retains all repetitions. Timing excludes workload generation and the separate memory-tracing passes. Python garbage collection was disabled during each timed loop, then restored. These are throughput measurements for this synthetic workload, not exchange latency guarantees.

The roughly linear increase in traced memory reflects the growing trade history and active orders. See [evaluation method](evaluation.md) for commands and interpretation.
