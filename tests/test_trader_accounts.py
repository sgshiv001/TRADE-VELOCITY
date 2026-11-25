import os
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest
from starlette.websockets import WebSocketDisconnect

from stock_engine.api import create_app
from stock_engine.security import COOKIE, SecuritySettings


ORIGIN = "https://tradevelocity.test"
PASSWORD = "test-only long password"


@pytest.fixture
def backend(tmp_path):
    url = os.environ.get("TRADEVELOCITY_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires an isolated PostgreSQL database")

    def create():
        return create_app(data_dir=tmp_path, serve_frontend=False, database_url=url,
                          security=SecuritySettings("accounts", ORIGIN))
    return create


def register(client):
    username = "trader_" + uuid4().hex[:16]
    response = client.post("/api/auth/register", json={"username": username.upper(), "password": PASSWORD})
    assert response.status_code == 201
    cookie = response.headers["set-cookie"].lower()
    assert all(part in cookie for part in ("httponly", "secure", "samesite=strict", "path=/"))
    trader = client.get("/api/auth/status").json()["trader"]
    assert trader["username"] == username
    assert trader["tutorial_seen"] is False
    return trader


def test_trader_data_and_tutorial_persist_across_server_restart(backend):
    client = TestClient(backend(), base_url=ORIGIN)
    assert client.get("/api/ready").json() == {"status": "ready", "storage": "postgresql"}
    assert client.post("/api/session").status_code == 401
    trader = register(client)
    workspace = trader["workspace_id"]
    headers = {"X-Session-ID": workspace}
    order = {"order_id": "S1", "symbol": "ACME", "side": "SELL", "quantity": 5, "price": "100"}
    assert client.post("/api/lab/orders", headers=headers, json=order).is_success
    assert client.post("/api/auth/tutorial").json() == {"tutorial_seen": True}
    token = client.cookies.get(COOKIE)

    restarted = TestClient(backend(), base_url=ORIGIN, cookies={COOKIE: token})
    assert restarted.get("/api/auth/status").json()["trader"]["tutorial_seen"] is True
    assert restarted.post("/api/session").json()["session_id"] == workspace
    assert restarted.get("/api/lab?symbol=ACME", headers=headers).json()["orders"][0]["remaining"] == 5
    assert restarted.post("/api/auth/logout").is_success
    old_session = TestClient(restarted.app, base_url=ORIGIN, cookies={COOKIE: token})
    assert old_session.get("/api/lab", headers=headers).status_code == 401
    assert restarted.post("/api/auth/login", json={"username": trader["username"], "password": PASSWORD}).is_success
    assert restarted.get("/api/auth/status").json()["trader"]["workspace_id"] == workspace


def test_accounts_cannot_read_modify_or_subscribe_to_other_workspaces(backend):
    app = backend()
    first = TestClient(app, base_url=ORIGIN)
    second = TestClient(app, base_url=ORIGIN)
    mine = register(first)["workspace_id"]
    theirs = register(second)["workspace_id"]
    assert mine != theirs
    wrong_workspace = {"X-Session-ID": theirs}
    assert first.get("/api/lab", headers=wrong_workspace).status_code == 401
    assert first.post("/api/lab/reset", headers=wrong_workspace).status_code == 401
    assert first.post("/api/session", headers=wrong_workspace).json()["session_id"] == mine
    socket_headers = {"Host": "tradevelocity.test", "Origin": ORIGIN,
                      "Cookie": f"{COOKIE}={first.cookies.get(COOKIE)}"}
    with pytest.raises(WebSocketDisconnect):
        with first.websocket_connect(f"/api/live?session_id={theirs}", headers=socket_headers):
            pytest.fail("An account received another trader's live subscription")
    with first.websocket_connect(f"/api/live?session_id={mine}", headers=socket_headers) as socket:
        assert socket.receive_json() == {"type": "connected", "revision": 0}


def test_bad_sign_in_and_duplicate_registration(backend):
    client = TestClient(backend(), base_url=ORIGIN)
    trader = register(client)
    assert client.post("/api/auth/logout").is_success
    username = trader["username"]
    assert client.post("/api/auth/register", json={"username": username, "password": PASSWORD}).status_code == 409
    invalid_password = "x" * 129
    invalid_request = client.post("/api/auth/login", json={"username": username, "password": invalid_password})
    assert invalid_request.status_code == 422
    assert invalid_password not in invalid_request.text
    assert client.post("/api/auth/login", json={"username": username, "password": "wrong"}).status_code == 401
    assert client.get("/api/auth/status").json()["authenticated"] is False


def test_shared_depth_updates_both_traders_and_survives_restart(backend, monkeypatch):
    app = backend()
    buyer = TestClient(app, base_url=ORIGIN)
    seller = TestClient(app, base_url=ORIGIN)
    outsider = TestClient(app, base_url=ORIGIN)
    buyer_trader, seller_trader, outsider_trader = map(register, (buyer, seller, outsider))
    symbol = "QA" + uuid4().hex[:12].upper()
    buyer_headers = {"X-Session-ID": buyer_trader["workspace_id"], "Idempotency-Key": "order-1"}
    seller_headers = {"X-Session-ID": seller_trader["workspace_id"], "Idempotency-Key": "order-1"}
    outsider_headers = {"X-Session-ID": outsider_trader["workspace_id"]}
    order = {"order_id": "personal-reference", "symbol": symbol, "side": "BUY",
             "quantity": 10, "price": "1800"}
    socket_headers = {"Host": "tradevelocity.test", "Origin": ORIGIN,
                      "Cookie": f"{COOKIE}={seller.cookies.get(COOKIE)}"}
    with seller.websocket_connect(f"/api/live?session_id={seller_trader['workspace_id']}",
                                  headers=socket_headers) as socket:
        assert socket.receive_json()["type"] == "connected"
        placed = buyer.post("/api/exchange/orders", headers=buyer_headers, json=order)
        assert placed.is_success, placed.text
        assert socket.receive_json() == {"type": "exchange_changed"}
    assert buyer.post("/api/exchange/orders", headers=buyer_headers, json=order).json() == placed.json()
    order_id = placed.json()["order_id"]
    state = seller.get(f"/api/exchange?symbol={symbol}", headers=seller_headers).json()
    assert state["book"]["bids"] == [{"price": "1800.00", "quantity": 10, "orders": 1}]
    assert state["orders"] == []
    assert seller.delete(f"/api/exchange/orders/{order_id}", headers=seller_headers).status_code == 404
    assert seller.patch(f"/api/exchange/orders/{order_id}", headers=seller_headers,
                        json={"quantity": 20, "price": "1800"}).status_code == 404
    fill = seller.post("/api/exchange/orders", headers=seller_headers,
                       json={**order, "side": "SELL", "quantity": 5, "price": "1799"})
    assert fill.is_success, fill.text
    assert fill.json()["filled"] == 5
    assert float(fill.json()["trades"][0]["price"]) == 1800
    assert buyer.get("/api/exchange/trades", headers=buyer_headers).json()["total"] == 1
    assert seller.get("/api/exchange/trades", headers=seller_headers).json()["total"] == 1
    assert outsider.get("/api/exchange/trades", headers=outsider_headers).json()["total"] == 0
    assert seller.get(f"/api/lab?symbol={symbol}", headers=seller_headers).json()["book"]["bids"] == []

    monkeypatch.setenv("TRADEVELOCITY_ADMIN_USERNAME", buyer_trader["username"])
    restarted = backend()
    buyer_after = TestClient(restarted, base_url=ORIGIN, cookies={COOKIE: buyer.cookies.get(COOKIE)})
    seller_after = TestClient(restarted, base_url=ORIGIN, cookies={COOKIE: seller.cookies.get(COOKIE)})
    state = buyer_after.get(f"/api/exchange?symbol={symbol}", headers=buyer_headers).json()
    assert state["book"]["bids"][0]["quantity"] == state["orders"][0]["remaining"] == 5
    assert seller_after.post("/api/auth/activity").is_success
    assert seller_after.get("/api/admin/activity").status_code == 403
    assert buyer_after.get("/api/auth/status").json()["trader"]["admin"] is True
    report = buyer_after.get("/api/admin/activity").json()
    row = next(user for user in report["users"] if user["username"] == seller_trader["username"])
    assert row["active"] and row["orders"] == row["executions"] == 1
    assert set(row) == {"username", "active", "last_active_at", "orders", "executions"}
