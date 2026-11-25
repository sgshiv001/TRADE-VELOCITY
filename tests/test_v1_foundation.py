import numpy as np
from fastapi.testclient import TestClient

from stock_engine.analyst import one_session_forecast
from stock_engine.api import create_app
from stock_engine.web_assets import app_pages, inline_script_hashes


def test_one_session_forecast_has_calibrated_bounds_and_requires_history():
    rng = np.random.default_rng(12)
    prices = 100 * np.exp(np.cumsum(rng.normal(0.0008, 0.014, 400)))
    assert one_session_forecast(prices[:60], prices[59]) is None
    forecast = one_session_forecast(prices, prices[-1])
    assert forecast["lower"] <= forecast["point"] <= forecast["upper"]
    assert forecast["fit_samples"] + forecast["selection_samples"] + forecast["calibration_samples"] == 379
    assert forecast["calibration_samples"] >= 40


def test_exported_pages_receive_only_their_own_inline_script_hashes(tmp_path, monkeypatch):
    (tmp_path / "index.html").write_text("<script>self.exported = 1;</script>", encoding="utf-8")
    (tmp_path / "app.html").write_text("<script>self.exported = 2;</script>", encoding="utf-8")
    monkeypatch.setenv("TRADEVELOCITY_WEB_DIR", str(tmp_path))
    client = TestClient(create_app(data_dir=tmp_path / "sessions"))
    expected = inline_script_hashes(tmp_path, app_pages(tmp_path))
    app = client.get("/app")
    assert app.status_code == 200 and "exported = 2" in app.text
    policy = app.headers["Content-Security-Policy"]
    assert expected["/app"] in policy
    assert expected["/"] not in policy
    assert "script-src 'unsafe-inline'" not in policy
    assert app.headers["Cache-Control"] == "no-store"
