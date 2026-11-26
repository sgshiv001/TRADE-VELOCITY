# TradeVelocity ADSA demo

## Live 2.0 beta

Open the [hosted app](https://gettradevelocity.onrender.com) before presenting so the service has time to start. Sign in to two trader accounts in separate browser profiles with the same stock selected. Follow or skip the tutorial. Stock prices and depth may change between rehearsal and presentation.

| Time | What to show | What to explain |
| --- | --- | --- |
| 0:00–0:45 | Open the **Trading terminal**, identify the reference price and its timestamp, and check **Market depth**. Prepare the selling account with at least five paper shares of the chosen stock. If needed, use a buy limit at the current best ask to acquire them before the demo. | The price chart uses market data. Orders execute against the shared simulator. |
| 0:45–1:45 | Place a buy limit for 10 shares below the best ask. Confirm the bid is at the front of the queue. In the other account, sell five shares at that price. | The best price gets priority. At the same price, the oldest order goes first. The resting bid sets the execution price. |
| 1:45–3:00 | Show the fill in **Trade history** and the five remaining shares in **Orders**. Open **Portfolio** to show the updated holdings and cash. Cancel the remaining bid after the demo. | The engine updates both accounts. A partial fill leaves the unfilled quantity on the book. |

Use the [current downloads](https://gettradevelocity.onrender.com/download) to present from a connected desktop or mobile client. The local engine demo below works with the previous Windows build if you need an offline example.

## Local engine demo with v0.3.4

On the presentation PC, extract the full Windows x64 ZIP and open
`TradeVelocity/TradeVelocity.exe`. Start at **Overview** with the local workspace
connected. Use `ACME` as the custom symbol if its book and trade history are
empty. For another rehearsal, use a fresh symbol such as `ACME2`.
[Download the TradeVelocity v0.3.4 Windows ZIP](https://github.com/sgshiv001/TRADE-VELOCITY/releases/download/v0.3.4/TradeVelocity-Windows-x64.zip)

### Three-minute run

| Time | What to do | What to explain |
| --- | --- | --- |
| 0:00–0:25 | Open **Orders & depth**, enter `ACME` in **Custom engine symbol**, and click **Use symbol**. | The engine keeps a separate buy and sell book for each symbol. Orders are simulated locally. |
| 0:25–1:15 | Submit two **Limit** sells, first 150 shares at ₹105 and then 100 at ₹106. Submit a **Limit** buy of 100 at ₹106. | The buy limit accepts either price. The engine fills all 100 shares at the lowest resting ask of ₹105, leaving 50 shares at ₹105 and all 100 at ₹106. |
| 1:15–1:55 | Point to the two rows in **Active orders**, then open **Trade history** and search for `ACME`. Show the trade for 100 shares at ₹105. | A heap finds the best price and an AVL tree keeps the depth ordered. At each price, a FIFO queue gives the earliest order priority. An order-ID hash table finds orders for cancellation. |
| 1:55–3:00 | Open **Performance**. Choose **Deep-book matching**, set **Commands** to **5,000**, then click **Run benchmark**. Compare the median **Commands / sec** for each engine. | Each engine processes the same commands and produces 2,500 trades per run. The benchmark checks that their matching outcomes agree before it times three runs per engine. The linear book scans price levels, while the indexed book uses its heap and price indexes. Throughput depends on the machine and workload. |

In the browser rehearsal, the median was about 55,700 commands per second
for the indexed engine and 7,900 for the linear engine on this workload.

If asked about scaling, let `P` be the number of active price levels on one
side. The list takes `O(P)` to find the best price. With a current heap root,
the indexed book can read the best price in expected constant time, and
inserting a new price level takes amortized expected `O(log(P + 1))`.
[Engine architecture and complexity](architecture.md)

### Terminal backup

From the repository root after completing the [Python setup](../README.md#run-it-locally),
run the existing scenario and the same benchmark from PowerShell.

```powershell
.\.venv\Scripts\python.exe -m stock_engine.cli run scenarios/order-lifecycle.json
.\.venv\Scripts\python.exe scripts/compare_engines.py --sizes 5000 --workloads deep --symbols 1 --seed 42 --repeats 3 --output (Join-Path $env:TEMP 'tradevelocity-adsa-demo.csv')
```

The scenario continues past the live demo. Point to its first trade,
`ACME 100 @ INR 105.00 (B1 / S1)`, to show the same partial fill. The second
command prints all six benchmark measurements and saves a CSV.

### Legacy Windows package verification

All seven GitHub checks passed for the **v0.3.4 Windows x64 pre-release**, and the released ZIP passed a
fresh extraction and Windows launch on this PC. The app also recovered the
demo trade and remaining orders after a local server restart during browser
rehearsal. [GitHub Actions run](https://github.com/sgshiv001/TRADE-VELOCITY/actions/runs/43043589293)

The package is unsigned. The independent Windows PC test is pending.
[Windows acceptance checklist](windows-release.md#device-matrix-and-acceptance-checklist)
