# Change log

This log records the project implemented through 29 September 2026. Original
commit dates are taken from Git. Later milestones summarize the development
session and current files; they do not imply separate commits existed for every
intermediate edit. See [the detailed development log](docs/development-log.md)
and `git log --all --stat` for the full available record.

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
