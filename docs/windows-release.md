# Windows release and compatibility checklist

This is a portable **Windows x64** application. Extract the entire ZIP before
opening `Launch_Desktop.vbs` or `TradeVelocity/TradeVelocity.exe`; keep `_internal`
with the executable. The Python runtime and built interface are bundled; the
target PC does not need a separate Python or Node.js installation.
No installer, certificate purchase, runtime download, or system change runs
automatically. A portable app still needs compatible Windows/browser runtimes.

For the local pre-publication test package, open the ZIP's `START-HERE.txt` for
short launch instructions and manual checks that do not clear your saved data.
Source copy: `docs/windows-start-here.txt`. Preparing
or building this package does not publish a GitHub release or deploy the app.

## Read-only prerequisite check

Run the packaged EXE with `--check-system`. It writes
`%LOCALAPPDATA%\TradeVelocity\windows-readiness.json` without starting a window
or matching server. From source:

```powershell
.\.venv\Scripts\python.exe app.py --check-system
```

Checks cover Windows 10/11 x64, 64-bit Python/build, installed WebView2 Evergreen
Runtime, and .NET Framework 4.6.2 or newer. A missing prerequisite stops desktop
startup with a useful message; it is not silently installed.

Use the official [WebView2 distribution guidance](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution)
and [runtime download page](https://developer.microsoft.com/en-us/microsoft-edge/webview2/).
For .NET, use Microsoft's [.NET Framework downloads](https://dotnet.microsoft.com/en-us/download/dotnet-framework).
Manually install only what your PC is missing, then rerun the check.

## Build, verify, and package

```powershell
.\.venv\Scripts\python.exe scripts/build_desktop.py
.\dist\TradeVelocity\TradeVelocity.exe --smoke-test
```

Building produces the EXE folder, ZIP, and `dist/TradeVelocity-release.json`.
The packager validates frontend/calibration agreement, checks archive CRC, and
records SHA-256 hashes. Smoke uses separate sessions/profile, renders the UI,
matches orders, and checks both the repetitive and high-volume AI regressions.
It closes its own window/server. Normal saved sessions are not cleared or seeded.

## Optional certificate signing — tooling prepared, not signed

The current local EXE is unsigned. A real trusted publisher signature needs
your code-signing certificate/private key and Microsoft SignTool; this project
does not obtain them, create a fake trusted certificate, or bypass SmartScreen.
See [Microsoft SignTool documentation](https://learn.microsoft.com/en-us/windows/win32/seccrypto/signtool).

The signing helper selects an explicit certificate already in your Windows
certificate store by its 40-hex thumbprint, uses SHA-256 and an HTTPS RFC3161
timestamp service, then verifies with `/pa /all /v`. It never takes a private-key
password as a CLI argument or puts it in Git. Run `--dry-run` first:

```powershell
.\.venv\Scripts\python.exe scripts/sign_desktop.py --certificate-thumbprint YOUR_40_HEX_THUMBPRINT --timestamp-url https://YOUR_RFC3161_SERVICE --dry-run
```

Only after supplying your actual certificate and timestamp provider, remove
`--dry-run`. Then repackage without rebuilding:

```powershell
.\.venv\Scripts\python.exe scripts/build_desktop.py --package-only
Get-AuthenticodeSignature -LiteralPath .\dist\TradeVelocity\TradeVelocity.exe
Get-FileHash -Algorithm SHA256 -LiteralPath .\dist\TradeVelocity-Windows-x64.zip
```

Rebuilding replaces the EXE and removes the prior signature. Signature checks
and archive hashes are different evidence; hashes do not prove publisher trust.

## Device matrix and acceptance checklist

| Target | Evidence / required check |
| --- | --- |
| Current Windows 11 x64 machine | Actual prerequisites, native packaged smoke, matching and AI checks |
| Fresh folder with spaces on this machine | Extracted ZIP smoke; independent writable data path |
| Different Windows 10/11 x64 PC | Still requires a physical-device run; not inferred from this machine |
| x86 / native ARM64 | Not included or certified by the x64 build |
| Browser at 390 / 820 / 1440 pixels | Automated responsive-layout coverage, not physical-device certification |

Before distributing: verify the ZIP hash/CRC, extract rather than run inside
the archive, check prerequisites, place a matched pair, amend/cancel an order,
confirm persistence after restart, inspect light/dark company controls, test
an occupied port, and verify the server closes with the window.

For a small beta, ask willing testers on other PCs to record Windows/build
version, prerequisite report, expected/actual behavior, exact reproduction steps,
and a screenshot/log with access keys and personal records removed. Do not claim
other-PC compatibility until those results are received. No beta invitations,
uploads, remote installs, or purchases were performed here.
