# Project Problem Statement

## Short name

**MarketLab** is the application name. For an academic title, use **TradeVelocity: A Data-Structure-Based Stock Order Matching Engine**.

## The problem

An exchange receives buy and sell orders for many securities. It must select compatible orders using price-time priority, execute complete and partial trades, maintain an accurate order book, support cancellation and replacement, and answer market-depth and trading-history queries as the order stream grows.

A list-only implementation repeatedly scans all orders and price levels. That makes best-price lookup, cancellation, and range statistics increasingly expensive. The project studies how explicit data-structure choices improve those hot paths while preserving deterministic matching rules.

## Project objective

Build an educational, local stock-exchange simulation that:

- matches limit and market orders at the resting order's price;
- preserves FIFO order within each price level;
- supports partial fills, cancellation, and modification;
- maintains independent books for multiple companies;
- records trades and exposes volume, VWAP, price, and depth statistics;
- compares indexed price-level management with a linear reference implementation;
- presents company history, charts, market trends, and virtual portfolio profit/loss in a professional React application.

The system is a simulation. It does not connect to NSE/BSE, place real trades, or provide investment advice.

## Data structures and responsibilities

| Requirement | Project structure | Reason |
| --- | --- | --- |
| Best buy price | Custom max heap | Keeps the highest bid available at the root |
| Best sell price | Custom min heap | Keeps the lowest ask available at the root |
| Same-price priority | Doubly linked FIFO queue | Preserves arrival order and supports direct unlinking |
| Order and price lookup | Separate-chaining hash table | Expected constant-time lookup and cancellation |
| Ordered market depth | AVL tree | Supports sorted price levels and depth queries |
| Volume range queries | Fenwick tree | Prefix differences in logarithmic time |
| Trade history | Dynamic array plus binary search | Append efficiently and find trade IDs by order |
| Paper-account accounting | Decimal positions and journal | Makes cash, average cost, and P/L reproducible |

## Matching rules

1. Validate symbol, side, quantity, price, and unique order ID.
2. Read the best compatible price on the opposite side.
3. Match the oldest order at that price.
4. Execute the smaller remaining quantity at the resting order's price.
5. Remove completed orders, retain partial orders in their FIFO position, and continue matching.
6. Rest an unfilled limit remainder; expire an unfilled market remainder.
7. Record the trade, volume, statistics, and session event.

## Acceptance criteria

### Core correctness

- A crossing buy and sell order produces a trade at the resting price.
- Partial fills leave the correct open quantity on the book.
- Equal-price orders execute FIFO.
- Non-crossing orders rest at their price.
- Market-order remainders expire.
- Cancellation and modification update every index without stale active orders.
- Multiple symbols remain isolated.

### Application behavior

- The Markets screen shows eight real companies with dated historical bars, adjusted growth, candlesticks, moving averages, volume, and drawdown.
- The paper portfolio executes against synthetic liquidity and shows holdings, cash, average cost, realized P/L, unrealized P/L, and account equity.
- The Matching Lab shows depth, active orders, executions, cancellation, replacement, and import/export.
- The Experiments screen shows recorded benchmarks and can run isolated comparisons without changing a user's sessions.
- A missing or invalid market snapshot is labeled as simulated data rather than presented as real history.

### Evidence for the submission

- Unit and API tests cover structures, matching, replay, validation, portfolio conservation, persistence, and concurrency.
- A benchmark compares the production indexed book with a list-based reference while checking that both produce identical outcomes.
- The report includes actual measured results, workload definitions, hardware/software versions, and memory observations.
- Complexity claims describe average/amortized behavior and their assumptions. They are not replaced by unsupported claims such as “100x faster” or “less than 1 ms” unless a reproducible run demonstrates them.

## Optional AI automation layer

AI should be an explainability and analysis layer around the deterministic engine, not part of the matching decision. A robust semester-friendly extension is:

- generate a plain-language post-trade report from structured trades, depth, volume, and price indicators;
- flag explainable patterns such as unusually large orders, rapid cancel/replace activity, spread widening, or volume spikes;
- summarize bullish, bearish, and neutral evidence from the selected historical window;
- answer questions about the current session using retrieved project data only;
- attach the input snapshot, rule/indicator values, model name, and timestamp to every generated report.

Implement the rules locally first so the feature works without an API key. An optional hosted LLM can convert those structured findings into prose, but it must not invent prices, execute orders, override risk checks, or be required for the core demo. Label generated text as educational analysis.

## Recommended submission package

1. Problem statement and scope.
2. Architecture and DSA complexity report.
3. Source code with focused modules and type/validation boundaries.
4. Tests with a passing test command and coverage output if available.
5. Reproducible benchmark CSV and a short interpretation of its tradeoffs.
6. React application screenshots and a two-minute demo script.
7. Setup guide covering Python, Node.js, market-data provenance, paper-account rules, and known limitations.
8. Optional AI analysis report with example input and generated output.

## Suggested short names

- **MarketLab** — best for the complete app and demo.
- **TradeVelocity** — best for a performance-focused academic title.
- **OrderFlow** — concise and exchange-oriented.
- **TradeMatch** — clear and approachable.

Use “High-Performance Stock Market Order Matching Engine Using Advanced Data Structures” as the formal report title if your department prefers a descriptive title; use MarketLab in the UI and repository README.
