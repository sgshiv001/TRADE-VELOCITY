# TradeVelocity

TradeVelocity is a paper trading simulator we built for our Advanced Data Structures and Algorithms project at Bennett University. In the 2.0.0 demo release, you can start with ₹10 lakh in virtual funds, place limit orders, and see how the shared order book handles each fill. PostgreSQL saves accounts, orders, and portfolio records across supported devices. All trading is simulated.

[Open the live app](https://gettradevelocity.onrender.com) · [Download v2.0.0](https://github.com/sgshiv001/TRADE-VELOCITY/releases/tag/v2.0.0) · [Project website](https://sgshiv001.github.io/TRADE-VELOCITY/) · [Presentation demo](docs/adsa-demo.md)

![Historical price chart from the TradeVelocity 2.0 public preview](docs/assets/trading-preview.webp)

## Try a paper trade

1. [Create a trader account](https://gettradevelocity.onrender.com/signup) and follow or skip the first-run tutorial. You can reopen it from **Help**.
2. Open the **Trading terminal**, choose a supported stock, and check its reference price and **Market depth**. Enter a share quantity and limit price, then review and confirm the order.
3. Check **Orders**, **Trade history**, and **Portfolio** to see what filled, what remains open, and how the fill changed your virtual balance.

For a partial-fill demo, open two trader accounts in separate browsers. Place a resting bid for 10 shares. Then use the other account, which needs at least 5 shares of the same stock, to sell 5 at the bid price. If the resting order is first in line, 5 shares fill and the remaining 5 stay on the book. The [demo guide](docs/adsa-demo.md) walks through the setup.

## What you can explore

| Area | What you can do |
| --- | --- |
| Trading terminal | See simulated bids and asks, place confirmed limit orders, and inspect fills and open orders. |
| Market research | Browse supported NSE stocks, check timestamped price references, study historical charts, and save watchlists. Provider quotes may be delayed. |
| Portfolio and funds | Track virtual cash, reservations, holdings, and executions. |
| AI Analyst and Assistant | Explore technical indicators, view forecast ranges when available, and get explanations of the evidence. |
| Admin dashboard | Authorized admins can view account activity and service status. |

The [matching engine](src/stock_engine/) uses heaps for best-price lookup, AVL trees for ordered depth, FIFO queues at each price, hash tables for order lookup, and a Fenwick tree for volume queries. The [architecture notes](docs/architecture.md) explain the trade-offs and complexity. This is an educational simulator with no brokerage connection.

## Downloads

| Device | Open or download | Preview details |
| --- | --- | --- |
| Web | [Open TradeVelocity](https://gettradevelocity.onrender.com) | The free host may take a moment to wake up. |
| Windows x64 | [Download the portable EXE](https://github.com/sgshiv001/TRADE-VELOCITY/releases/download/v2.0.0/TradeVelocity-Trader.exe) | Unsigned preview connected to the hosted app. |
| macOS | [Apple silicon](https://github.com/sgshiv001/TRADE-VELOCITY/releases/download/v2.0.0/TradeVelocity-macOS-arm64.zip) · [Intel](https://github.com/sgshiv001/TRADE-VELOCITY/releases/download/v2.0.0/TradeVelocity-macOS-x64.zip) | Desktop ZIP previews with Apple notarization pending. |
| Android | [Download the APK](https://github.com/sgshiv001/TRADE-VELOCITY/releases/download/v2.0.0/TradeVelocity-Android.apk) | Debug-signed test build for Android 7 and later. |
| iPhone and iPad | [Safari installation guide](https://gettradevelocity.onrender.com/download) | Install the web app through Safari. |

See the [2.0.0 release notes](https://github.com/sgshiv001/TRADE-VELOCITY/releases/tag/v2.0.0) and the [downloads page](https://gettradevelocity.onrender.com/download) for installation details and file checksums. Android launch was checked on an emulator, and both Mac packages were validated on build runners. Live email-code signup is pending email delivery setup.

## Run it locally

Use Python 3.10+, Node.js 22, and pnpm 11.25.0. From the repository root in PowerShell:

~~~powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[app,test,postgres,accounts]"
pnpm install --frozen-lockfile
pnpm build:web
$env:TRADEVELOCITY_WEB_DIR = Join-Path (Get-Location) 'apps/web/out'
.\.venv\Scripts\python.exe scripts/browser_test_server.py --port 8804
~~~

Open `http://127.0.0.1:8804` for the local practice workspace. See [hosted setup](docs/hosted-workspace.md) for PostgreSQL and connected accounts, and the [2.0 release guide](docs/tradevelocity-2.0.md) for staging and deployment.

Run the Python tests with `.\.venv\Scripts\python.exe -m pytest -q` and the shared client tests with `pnpm test:shared`. [GitHub Actions](https://github.com/sgshiv001/TRADE-VELOCITY/actions) shows current build and test results.

## Team

We are **Hash Syndicate**. We built TradeVelocity together and focused on these areas of the project.

| Member | Project contribution |
| --- | --- |
| Shivanshu Gupta | Project concept, application design, core order-matching engine, and admin dashboard |
| Aditya Verma | Backend development, database integration, and support for app operations |
| Sourabh Gupta | Trading frontend development and testing of order placement and execution |
| Harshit Sharma | AI feature development and model training for the in-app assistant |

[Team page](docs/team.md) · [Evaluation results](docs/evaluation.md) · [AI calibration](docs/ai-calibration-report.md) · [Development log](docs/development-log.md) · [MIT license](LICENSE)
