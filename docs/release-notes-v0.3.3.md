# TradeVelocity v0.3.3 — Windows release notes

**Local release candidate, prepared 3 October 2026. Not published.**
This is the full application, not a presentation or preset-data edition.
Publish only after the user finishes testing and approves the release.

## Included

- Windows x64 desktop window and the shared local web application.
- Price/time order matching, limit/market orders, partial fills, amendment and
  cancellation, custom symbols, depth and complete execution history.
- Persistent SQLite sessions, retry-safe commands, timestamp-preserving
  export/import and saved AI investigation notes.
- Light/dark themes, readable company lists, watchlists, historical charts and
  responsive workspace pages.
- Advisory calibrated execution watchdog v3 with fixed baseline, explicit
  detector attribution and the previously missed large-execution regressions.
- Read-only Windows prerequisite checks, automatic desktop port selection and
  shutdown of the application's own server.
- Portable ZIP with a double-click launcher, bundled Python/UI, `START-HERE.txt`
  manual-test instructions and the full Windows guide.

## Test before publication

Local automated verification on 3 October: **159 Python tests in 20.45 seconds**,
**10 browser tests in 17.0 seconds**, production frontend build, and actual
packaged Windows smoke passed. Native smoke checks UI rendering, the live
WebSocket status, seven matched shares/one trade, six measured benchmark rows,
46 AI observations, both regression cases, and release of its owned port.
Normal user sessions were not read or cleared by these isolated checks.

Extract the whole ZIP and read `START-HERE.txt`. Test launch, matching, saved
data after restart, amendment/cancellation, themes, exports and shutdown. Use a
new custom symbol to avoid interacting with existing open orders. Keep the
original records; do not clear the session just to run the checks.

The latest archive hashes and automated smoke receipt are generated locally
under `dist/`. Existing reports retain their historical verification dates and
hashes; they are not measurements of every later rebuild. A different physical
PC still needs its own test. Passing automated checks is not user acceptance.

## Boundaries

Requires Windows 10/11 x64, WebView2 Evergreen and .NET Framework 4.6.2+.
This portable EXE is unsigned; do not disable system security to run it.
No broker connection, real-money execution, public deployment, or automatic
counterparties are included. Provider history is dated daily data, not live
quotes. AI scores request human review; they are not fraud probabilities.

Source on GitHub and an uploaded Windows release are separate. This local
package preparation does not push files, upload assets, create a release, or
deploy the web application.
