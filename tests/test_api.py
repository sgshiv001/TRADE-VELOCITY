from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient
from stock_engine.api import create_app
from stock_engine.companies import COMPANIES
from stock_engine.market_data import FIELDS, MarketData


@pytest.fixture
def market():
    frame = pd.DataFrame([[100, 102, 98, 100, 100, 1000]] * 120,
                         index=pd.bdate_range("2025-01-01", periods=120), columns=FIELDS)
    return MarketData({symbol: frame.copy() for symbol in COMPANIES}, "Test daily provider", "2025-06-20T00:00:00Z")


@pytest.fixture
def client(tmp_path, market):
    return TestClient(create_app(market=market, data_dir=tmp_path, serve_frontend=False))


def session(client):
    response = client.post("/api/session")
    assert response.status_code == 200
    return {"X-Session-ID": response.json()["session_id"]}


def test_real_company_universe_adjusted_history_and_provenance(client):
    response = client.get("/api/market")
    assert response.status_code == 200
    data = response.json()
    assert len(data["companies"]) == 8
    assert not data["is_demo"]
    assert data["source"] == "Test daily provider"
    history = client.get("/api/companies/HDFCBANK?period=1M").json()
    assert len(history["performance"]) == 5
    assert history["history"][-1]["rsi"] == 50
    assert "adjusted" in history["basis"]
    assert client.get("/api/companies/UNKNOWN").status_code == 404
    assert client.get("/api/companies/RELIANCE?period=invalid").status_code == 422
    insight = client.get("/api/analysis/RELIANCE?period=1Y")
    assert insight.status_code == 200
    assert insight.json()["signal"] in {"Bullish", "Bearish", "Mixed"}
    assert insight.json()["method"].startswith("TradeVelocity Rules")
    assert len(insight.json()["evidence"]) == 3
    assert client.get("/api/analysis/UNKNOWN").status_code == 404


def test_paper_buy_sell_rejection_and_account_isolation(client):
    first, second = session(client), session(client)
    buy = client.post("/api/portfolio/orders", headers=first, json={"symbol": "RELIANCE", "side": "BUY", "quantity": 10})
    assert buy.status_code == 200
    assert buy.json()["result"]["filled"] == 10
    before = client.get("/api/portfolio", headers=first).json()
    assert before["holdings"][0]["Shares"] == 10
    rejected = client.post("/api/portfolio/orders", headers=first, json={"symbol": "RELIANCE", "side": "SELL", "quantity": 11})
    assert rejected.status_code == 400
    after = client.get("/api/portfolio", headers=first).json()
    assert after["cash"] == before["cash"] and after["holdings"] == before["holdings"]
    sold = client.post("/api/portfolio/orders", headers=first, json={"symbol": "RELIANCE", "side": "SELL", "quantity": 5})
    assert sold.status_code == 200
    assert sold.json()["portfolio"]["holdings"][0]["Shares"] == 5
    assert sold.json()["portfolio"]["realized_pnl"] == pytest.approx(-1)
    assert client.get("/api/portfolio", headers=second).json()["holdings"] == []


def test_saved_paper_and_lab_sessions_restore_in_new_app(tmp_path, market):
    first = TestClient(create_app(market=market, data_dir=tmp_path, serve_frontend=False))
    header = session(first)
    first.post("/api/portfolio/orders", headers=header, json={"symbol": "TCS", "side": "BUY", "quantity": 10})
    first.post("/api/lab/demo", headers=header)
    expected = first.get("/api/portfolio", headers=header).json()
    restored = TestClient(create_app(market=market, data_dir=tmp_path, serve_frontend=False))
    actual = restored.get("/api/portfolio", headers=header).json()
    assert actual["cash"] == expected["cash"]
    assert actual["holdings"] == expected["holdings"]
    assert actual["history"] == expected["history"]
    assert restored.get("/api/lab", headers=header).json()["events"] == 9


def test_invalid_identifiers_and_quantity_are_rejected(client):
    assert client.get("/api/portfolio").status_code == 422
    assert client.get("/api/portfolio", headers={"X-Session-ID": "../../private"}).status_code == 401
    header = session(client)
    for quantity in [0, -1, True, 1.5]:
        assert client.post("/api/portfolio/orders", headers=header,
                           json={"symbol": "TCS", "side": "BUY", "quantity": quantity}).status_code == 422
    assert client.post("/api/portfolio/orders", headers=header,
                       json={"symbol": "UNKNOWN", "side": "BUY", "quantity": 1}).status_code == 400


def test_concurrent_buys_do_not_overspend_virtual_cash(client):
    header = session(client)
    def buy(_):
        return client.post("/api/portfolio/orders", headers=header,
                           json={"symbol": "RELIANCE", "side": "BUY", "quantity": 5000}).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = sorted(pool.map(buy, range(2)))
    assert results == [200, 400]
    data = client.get("/api/portfolio", headers=header).json()
    assert data["cash"] == pytest.approx(499500)
    assert data["holdings"][0]["Shares"] == 5000


def test_failed_data_refresh_keeps_snapshot_and_holdings(client, monkeypatch):
    header = session(client)
    client.post("/api/portfolio/demo", headers=header)
    before = client.get("/api/portfolio", headers=header).json()
    def fail():
        raise RuntimeError("provider unavailable")
    monkeypatch.setattr("stock_engine.api.download_market_data", fail)
    assert client.post("/api/market/refresh").status_code == 503
    after = client.get("/api/portfolio", headers=header).json()
    assert before == after
    assert client.get("/api/market").json()["source"] == "Test daily provider"


def test_lab_place_partial_fill_modify_cancel_and_import_validation(client):
    header = session(client)
    orders = [("S1", "SELL", 150, "105"), ("B1", "BUY", 100, "106")]
    for order_id, side, quantity, price in orders:
        assert client.post("/api/lab/orders", headers=header,
                           json={"order_id": order_id, "symbol": "ACME", "side": side, "quantity": quantity, "price": price}).status_code == 200
    lab = client.get("/api/lab", headers=header).json()
    assert lab["book"]["asks"][0]["quantity"] == 50
    assert lab["trades"][0]["price"] == 105
    assert client.patch("/api/lab/orders/S1", headers=header, json={"quantity": 30, "price": "107"}).status_code == 200
    assert client.delete("/api/lab/orders/S1", headers=header).status_code == 200
    exported = client.get("/api/lab/export", headers=header).json()
    assert len(exported["events"]) == 4
    assert client.post("/api/lab/import", headers=header, json={}).status_code == 400
    assert client.get("/api/lab/export", headers=header).json() == exported
    assert client.post("/api/lab/import", headers=header, json=exported).status_code == 200


def test_demo_and_reset_portfolio_preserve_matching_lab(client):
    header = session(client)
    client.post("/api/lab/demo", headers=header)
    demo = client.post("/api/portfolio/demo", headers=header).json()
    assert len(demo["holdings"]) == 4
    assert all("simulated purchase" in fill["Note"] for fill in demo["fills"])
    reset = client.post("/api/portfolio/reset", headers=header).json()
    assert reset["holdings"] == [] and reset["cash"] == 1_000_000
    assert client.get("/api/lab", headers=header).json()["events"] == 9


def test_comparison_isolated_from_accounts_and_labs(client):
    header = session(client)
    before = client.get("/api/portfolio", headers=header).json()
    response = client.post("/api/experiments", json={"workload": "deep", "count": 100})
    assert response.status_code == 200
    assert len(response.json()) == 6
    assert all(row["trades"] == 50 for row in response.json())
    assert client.get("/api/portfolio", headers=header).json() == before
