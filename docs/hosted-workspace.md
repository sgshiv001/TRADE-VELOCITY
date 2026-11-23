# Host the TradeVelocity workspace

The hosted app serves the React interface, FastAPI and WebSocket updates
over the same HTTPS origin. Traders create a username and password at
`/signup` and sign in at `/login`. Every account has its own saved order book
and trades. The first visit offers a tutorial with **Skip tutorial**, and
**Open tutorial** in the workspace footer lets traders run it again.

Use one backend replica and a private PostgreSQL service. A single replica
keeps live subscriptions and the in-memory order book on the same server.
Use a persistent PostgreSQL volume and schedule backups at the provider.
Existing desktop and private workspaces can be moved using session export
and import from **Trade history**.

## Railway

Add a PostgreSQL service and an app service that builds this repository.
Generate an HTTPS domain for the app. The checked-in Railway configuration
uses `deploy/Dockerfile` and checks PostgreSQL readiness before routing traffic.
Set these variables on the app service.

| Variable | Value |
| --- | --- |
| `TRADEVELOCITY_MODE` | `accounts` |
| `TRADEVELOCITY_ORIGIN` | The exact public HTTPS origin |
| `TRADEVELOCITY_DATA_DIR` | `/data/sessions` |
| `DATABASE_URL` | Reference the PostgreSQL service's private `DATABASE_URL` |

Leave `TRADEVELOCITY_ACCESS_KEY` unset in accounts mode. Mount an app volume at
`/data` if refreshed market history should survive redeployment. Accounts,
orders and tutorial status are stored in PostgreSQL. Run with one replica.
[Railway PostgreSQL](https://docs.railway.com/databases/postgresql)

After deploying, check `/api/ready` for `{"status":"ready","storage":"postgresql"}`.
Create two test accounts. Place orders in one, sign in to the other and confirm
it has its own empty book. Check that Skip persists after reloading and that
orders survive a backend restart. Use fresh credentials for the live service.

## Self-hosted HTTPS

The Docker Compose configuration can also serve accounts behind Caddy.
Set `TRADEVELOCITY_MODE=accounts`, `TRADEVELOCITY_DOMAIN`, and
`TRADEVELOCITY_DATABASE_URL` in the ignored `deploy/.env`. Set
`TRADEVELOCITY_ACCESS_KEY` to an empty value. PostgreSQL should be reachable
from the container and use a dedicated database.
[Compose and Caddy setup](private-deployment.md)

The current account flow uses usernames and passwords. Keep the password in
a password manager. Email recovery requires an additional verified recovery
channel. The matching workspace is for simulated trades.
