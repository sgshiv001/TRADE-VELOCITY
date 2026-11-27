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


def test_desktop_signin_export_is_routed_with_its_content_security_policy(tmp_path, monkeypatch):
    (tmp_path / "index.html").write_text("<title>Home</title>", encoding="utf-8")
    (tmp_path / "desktop-sign-in.html").write_text("<script>self.desktopSignIn = true;</script>", encoding="utf-8")
    monkeypatch.setenv("TRADEVELOCITY_WEB_DIR", str(tmp_path))
    client = TestClient(create_app(data_dir=tmp_path / "sessions"))
    response = client.get("/desktop-sign-in?request=example")
    assert response.status_code == 200
    assert "desktopSignIn = true" in response.text
    assert response.headers["Cache-Control"] == "no-store"
    expected = inline_script_hashes(tmp_path, app_pages(tmp_path))
    assert expected["/desktop-sign-in"] in response.headers["Content-Security-Policy"]


def test_offline_workspace_survives_restart_and_demo_uses_an_isolated_book(tmp_path):
    def boot():
        return TestClient(create_app(data_dir=tmp_path, database_url="", offline=True, serve_frontend=False))

    first = boot()
    session = first.post("/api/session").json()["session_id"]
    headers = {"X-Session-ID": session}
    assert first.post("/api/lab/orders", headers=headers, json={"order_id": "private-practice", "symbol": "ACME",
                       "side": "BUY", "quantity": 2, "price": "100"}).is_success
    result = first.get("/api/demo/fifo/DEMOA1234567?step=3").json()
    assert [(order["filled"], order["remaining"]) for order in result["orders"]] == [(10, 0), (5, 5), (15, 0)]
    assert [(fill["buyer"], fill["quantity"]) for fill in result["executions"]] == [("Buy 1", 10), ("Buy 2", 5)]
    assert first.get("/api/demo/fifo/DEMO98765432?step=0").json()["book"]["bids"] == []
    restarted = boot()
    assert restarted.post("/api/session").json()["session_id"] == session
    orders = restarted.get("/api/lab?symbol=ACME", headers=headers).json()["orders"]
    assert len(orders) == 1 and orders[0]["order_id"] == "private-practice"
