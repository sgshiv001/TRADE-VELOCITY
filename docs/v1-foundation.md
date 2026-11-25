# TradeVelocity 0.5.0 release and build guide

The hosted app serves a Next.js export from FastAPI at the same origin as the API and WebSocket endpoint. Existing login cookies, PostgreSQL accounts, and order records carry over. The legacy Vite build still runs with the local Windows launcher.

## Try the funded book

1. Sign in and open **Funded terminal**. Choose a supported symbol and load simulated depth. The app labels its provider reference and timestamp.
2. Review a limit buy and confirm it. The engine matches against the shared funded book. Unfilled buy quantities reserve virtual cash. A sell uses the shares available after open sell orders.
3. Check **Orders**, **Portfolio**, **Virtual funds**, and **Notifications**. Trade history lets you pick the funded book, the earlier shared practice book, or the private archive.

The funded book gives each trader INR 1,000,000 in virtual cash and starts without holdings. Market reference data is separate from simulated executions. A virtual maker supplies a bid and ask with an approximate 0.15% spread on either side of the reference. The funded venue supports confirmed limit orders and prevents crossing your own order. Practice modes retain their existing order types.

The PostgreSQL session transaction saves journal events, revision, and request receipts. Replaying these events restores orders and fills. Wallet top-ups commit to the same funded session. Portfolio valuation uses weighted average cost and labels daily closes separately from simulated fill marks. This release uses INR and charges zero simulated fees.

## AI Analyst

The analyst reports sourced daily history, a trend summary, the MACD histogram, a paper signal, and a next-session price range where enough data exists. The model compares ridge regression with an unchanged-price baseline on a chronological selection window, then estimates its range from a later calibration window. Stale history is labeled and does not generate an active signal. These estimates are informational and never submit an order.

## Build locally

Use Node.js 22, pnpm 11.25.0, and Python 3.10 or newer. From the repository root:

```powershell
pnpm install --frozen-lockfile
pnpm build:web
pnpm build:desktop
pnpm check:mobile
pnpm test:shared
python -m pip install -e ".[app,test,postgres,accounts]"
```

To open the Next.js UI with disposable local storage, run the following, then visit `http://127.0.0.1:8804`:

```powershell
$env:TRADEVELOCITY_WEB_DIR = Join-Path (Get-Location) 'apps/web/out'
python scripts/browser_test_server.py --port 8804
```

The funded book requires hosted accounts and PostgreSQL. See [hosted setup](hosted-workspace.md). For native smoke testing, point `EXPO_PUBLIC_API_URL` at the HTTPS deployment, then run `pnpm --filter @tradevelocity/mobile start`. Expo stores the session token on the device. Enrolled biometrics can gate access to that saved session. The existing Capacitor test APK uses the deployed web app.

`pnpm --filter @tradevelocity/desktop dev` launches the Electron client. Its packaged client opens the hosted app with renderer sandboxing and a restricted navigation policy. The package configuration targets Windows NSIS/MSI, macOS DMG and Linux AppImage/DEB. Expo EAS profiles define Android APK and AAB targets.

## Release boundaries

This is a V1 foundation release, not a finished 1.0. The Electron and Expo source builds do not establish native signing or store readiness. The Expo Android export is a JavaScript bundle. It is not a new APK or AAB. Signed desktop and iOS releases need the appropriate runners and signing credentials. Production push/email, licensed data or news feeds, the conversational assistant, Redis workers, SQLAlchemy/Alembic migration of the existing backend, and CUDA training remain future work. The installable web app provides an offline screen. Account values and orders require an active connection.
