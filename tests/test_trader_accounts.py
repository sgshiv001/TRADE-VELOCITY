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
