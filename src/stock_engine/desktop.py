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
                                               host="127.0.0.1", port=port, workers=1, log_level="warning"))
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
        window = webview.create_window("TradeVelocity — Market & Engine Lab", f"http://127.0.0.1:{port}/?build={build_id}",
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
                demo = request("/lab/watchdog/demo", {}, sid)
                benchmark = request("/experiments", {"count": 100, "workload": "deep"}, sid)
                simulation = request("/lab/simulate", {"count": 100}, sid)
                outcome.update(heldout=demo["evaluation"]["heldout"],
                               detected=demo["evaluation"]["true_positives"],
                               benchmark_rows=len(benchmark), simulation_commands=simulation["commands"])
                deadline = time.monotonic() + 30
                while time.monotonic() < deadline:
                    rendered = window.evaluate_js("Boolean(document.querySelector('#root')?.textContent.includes('VELOCITY'))")
                    if rendered:
                        outcome.update(ok=True, port=port, title=window.title)
                        break
                    time.sleep(.2)
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
