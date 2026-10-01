"""Regression checks for launch ownership and occupied ports."""

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
import urllib.request

import pytest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("trade_velocity_launcher", ROOT / "app.py")
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


@contextmanager
def healthy_server(payload):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode())

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_port
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_other_healthy_service_is_not_reused_or_stopped():
    with healthy_server({"status": "ok"}) as port:
        assert not launcher.app_is_running(port)
        with pytest.raises(RuntimeError, match="--port 8001"):
            launcher.serve(port, None, skip_build=True)
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health") as response:
            assert response.status == 200


def test_existing_app_opens_selected_browser_without_rebuilding(monkeypatch):
    opened = []
    monkeypatch.setattr(launcher, "open_browser", lambda browser, url: opened.append((browser, url)))
    monkeypatch.setattr(launcher, "build_frontend", lambda _: pytest.fail("existing server was rebuilt"))
    with healthy_server({"status": "ok", "application": launcher.APP_ID}) as port:
        assert launcher.serve(port, "chrome", skip_build=False) == 0
        assert opened == [("chrome", f"http://127.0.0.1:{port}/")]
        assert launcher.app_is_running(port)


def test_missing_browser_falls_back_to_system_default(monkeypatch):
    opened = []
    monkeypatch.setattr(launcher, "browser_path", lambda _: None)
    monkeypatch.setattr(launcher.webbrowser, "open", lambda url: opened.append(url) or True)
    launcher.open_browser("chrome", "http://127.0.0.1:8000/")
    assert opened == ["http://127.0.0.1:8000/"]


def run_windows_shortcut(path, arguments, cwd):
    """Use CMD's explicit outer quoting for batch files in paths with spaces."""
    interpreter = os.environ.get("COMSPEC", "cmd.exe")
    command = f'"{interpreter}" /d /s /c ""{path}" {subprocess.list2cmdline(arguments)}"'
    return subprocess.run(command, cwd=cwd, input="\n", capture_output=True,
                          text=True, timeout=30)


@pytest.mark.skipif(os.name != "nt", reason="Windows batch shortcut")
def test_windows_shortcut_reports_missing_environment(tmp_path):
    project = tmp_path / "project folder with spaces"
    project.mkdir()
    shortcut = project / "Launch_TradeVelocity.bat"
    shortcut.write_bytes((ROOT / shortcut.name).read_bytes())
    (project / "app.py").write_bytes((ROOT / "app.py").read_bytes())
    result = run_windows_shortcut(shortcut, ["--no-browser"], tmp_path)
    assert result.returncode == 1
    assert "Python environment was not found" in result.stdout
    assert "pip install -e" in result.stdout


@pytest.mark.skipif(os.name != "nt", reason="Windows batch shortcut")
def test_windows_shortcut_uses_its_folder_and_forwards_launch_options(tmp_path):
    project = tmp_path / "project folder with spaces"
    project.mkdir()
    shortcut = project / "Launch_TradeVelocity.bat"
    shortcut.write_bytes((ROOT / shortcut.name).read_bytes())
    (project / "app.py").write_bytes((ROOT / "app.py").read_bytes())
    subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(project / ".venv")],
                   check=True, capture_output=True, text=True, timeout=30)
    # A verified running app is reused without third-party dependencies or a build.
    with healthy_server({"status": "ok", "application": launcher.APP_ID}) as port:
        result = run_windows_shortcut(shortcut,
                                      ["--no-browser", "--skip-build", "--port", str(port)],
                                      tmp_path)
        assert result.returncode == 0, result.stdout + result.stderr
        assert f"already running at http://127.0.0.1:{port}/" in result.stdout
        assert "Select a browser" not in result.stdout
        assert "Using project Python" not in result.stdout
    rejected = run_windows_shortcut(shortcut, ["--port", "0", "--no-browser"], tmp_path)
    assert rejected.returncode == 2
    assert "port must be between 1 and 65535" in rejected.stderr
    assert "Review the error above" in rejected.stdout


def test_stopping_launcher_releases_server_port():
    entry_file = "app.py"
    pytest.importorskip("uvicorn")
    if not (ROOT / "frontend/dist/index.html").exists():
        pytest.skip("build the frontend before running launcher integration checks")
    with socket.socket() as candidate:
        candidate.bind(("127.0.0.1", 0))
        port = candidate.getsockname()[1]
    process = subprocess.Popen(
        [sys.executable, str(ROOT / entry_file), "--no-browser", "--skip-build", "--port", str(port)],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    try:
        deadline = time.monotonic() + 30
        while not launcher.app_is_running(port):
            if process.poll() is not None:
                pytest.fail(process.communicate()[0])
            if time.monotonic() > deadline:
                pytest.fail("launcher did not become ready within 30 seconds")
            time.sleep(0.1)
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/") as response:
            assert response.status == 200
            html = response.read().decode()
            assert 'id="root"' in html
            assert "<title>TradeVelocity | Order Matching Engine</title>" in html
        base_python = Path(sys.base_prefix) / ("python.exe" if os.name == "nt" else "bin/python3")
        second = subprocess.run(
            [str(base_python if base_python.exists() else sys.executable),
             str(ROOT / "app.py"), "--no-browser", "--skip-build", "--port", str(port)],
            cwd=ROOT, capture_output=True, text=True, timeout=10,
        )
        assert second.returncode == 0, second.stdout + second.stderr
        assert "already running" in second.stdout
        assert launcher.app_is_running(port)
    finally:
        if process.poll() is None:
            process.terminate()
        try:
            process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate(timeout=5)
    # VS Code's stop button must not leave an orphan Uvicorn child behind.
    with socket.socket() as released:
        if os.name == "nt":
            released.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        else:
            released.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        released.bind(("127.0.0.1", port))
