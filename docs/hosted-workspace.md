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

## Render Free and Neon

Create a free PostgreSQL project in Neon and copy its direct connection URL
with TLS enabled. In Render, create a Blueprint from this repository and
select the branch containing `render.yaml`. Keep the web service on the Free
plan and enter the Neon URL in the `DATABASE_URL` secret field. Use the
actual HTTPS address Render assigns. The app reads it from
`RENDER_EXTERNAL_URL` and uses it for origin checks.

Orders, accounts and tutorial settings persist in Neon when Render sleeps or
restarts. Refreshed market files are temporary on the Free web service.
[Render free services](https://render.com/docs/free) · [Render Blueprints](https://render.com/docs/infrastructure-as-code)

Before sharing the address, confirm `/api/ready` reports `postgresql` and
verify signup, sign-in and the tutorial in the deployed app. If you later
attach a custom domain, set `TRADEVELOCITY_ORIGIN` to its exact HTTPS origin.

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
