# Change log

This log records the project implemented through 29 September 2026. Original
commit dates are taken from Git. Later milestones summarize the development
session and current files; they do not imply separate commits existed for every
intermediate edit. See [the detailed development log](docs/development-log.md)
and `git log --all --stat` for the full available record.

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
