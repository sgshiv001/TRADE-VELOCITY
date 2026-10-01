"""Desktop lifecycle checks; actual native/frozen smoke tests are run separately."""
import json
import socket

import pytest

pytest.importorskip("webview")
import webview
from stock_engine import desktop


@pytest.fixture(autouse=True)
def isolated_prerequisite_check(monkeypatch):
    # Lifecycle tests mock the native window; real prerequisites are validated
    # by the separate actual Windows smoke and dedicated prerequisite tests.
    monkeypatch.setattr("stock_engine.windows_checks.check_windows",lambda:{"ready":True,"problems":[],"test_fixture":True})


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
    assert receipt["matched_shares"] == 7
    assert receipt["recorded_trades"] == 1
    assert receipt["observations"] == 1
    assert receipt["benchmark_rows"] == 6
    assert receipt["calibrated_alert"]
    assert receipt["model_version"] == "execution-watchdog-v3"
    assert receipt["calibrated_observations"] == 46
    assert receipt["calibration"]["forest_margin"] == .08
    assert receipt["calibration"]["fit_observations"] == 24
    assert receipt["calibration"]["cutoff_observations"] == 16
    assert "robust_guard" in receipt["detectors"]
    assert receipt["matching_unchanged_by_monitor"]
    assert receipt["high_volume_regression"]
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
