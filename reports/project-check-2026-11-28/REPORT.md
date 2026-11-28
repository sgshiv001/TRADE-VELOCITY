# TradeVelocity 2.1.0 verification report

**Date:** 2026-11-28  
**Version:** `2.1.0` (built from `main` @ `4194451` + `CHANGELOG.md` / `docs/index.html` metadata updates)  
**Environment:** Windows 11 x64 (`10.0.26300-SP0`) · Python `3.14.7` · Node.js `v24.21.0` · pnpm `11.25.0` · Electron `45.5.0`

---

## Verification Summary

| Check | Command | Result |
| --- | --- | --- |
| Next.js static export | `pnpm build:web` | **Passed** — Next.js `16.4.6` (Turbopack) built 9 static routes into `apps/web/out/` |
| Desktop TypeScript build | `pnpm build:desktop` | **Passed** — compiled `apps/desktop/dist/` |
| Shared TS client tests | `pnpm test:shared` | **Passed** — 2 / 2 Vitest assertions in `packages/client/src/index.test.ts` (666 ms) |
| TypeScript type-checks | `tsc --noEmit` (`apps/desktop`, `apps/web`, `frontend`) | **Passed** — 3 / 3 configs exited 0 |
| Python test suite | `.\.venv\Scripts\python.exe -m pytest -q -ra` | **180 passed, 16 skipped** in 34.56 s (196 collected; 16 PostgreSQL cases skipped without `TRADEVELOCITY_TEST_DATABASE_URL`) |
| Browser E2E (Next.js export) | `TRADEVELOCITY_WEB_DIR=apps/web/out pnpm --filter tradevelocity-app exec playwright test --grep "order lifecycle\|themes, dark dropdowns\|intraday quote chart\|presentation demo"` | **5 passed** in 19.3 s (headless Chromium) |
| Frozen presentation engine smoke | `TradeVelocityEngine.exe --data-dir <tmp> --frontend <bundled-web>` | **Passed** — rejected unauthenticated requests with `403`; authenticated `/api/health` (`version: 2.1.0`), `/api/ready` (`sqlite`), and `/app` (`8,234` bytes) returned `200`; clean exit `0` on stdin EOF |
| Scenario replay | `.\.venv\Scripts\python.exe -m stock_engine.cli run scenarios/order-lifecycle.json` | **Passed** — 9 events, 4 trades (`ACME`: 190 shares / VWAP ₹104.63; `TECH`: 40 shares / VWAP ₹200.00) |
| Dependency consistency | `.\.venv\Scripts\python.exe -m pip check` | **Passed** — no broken requirements |

---

## Rebuilt Windows Presentation Artifact

- **File:** `dist/TradeVelocity-2.1.0-Windows-x64.exe` (copied from `apps/desktop/build/presentation/TradeVelocity-2.1.0-Windows-x64.exe`)
- **Size:** `189,326,351` bytes (~180.56 MiB)
- **Built At:** `2026-11-28T18:03:28`
- **SHA-256:** `31741498b12635aa274212f9c6dab26020d1498b96afb7d49c0e78018ed41ba4`
- **Signing Status:** Unsigned (`signExecutable: false`)

---

## Fresh Benchmark Run (`benchmarks/results.csv`)

Command: `.\.venv\Scripts\python.exe scripts/benchmark.py --sizes 1000,10000,100000 --repeats 3 --seed 42 --symbols 5 --trace-memory`

| Orders | Symbols | Trades | Median Throughput | Peak Traced Memory |
| ---: | ---: | ---: | ---: | ---: |
| 1,000 | 5 | 764 | 100,711 orders/s | 0.49 MiB |
| 10,000 | 5 | 8,049 | 97,574 orders/s | 3.63 MiB |
| 100,000 | 5 | 81,137 | 93,222 orders/s | 33.27 MiB |

---

## Scope & Remaining External Actions

- **PostgreSQL & HTTPS account specs:** 16 pytest cases (`test_database.py` × 5, `test_trader_accounts.py` × 11) and `frontend/e2e/accounts.spec.ts` require an isolated PostgreSQL / HTTPS accounts test environment; the GitHub Actions `Tests` and `V1 client builds` workflows passed on `4194451`.
- **GitHub Release `v2.1.0`:** The remote `v2.1.0` release currently hosts the earlier `ebbaadd` Windows binary (`171,553,121` bytes) published prior to `4194451` and today's docs/report updates. Commit, tag/re-tag, and upload the rebuilt EXE + `SHA256SUMS.txt` when ready to update the public release.
