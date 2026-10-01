# TradeVelocity — local completion and test report

Release **0.3.3**, completed **2 October 2026**. Verification performed
**1 October 2026, India time**.
Scope: Windows desktop and local web app using your own matching engine, with
no broker connection or real-money execution. Signing/hosting **tooling only**,
as requested. These checks establish a tested local build, not a guarantee
that no defect can exist.

1. **Matching and saved data — passed.** Automated coverage includes price/FIFO
   priority, partial fills, market-order expiry, cancellation/amendment,
   multi-symbol quantities, concurrent operations, session isolation, SQLite
   persistence, failure rollback, and durable idempotent retry receipts. Export,
   import/replay, complete trade pagination and timestamps are covered. New
   application sessions stay empty; test workloads never seed normal sessions.

2. **Python regression suite — passed.** Command:
   `.\.venv\Scripts\python.exe -m pytest -q -ra`.
   Final result: **159 passed in 29.84 seconds**, no failures or skips, including
   the security and release-tool checks. Environment: Python **3.14.7**,
   scikit-learn **1.9.1**, Windows 11 x64. Prepared GitHub Actions matrices have
   not been remotely executed for these changes.

3. **Frontend and browser — passed.** `npm run build` type-checks and builds the
   production UI (1,748 modules). `npm run test:e2e`: **10 passed in 19.7 seconds**
   on Chromium with disposable backend storage. Checks cover real matching,
   amendment/cancellation, live second-tab updates, dropped-response retry,
   exports/imports with timestamps, saved AI reviews, both themes/readable dark
   dropdowns, watchlists, chart controls, ten reloads/reconnects, and every
   workspace page at **390, 820 and 1440 pixels**. Responsive automation is not
   physical mobile-device certification. The private login/logout UI test uses
   a labelled route fixture, not live HTTPS authentication.

4. **AI calibration v3 — completed within its stated scope.** The earlier
   high-volume miss and repetitive-baseline miss are covered by regressions.
   Development-only selection uses 54 candidates and a fixed 24-fit/16-cutoff
   baseline. The fresh controlled set detects **1,536/1,536 extreme deviations**
   with **0/15,360** normal controls flagged. Old regression cases detect
   **768/768**, with **0/7,680** false alerts. Results reproduce across two runs.
   Most detections come from explicit guards, not the forest alone. This is
   finite synthetic evaluation, **not 100% real-market fraud accuracy**. Review
   [the full AI report](ai-calibration-report.md) and
   [raw results](../benchmarks/ai-calibration.json) for limits and attribution.

5. **Windows connection-reset issue — repaired and checked.** Web and desktop
   servers now use the supported Selector event loop and SansIO WebSocket
   transport. Python coverage includes 20 disconnect/reconnect cycles; the
   final browser suite includes ten rapid reloads. The earlier WinError 10054
   diagnostic did not recur in that run. This is regression evidence, not an
   unlimited network-stress or uptime guarantee.

6. **Local protections and optional private access — implemented/tested.**
   Local mode rejects foreign hosts/origins and non-loopback clients. Private
   mode requires an HTTPS origin and non-placeholder access key, issues
   Secure/HTTP-only/Strict cookies, supports expiry/logout revocation, and checks
   established WebSockets before further updates. Tests cover bearer access,
   malformed hosts, unauthorized requests, rate-window recovery, expensive
   operation limits, body limits and security headers. API security tests use
   real in-process routes/cookies/sockets, **not a live TLS proxy**. One shared
   operator key does not provide separate user-account ownership. These controls
   are not an independent security audit. See
   [private-hosting tools](private-deployment.md).

7. **Windows prerequisite/signing tools — prepared.** Frozen and source
   `--check-system` both pass: Windows 11 x64, WebView2 **154.0.4258.37**, .NET
   Framework release **533509**. Missing prerequisites receive a clear startup
   message; no runtime is downloaded or installed automatically. Signing helper
   tests and a placeholder `--dry-run` pass. No actual certificate, SignTool
   execution or timestamp-service call was used. Authenticode status of this
   EXE is **NotSigned**. Read [Windows instructions](windows-release.md).

8. **Real frozen Windows ZIP — passed on this machine.** The local
   `dist/TradeVelocity-Windows-x64.zip` contains **2,610**
   CRC-verified entries, **120,365,325 bytes**, the folder shortcut and bundled
   Windows instructions. EXE/frontend/calibration agree with the release build.
   It was extracted into a fresh folder with spaces, given independent writable
   application storage, and launched with Python/Node excluded from PATH and
   no source virtual environment. Both prerequisite check and native smoke
   exited **0**. The actual hidden WebView rendered the UI, matched **7 shares /
   1 trade**, measured six benchmark rows, exercised **46 AI observations**,
   detected the large execution and high-volume regression, and preserved
   matching records. While a test listener held port **8765**, a second smoke
   chose **57794** and released it on exit. Evidence:
   [portable smoke receipt](../benchmarks/portable-smoke.json) and the local
   `dist/TradeVelocity-release.json`. Generated binaries/manifests are excluded
   from source control; reproduce them using the Windows build instructions.

   ZIP SHA-256:
   `eb58948bd0351dc93acfe7282dabc74e37f59b6bf0addcf1a5804d4a1afac0b9`.
   Hashes verify file identity/integrity, not publisher trust.

9. **Dependencies and documentation — checked.** `pip check` reports no broken
   requirements; `npm audit` reports **zero known vulnerabilities** for the
   installed lockfile at verification time. Neither substitutes for a security
   audit. The browser run printed a benign Node `NO_COLOR`/`FORCE_COLOR` warning,
   not an application failure. README, architecture, current/archived AI reports,
   release instructions, changelog and development log describe the same local
   release and preserve historical evidence.

10. **Left intentionally unperformed or unverified at verification.** No certificate purchase,
    signing, public deployment, domain configuration, GitHub commit/push, or
    remote test run was performed. Docker/SignTool are not installed here;
    Docker/Caddy templates and live TLS must be tested on a future chosen host.
    A different physical Windows PC is unavailable, so this release is not
    cross-PC certified. Real-market labelled AI evaluation, poisoned baselines,
    subtle abuse, ordinary regime shifts, unfilled/cancelled-order abuse, and
    multi-user account authorization remain outside the completed local scope.
    The user subsequently authorized source/README/repository publication on
    **2 October 2026**; use Git history and GitHub Actions for its actual commit
    and remote test status. Publishing source does not deploy the web app.

11. **Shutdown and cleanup.** Both native smoke processes exited and their
    app ports were released; the browser test server stopped. Normal saved
    application sessions were not used or cleared. Automatic deletion of the
    generated test extraction was blocked by command policy, so only this
    disposable copy remains for optional manual removal:
    `%LOCALAPPDATA%\Temp\TradeVelocity Release Check 94f61b09-1577-4961-a9a2-03b135307482`.
    It is test output, not a project backup or required app folder.

12. **Launch the finished local build.** Extract the complete ZIP, keep
    `_internal` beside the EXE, and double-click `Launch_Desktop.vbs` or
    `TradeVelocity/TradeVelocity.exe`. From this source folder, use
    `.\.venv\Scripts\python.exe app.py --desktop` for Windows, or
    `.\.venv\Scripts\python.exe app.py` for the browser app. A browser-mode
    occupied port can be changed with `--port 8001`.
