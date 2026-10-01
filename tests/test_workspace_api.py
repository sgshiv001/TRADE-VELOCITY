from concurrent.futures import ThreadPoolExecutor
import json
import sqlite3
from uuid import uuid4

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
    return TestClient(create_app(market=market, data_dir=tmp_path / "sessions", serve_frontend=False))


def session(client):
    response = client.post("/api/session")
    assert response.status_code == 200
    return {"X-Session-ID": response.json()["session_id"]}


def order(client, header, identifier, side, quantity, price="100", symbol="RELIANCE"):
    return client.post("/api/lab/orders", headers=header, json={"order_id": identifier,
                       "symbol": symbol, "side": side, "quantity": quantity, "price": price})


def test_new_sessions_are_empty_without_generated_liquidity(client):
    first, second = session(client), session(client)
    assert client.get("/api/health").headers["cache-control"] == "no-store"
    assert client.get("/api/health").json()["real_money"] is False
    for header in [first, second]:
        lab = client.get("/api/lab", headers=header).json()
        assert lab["orders"] == lab["trades"] == []
        assert lab["events"] == 0
    assert order(client, first, "EMPTY-MARKET", "BUY", 2, None).json()["filled"] == 0
    assert client.get("/api/lab", headers=second).json()["events"] == 0


@pytest.mark.parametrize("path", ["/api/lab/demo", "/api/lab/watchdog/demo", "/api/lab/simulate", "/api/portfolio/demo", "/api/portfolio/orders"])
def test_removed_presets_cannot_replace_a_session(client, path):
    header = session(client)
    order(client, header, "KEEP", "SELL", 3)
    before = client.get("/api/lab/export", headers=header).json()
    assert client.post(path, headers=header, json={}).status_code == 404
    assert client.get("/api/lab/export", headers=header).json() == before


def test_order_lifecycle_and_replay_are_real_engine_outcomes(client):
    header = session(client)
    assert order(client, header, "SELL", "SELL", 15, "105").status_code == 200
    filled = order(client, header, "BUY", "BUY", 10, "106").json()
    assert filled["filled"] == 10
    state = client.get("/api/lab", headers=header).json()
    assert state["book"]["asks"][0]["quantity"] == 5
    assert state["trades"][0]["price"] == 105
    assert client.patch("/api/lab/orders/SELL", headers=header, json={"quantity": 3, "price": "107"}).status_code == 200
    assert client.delete("/api/lab/orders/SELL", headers=header).status_code == 200
    exported = client.get("/api/lab/export", headers=header).json()
    assert len(exported["events"]) == 4
    assert client.post("/api/lab/import", headers=header, json={}).status_code == 400
    assert client.get("/api/lab/export", headers=header).json() == exported
    assert client.post("/api/lab/reset", headers=header).status_code == 200
    assert client.get("/api/lab", headers=header).json()["total_trades"] == 0
    assert client.post("/api/lab/import", headers=header, json=exported).status_code == 200
    assert client.get("/api/lab", headers=header).json()["trades"][0]["quantity"] == 10


def test_persistence_and_legacy_account_preservation(tmp_path, market):
    directory = tmp_path / "sessions"
    directory.mkdir()
    header = {"X-Session-ID": str(uuid4())}
    path = directory / f'{header["X-Session-ID"]}.json'
    payload = {"lab": {"version":1, "events":[{"type":"place","order_id":"SAVE","symbol":"RELIANCE","side":"SELL","quantity":4,"price":"100"}]}, "broker":{"old_virtual_account": "preserve without operating"}}
    path.write_text(json.dumps(payload))
    restored = TestClient(create_app(market=market, data_dir=directory, serve_frontend=False))
    assert restored.get("/api/lab", headers=header).json()["orders"][0]["remaining"] == 4
    order(restored, header, "AFTER-RESTART", "BUY", 2)
    assert json.loads(path.read_text())["broker"] == payload["broker"]
    assert restored.get("/api/lab", headers=header).json()["stats"]["volume"] == 2
    assert restored.app.state.store.load(header["X-Session-ID"])["broker"] == payload["broker"]
    assert json.loads(path.read_text()) == payload
    again = TestClient(create_app(market=market, data_dir=directory, serve_frontend=False))
    assert again.get("/api/lab", headers=header).json()["stats"]["volume"] == 2


def test_trade_timestamps_survive_restart_and_export(tmp_path, market):
    directory = tmp_path / "sessions"
    first = TestClient(create_app(market=market,data_dir=directory,serve_frontend=False))
    header = session(first)
    order(first,header,"S","SELL",4)
    original = order(first,header,"B","BUY",2).json()["trades"][0]
    restored = TestClient(create_app(market=market,data_dir=directory,serve_frontend=False))
    assert restored.get("/api/lab",headers=header).json()["trades"][0] == original


@pytest.mark.parametrize("action", ["place", "modify", "cancel", "reset", "import"])
def test_failed_save_rolls_back_every_mutation(client, monkeypatch, action):
    header = session(client)
    order(client,header,"S","SELL",5)
    order(client,header,"B","BUY",2)
    before = client.get("/api/lab",headers=header).json()
    exported = client.get("/api/lab/export",headers=header).json()
    def fail(*args,**kwargs):
        raise sqlite3.OperationalError("simulated disk failure")
    with monkeypatch.context() as patch:
        patch.setattr(client.app.state.store,"save",fail)
        if action == "place": response = order(client,header,"FAIL","BUY",1)
        elif action == "modify": response = client.patch("/api/lab/orders/S",headers=header,json={"quantity":9,"price":"90"})
        elif action == "cancel": response = client.delete("/api/lab/orders/S",headers=header)
        elif action == "reset": response = client.post("/api/lab/reset",headers=header)
        else: response = client.post("/api/lab/import",headers=header,json={"version":1,"events":[]})
    assert response.status_code == 503
    assert client.get("/api/lab",headers=header).json() == before
    assert client.get("/api/lab/export",headers=header).json() == exported
    restored = TestClient(create_app(market=client.app.state.market,data_dir=client.app.state.data_dir,serve_frontend=False))
    assert restored.get("/api/lab",headers=header).json() == before


def test_idempotency_survives_restart_and_rejects_different_inputs(tmp_path, market):
    directory = tmp_path / "sessions"
    client = TestClient(create_app(market=market,data_dir=directory,serve_frontend=False))
    header = session(client)
    order(client,header,"S","SELL",5)
    retry_header = {**header,"Idempotency-Key":"retry-1"}
    first = order(client,retry_header,"B","BUY",2)
    assert order(client,retry_header,"B","BUY",2).json() == first.json()
    restored = TestClient(create_app(market=market,data_dir=directory,serve_frontend=False))
    assert order(restored,retry_header,"B","BUY",2).json() == first.json()
    assert order(restored,retry_header,"B","BUY",3).status_code == 409
    assert restored.get("/api/lab",headers=header).json()["stats"]["volume"] == 2


def test_live_updates_follow_commits_and_are_session_isolated(client, monkeypatch):
    header, other = session(client), session(client)
    with client.websocket_connect(f'/api/live?session_id={header["X-Session-ID"]}') as socket:
        assert socket.receive_json() == {"type":"connected","revision":0}
        order(client,other,"OTHER","SELL",3)
        order(client,header,"S","SELL",5)
        assert socket.receive_json() == {"type":"changed","revision":1}
        assert len(client.app.state.sessions[header["X-Session-ID"]].listeners) == 1
    assert client.app.state.sessions[header["X-Session-ID"]].listeners == []


def test_repeated_live_disconnects_release_listeners(client):
    header = session(client)
    for index in range(20):
        with client.websocket_connect(f'/api/live?session_id={header["X-Session-ID"]}') as socket:
            assert socket.receive_json()["type"] == "connected"
            order(client, header, f"RECONNECT-{index}", "SELL", 1)
            assert socket.receive_json() == {"type": "changed", "revision": index + 1}
        assert client.app.state.sessions[header["X-Session-ID"]].listeners == []


def test_sparse_history_is_json_safe_without_fabricated_returns(tmp_path):
    frame = pd.DataFrame([[100,102,98,100,100,1000]] * 2,index=pd.to_datetime(["2026-01-01","2026-09-30"]),columns=FIELDS)
    client = TestClient(create_app(market=MarketData({"RELIANCE":frame},"Sparse provider","2026-09-30"),data_dir=tmp_path,serve_frontend=False))
    response = client.get("/api/companies/RELIANCE?period=1M")
    assert response.status_code == 200
    assert len(response.json()["history"]) == 1
    assert response.json()["metrics"]["change_pct"] is None
    assert response.json()["metrics"]["volatility_pct"] is None
    assert response.json()["metrics"]["growth_pct"] is None
    assert client.get("/api/analysis/RELIANCE?period=1M").status_code == 404


def test_concurrent_orders_cannot_overfill_counterparty(client):
    header = session(client)
    order(client, header, "MAKER", "SELL", 5)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda index: order(client, header, f"BUY-{index}", "BUY", 4).json(), range(2)))
    assert sorted(result["filled"] for result in results) == [1, 4]
    lab = client.get("/api/lab", headers=header).json()
    assert lab["stats"]["volume"] == 5
    assert sum(row["remaining"] for row in lab["orders"]) == 3


def test_full_history_pagination_search_and_export(client):
    header = session(client)
    order(client, header, "MAKER", "SELL", 120)
    for index in range(120):
        assert order(client, header, f"TAKER-{index}", "BUY", 1).status_code == 200
    page = client.get("/api/lab/trades?offset=100&limit=50", headers=header).json()
    assert page["total"] == 120 and len(page["trades"]) == 20
    assert page["trades"][-1]["trade_id"] == 1
    found = client.get("/api/lab/trades?query=TAKER-119", headers=header).json()
    assert found["total"] == 1
    assert len(client.get("/api/lab/trades/export", headers=header).json()) == 120
    assert client.get("/api/lab/trades?offset=-1", headers=header).status_code == 422


def test_watchdog_supports_user_symbols_without_preset_activity(client):
    header = session(client)
    order(client, header, "CUSTOM-S", "SELL", 4, symbol="MYSTOCK")
    order(client, header, "CUSTOM-B", "BUY", 2, symbol="MYSTOCK")
    report = client.get("/api/lab/watchdog?symbol=MYSTOCK", headers=header).json()
    assert report["status"] == "warming_up" and report["observations"] == 1
    assert report["alerts"] == []
    assert client.get("/api/lab/watchdog?symbol=RELIANCE", headers=header).json()["observations"] == 0


def test_input_and_session_validation(client):
    assert client.get("/api/lab").status_code == 422
    assert client.get("/api/lab", headers={"X-Session-ID": "../../private"}).status_code == 401
    header = session(client)
    for quantity in [0, -1, True, 1.5]:
        assert order(client, header, "INVALID", "BUY", quantity).status_code == 422
    assert order(client, header, "INVALID", "BUY", 1, symbol="bad symbol").status_code == 422


def test_real_history_and_computed_metrics(client):
    data = client.get("/api/market").json()
    assert data["available"] and len(data["companies"]) == 8
    history = client.get("/api/companies/HDFCBANK?period=1M").json()
    assert history["history"][-1]["rsi"] == 50
    assert "adjusted" in history["basis"]
    assert client.get("/api/companies/UNKNOWN").status_code == 404
    assert client.get("/api/companies/RELIANCE?period=invalid").status_code == 422
    assert client.get("/api/analysis/RELIANCE").json()["signal"] in {"Bullish", "Bearish", "Mixed"}


def test_missing_data_does_not_prevent_order_entry(tmp_path):
    client = TestClient(create_app(market=MarketData({}, "Unavailable", ""), data_dir=tmp_path, serve_frontend=False))
    assert client.get("/api/market").json()["companies"] == []
    assert client.get("/api/companies/RELIANCE").status_code == 503
    header = session(client)
    assert order(client, header, "NO-MARKET", "SELL", 5).status_code == 200


def test_failed_refresh_preserves_orders_and_snapshot(client, monkeypatch):
    header = session(client)
    order(client, header, "KEEP", "SELL", 5)
    before = client.get("/api/lab/export", headers=header).json()
    def fail():
        raise RuntimeError("provider unavailable")
    monkeypatch.setattr("stock_engine.api.download_market_data", fail)
    assert client.post("/api/market/refresh").status_code == 503
    assert client.get("/api/lab/export", headers=header).json() == before
    assert client.get("/api/market").json()["source"] == "Test daily provider"


def test_successful_refresh_persists_outside_the_packaged_app(tmp_path, market, monkeypatch):
    monkeypatch.setattr("stock_engine.api.download_market_data", lambda: market)
    directory = tmp_path / "sessions"
    client = TestClient(create_app(market=market, data_dir=directory, serve_frontend=False))
    assert client.post("/api/market/refresh").status_code == 200
    assert (tmp_path / "market-history.json").exists()
    restored = TestClient(create_app(data_dir=directory, serve_frontend=False))
    assert restored.get("/api/market").json()["source"] == market.source


def test_benchmarks_do_not_change_the_active_session(client):
    header = session(client)
    order(client, header, "KEEP", "SELL", 1)
    before = client.get("/api/lab/export", headers=header).json()
    response = client.post("/api/experiments", json={"workload": "deep", "count": 100})
    assert response.status_code == 200 and len(response.json()) == 6
    assert client.get("/api/lab/export", headers=header).json() == before
