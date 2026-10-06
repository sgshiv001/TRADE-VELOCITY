# Change log

This log records the project implemented through 2 October 2026. Original
commit dates are taken from Git. Later milestones summarize the development
session and current files; they do not imply separate commits existed for every
intermediate edit. See [the detailed development log](docs/development-log.md)
and `git log --all --stat` for the full available record.

## 2026-10-03 — Prepare Windows 0.3.3 locally before manual acceptance

- Rebuild the full portable Windows app from the current source; do not create
  a GitHub release, upload binaries, deploy, commit, or push this preparation.
- Include `START-HERE.txt` with direct launch and safe matching/restart/export
  checks using a separate custom symbol without clearing existing records.
- Repair the obsolete explicit SansIO hidden-import name by reading Uvicorn's
  installed protocol mapping in the build specification. Its standard hook
  already collected the implementation; this removes the misleading build error.
- Strengthen native smoke to require live WebSocket UI status as well as
  frontend rendering, matching and AI checks. Add receipt assertion coverage.
- Verification: **159 Python tests in 20.45 seconds**, **10 browser tests in
  17.0 seconds**, production UI build and actual frozen native smoke passed.
  Run with isolated writable storage and Python/Node excluded from PATH. The
  app releases its own port and preserves normal user data.
- Retain the regenerated CRC/SHA-256 manifest and local acceptance receipt in
  `dist/`; preserve older reports with their original dates/hashes. Signing and
  different-PC validation remain outstanding. User testing/publication are pending.

## 2026-10-02 — Publish the tested local application and repository presentation

- Update the README with verified Windows/web status, exact local test counts,
  launch/build instructions, actual light/dark screenshots, team credits, and
  clear boundaries rather than an unsupported zero-defect claim.
- Prepare publication to the existing public `sgshiv001/TRADE-VELOCITY` main
  branch, including current app source, tests, measured results and guides.
- Refresh the repository About description/topics to match Windows desktop,
  local web matching, persistent sessions and advisory AI analytics.
- Keep generated builds, dependencies, saved sessions, credentials and unrelated
  coursework out of Git. Generalize the machine-specific temporary path in
  published evidence and remove links to ignored local build outputs.
- Local app verification is unchanged: 159 Python tests, 10 browser tests and
  frozen Windows smoke passed. Remote CI status is separate and is available
  on GitHub Actions; source publication does not deploy the application.

## 2026-10-02 — Local release hardening and watchdog v3, application 0.3.3

Implementation and verification ran on 1 October; the completion report and
final documentation were finished on 2 October (India time).

- Repair the previous high-volume AI miss with a fixed raw-count envelope and
  require robust corroboration for forest alerts. Select five settings using
  54 candidates on development data; retain the old evaluation as regression
  evidence and reserve new seeds 3000–3031 only after selection.
- Controlled fresh result: 1,536/1,536 extreme deviations detected, zero false
  alerts among 15,360 normal controls. Explicit guards account for most alerts;
  these finite synthetic results do not establish real-market fraud accuracy.
- Use a supported Selector event loop and SansIO WebSocket transport on Windows;
  repeated reconnect/disconnect checks no longer reproduce WinError 10054.
- Add local Host/origin/client restrictions, bounded requests and payloads,
  security headers, and optional single-operator access-key/cookie protection.
  Prepare non-root Docker/Caddy HTTPS templates without deploying them.
- Add read-only Windows/WebView2/.NET diagnostics, fail clearly on missing
  prerequisites, and prepare certificate-store signing with verification and
  dry-run support. The current portable executable remains unsigned.
- Build a verified portable ZIP with CRC and SHA-256 manifest. Run the frozen
  application from a fresh folder with spaces and isolated writable data,
  excluding Python/Node from PATH. Native matching, UI rendering, both AI
  regressions, clean shutdown, and occupied-port recovery pass.
- Final checks: **159 Python tests in 29.84 seconds**, **10 browser tests in
  19.7 seconds**, production UI build, healthy Python requirements, and zero
  known npm vulnerabilities. The browser gate test uses a UI fixture; real
  API/cookie/WebSocket controls have separate in-process tests, not live TLS QA.
- Publish the local [completion/test report](docs/completion-report.md), current
  [AI report](docs/ai-calibration-report.md), and Windows/private-hosting guides.
  Preserve the v2 report and measurements. No signing, deployment, purchase,
  GitHub push, or user-session clearing occurred. Automated cleanup of the
  generated temporary extraction was blocked; its location is in the report.

## 2026-10-01 — Calibrated execution watchdog, application 0.3.2

- Split the fixed 40-execution baseline into 24 fitting and 16 cutoff
  observations. Combine Isolation Forest with explicit robust-deviation guards,
  log-transformed count/depth features, fixed-cutoff severity, and detector labels.
- Select forest margin 0.08, robust floor 6.0, and padding 1.0 on development
  workloads only. Package the selected settings for Windows and browser modes.
- Add an isolated reproducible evaluator with 16 candidates, separate held-out
  seeds, comparison to the old method, detector attribution, and all error cases.
- Held-out controlled result: 767/768 deviations detected, 6/7,680 normal
  controls falsely flagged; precision 99.22%, recall 99.87%. Explicit guards
  account for most detections. One high-volume miss is retained and documented;
  these are not real-market fraud accuracy figures.
- Cover the original repetitive-baseline miss in Python, browser, and packaged
  Windows checks; verify AI reporting does not change matching records.
- Repair WebSocket disconnect cleanup exposed by the complete suite and add
  repeated-disconnection coverage. Preserve request cancellation semantics.
- Verification: 124 Python tests, 5 browser tests, production UI build, dependency
  checks, and native Windows smoke passed. See the
  [archived v2 calibration report](docs/ai-calibration-v2-report.md) for warnings and limits.
- Update README, architecture, evaluation references, and local Windows build.
  No user session was seeded/cleared; no GitHub push was performed.

## 2026-09-30 — Windows and web matching workspace without presets

- Replace the presentation interface with operational overview, order entry,
  depth, market history, execution monitoring, full trade history, and measured
  performance tools. Both modes use the same engine and application source.
- Remove demoapp.py, classroom generators and APIs, injected trading sessions,
  generated-price fallback, and illustrative data-structure/analytics screens.
  New sessions are empty; saved records are preserved rather than erased.
- Add order amendments, custom symbols, full-history search/pagination and CSV
  export, plus session import with confirmation and engine replay validation.
- Refresh actual provider history into writable application storage. Missing
  history stays unavailable; failed refreshes preserve orders and cached data.
- Remove virtual-account operations from the app; preserve legacy account data
  on disk. Execution remains local, without a broker or real-money transfers.
- Update Windows packaging, VS Code configurations, README, and architecture.
- Verification: production frontend build; 93 tests passed; packaged smoke exit
  0 with 7 matched shares and 1 trade; real Windows window opened and shut down;
  browser matching/amendment/history, provider refresh, analysis, and themes
  checked. The provider returned history dated 30 September 2026.

## 2026-09-29 — Readable dropdowns in dark mode

- Apply the dark color scheme to native select menus and set option text and
  background colors explicitly, including the company picker and other lists.
- Rebuild and visually check the Windows desktop app with the company menu open.

## 2026-09-29 — Complete automated build checks

- Build the production React interface once on GitHub Actions and pass that
  build to every Python test job, so launcher integration checks can run.
- Run the full Python suite on Ubuntu and Windows with Python 3.11 and 3.13;
  install the desktop runtime on Windows so desktop lifecycle tests run there.
- Show the current workflow status in the README.

## 2026-09-29 — Repository presentation

- Refresh the README with a concise project overview, clear safety boundary,
  technology badges, faster setup instructions, and direct links to the demo,
  architecture, measured results, and development history.
- Add an accessible, repository-native SVG illustrating order entry, matching,
  simulation, and the separate AI execution watchdog.
- Explain the TradeVelocity name and the order-matching problem in plain language;
  clarify that AI flags unusual simulated executions for human review and does not
  make trading or matching decisions.

## 2026-09-29 — Desktop app, professional themes, and execution watchdog

- Add an optional native Windows desktop window through `app.py --desktop`,
  folder launch via `Launch_Desktop.vbs`, a portable PyInstaller build, and a
  generated TV icon. Bundle Python and the built UI; retain browser mode.
- Persist desktop sessions under `%LOCALAPPDATA%\TradeVelocity`; bind only to
  loopback, fall back from occupied ports, and stop the owned server on close.
- Default to a clean light interface, add a saved slate dark theme, rounded
  cards, improved typography, keyboard focus indicators, responsive forms,
  and local font fallbacks without external font downloads.
- Fingerprint desktop entry URLs and avoid cached entry HTML/API state after
  rebuilding, while preserving saved accounts and theme preferences.
- Replace animated simulator estimates with backend order execution controlled
  by scenario, seed, quantity, buy probability and market-order percentage.
- Add a manual buy/sell order ticket, cancellation controls, complete session
  export, and a confirmed lab reset. Clearly label the newest-100-trade view.
- Monitor actual execution features with a fixed 40-observation baseline;
  never fit on the later scored observations. Keep historical AI separate.
- Add a repeatable classroom demo: 40 training and 50 held-out observations,
  including 10 injected spikes. On this machine: 10 detected, 0 missed, 7 false
  alarms, 33 correct normal observations; synthetic precision 58.8%, recall 100%.
- Add real in-app indexed/linear benchmark execution and export. Retain earlier
  benchmark evidence; save this run separately as `desktop-comparison.csv`.
- Verify 96 local tests, including actual API calls with desktop lifecycle
  checks. Native and packaged-window verification is recorded in the log.

## 2026-09-29 — Add a Windows double-click shortcut

- Add `Launch_TradeVelocity.bat` in the existing project folder at the user's
  request. It delegates to `app.py` rather than duplicating the application.
- Use the project `.venv` and the launcher's own directory, including paths with
  spaces. Keep browser selection, forward command-line options, and leave
  startup/setup errors visible in the window.
- Keep `app.py` and `demoapp.py` as the only Python entry files. Update README
  with the double-click instructions.
- Ensure batch files use CRLF line endings on checkout. Add Windows checks for
  paths with spaces, another working directory, missing setup, option forwarding
  and preservation of Python error codes. Full local suite: **85 passed**.

## 2026-09-29 — Simplify launch files and project presentation

- Use the name **TradeVelocity** with the full title **High-Performance Stock
  Market Order Matching Engine with Advanced Data Structures, Market Simulation
  and AI Analytics**.
- Keep `app.py` as the full-app launcher; rename the presentation entry to
  `demoapp.py` and add verified price/FIFO/partial-fill/cancellation/VWAP examples.
- Update VS Code run/demo configurations and launcher regression paths.
- Remove batch/compatibility launchers, the phase-1 setup entry/configuration,
  duplicate requirements list, legacy Streamlit dashboard and its tests, and
  obsolete guides/problem-statement file.
- Remove empty output placeholders, an outdated screenshot, unused chart code,
  unused AI page, and unused Recharts/Streamlit dependencies. Python dependencies
  now have one source of truth in `pyproject.toml`.
- Shorten README with the meaning of the project name, the problem being solved,
  two run commands, a compact structure, and clear feature limitations.
- Keep the matching engine, API, historical data, benchmark evidence, current
  tests, and complete Git history. Removed files remain recoverable from Git;
  no new backup folder is created.
- Update the existing public GitHub repository's description and topics without
  creating or renaming a repository.
- Validation: **83 tests passed**, TypeScript/Vite production build succeeded,
  both entry files served the built UI and released their ports, and the
  terminal demo passed all matching checks. See the development log for details.
- Automatic approval review blocked removal of leftover local cache/empty
  directories. These directories are not part of the GitHub upload.

## 2026-09-29 — Consolidate the single project folder

- Clarified that the original `ADSA PROJECT` working folder and Trade Velocity
  are the same project, not separate applications.
- Verified all 83 tracked files in the nested checkout matched the original
  checkout, apart from Windows line endings; no unique edits required merging.
- Removed the nested checkout from the working project. The original root
  retains all source, Git history/remote, Python environment, frontend
  dependencies, and local sessions.
- Updated README/contribution guidance to use the original single working root.
- A temporary duplicate backup was created before the user clarified that no
  backup should remain. Its deletion was requested and attempted, but automatic
  command policy rejected removal. It remains outside the project pending manual
  deletion; the project itself has no nested duplicate.

## 2026-09-29 — Complete launcher and GitHub publication

### Added

- Root `app.py` to run the complete React + FastAPI application.
- Browser selection for Edge, Chrome, Firefox, and the system default, plus
  `--browser`, `--no-browser`, `--port`, and `--skip-build` options.
- Windows `app.bat`, and compatibility through `run_app.bat` and
  `scripts/run_app.py`.
- Startup dependency checks with a project-interpreter installation command.
- `tests/test_launcher.py` covering other occupied services, reuse of an
  existing app, missing-browser fallback, frontend serving, and server cleanup.
- Comprehensive current README, this change log, detailed development log,
  contribution instructions, and a documented future-update workflow.

### Changed and fixed

- VS Code **Trade Velocity: Run App** now launches root `app.py` with the
  project's `.venv` and an interactive integrated terminal.
- The run task uses a process command with separate arguments, avoiding a
  quoted executable being misinterpreted by PowerShell.
- The classroom launcher delegates server/browser handling to the shared
  launcher after its deterministic walkthrough.
- Uvicorn runs in the selected interpreter's server process instead of a
  detached child of the former build runner. Stopping the configured VS Code
  launcher releases the server port.
- System-Python launches delegate to `.venv` with properly quoted arguments;
  this fixes paths containing spaces and preserves the child exit status.
- The launcher reserves its port before building, reports occupied ports, and
  reuses only a health response identifying this application.
- `/api/health` now includes `application: trade-velocity`.
- Browser opening happens after server startup. Missing browser executables
  fall back to the system browser; failures retain a usable local URL.
- Git excludes local session journals, environments, dependencies, build
  caches, `.env` files, the embedded clone, and unrelated coursework.
- CI's frontend job also runs launcher checks against its real production
  build; the port-release assertion handles Windows/Linux socket semantics.
- The existing `sgshiv001/TRADE-VELOCITY` remote is used. Original engine history
  and the GitHub repository's initial commit are retained without a force push.

### Validation

- Frontend production build succeeded during launcher verification.
- Targeted launcher/API run: **13 passed**; launcher checks were rerun after the
  Windows delegation fix: **4 passed**.
- A full launcher built the UI and served `/`, `/api/health`, and market data for
  eight companies. Ctrl+C completed application shutdown.
- A smoke run through the VS Code extension's bundled debugpy also started and
  stopped successfully. These checks do not imply every UI interaction was
  browser-tested.
- Publication validation: **85 tests passed in 13.16 seconds**, production
  frontend build succeeded, dependency check passed, and the demo scenario
  replayed with nine events/four trades. See the detailed development log.
- Published 83 project files to the existing public repository's `main` branch.
  Implementation commit: `c331e27`; history-integration merge: `4e159b8`.
  GitHub's remote SHA and file tree were verified after the successful push.
  GitHub Actions started for that push; local results above are separate from
  its eventual hosted CI result.

## 2026-09-28 to 2026-09-29 — Historical AI and runtime fixes

### Added

- `anomaly.py`: 13-feature OHLCV preparation, StandardScaler, and a 150-tree
  Isolation Forest with seed 42.
- Normalized display scores, model flags, latest feature vector, recent
  timeline, and historical-proxy descriptions.
- `GET /api/ai/anomalies/{symbol}` and active React AI Monitor integration.
- `tests/test_anomaly.py` for feature preparation and anomaly reports.
- Deterministic `class_demo.py` with multi-price matching, VWAP, and partial
  execution, plus terminal-only rehearsal and presentation guidance.

### Fixed

- Test dependencies switched to `httpx2>=2,<3` for the installed Starlette
  TestClient, removing its non-blocking httpx deprecation warning in the tested
  environment.
- Python app dependencies include Uvicorn, FastAPI, NumPy, pandas, scikit-learn,
  and yfinance; launch configuration uses the project interpreter.
- Classroom terminal output uses ASCII-safe separators for Windows consoles.
- Running development servers were stopped after port-8000 contention was
  identified. The later shared launcher provides explicit occupied-port checks.

### Limitations recorded

- Historical order-flow fields are proxies, not observed exchange orders.
- The model fits and scores the same window; displayed unusualness is neither
  fraud probability nor validated forecasting accuracy.
- The displayed top features are standardized deviations, not causal/model
  attributions.
- The original debugger-specific missing-Uvicorn error was not reproduced in
  the old runner; the shared launcher now uses direct imports and was verified
  under bundled debugpy.

## 2026-09-28 — React application, data, experiments, and academic setup

### Application and market data

- Added FastAPI routes for sessions, matching lab, account actions, history,
  analysis, and recorded/fresh experiments.
- Added the React/TypeScript/Vite client, typed API helpers, charts, CSS, favicon,
  and locked npm dependency file.
- Implemented the initial MarketLab company/portfolio interface, then redesigned
  the active layout as the dark Trade Velocity engine laboratory with landing
  page, responsive sidebar, and eight navigation pages.
- Added profiles and dated history for eight NSE companies, adjusted-price
  indicators, provider refresh, snapshot serialization, and explicit simulated
  fallback handling.
- Added a Decimal-based paper broker with synthetic liquidity, cash/holdings,
  realized/unrealized P/L, and atomic local account/lab session journals.
- Added rule-based historical insight generation separate from matching.

### Core structures and measurements

- Added separate-chaining hash tables for order IDs and direct price-level
  lookup, with growth/shrink behavior and cached hashes.
- Added bottom-up heap construction, linear Fenwick-capacity rebuilds, and
  tests for structure invariants, collisions, lifecycle operations, churn,
  reference matching, and concurrency.
- Added an unsorted-list price-book comparison engine, controlled mixed/deep/
  cancellation workloads, final-outcome verification, alternating timed runs,
  and separate memory measurements.
- Recorded `benchmarks/custom-structures.csv` and `benchmarks/comparison.csv`.
  Updated architecture, complexity, evaluation, and measured-result reports.
  Results include workloads where lists have lower overhead.

### Academic setup and documentation

- Added central `config/settings.py`, root `main.py` setup check, supplemental
  `requirements.txt`, MIT license, and phase-1 documentation/tests.
- Added placeholder directories for raw/processed/generated data, benchmark
  outputs, and report figures/results.
- Added problem statement, app/demo/classroom guides, and a screenshot from
  the earlier MarketLab layout.
- Expanded GitHub Actions to cover the Python application/dashboard and frontend.

### Current UI limitations

- DSA diagrams are illustrative; they do not instrument the engine's actual
  mutations or provide verified AVL rotation traces.
- Simulator controls animate counters rather than submitting that configured
  workload. Actual concurrent submissions are available through the CLI.
- Some analytics graphics are illustrative. The current frontend does not expose
  all paper-account/manual-order capabilities implemented by the API.
- Recorded benchmark CSVs and reports are the authoritative measurement
  evidence; the frontend's benchmark table does not normalize every CSV schema.

## 2026-09-28 — Existing GitHub repository initialized

- GitHub repository `sgshiv001/TRADE-VELOCITY` initially contained a heading-only
  README and `.gitattributes`.
- Commit: `1814dfc0b681fe7799ee9dbaf0ac4f198820f379`, **Initial commit**,
  recorded at 23:55:05 +05:30. This separate repository history is retained.

## 2026-09-24 — Complete stock matching engine project

- Commit: `4c84a91`, recorded at 15:55:29 +05:30.
- Added scenario sessions and JSON replay, example scenario, repeated benchmark
  script and baseline CSV, dashboard/session tests, and GitHub Actions.
- Expanded the dashboard, CLI, matching implementation, README, and design,
  evaluation, and results documentation.
- Git records **17 files changed, 800 insertions, 134 deletions**.

## 2026-09-24 — Initial stock order matching engine

- Commit: `67a4520`, recorded at 11:59:49 +05:30.
- Added Python package/configuration, matching/order models, custom structure
  implementations, CLI demonstration, initial Streamlit dashboard, README,
  ignored development artifacts, and engine tests.
- Git records **10 files changed, 1,073 insertions**.

## Future updates

Add a dated entry describing each meaningful change and its verification.
Use Git commits for exact file diffs and [CONTRIBUTING.md](CONTRIBUTING.md) for
the update procedure. Do not claim an automatic transcript of uncommitted edits.
