# TradeVelocity

**High-Performance Stock Market Order Matching Engine with Advanced Data Structures, Market Simulation and AI Analytics**

An educational stock-market simulation built with Python, FastAPI, and React. It matches buy and sell orders, explains the data structures behind an order book, and analyzes dated market history.

[How to run](#run-the-app) · [Classroom demo](#show-how-it-works) · [Architecture](docs/architecture.md) · [Measured results](docs/results.md) · [Change log](CHANGELOG.md)

## What does TradeVelocity mean?

**Trade** means buying and selling shares. **Velocity** represents the speed and flow of orders through the system. Together, **TradeVelocity** describes the project's goal: process orders efficiently while keeping every match correct and fair.

The name describes the idea behind the project. Performance is demonstrated by measured benchmarks rather than a promise about real exchange speed.

## What problem does this project solve?

A stock market receives many buy and sell orders at different prices and times. The system must find a compatible buyer and seller, select the best price first, preserve arrival order at the same price, handle partial fills and cancellations, and keep the order book accurate.

A simple implementation repeatedly scans unsorted lists. That work becomes expensive as the number of price levels grows. TradeVelocity studies how custom data structures organize these operations and compares the indexed approach with a list-based reference. Small books can still favor the simpler list, so both results are reported.

The project brings together three parts:

1. **Matching engine:** correctly execute compatible orders using price-time priority.
2. **Market simulation:** generate repeatable workloads and inspect their trades, depth, volume, and performance.
3. **AI analytics:** flag unusual historical observations without changing the engine's matching decisions.

This is a learning and experimentation project. It uses simulated orders and virtual funds, not a live exchange or real-money trading.

## What is included?

- Limit and market orders, partial fills, cancellation, modification, and multiple symbols.
- Order-book depth, trade history, VWAP, and volume queries.
- Custom heaps, FIFO queues, hash tables, AVL trees, and Fenwick trees.
- A React interface with Engine, Order Book, DSA Lab, Simulator, Analytics, AI Monitor, Benchmark, and History pages.
- Historical data for eight NSE companies and an Isolation Forest analysis pipeline.
- A paper-account API with local JSON session persistence.
- Repeatable tests and benchmark CSVs with documented workloads.

## Run the app

**Windows shortcut:** after the setup below, double-click `Launch_TradeVelocity.bat`
inside this project folder. It runs `app.py` using the project's `.venv`, keeps
browser selection, and leaves startup errors visible. Keep its window open while
using the app; press **Ctrl+C** to stop.

You need **Python 3.10+** and **Node.js 22 with npm**. In PowerShell, from the project folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[app,test]"
.\.venv\Scripts\python.exe app.py
```

Choose Edge, Chrome, Firefox, or your default browser when prompted. The launcher installs missing frontend dependencies, builds the UI, starts FastAPI, and opens `http://127.0.0.1:8000`. Keep the terminal open; **Ctrl+C** stops the server.

In VS Code, select **TradeVelocity: Run App** and press **F5**. Your existing folder named `ADSA PROJECT` is this same project; no second or nested project folder is needed.

For macOS/Linux, use `.venv/bin/python` instead of `.venv\Scripts\python.exe`.

Useful options: `--skip-build` reuses the previous frontend build, `--port 8001` selects another port, and `--no-browser` lets you open the address manually.

## Show how it works

```powershell
.\.venv\Scripts\python.exe demoapp.py
```

`demoapp.py` executes and checks real engine examples: multi-price matching, FIFO priority, partial fills, cancellation, and statistics. It then opens the same application for your presentation.

For a terminal-only demonstration:

```powershell
.\.venv\Scripts\python.exe demoapp.py --terminal-only
```

In the browser, select **ENTER ENGINE**, click **Load demo flow**, then inspect **Order Book** and **History**. Use **DSA Lab** to explain the structures and **AI Monitor** to discuss historical anomaly flags.

There are only two Python application entry files: **app.py** to launch and **demoapp.py** to demonstrate. **Launch_TradeVelocity.bat** is the Windows double-click shortcut to `app.py`. The folders below contain the code and evidence those files need.

## How the engine works

An incoming order checks the best compatible price on the opposite side. It matches the oldest order at that price and executes at the resting order's price. It continues until filled or liquidity runs out. Unfilled limit quantities remain on the book; unfilled market quantities expire.

| Data structure | Job |
| --- | --- |
| Min/max binary heaps | Find the best ask and bid |
| FIFO queues | Preserve time priority at one price |
| Hash tables | Find orders and price levels |
| AVL trees | Keep price levels ordered for depth queries |
| Fenwick trees | Calculate cumulative and range trading volume |

See [architecture and complexity](docs/architecture.md) for the algorithm, invariants, and costs.

## AI and demo limitations

The AI pipeline uses **StandardScaler + Isolation Forest** on historical OHLCV features. It fits and scores the same window. Order-flow fields derived from daily bars are proxies; scores are relative unusualness, not fraud probabilities or forecasts. AI never decides which orders trade.

The Engine demo, order book, history, and anomaly report use the backend. DSA diagrams illustrate concepts. The Simulator page currently animates counters rather than submitting its selected workload, and some analytics widgets are illustrative. For actual engine simulation or fresh measurements, use the commands below. The paper-account API has more capabilities than the current UI exposes.

The bundled market snapshot is dated, not a live feed. Its metadata records the source/date, and failed refreshes preserve the existing data. Local account sessions are saved under `.marketlab/` and excluded from Git. Source-code licensing does not replace the market provider's data terms.

## Tests and experiments

Build the frontend before running the full suite:

```powershell
cd frontend
npm ci
npm run build
cd ..
.\.venv\Scripts\python.exe -m pytest -q
```

Actual concurrent simulation and a controlled benchmark:

```powershell
.\.venv\Scripts\python.exe -m stock_engine.cli simulate --orders 10000 --workers 4 --seed 42
.\.venv\Scripts\python.exe scripts/compare_engines.py --sizes 1000,5000,10000 --workloads mixed,deep,cancel --repeats 3 --trace-memory
```

See [evaluation methods](docs/evaluation.md) and [recorded results](docs/results.md). API documentation is available at `http://127.0.0.1:8000/docs` while the app runs.

## Project structure

```text
app.py                  Launch the complete app
demoapp.py              Verified examples + classroom launch
Launch_TradeVelocity.bat Windows double-click shortcut to app.py
frontend/               React and TypeScript interface
src/stock_engine/       Matching, data structures, API, data, and AI
scripts/                Benchmark and market-data tools
scenarios/              Reproducible matching scenario
benchmarks/             Recorded measurement CSVs
tests/                  Correctness and startup checks
docs/                   Architecture, results, and development history
pyproject.toml          Python package and dependencies
```

Older launcher names and the legacy Streamlit/setup files were removed. Their committed history remains available in Git. Update [CHANGELOG.md](CHANGELOG.md) for future changes; [the development log](docs/development-log.md) preserves the implementation history.

## License

Project source is licensed under [MIT](LICENSE).
