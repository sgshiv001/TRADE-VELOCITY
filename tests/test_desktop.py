"""Desktop lifecycle checks; actual native/frozen smoke tests are run separately."""
import json
import socket

import pytest

pytest.importorskip("webview")
import webview
from stock_engine import desktop


def test_desktop_smoke_runs_real_api_and_releases_owned_port(tmp_path, monkeypatch):
    class Window:
        title = "TradeVelocity"
        destroyed = False
        def evaluate_js(self, script):
            return True
        def destroy(self):
            self.destroyed = True

    window = Window()
    captured = {}
    def create_window(title, url, **options):
        captured.update(title=title, url=url, options=options)
        return window
    def start(func=None, **options):
        captured["storage"] = options["storage_path"]
        func()
    monkeypatch.setattr(desktop, "data_directory", lambda: tmp_path)
    monkeypatch.setattr(webview, "create_window", create_window)
    monkeypatch.setattr(webview, "start", start)
    assert desktop.run_desktop(smoke_test=True) == 0
    receipt = json.loads((tmp_path / "smoke-test.json").read_text())
    assert receipt["ok"]
    assert receipt["heldout"] == 50
    assert receipt["detected"] > 0
    assert receipt["benchmark_rows"] == 6
    assert receipt["simulation_commands"] == 100
    assert window.destroyed
    assert captured["options"]["hidden"]
    assert "?build=" in captured["url"]
    assert "smoke-webview" in captured["storage"]
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", receipt["port"]))


def test_desktop_frontend_failure_still_shuts_down(tmp_path, monkeypatch):
    class Window:
        destroyed = False
        def evaluate_js(self, script):
            raise RuntimeError("Render failed")
        def destroy(self):
            self.destroyed = True
    window = Window()
    monkeypatch.setattr(desktop, "data_directory", lambda: tmp_path)
    monkeypatch.setattr(webview, "create_window", lambda *a, **kw: window)
    monkeypatch.setattr(webview, "start", lambda func, **kw: func())
    assert desktop.run_desktop(smoke_test=True) == 1
    assert window.destroyed
    assert json.loads((tmp_path / "smoke-test.json").read_text())["error"] == "Render failed"
