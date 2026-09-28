# MarketLab React app

MarketLab pairs a React/TypeScript interface with the existing Python matching engine through FastAPI. Recharts renders price, volume, allocation, and benchmark charts; a small SVG renderer draws OHLC candlesticks. The app runs on the local computer and uses virtual funds.

## Run the app

Install Python 3.10+ and Node.js 22 LTS. From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[app,test]"
.\.venv\Scripts\python.exe app.py
```

The launcher asks for Edge, Chrome, Firefox, or the system default browser. It installs locked frontend dependencies if missing, builds React, serves the client and API at **http://127.0.0.1:8000**, and opens the browser after the server is ready. It prefers the project's `.venv` when started with `python app.py`.

You can double-click `app.bat` or use **Trade Velocity: Run App** with F5 in VS Code. The existing `scripts/run_app.py` and `run_app.bat` commands also use this launcher. On later starts, use `--skip-build` to reuse the client build. Use `--port 8001` if port 8000 is occupied, `--browser chrome` to skip the selection prompt, or `--no-browser` to open the address manually. Keep the terminal running; Ctrl+C stops the server. A second launch reuses an existing Trade Velocity server without taking ownership of it.

For frontend development, start these in separate terminals:

```powershell
.\.venv\Scripts\python.exe -m uvicorn stock_engine.api:app --host 127.0.0.1 --port 8000 --reload
cd frontend
npm ci
npm run dev
```

Open Vite's displayed address (normally http://127.0.0.1:5173). Its `/api` proxy forwards to Python on port 8000. Interactive endpoint documentation is available at http://127.0.0.1:8000/docs.

## Explore the five screens

1. **Overview:** company watchlist, 30-session sparklines, daily changes, market breadth, sector movement, and a selectable price chart. Search by company, symbol, or sector. Starred companies are saved in the browser.
2. **Markets:** eight NSE companies, official profile links, price history from one month to five years, area/candlestick charts, 20/50-day moving averages, trading volume, period returns, annualized growth, and maximum drawdown. The investment calculator illustrates adjusted-price growth.
3. **My portfolio:** a ₹10,00,000 virtual account, market buys and sells, holdings, allocation, average cost, realized/unrealized P/L, fill history, and JSON export. Load the sample portfolio to see four simulated purchases at historical reference prices. This explicitly replaces the current paper account after its confirmation dialog.
4. **Matching lab:** an independent exchange sandbox with limit/market orders, price-time priority, depth, partial executions, cancel/replace, trades, and scenario import/export. **Load example market** restores the existing two-symbol project scenario. Paper-account changes do not alter this sandbox.
5. **Experiments:** recorded median throughput at three sizes and three workloads, custom structure complexity, and fresh indexed-versus-list comparisons. New experiments check equal outcomes before timing and run in separate engines.

## Market data

The bundled snapshot contains 1,241 daily bars per company, downloaded from Yahoo Finance through `yfinance` on **28 September 2026**. Companies: Reliance Industries, TCS, Infosys, HDFC Bank, ICICI Bank, Bharti Airtel, Larsen & Toubro, and ITC. Each source link, retrieval time, and company bar date is shown in the app. The latest daily bar can be delayed or incomplete; it is not a live quote feed.

**Refresh data** fetches a complete replacement snapshot for all eight companies. An unsuccessful fetch keeps the previous snapshot. To refresh from a terminal:

```powershell
.\.venv\Scripts\python.exe scripts/refresh_market_data.py
```

Charts, growth, and moving averages use dividend/split-adjusted prices. Candlestick OHLC uses each day's adjustment ratio. Latest quotes and portfolio valuation use raw daily Close. Periods are measured relative to the most recent available bar, so the bundled app works offline. A missing or invalid snapshot produces an explicitly labeled, deterministic simulated history. Company facts remain separate from that simulated history. The tracked equal-weight company basket and sector groups are not exchange indexes.

Historical data can be revised by its provider. `yfinance` is an unofficial research/education client; consult [its documentation and data-use notice](https://github.com/ranaroussi/yfinance) before redistributing data.

## Portfolio accounting and execution

The paper broker seeds three synthetic liquidity levels on each side of each company's reference price, with 5,000 shares per level and progressively wider spreads. It submits market orders to the custom engine and accounts for actual fills. These are simulated trades against synthetic liquidity, not executions at Yahoo Finance or NSE. A market remainder expires if depth is exhausted.

- Cash decreases by the purchase notional and increases by the sale notional.
- Average cost is total remaining purchase cost divided by held shares.
- Realized P/L is sale proceeds minus the average-cost basis of the shares sold.
- Unrealized P/L is the latest raw daily mark times held shares minus remaining cost.
- Account equity is cash plus holdings' market value; total P/L is equity minus initial cash.

Money uses `Decimal` accounting rounded to paise. The account rejects insufficient cash and sells beyond owned shares. There is no short selling, brokerage, tax, or real broker integration. The sample portfolio fills are tagged with their historical reference dates, and purchase spreads apply to those reference prices too.

## Saved state and scope

The browser retains a random local session ID. The server saves successful paper-account and matching-lab commands atomically under `.marketlab/sessions/<session-id>.json`, replaying them after a restart. The account journal restores cash, holdings, and realized P/L; engine trade timestamps are regenerated during replay. Clearing browser storage starts another account, while existing server files remain. Export journals/scenarios before moving machines.

The app deliberately binds to `127.0.0.1` and runs with one server worker. Its local session token is not a production login system. Multi-user hosting would require authentication, transactional database storage, worker coordination, and deployment controls. Historical downloads require internet access; the bundled snapshot and local trading work without it. Web fonts fall back to system fonts when offline.

## Verify changes

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[app,dashboard,test]"
.\.venv\Scripts\python.exe -m pytest -q
cd frontend
npm ci
npm run build
```

The Python suite covers core matching, custom structures, replay, portfolio conservation and partial fills, invalid/rejected requests, isolated accounts, concurrent cash checks, saved-session recovery, historical-data cleanup/provenance, and comparison equivalence. The build checks TypeScript and bundles the client. CI runs Python checks on Windows/Linux and builds React on Linux. The legacy Streamlit interface remains an optional DSA demonstration tool.
