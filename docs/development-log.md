# Detailed development and update log

## Repository publication and verified-PC presentation — 2 October 2026

The user confirmed local use and explicitly requested a README/About update
and push to the existing repository. Confirm the recorded passing Windows/web
checks first; do not represent finite tests as proof that no defect exists.

- Identify the existing public `sgshiv001/TRADE-VELOCITY` repository and `main`
  branch; compare the remote head before publication. No new repository is made.
- Add the current 0.3.3 verified-on-this-PC status, actual light/dark screenshots
  from isolated browser QA, current functionality, preserved team credits, and
  direct completion/Windows guides to the README.
- Generalize the temporary extraction path in new public evidence, remove
  links to ignored local build artifacts, and review the upload for secrets,
  private app sessions, environments, generated binaries and unrelated files.
- Publish the completed matching workspace, persistent retries/reviews, AI v3,
  Windows/security/release tools, frontend/browser tests and recorded results.
  Update the About description and topics to describe the local Windows/web
  app, not a broker connection or public multi-user exchange.
- Use normal commits/pushes without rewriting remote history. The actual
  publication SHA is available in Git history. Treat GitHub Actions outcomes
  separately from the already-passing local results; do not invent remote CI
  success. No certificate signing, purchase or live web deployment is included.

## Local completion and release checks — 1–2 October 2026

The user requested the remaining fixes and a list-format report, choosing
**tooling only; keep the app local** for Windows signing and deployment.
Application version: **0.3.3**. Work and checks below are local, not remote CI.

1. Repair the v2 high-volume seed-2009 miss using a fixed raw-count envelope.
   Require robust feature corroboration for forest alerts. Development-only
   selection over 54 candidates chooses margin 0.08, robust floor 8.0, padding
   1.0, confirmation 4.0, and size multiplier 20.0. Preserve the 24-fit/16-cutoff
   baseline and advisory isolation from matching.
2. Treat the former held-out seeds as regression cases, not untouched evidence.
   Reserve seeds 3000–3031 for a new 192-stream controlled evaluation. Fresh
   results: TP 1,536, FP 0, FN 0, TN 15,360; old regression: TP 768, FP 0,
   FN 0, TN 7,680. Two evaluator runs reproduce settings/counts. Document
   extreme synthetic deviations, repeated profiles, guard-dominant attribution,
   fixed ordering, and unvalidated real-market/baseline-contamination behavior.
3. Replace the Windows Proactor transport with Uvicorn's supported custom
   Selector-loop factory and SansIO WebSocket transport. Preserve cancellation
   handling; Python tests cover 20 disconnects and browser QA covers ten rapid
   reloads. The final browser run does not reproduce WinError 10054.
4. Add fail-closed opt-in private hosting, Secure/HTTP-only/Strict cookies,
   server-side revocation, bearer clients, HTTP/WebSocket Host/origin checks,
   rate/body/concurrency limits, and response headers. Local launches remain
   loopback-only with no login requirement. Test malformed hosts, foreign
   clients, expiration, logout, and authorized-socket revocation. This is one
   trusted operator/shared key, not isolated multi-user accounts.
5. Prepare Docker/Caddy templates and the hosting entry, but do not install
   Docker, run containers, configure DNS/TLS, or publish. The UI access-gate
   browser test is an explicit fixture; backend security tests exercise real
   ASGI routes/cookies/sockets in-process, not a live HTTPS reverse proxy.
6. Add read-only Windows prerequisite diagnostics and optional SignTool
   certificate-store signing/verification. The real local prerequisite check
   passes on Windows 11 x64, WebView2 154.0.4258.37 and .NET release 533509.
   A placeholder dry-run validates command construction without accessing a
   certificate or timestamp service. Authenticode remains **NotSigned**.
7. Rerun the full current suite: **159 passed in 29.84 seconds**, no skips.
   TypeScript/Vite production build succeeds (1,748 modules). Chromium QA:
   **10 passed in 19.7 seconds**. npm audit reports zero known vulnerabilities;
   pip check reports no broken requirements. A Node color-environment warning
   is harmless and recorded in the completion report.
8. Repackage the latest built EXE with corrected Windows instructions. CRC
   passes for 2,610 ZIP entries; EXE, frontend and calibration agree. Extract
   it into a fresh temporary folder with spaces. Use isolated LOCALAPPDATA
   and writable sessions, clear Python search settings, and restrict PATH to
   Windows/system32. No project source, virtual environment or node_modules is
   present in the extraction. Frozen prerequisite and native smoke exit 0.
9. The actual hidden WebView renders the frontend; the native smoke matches
   seven shares/one trade, measures six isolated benchmark rows, loads v3,
   checks 46 execution observations plus the high-volume regression, and
   proves monitoring leaves matching exports unchanged. Repeat while an owned
   test listener holds 8765: the app selects 57794 and releases it afterward.
   Both owned Windows processes exit. Retain the machine-readable evidence in
   [portable-smoke.json](../benchmarks/portable-smoke.json).
10. Create the [completion report](completion-report.md), update this log and
    changelog, and preserve v2 evidence under explicitly archived names. The
    generated extraction's deletion is blocked by command policy; do not use
    another deletion method to evade that restriction. Its exact path is in
    the report/receipt for optional manual cleanup. Normal app data is intact.
    No GitHub commit/push, certificate purchase/signing, or deployment occurs.

## Execution-watchdog calibration — 1 October 2026

The user's request was to complete AI calibration and provide a test report.
This work calibrates advisory execution monitoring, not real-money routing or
historical daily-bar anomaly analysis. Application version: 0.3.2.

- Replace default forest decisions with a hybrid fixed-baseline detector:
  24 fit observations, 16 cutoff observations, logged positive count/depth
  features, median/MAD guards with scale floors, and per-branch labels.
- Select parameters on 48 development streams; generate 96 held-out streams
  only afterward. Retain every candidate, aggregate result, profile/deviation
  counts, detector contributions, and every error in ai-calibration.json
  (subsequently preserved as ai-calibration-v2.json).
- Run the evaluator twice; selected settings and confusion counts reproduced.
  Result: TP 767, FP 6, FN 1, TN 7,674. The high-volume seed-2009 miss is
  documented, not eliminated by tuning against held-out evidence. Synthetic,
  partly deterministic profiles do not establish real-market fraud accuracy.
- Add Python and real-browser regression coverage for the original missed
  large execution. Preserve stable earlier severity, saved reviews, cached
  models, baseline/fit separation, and advisory matching isolation.
- The initial complete-suite run exposed a WebSocket cleanup cancellation
  race (122 passed, one failed). Reproduce it independently, shield finalization
  according to AnyIO guidance, and test 20 reconnect/disconnect cycles. The
  final complete run passed **124 tests in 19.88 seconds** with no skips.
- Production UI build succeeded; final browser run passed **5 tests in
  12.4 seconds**, including review persistence and the calibrated regression.
  Windows printed one closed-connection WinError 10054 diagnostic during that
  run; it did not fail an assertion. npm audit reported zero known
  vulnerabilities; pip check found no broken requirements.
- Rebuild the native Windows application with selected JSON settings. Hidden
  packaged smoke exited 0, rendered the frontend, matched 7 shares/one trade,
  measured six isolated benchmark rows, and exercised 46 execution observations
  in a separate calibration session. It detected AI-LARGE-BUY through the
  robust guard, loaded version v2 and the 24/16 split, and verified exported
  matching records were unchanged by monitoring. Its own server/window closed.
- Refresh the portable ZIP with this rebuilt executable and folder shortcut.
  Verify CRC integrity for all 2,655 entries and exact EXE/frontend/settings
  agreement. No app process or test listeners on 8765/8804 remained afterward.
- Write the [v2 calibration report](ai-calibration-v2-report.md), refresh current
  architecture/evaluation/README explanations, and retain archived old results.
  All changes are local; no GitHub push or production/session mutation was done.

## Operational matching workspace — 30 September 2026

The user replaced the unfinished walkthrough with removal of demo/classroom
features and selected an own-engine app without real-money execution. This
update implements Windows and local browser modes, not public deployment.

- Replace App.tsx/Experience.tsx with Workspace.tsx/Trading.tsx. Remove the
  presentation entry, injected sessions, simulator controls, DSA illustrations,
  and placeholder analytics. Show actual orders, trades, depth, provider history,
  computed metrics, and activity-based AI monitoring.
- Remove demoapp.py, its configurations/tests, preset APIs, classroom generators,
  and evaluation script. Retain the developer fixture as order-lifecycle.json;
  it is not included in the desktop package or applied to application sessions.
- New sessions start empty. Existing commands and legacy virtual-account records
  stay on disk. Add amendment, custom symbols, complete trade search/pagination,
  full CSV export, and confirmed session import/clear with engine replay checks.
- Missing history stays unavailable; no prices or counterparties are generated.
  Refresh provider history into writable user storage, preserving orders and
  cached history on failure. AI observes the user's actual executed orders.
- Keep one application entry and the Windows/browser shortcuts. No new project
  or backup folder. Update README, architecture, packaging, and CI references.

Verification: frontend build passed; **93 tests passed in 11.61 seconds**. These
include removed-route, empty-session, persistence/legacy, concurrent quantity,
amendment/replay, full-history, unavailable-data and refresh-cache regressions.

An isolated browser test submitted a sell for 5 at 100 and a buy for 3: 3 matched,
2 remained. Amended the remainder to 4 at 101; history retained the original
execution. Reopening restored the session. Canceling clear confirmation kept
records. Provider refresh returned history dated 30 September; analysis computed
results. Light/dark layouts were inspected, with no classroom controls.

Final packaged smoke: exit 0, 7 matched shares, 1 trade, 1 watchdog observation,
6 isolated benchmark rows, and rendered UI. The real Windows window also opened
with saved user records intact. Closing stopped its server. Browser testing was
stopped; ports 8765 and 8799 had no listeners afterward. GitHub was not modified.
Historical entries below describe removed features, not current instructions.

## What this log covers

This is the available project history through 1 October 2026. Two original
engine commits and the existing GitHub initialization commit have exact Git
timestamps. Later working-directory development is summarized from the
implementation and development session. Intermediate versions that were never
committed cannot be reconstructed as exact per-edit diffs.

The [change log](../CHANGELOG.md) is the readable update summary. Git history is
the exact audit of committed content. No benchmark or test result is inferred
from a diagram, screenshot, or intended feature.

## Recorded commits before publication

| Date/time (+05:30) | Commit | Recorded change |
| --- | --- | --- |
| 2026-09-24 11:59:49 | `67a4520` | Initial Python matching engine, models, structures, CLI, dashboard, tests |
| 2026-09-24 15:55:29 | `4c84a91` | Session replay, scenario, baseline experiment, reports, tests, CI |
| 2026-09-28 23:55:05 | `1814dfc` | Existing TRADE-VELOCITY repository initialized with README and attributes |

The same project's local engine and GitHub initialization originally had two
Git histories; they were not separate applications.
Publication brings them together using a merge, preserving their commits and
the existing remote branch. The publication and merge IDs are visible in
`git log --all`; this file does not embed its own future commit ID.

## Development sequence after the engine commits

The following milestones are ordered by development flow. Their intermediate
edits were not individual historical commits, so dates refer to the development
period rather than invented per-file timestamps.

1. **Custom indexing improvements:** separate-chaining hash tables replace
   built-in order/price lookup paths; resize and collision behavior is tested.
2. **Structure maintenance:** bottom-up heap construction and linear Fenwick
   rebuilding reduce rebuilding overhead; AVL/FIFO/heap/hash/Fenwick invariants
   receive dedicated tests.
3. **Lifecycle correctness:** placement, cancellation, replacement, stale heap
   entries, partial fills, and multi-symbol conservation are checked against
   reference behavior.
4. **Controlled comparison:** indexed and linear price books share matching
   rules; mixed, deep, and cancellation workloads verify equal final outcomes
   before measuring throughput and memory.
5. **Measured evidence:** custom-structure and comparison CSVs are retained,
   including repetitions/outliers and cases where lists are faster.
6. **Historical company data:** company profiles, dated OHLCV snapshot, adjusted
   indicators, refresh, provider failure handling, and simulated fallback.
7. **Paper accounting:** virtual liquidity, Decimal money, cash/positions,
   realized/unrealized P/L, and local JSON restoration.
8. **FastAPI application:** session-isolated lab/account routes, history,
   insights, import/export, and isolated experiments.
9. **Initial React interface:** Vite/TypeScript client, typed API access, charts,
   market/company/portfolio views, local session identification.
10. **Academic phase-1 setup:** configuration module, setup check, license,
    dependency list, placeholder data/report folders, and phase-1 report/tests.
11. **Trade Velocity redesign:** dark landing page and sidebar; Engine, Order
    Book, DSA Lab, Simulator, Analytics, AI Monitor, Benchmark, History.
12. **Classroom walkthrough:** 250-share multi-level execution, partial fill,
    VWAP explanation, terminal-only rehearsal, and presentation guide.
13. **Windows/VS Code launch setup:** `.venv` debug configurations, batch entry
    points, integrated-terminal launch, frontend build/run tasks.
14. **Test-client warning:** installed Starlette's httpx deprecation addressed
    by using the supported `httpx2` test dependency.
15. **Historical AI:** OHLCV feature engineering, scaler + Isolation Forest,
    normalized display scores, flags, feature descriptions, endpoint and UI.
16. **Port conflict investigation:** an already-running app owned port 8000;
    stopped test services so the user could launch from VS Code.
17. **Shared full-app launcher:** root `app.py` asks for a browser, reserves the
    port, builds React, imports the API, and runs Uvicorn in the server process.
18. **Launcher ownership and paths:** avoid the former runner's orphan server,
    fix quoted PowerShell tasks, prefer `.venv`, fix Windows paths with spaces,
    identify existing servers, and preserve delegated exit codes.
19. **Regression and startup checks:** complete app/API and debugger smoke runs,
    existing-server reuse, other occupied services, fallback browser behavior,
    and server-port release.
20. **Existing repository publication:** connect this project to the user's
    existing TRADE-VELOCITY remote, expand the README, record this log/change
    history, define contributions, review upload scope, and extend launcher CI.

## Historical file inventory before launch-file cleanup

This table records the publication state. Some files below were later removed
or renamed during cleanup; use the README for the current project structure.

| Files / directory | Implemented responsibility or update |
| --- | --- |
| `src/stock_engine/models.py` | Orders, sides, trades, results, and Decimal fields |
| `src/stock_engine/structures.py` | FIFO, hash tables, heaps, AVL trees, Fenwick indexes |
| `src/stock_engine/engine.py` | Symbol books, matching, cancellation/replacement, statistics |
| `src/stock_engine/session.py` | Successful command journal, save/load, deterministic replay |
| `src/stock_engine/cli.py` | Demonstrations, replay, benchmark, threaded submissions |
| `src/stock_engine/experiments.py` | Linear book, workload generator, verification, timing/memory |
| `src/stock_engine/companies.py` | Historical-company metadata and source links |
| `src/stock_engine/market_data.py` | OHLCV load/refresh, serialization, fallback, indicators |
| `src/stock_engine/data/market-history.json` | Dated bundled input data with source metadata |
| `src/stock_engine/portfolio.py` | Virtual-account liquidity and Decimal accounting |
| `src/stock_engine/analysis.py` | Rule-based historical evidence and insights |
| `src/stock_engine/anomaly.py` | Historical proxies, scaling, Isolation Forest, report |
| `src/stock_engine/api.py` | HTTP routes, local session persistence, frontend mount |
| `frontend/src/App.tsx`, `styles.css` | Active dark interface and educational/demo interactions |
| `frontend/src/api.ts`, `types.ts` | Typed API/session access and formatting |
| `frontend/src/charts.tsx`, `main.tsx` | Chart helpers and React entry point |
| `frontend/package*.json`, Vite/TS config | Client dependencies, lockfile, build configuration |
| `frontend/index.html`, `public/favicon.svg` | HTML shell and favicon |
| `dashboard.py` | Legacy Streamlit matching/experiment interface |
| `app.py`, `app.bat`, `run_app.bat`, `scripts/run_app.py` | Shared complete-app launcher and entry points |
| `class_demo.py` | Deterministic teaching walkthrough and shared app startup |
| `scripts/benchmark.py`, `compare_engines.py` | Repeatable benchmark output |
| `scripts/refresh_market_data.py` | Explicit historical-data refresh |
| `benchmarks/*.csv` | Dated baseline, custom-structure, and comparison measurements |
| `scenarios/demo.json` | Nine-event, two-symbol matching scenario |
| `config/`, `main.py` | Academic defaults and configuration check |
| `tests/` | Engine/structure/lifecycle, API/account, data, AI, CLI, and launcher coverage |
| `docs/` | Architecture, methods/results, guides, phase-1 setup, development record |
| `docs/screenshots/marketlab-overview.png` | Screenshot from the earlier MarketLab interface |
| `data/`, `reports/`, `benchmarks/results/` | Placeholder output directories retained with `.gitkeep` |
| `.vscode/` | Shareable Python debug and build/run tasks |
| `.github/workflows/tests.yml` | Windows/Linux Python checks and frontend/launcher job |
| `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md` | Description, update history, future contribution procedure |
| `pyproject.toml`, `requirements.txt` | Package/extras and supplemental dependencies |
| `.gitignore`, `.gitattributes`, `LICENSE` | Upload exclusions, text handling, MIT source license |

## Verification already completed during launcher development

- Frontend: TypeScript checking and Vite production build completed.
- Targeted API/launcher suite: **13 passed in 9.53 seconds**.
- Launcher-only rerun after Windows delegation fix: **4 passed in 4.25 seconds**.
- Full-build startup: `/` and `/api/health` returned HTTP 200; `/api/market`
  returned eight companies. The deterministic classroom walkthrough matched
  250 shares over three prices and left 50 shares in its separate partial-fill
  example.
- Bundled debugpy startup and Ctrl+C shutdown succeeded. Test app/debugger ports
  were checked free afterward. This is a runtime smoke check, not proof that
  every rendered UI control is connected or visually verified.

## Publication validation

Completed on 29 September 2026 in the existing Windows project environment:

- Full suite: **85 passed in 13.16 seconds** with no skipped tests reported.
- `npm run build`: TypeScript check and Vite production build succeeded;
  Vite reported 1,743 transformed modules and 1.49 seconds for its build.
- `python -m pip check`: no broken requirements found.
- Scenario replay: nine events, four trades; ACME executed 190 shares and TECH
  executed 40 shares.
- All local Markdown links in README, change log, contribution guide, and this
  development log resolve to existing files.
- Upload review found 83 project files at preparation time. Local environments,
  installed dependencies, production builds, caches, saved sessions, the nested
  clone, and unrelated coursework are ignored. A file-content check found no
  matching GitHub/OpenAI token strings or private-key markers; it is a targeted
  check, not a guarantee that all possible sensitive formats are detectable.
- The existing GitHub API identified `sgshiv001/TRADE-VELOCITY` as public with
  default branch `main`. Its initial commit was fetched before integrating the
  histories.

### Verified GitHub publication

Implementation commit `c331e27` records 75 changed files, 7,518 insertions,
and 68 deletions relative to the preceding local engine commit. Merge
`4e159b8bb09fb5213c13e7c88f4dc3c67d8a3093` integrates the existing remote's initial
history. The push fast-forwarded `sgshiv001/TRADE-VELOCITY` `main` from
`1814dfc` to `4e159b8` without force.

GitHub's remote branch SHA matched the merge commit. Its recursive file tree
contained 83 project files, including the README, change log, this development
log, launcher, API, npm lockfile, launcher tests, and workflow. GitHub Actions
started for that push; its hosted outcome was still pending when this record
was written. The 85-test result above is the completed local validation.

A documentation-only follow-up records this verified publication; its exact
commit ID and any later updates are available from Git history.

## Upload scope

Publish source, lockfile, tests, guides, measured benchmark CSVs, scenario,
bundled historical data, and shareable launch/CI configuration. Keep `.venv`,
`node_modules`, builds/caches, local `.marketlab` sessions, logs, and secrets
local. The nested clone and unrelated lab-assignment documents are excluded;
their local files were preserved during publication.

## Single-folder correction — 29 September 2026

The user clarified that the existing `ADSA PROJECT` folder is the project named
Trade Velocity. Updating the initially empty nested checkout during publication
had duplicated its files; a second working project was not needed.

Both checkouts had the same Git HEAD and no uncommitted nested changes. All 83
tracked files matched after accounting for LF/CRLF endings. The original working
root already contained every application file, so consolidation required removing
the redundant copy, not overwriting or combining conflicting source versions.
The nested checkout is no longer inside the working project. Its original
environment, installed dependencies, local sessions, and GitHub connection remain
in the original root.

A temporary external backup was made before the user specified no backups.
Automatic command policy rejected both the combined check/removal and the
separately verified exact-path removal, so that redundant external copy still
requires manual deletion. No further copies or backups were created. README and
contribution guidance now describe one project and one working folder.

## How to maintain the complete committed history

For each future change, add a dated entry to `CHANGELOG.md`, describe the
verification and affected files here when material, and commit the change.
Use these commands to inspect exact committed differences:

```powershell
git log --all --date=iso-strict --format=fuller --stat
git log --all --name-status
git show <commit-id>
git diff <older-commit> <newer-commit>
```

Do not add credentials, personal session exports, unmeasured performance
claims, or reconstructed timestamps to the development log.

## Launch-file and presentation cleanup — 29 September 2026

The user requested one full-app launcher and one working demonstration. The
current entry files are `app.py` and `demoapp.py`. The demonstration now checks
multi-price execution, VWAP, FIFO priority, partial remainder, and cancellation
using the actual matching engine before opening the same application.

Removed the alternate batch/build launchers, old `main.py`/phase-1 configuration,
supplemental requirements file, legacy Streamlit interface/tests, obsolete
setup/demo/app guides and problem-statement copy, unused frontend chart/AI code,
outdated screenshot, and empty output placeholders. Supporting engine modules,
current API/UI, market snapshot, benchmark scripts/CSVs, scenario, tests, and
design/evaluation reports remain. Deletions are recoverable from prior commits,
with no additional backup directory.

README now explains **TradeVelocity** as trade plus the speed/flow of orders,
and describes the problem: efficiently find compatible prices while preserving
FIFO fairness and accurate order/trade state. The full academic title is kept
under the project name. The existing public `sgshiv001/TRADE-VELOCITY`
repository's description was updated to the full project title and the
Python/FastAPI/React stack. Topics now cover ADSA, data structures, order matching,
market simulation, Isolation Forest, Python, FastAPI, and React. Repository name,
visibility, default branch, and existing history were preserved.

### Cleanup validation

- Full local suite: **83 passed in 11.74 seconds**, with no skipped tests or
  warning summary. This includes the three demonstration regression checks and
  integration checks for both `app.py` and `demoapp.py`.
- Both entry files started real Uvicorn servers, returned a healthy app identity
  and the built frontend with the TradeVelocity title, reused an existing app
  from another Python interpreter, and released their ports after shutdown.
  The integration tests stopped their own temporary servers.
- Terminal-only demonstration: all engine checks passed. The 250-share purchase
  executed 50 at 105, 100 at 106, and 100 at 107; VWAP was 106.20. Separate checks
  verified the 50-share partial remainder, same-price FIFO, and cancellation.
- `npm run build`: TypeScript and Vite production build succeeded; Vite reported
  1,743 transformed modules and 2.15 seconds for its build. Unused Recharts
  dependencies were pruned and the npm lockfile was updated.
- `python -m pip check`: no broken requirements found.
- Verified the root has only the two Python application entry files; 60 project
  files remain in the upload scope. Local Markdown links (18 checked) resolve,
  and VS Code/frontend JSON configurations parse successfully.
- `git diff --check` passed. No additional backup directory was created. Local
  environments, installed dependencies, session journals, caches, and unrelated
  coursework stay excluded from publication.
- Automatic approval review rejected removal of two generated `config` bytecode
  files and leftover empty placeholder directories. No alternate deletion method
  was attempted; these local leftovers are excluded or have no tracked files,
  so they do not appear in the uploaded repository.

The cleanup commit and its verified remote state are available in Git history;
the hosted CI outcome is separate from the completed local checks above.

## Windows folder shortcut — 29 September 2026

At the user's request, added `Launch_TradeVelocity.bat` directly in the existing
project root. Double-clicking opens a console, enters the launcher's own folder,
and runs the existing `app.py` with `.venv\Scripts\python.exe`. Browser selection,
frontend building, server reuse and port handling remain in the shared Python
launcher. The batch file forwards options, preserves the Python exit status,
and pauses on missing setup or startup failure so errors remain visible. It does
not create another Python application or detach a background server.

README explains the shortcut. `.gitattributes` specifies CRLF for batch files.
Windows regression checks copy the wrapper and real `app.py` to a temporary path
with spaces, launch from another directory, verify existing-server reuse and
option forwarding, check missing-environment guidance, and preserve argparse's
exit code for an invalid port. The tests do not open a user's browser or stop an
unrelated process.

Validation: **85 tests passed in 12.40 seconds** with no skipped tests or warning
summary. `git diff --check` passed. Saved app sessions were preserved; no new
project or backup folder was created.

## Desktop, professional themes, and execution watchdog — 29 September 2026

The requested next-stage upgrade stays in the existing project and reuses
`app.py` as the Python entry point. Browser mode and `demoapp.py` remain intact.

Implementation:

- `ExchangeSession` derives execution telemetry from successful commands and
  rebuilds it on replay. Imported telemetry cannot override engine outcomes.
  Features describe actual executed-order quantities and prices, the number of
  fills, submitted quantity, and pre-command top-30-level bid/ask depth.
- `watchdog.py` fits a StandardScaler/Isolation Forest on the first 40 execution
  observations for each supported lab symbol and scores subsequent observations
  without fitting on them. Alerts remain advisory; matching rules are unchanged.
- The classroom scenario generates 90 executions from 180 real commands: 40
  training, 20 unseen normal, 10 injected spikes, 20 subsequent normal. Labels
  are withheld from the model and used only for evaluation. The measured result
  is 10 detected, 0 missed, 7 false alarms, 33 correct normal; precision 58.8%,
  recall 100%. These numbers are synthetic, not a fraud-accuracy claim.
- The Simulator submits a seeded workload to the real session instead of
  incrementing animated estimates. Its timing includes telemetry. Benchmark
  controls execute the existing indexed/linear comparison with three repeats.
- Add buy/sell limit and market order entry, visible acknowledgements/errors,
  cancellation, full command export, and an explicit reset confirmation. History
  labels its newest-100-trade limit; engine totals use the full trade count.
- Add a bright default theme, a saved slate dark mode, responsive forms, rounded
  surfaces, readable hierarchy, keyboard focus states, and a code-native TV icon.
  Remove external font fetching. Recover stale local sessions for all APIs.
- Prevent stale desktop HTML after upgrades with a frontend-build fingerprint
  on the window URL and `no-store` headers on entry HTML and API responses.
- Add `app.py --desktop`, a pywebview/WebView2 window, `Launch_Desktop.vbs`, and a
  PyInstaller spec/build script. The portable app contains Python and built UI;
  target Windows PCs still require WebView2. It is not a signed installer.
- Desktop storage is separate under `%LOCALAPPDATA%\TradeVelocity`. Startup
  reserves loopback port 8765 or falls back to an OS-selected port; closing the
  window stops only its own server. Build replacement is limited to the generated
  `dist/TradeVelocity` folder; saved sessions are outside build output.

Verification:

- Production TypeScript/Vite build succeeded.
- Final local suite: **96 passed in 16.86 seconds**, including warmup, holdout,
  replay, API isolation, input validation, simulator scenarios, and desktop
  server teardown. Desktop unit tests replace only the GUI; real API processing
  runs in them. CI without optional desktop dependencies skips those GUI tests.
- Actual native-window smoke test succeeded with real AI, simulation, benchmark,
  and production frontend rendering. Its server was stopped after the test.
- Packaged `TradeVelocity.exe --smoke-test` exited **0** and recorded `ok: true`,
  50 heldout observations, 10 detected spikes, six benchmark rows, and 100
  simulation commands. Smoke sessions/profile are separate from user sessions.
- The root VBS shortcut starts the packaged EXE with a visible window (style 1),
  rather than hiding the GUI. Its first hidden-style check was corrected before
  handoff. The shortcut and real packaged window were both checked locally.
- Computer-use screenshots verified the real desktop welcome, workspace, and
  light/dark watchdog layouts. Later input verification was limited by the UI
  helper reporting `failed to activate captured window`; no claim is made that
  every frontend interaction was exercised through that helper.
- Fresh 54-row comparison evidence is saved as `desktop-comparison.csv`; the
  earlier comparison CSV and its documented tables were preserved unchanged.
  AI evaluation includes Python/model/platform provenance in JSON.

The build and dist directories are ignored generated artifacts, not another
source project. These changes are local; no GitHub push was requested in this
upgrade turn.
