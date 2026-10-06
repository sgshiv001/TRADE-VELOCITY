"""Native Windows window backed by the local API; owns and stops its server."""
from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path
import socket
import sys
import threading
import time
import urllib.request


def data_directory() -> Path:
    return Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "TradeVelocity"


def run_desktop(smoke_test: bool = False) -> int:
    import uvicorn
    import webview
    from .api import create_app, PROJECT_ROOT
    from .server_runtime import server_options
    from .windows_checks import check_windows

    prerequisites = check_windows()
    if os.name == "nt" and not prerequisites["ready"]:
        raise RuntimeError("Windows prerequisites are missing: " + "; ".join(prerequisites["problems"]) +
                           ". See docs/windows-release.md for official setup links. Nothing was installed automatically.")

    directory = data_directory()
    directory.mkdir(parents=True, exist_ok=True)
    # GUI executables have no stdout/stderr; keep useful local diagnostics.
    if sys.stdout is None:
        sys.stdout = (directory / "desktop.log").open("a", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = sys.stdout
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if os.name == "nt":
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
    try:
        try:
            listener.bind(("127.0.0.1", 8765))
        except OSError:
            listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        session_directory = directory / ("smoke-sessions" if smoke_test else "sessions")
        server = uvicorn.Server(uvicorn.Config(create_app(data_dir=session_directory),
                                               host="127.0.0.1", port=port, log_level="warning", **server_options()))
        thread = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
        thread.start()
        deadline = time.monotonic() + 30
        while not server.started:
            if not thread.is_alive() or time.monotonic() > deadline:
                server.should_exit = True
                thread.join(timeout=5)
                raise RuntimeError("The local desktop server could not start. See desktop.log.")
            time.sleep(.05)
        webview.settings["ALLOW_DOWNLOADS"] = True
        build_id = hashlib.sha256((PROJECT_ROOT / "frontend" / "dist" / "index.html").read_bytes()).hexdigest()[:12]
        window = webview.create_window("TradeVelocity — Matching Workspace", f"http://127.0.0.1:{port}/?build={build_id}",
                                       width=1380, height=900, min_size=(820, 600),
                                       background_color="#f5f7fb", hidden=smoke_test, text_select=True)
        outcome = {"ok": False}

        def verify_window():
            try:
                client = urllib.request.build_opener(urllib.request.ProxyHandler({}))
                url = f"http://127.0.0.1:{port}/api"
                def request(path, payload=None, session_id=None):
                    headers = {"Content-Type": "application/json"}
                    if session_id:
                        headers["X-Session-ID"] = session_id
                    req = urllib.request.Request(url + path, data=json.dumps(payload).encode() if payload is not None else None, headers=headers)
                    with client.open(req, timeout=20) as response:
                        return json.load(response)
                sid = request("/session", {})["session_id"]
                request("/lab/orders", {"order_id": "SMOKE-SELL", "symbol": "RELIANCE", "side": "SELL", "quantity": 7, "price": "100"}, sid)
                matched = request("/lab/orders", {"order_id": "SMOKE-BUY", "symbol": "RELIANCE", "side": "BUY", "quantity": 7, "price": "100"}, sid)
                state = request("/lab?symbol=RELIANCE", session_id=sid)
                watchdog = request("/lab/watchdog?symbol=RELIANCE", session_id=sid)
                benchmark = request("/experiments", {"count": 100, "workload": "deep"}, sid)
                if matched["filled"] != 7 or state["total_trades"] != 1 or state["orders"]:
                    raise RuntimeError("Matching verification failed")
                outcome.update(matched_shares=matched["filled"], recorded_trades=state["total_trades"],
                               observations=watchdog["observations"], benchmark_rows=len(benchmark))
                # Exercise the packaged model and calibration data, not just warm-up.
                calibration_sid = request("/session", {})["session_id"]
                for index in range(45):
                    shares = 10 + index % 17
                    price = f"{100 + (index % 5 - 2) / 10:.2f}"
                    for side in ("SELL", "BUY"):
                        request("/lab/orders", {"order_id": f"AI-{side}-{index}", "symbol": "RELIANCE",
                                                "side": side, "quantity": shares, "price": price}, calibration_sid)
                for side in ("SELL", "BUY"):
                    request("/lab/orders", {"order_id": f"AI-LARGE-{side}", "symbol": "RELIANCE",
                                            "side": side, "quantity": 5000, "price": "130"}, calibration_sid)
                before_monitor = request("/lab/export", session_id=calibration_sid)
                calibrated = request("/lab/watchdog?symbol=RELIANCE", session_id=calibration_sid)
                alert = next((row for row in calibrated["alerts"] if row["order_id"] == "AI-LARGE-BUY"), None)
                if (not alert or "robust_guard" not in alert["detectors"]
                        or calibrated["model_version"] != "execution-watchdog-v3"
                        or calibrated["calibration"]["fit_observations"] != 24
                        or calibrated["calibration"]["cutoff_observations"] != 16
                        or calibrated["calibration"]["forest_margin"] != .08
                        or request("/lab/export", session_id=calibration_sid) != before_monitor):
                    raise RuntimeError("Packaged AI calibration verification failed")
                outcome.update(calibrated_alert=True, model_version=calibrated["model_version"],
                               calibrated_observations=calibrated["observations"],
                               calibration=calibrated["calibration"], detectors=alert["detectors"],
                               matching_unchanged_by_monitor=True)
                # Previous high-volume miss: size/price movement is not required
                # when a count exceeds the calibrated raw-count envelope.
                from .calibration import workload
                rows, _ = workload("high_volume",2009)
                from .watchdog import ExecutionMonitor
                high_volume = ExecutionMonitor().report(rows,"RELIANCE")
                if not high_volume["timeline"][-1]["needs_review"] or "size_envelope" not in high_volume["timeline"][-1]["detectors"]:
                    raise RuntimeError("Packaged high-volume regression failed")
                outcome.update(high_volume_regression=True, prerequisites=prerequisites)
                deadline = time.monotonic() + 30
                while time.monotonic() < deadline:
                    rendered = window.evaluate_js("Boolean(document.querySelector('#root')?.textContent.includes('VELOCITY'))")
                    live = window.evaluate_js("Boolean(document.querySelector('main [role=status]')?.textContent.includes('LIVE WORKSPACE UPDATES'))")
                    if rendered and live:
                        outcome.update(ok=True, port=port, title=window.title, live_workspace=True)
                        break
                    time.sleep(.2)
                if not outcome["ok"]:
                    raise RuntimeError("Frontend rendering/live WebSocket connection did not become ready within 30 seconds")
            except Exception as exc:
                outcome["error"] = str(exc)
            finally:
                window.destroy()

        try:
            webview.start(verify_window if smoke_test else None, gui="edgechromium" if os.name == "nt" else None,
                          private_mode=False, storage_path=str(directory / ("smoke-webview" if smoke_test else "webview")))
        finally:
            server.should_exit = True
            thread.join(timeout=10)
        if smoke_test:
            (directory / "smoke-test.json").write_text(json.dumps(outcome), encoding="utf-8")
            return 0 if outcome["ok"] and not thread.is_alive() else 1
        return 0
    finally:
        listener.close()
