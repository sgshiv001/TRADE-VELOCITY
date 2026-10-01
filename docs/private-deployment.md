# Prepared private-hosting tools — not deployed

The app remains local by default. No hosting, domain, certificate, port-forward,
or external service was configured. These templates are for a future **private
single-operator workspace**, not public multi-user trading or broker execution.
The SQLite/session registry requires one application worker; people sharing the
access key are trusted operators, not isolated user accounts.

## Implemented safeguards

- Local mode rejects non-loopback connections, untrusted Host headers, and
  foreign browser origins, including WebSockets. No permissive CORS is enabled.
- Private mode fails closed without a valid HTTPS origin and a non-placeholder
  access key of at least 32 characters. The operator key must be random, not
  memorable. Never commit it or put it in a browser URL.
- Login issues an eight-hour Secure, HTTP-only, SameSite=Strict host cookie.
  It is not saved in local/session storage. Logout revokes it server-side;
  established WebSockets recheck authorization before sending the next update.
  Server restarts revoke these in-memory login sessions.
- Header-based bearer access is available for explicit trusted API clients.
  Session IDs alone do not bypass the private-mode access check.
- Host/origin validation, login/request/expensive-operation limits, an 8 MiB
  streamed request-body cap, bounded concurrent connections, and response
  security headers apply. OpenAPI/Swagger pages are disabled.
- The Docker template uses a non-root user, read-only app filesystem, writable
  persistent data volume, dropped capabilities, and no exposed app port. Caddy
  is the intended HTTPS reverse proxy. Authentication cookies require HTTPS.

These are defensive controls, not an independent security audit. CSP allows
inline styles needed by charts, not arbitrary inline scripts. TLS and DNS are
not tested by in-process API tests. Backups and access-key rotation remain the
operator's responsibility.

## Future opt-in setup

Docker/Compose is not installed on the current machine, so the container image
and live proxy/TLS flow were **not executed**. The templates must be built and
tested on the chosen host before use. Start with an isolated staging data volume
and never point a staging run at your only saved workspace.

1. Obtain your domain/host and install Docker using their official instructions.
2. Copy `deploy/.env.example` to an ignored `deploy/.env`; use your real domain.
3. Generate a cryptographically random key yourself (for example
   `python -c "import secrets; print(secrets.token_urlsafe(48))"`) and store it
   only in protected local configuration. This prints a secret: do not paste its
   output into logs, Git, a screenshot, or this chat.
4. Run `docker compose --env-file deploy/.env -f deploy/compose.yaml config`
   privately; config output can contain secrets, so do not publish it.
5. Only when you explicitly decide to deploy, run the matching Compose build/up
   commands on that host and test HTTPS, login/logout, denial without login,
   CSRF/origin checks, persistence, backups/restore, and restart behavior.

The deployment entry refuses local-mode hosting. The normal `app.py` launcher
continues to bind loopback; preparing these files does not expose the app.

Actual multi-user deployment additionally needs individual accounts, ownership
authorization, stronger quotas, backup/restore operations, secret management,
and load/security review. Real-market fraud validation additionally needs an
appropriately labelled dataset. Neither is implied by the local test results.
