# Backend and database

FastAPI serves the React interface, matching endpoints and WebSocket updates
from one origin. SQLite is the default local database. Setting
`TRADEVELOCITY_DATABASE_URL` or `DATABASE_URL` selects PostgreSQL instead.
Use one backend process with one worker because matching sessions and live
subscriptions are held in memory and restored from the database after restart.

## Run locally

From the repository root in PowerShell, install the app and build the interface.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[app,test,postgres]"
Push-Location frontend
npm ci
npm run build
Pop-Location
.\.venv\Scripts\python.exe -m stock_engine.server --local --port 8000
```

Open `http://localhost:8000`. With the default configuration, sessions,
successful order commands, AI review notes, revisions and retry receipts are
stored in `.marketlab/sessions/workspace.sqlite3`. Trades and resting orders
are reconstructed from those commands. An order acknowledgement is returned
after its database transaction commits.

Check the database connection from another terminal.

```powershell
Invoke-RestMethod http://localhost:8000/api/ready
```

The response reports `status` as `ready` and `storage` as `sqlite` or
`postgresql`. A database failure returns HTTP 503. `/api/health` reports
application liveness, while `/api/ready` checks an actual database connection
and initializes the required tables if necessary.

## Use PostgreSQL

Create a database and a role with permission to create its tables using your
local PostgreSQL installation or chosen database provider. Install the
`postgres` extra as shown above, then set its connection URL before starting
the backend. The environment value is read when the app starts.

```powershell
$env:TRADEVELOCITY_DATABASE_URL = Read-Host 'PostgreSQL connection URL'
.\.venv\Scripts\python.exe -m stock_engine.server --local --port 8000
```

Use a `postgresql://` or `postgres://` URL. Provider SSL options such as
`sslmode=require` can be supplied in its query string. The backend creates
`sessions`, `commands` and `receipts` tables on first connection. Commands,
metadata and retry receipts are saved in one transaction. Conflicting stale
revisions are rejected.

After an uncertain database save, the backend reloads saved session state
before retrying. Durable request receipts prevent duplicate executions when
the commit succeeds but its acknowledgement is lost.

Changing the database selects a different set of sessions. To move an existing
workspace, export it from **Trade history**, switch databases and restart, then
import the export into the new workspace. Local SQLite and legacy JSON files
remain available. Unset both database URL variables and restart to return to
SQLite.

## Connect Android locally

Build the frontend and start the backend first. Connect a device or emulator
with USB debugging enabled and use Android SDK platform-tools to forward the
device's port 8000 to the computer's port 8000.

```powershell
adb reverse tcp:8000 tcp:8000
.\.venv\Scripts\python.exe scripts/configure_android.py --url http://localhost:8000
npm ci
npx cap sync android
```

Build and run the Android project after syncing. The WebView loads the same
interface and API from `localhost:8000` through the USB tunnel. Run `adb reverse`
again after reconnecting the device. Each browser or device starts its own
matching session.

For a future hosted backend, pass its HTTPS origin to
`scripts/configure_android.py --url` and sync/rebuild the APK. Hosted access
uses the existing workspace sign-in. The script accepts an origin without a
path or credentials, removes wildcard navigation and disables mixed content.
The backend serves the interface and API together, including same-origin
cookies and WebSocket connections.
[Private hosting configuration](private-deployment.md)

## Database verification

The database tests cover restarts, partial fills, amendments, cancellations,
export/import, concurrent orders, atomic rollback and durable retry receipts.
To include PostgreSQL cases locally, provide a separate disposable test
database. Its connection value stays in the environment.

```powershell
$env:TRADEVELOCITY_TEST_DATABASE_URL = Read-Host 'Disposable PostgreSQL test database URL'
.\.venv\Scripts\python.exe -m pytest -q tests/test_database.py
```

CI also runs these cases against a PostgreSQL 17 service. The tests create
sessions and commands in the configured test database.
