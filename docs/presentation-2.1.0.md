# TradeVelocity 2.1.0 presentation script

## Open the workspace

1. For the live demonstration, open [TradeVelocity](https://gettradevelocity.onrender.com/app?view=demo) and sign in. In the Windows app, double-click `TradeVelocity-2.1.0-Windows-x64.exe`, choose **Continue in browser**, approve the code, then select **Presentation demo**.
2. For the offline demonstration, double-click the same EXE and choose **View → Offline demo**. The app shows **Offline demo** and opens the exercise using its bundled engine. Historical prices come from the bundled snapshot.

## Show price–time priority in four clicks

| Click | What the audience should see |
| --- | --- |
| **Place Buy 1 · 10 @ ₹100** | The synthetic order book shows a bid for 10 shares at ₹100. No executions yet. |
| **Place Buy 2 · 10 @ ₹100** | The same price level shows 20 shares across two orders. Buy 1 is first in line. |
| **Place Sell · 15 @ ₹100** | The execution table shows 10 shares against Buy 1, then 5 against Buy 2, both at ₹100. The order results show Buy 1 filled in full, Buy 2 partially filled, and the sell filled in full. The book retains one bid for 5 shares at ₹100. |
| **Reset demo** | A fresh `DEMO` symbol appears with an empty order book and execution table. |

Say “The two buys offered the same price. The earlier buy filled first, and the second buy kept its five unmatched shares on the book.” The exercise runs the same matching engine in an isolated scenario. It leaves the signed-in account’s orders, holdings, and history untouched.

## Show a saved account

With internet available, open the same account in Windows and in a browser. In **Trading terminal**, point out the price timestamp, then switch to **Orders**, **Trade history**, and **Portfolio** to show the account’s saved records. The **Presentation demo** stays available independently of these records.

Offline practice data lives under `%APPDATA%\TradeVelocity\offline-demo`. The live workspace uses the hosted PostgreSQL database.

## Release and rollback

The active release workflow packages the Next.js export and the local FastAPI engine into a single Windows x64 executable. The web release uses the existing Render Docker service and database. Version 2.1.0 makes no database schema changes.

If the web deployment needs to be reverted, select the previous successful deployment in Render and choose **Rollback to this deploy**. The previous deployment serves commit `d3eb12d` and has deploy ID `dep-dc46lbl6e07s73eb0s10`. Keep the current PostgreSQL database attached. Verify `/api/ready` and sign in after rollback.
