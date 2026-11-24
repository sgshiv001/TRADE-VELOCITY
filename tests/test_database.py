"""Exercise the public API against real SQLite and optional PostgreSQL storage."""

from concurrent.futures import ThreadPoolExecutor
import os
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest

from stock_engine.api import create_app
from stock_engine.storage import StorageError, create_store


@pytest.fixture(params=["sqlite", "postgresql"])
def database_url(request):
    if request.param == "sqlite":
        return ""
    url = os.environ.get("TRADEVELOCITY_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TRADEVELOCITY_TEST_DATABASE_URL to an isolated PostgreSQL test database")
    return url


def test_orders_replay_and_retry_receipts_survive_backend_restart(tmp_path, database_url):
    def backend():
        return TestClient(create_app(data_dir=tmp_path, serve_frontend=False, database_url=database_url))

    client = backend()
    assert client.get("/api/ready").json() == {
        "status": "ready", "storage": "postgresql" if database_url else "sqlite"}
    session_id = client.post("/api/session").json()["session_id"]
    headers = {"X-Session-ID": session_id}
    sell = {"order_id": "SELL", "symbol": "ACME", "side": "SELL", "quantity": 5, "price": "100"}
    buy = {**sell, "order_id": "BUY", "side": "BUY", "quantity": 3, "price": "101"}
    assert client.post("/api/lab/orders", headers=headers, json=sell).status_code == 200
    request_headers = {**headers, "Idempotency-Key": "retry-after-restart"}
    matched = client.post("/api/lab/orders", headers=request_headers, json=buy).json()
    assert matched["filled"] == 3
    exported = client.get("/api/lab/export", headers=headers).json()

    restarted = backend()
    assert restarted.post("/api/lab/orders", headers=request_headers, json=buy).json() == matched
    state = restarted.get("/api/lab?symbol=ACME", headers=headers).json()
    assert state["total_trades"] == 1
    assert state["trades"][0]["price"] == 100
    assert state["orders"][0]["remaining"] == 2
    assert restarted.get("/api/lab/export", headers=headers).json() == exported
    assert restarted.patch("/api/lab/orders/SELL", headers=headers,
                           json={"quantity": 4, "price": "102"}).status_code == 200
    assert restarted.delete("/api/lab/orders/SELL", headers=headers).status_code == 200
    final = backend().get("/api/lab?symbol=ACME", headers=headers).json()
    assert final["orders"] == []
    assert final["total_trades"] == 1

    assert restarted.post("/api/lab/reset", headers=headers).status_code == 200
    assert restarted.post("/api/lab/import", headers=headers, json=exported).status_code == 200
    restored = backend().get("/api/lab?symbol=ACME", headers=headers).json()
    assert restored["trades"] == state["trades"]
    assert restored["orders"][0]["remaining"] == 2


def test_database_transaction_rolls_back_every_table(tmp_path, database_url):
    store = create_store(tmp_path, database_url)
    sid = str(uuid4())
    store.save(sid, [], {"reviews": {}}, 0, receipt=("same-key", "first", {"ok": True}))
    # A duplicate receipt fails after both the metadata and command have changed.
    # The whole transaction must roll back, including the new event.
    import sqlite3
    with pytest.raises((sqlite3.Error, StorageError)):
        store.save(sid, [{"type": "cancel", "order_id": "A"}], {"reviews": {"1": "changed"}}, 1,
                   receipt=("same-key", "second", {"ok": False}))
    assert store.load(sid) == {"reviews": {}, "revision": 0, "lab": {"version": 2, "events": []}}
    assert store.receipt(sid, "same-key") == ("first", {"ok": True})


def test_concurrent_orders_conserve_database_records(tmp_path, database_url):
    client = TestClient(create_app(data_dir=tmp_path, serve_frontend=False, database_url=database_url))
    headers = {"X-Session-ID": client.post("/api/session").json()["session_id"]}
    assert client.post("/api/lab/orders", headers=headers, json={
        "order_id": "SELL", "symbol": "ACME", "side": "SELL", "quantity": 8, "price": "100"}).is_success

    def buy(index):
        return client.post("/api/lab/orders", headers=headers, json={
            "order_id": f"BUY-{index}", "symbol": "ACME", "side": "BUY", "quantity": 1, "price": "100"})

    with ThreadPoolExecutor(max_workers=4) as executor:
        assert all(response.is_success for response in executor.map(buy, range(8)))
    restarted = TestClient(create_app(data_dir=tmp_path, serve_frontend=False, database_url=database_url))
    state = restarted.get("/api/lab?symbol=ACME", headers=headers).json()
    assert state["total_trades"] == 8
    assert state["stats"]["volume"] == 8
    assert state["orders"] == []
    assert state["events"] == 9


def test_readiness_reports_database_failure_without_exposing_credentials(tmp_path, monkeypatch):
    client = TestClient(create_app(data_dir=tmp_path, serve_frontend=False, database_url=""))

    def unavailable():
        raise StorageError("database credential must stay private")

    monkeypatch.setattr(client.app.state.store, "check", unavailable)
    assert client.get("/api/health").status_code == 200
    response = client.get("/api/ready")
    assert response.status_code == 503
    assert "credential" not in response.text


def test_database_configuration_is_explicit(tmp_path, monkeypatch):
    monkeypatch.setenv("TRADEVELOCITY_DATABASE_URL", "mysql://private-credential@example/database")
    with pytest.raises(ValueError, match="postgres"):
        create_store(tmp_path)
    assert create_store(tmp_path, "").kind == "sqlite"


def test_failed_order_save_keeps_session_and_database_consistent(tmp_path, database_url, monkeypatch):
    client = TestClient(create_app(data_dir=tmp_path, serve_frontend=False, database_url=database_url))
    headers = {"X-Session-ID": client.post("/api/session").json()["session_id"]}
    order = {"order_id": "RETRY", "symbol": "ACME", "side": "SELL", "quantity": 5, "price": "100"}

    def unavailable(*args, **kwargs):
        raise StorageError("database is temporarily unavailable")

    with monkeypatch.context() as patch:
        patch.setattr(client.app.state.store, "save", unavailable)
        assert client.post("/api/lab/orders", headers=headers, json=order).status_code == 503
    assert client.get("/api/lab", headers=headers).json()["events"] == 0
    assert client.post("/api/lab/orders", headers=headers, json=order).status_code == 200
    restarted = TestClient(create_app(data_dir=tmp_path, serve_frontend=False, database_url=database_url))
    assert restarted.get("/api/lab", headers=headers).json()["events"] == 1


def test_lost_database_commit_acknowledgement_recovers_without_duplicate_trade(tmp_path, database_url, monkeypatch):
    client = TestClient(create_app(data_dir=tmp_path, serve_frontend=False, database_url=database_url))
    headers = {"X-Session-ID": client.post("/api/session").json()["session_id"]}
    order = {"order_id": "SELL", "symbol": "ACME", "side": "SELL", "quantity": 5, "price": "100"}
    assert client.post("/api/lab/orders", headers=headers, json=order).is_success
    save = client.app.state.store.save

    def commit_then_disconnect(*args, **kwargs):
        save(*args, **kwargs)
        raise StorageError("The database commit acknowledgement was lost")

    request_headers = {**headers, "Idempotency-Key": "commit-ack-lost"}
    buy = {**order, "order_id": "BUY", "side": "BUY", "quantity": 3}
    with monkeypatch.context() as patch:
        patch.setattr(client.app.state.store, "save", commit_then_disconnect)
        assert client.post("/api/lab/orders", headers=request_headers, json=buy).status_code == 503
    retried = client.post("/api/lab/orders", headers=request_headers, json=buy)
    assert retried.json()["filled"] == 3
    state = client.get("/api/lab?symbol=ACME", headers=headers).json()
    assert state["total_trades"] == 1
    assert state["orders"][0]["remaining"] == 2
    assert state["revision"] == 2
    assert client.post("/api/lab/orders", headers=headers,
                       json={**buy, "order_id": "AFTER-RECONNECT", "quantity": 2}).json()["filled"] == 2
    restarted = TestClient(create_app(data_dir=tmp_path, serve_frontend=False, database_url=database_url))
    state = restarted.get("/api/lab?symbol=ACME", headers=headers).json()
    assert state["stats"]["volume"] == 5
    assert state["total_trades"] == 2
    assert state["orders"] == []
