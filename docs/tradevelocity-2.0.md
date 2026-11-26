# TradeVelocity 2.0 development audit

## Starting point

The redevelopment branch starts at `5bb1ea2`. The hosted 0.5.1 site and its PostgreSQL readiness endpoint responded successfully. Keep that instance and its records in service during development. Use a separate PostgreSQL database for tests and staging.

| Area | What already works | What needs attention |
| --- | --- | --- |
| Public website and web workspace | Static Next.js export served by FastAPI, signup, sign-in, shared orders, funded paper trading, portfolio and watchlists | Replace the laboratory-style navigation and marketing page. Separate current provider quotes, historical chart prices, and simulated executions. |
| Trading and accounts | Server-side price–time matching, persistent command history, idempotent funded orders, full and partial fills, amendments, virtual cash and holdings | Funded trading currently accepts confirmed limit orders. Market orders need explicit protection and accounting tests before use in funded accounts. |
| Database and deployment | Hosted PostgreSQL, readiness probes, Docker and GitHub Actions | The current schema initializes accounts, sessions, command logs and receipts in application code. Formal versioned migrations and backup/restore rehearsal are prerequisites for a production schema change. |
| Market data and AI | Timestamped Yahoo Finance-compatible NSE quotes, adjusted daily history, RSI and moving averages, experimental next-session forecast with out-of-sample calibration | Only display supported symbols, horizons and available indicators. News, push delivery, broader exchange data and a configured language-model provider need separate integrations. |
| Windows and PWA | Separate trader/admin Electron launchers, previous portable EXEs, install manifest and offline page | Package a staging build against a verified backend. Preserve identities, sign with authorized credentials when available, and test upgrades. |
| Mobile and other desktop systems | Expo source for Android and iOS with a shared API client, existing Electron macOS/Linux targets, and a legacy Android APK | Extend the native experience using the same API. Verify the signing lineage before installing an update over the legacy Android package. macOS and iOS signing require a suitable host and credentials. |

## Supplied prototypes

`project (1).zip` contains a large Next.js design prototype with a trading workspace, AI pages, mobile navigation, and a combined TV mark. Its accounts, quotes, orders, and AI examples are generated or stored in the browser. `project.zip` contains a smaller dashboard prototype. Use both as design references. Keep the existing server responsible for orders and user records. The archives are outside the deployable source tree.

## Delivery sequence

1. Build the public website, release catalogue, theme, and connected web workspace. Wire the terminal, charts, account views, watchlists, and Analyst to the current APIs.
2. Extend supported data and forecasting through versioned additions. Validate each provider with known data and keep simulated orders independent of provider health. Use separate automated tests for any money or schema changes.
3. Build the native screens and staging installers against the same service. Test cross-device state and upgrade identity before preparing release metadata.
4. Rehearse backup, migration, and rollback against staging. Confirm credentials, provider rights, and release approval before publishing builds or changing production.

## Database recovery approach

Before any production migration, capture an encrypted database backup with the host's supported backup mechanism or PostgreSQL tools. Restore it to an isolated instance, verify row counts and replay representative funded books, then compare aggregate cash, reservations and holdings without exposing account records. A supported application rollback should run against the prior compatible schema. Restore a database backup only after accounting for writes made after the backup.

## Preview

The [editable Figma design](https://www.figma.com/design/Cw4EjL2sZallKygrN1VQs8) includes the landing page, desktop trading terminal and mobile markets screen. The website export adds `/download` and keeps `/app`, `/login` and `/signup` compatible with existing links.

Use a disposable PostgreSQL database and a local HTTPS origin for connected QA. Set `DATABASE_URL`, `TRADEVELOCITY_MODE=accounts`, `TRADEVELOCITY_ORIGIN=https://localhost:8443`, and absolute paths for `TRADEVELOCITY_DATA_DIR` and `TRADEVELOCITY_WEB_DIR`. Point the web path to `apps/web/out` after building the export.

```powershell
python -m pip install -e ".[app,postgres,accounts,migrations,test]"
pnpm install --frozen-lockfile
pnpm --filter @tradevelocity/web build
python -m alembic upgrade head
python -m uvicorn stock_engine.api:app --host 127.0.0.1 --port 8443 --loop stock_engine.server_runtime:create_loop --ws websockets-sansio --ssl-certfile ./staging.crt --ssl-keyfile ./staging.key
```

Supply a local certificate and key for the configured origin. Keep both out of version control. Run the migrations against the disposable database first. Revision `0001_persistent_books` adopts the existing schema and `0002_admin_activity_index` adds an index. The account, session, command and receipt rows stay intact. The baseline intentionally has no data-dropping downgrade.

The Windows preview configuration uses its own application ID and profile, points to the local staging service, and accepts its configured certificate fingerprint. Build it with a SHA-256 fingerprint from the same local certificate.

On Windows, prepare the Android build in a short checkout path without spaces. Set `node-linker=hoisted` in the build checkout's `.npmrc` before running `pnpm install --frozen-lockfile`. Run Expo prebuild and use the generated Gradle wrapper. The Expo config plugin shortens generated Android object file paths for the Windows compiler. The native package uses `com.tradevelocity.nativeapp` and accepts an `EXPO_PUBLIC_API_URL` HTTPS origin at build time. An APK signed with the debug key is suitable for emulator and local testing.

Run `node frontend/scripts/smoke-v2.mjs` while the local staging service is up. The smoke test creates a test trader, confirms a buy and sell, checks the same balance through device authentication, and exercises the watchlist, research screens and mobile browser navigation. Pass a directory as the first argument to capture screenshots.

## Verification

- The browser smoke test completed a confirmed paper buy and sell on PostgreSQL staging. It checked the wallet and execution history, saved a watchlist change, and confirmed that device authentication returned the same balance.
- The Windows preview EXE installed and the installed app reached a funded trading account on the same staging server. The MSI extracted successfully and contained the same app executable.
- Android built for ARM64 and x86-64. The APK signature verified, and Android's `bundletool validate` accepted the AAB. Both use a debug signing key. The APK installed and displayed its sign-in and account creation screens on the API 29 emulator. System UI errors interrupted the API 36 emulator check. The Android preview is configured for the existing hosted API. Android sign-in and trading against the 2.0 staging server still need device verification.
- The migration rehearsal restored an isolated PostgreSQL backup and preserved the account, session, command and receipt row counts.
- The iOS JavaScript export completed. A signed native iOS build requires macOS and Apple signing credentials.

## Release work remaining

Connected trading supports confirmed limit orders. Live stock references may be delayed, daily bars are timestamped, and the Analyst shows a historical forecast range only when the market data and model support it. Real news and sentiment, push delivery, a configured language-model provider, funded market-order types, and production credential recovery remain separate integrations. Signed distribution, physical-device and platform upgrades, and production deployment require a release review.
