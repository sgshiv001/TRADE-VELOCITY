import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from stock_engine.api import create_app
from stock_engine.security import COOKIE, MAX_BODY, SecuritySettings

KEY = "test-only-key-" + "x"*40
ORIGIN = "https://tradevelocity.test"


@pytest.fixture
def private(tmp_path):
    return TestClient(create_app(data_dir=tmp_path,serve_frontend=False,
                                security=SecuritySettings("private",ORIGIN,KEY)),base_url=ORIGIN)


@pytest.mark.parametrize("settings", [SecuritySettings(),None])
def test_local_host_and_origin_protection(tmp_path,settings):
    client = TestClient(create_app(data_dir=tmp_path,serve_frontend=False,security=settings))
    assert client.get("/api/health").status_code == 200
    assert client.post("/api/session",headers={"Origin":"https://evil.test"}).status_code == 403
    assert client.get("/api/health",headers={"Host":"evil.test"}).status_code == 403
    assert client.get("/api/auth/status").json() == {"required":False,"authenticated":True}
    assert client.get("/docs").status_code == 404
    assert client.get("/api/health").headers["x-content-type-options"] == "nosniff"


@pytest.mark.parametrize("settings", [("public","",KEY),("private","http://site.test",KEY),
                                     ("private",ORIGIN,"short"),("local","",KEY),
                                     ("private",ORIGIN,"REPLACE_WITH_A_RANDOM_KEY_OF_AT_LEAST_32_CHARACTERS"),
                                     ("private","https://user:password@site.test",KEY)])
def test_unsafe_configuration_fails_closed(settings):
    with pytest.raises(ValueError):
        SecuritySettings(*settings)


def login(client):
    response = client.post("/api/auth/login",json={"access_key":KEY},headers={"Origin":ORIGIN})
    assert response.status_code == 200
    return response


def test_private_sign_in_cookie_logout_and_bearer(private):
    assert private.post("/api/session").status_code == 401
    assert private.get("/api/auth/status").json()["authenticated"] is False
    assert private.post("/api/auth/login",json={"access_key":"wrong"}).status_code == 401
    response = login(private)
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie and "secure" in cookie and "samesite=strict" in cookie and "path=/" in cookie
    assert private.post("/api/session").status_code == 200
    assert private.get("/api/health").headers["strict-transport-security"] == "max-age=31536000"
    assert private.post("/api/auth/logout").status_code == 200
    assert private.post("/api/session").status_code == 401
    assert private.post("/api/session",headers={"Authorization":f"Bearer {KEY}"}).status_code == 200


def test_private_cross_origin_and_host_requests_are_rejected(private):
    assert private.post("/api/auth/login",json={"access_key":KEY},headers={"Origin":"https://evil.test"}).status_code == 403
    assert private.get("/api/health",headers={"Host":"evil.test"}).status_code == 403
    assert private.app.state.security.tokens == {}


def test_login_rate_limit_and_expiration(private):
    for _ in range(5):
        assert private.post("/api/auth/login",json={"access_key":"wrong"}).status_code == 401
    assert private.post("/api/auth/login",json={"access_key":KEY}).status_code == 429
    private.app.state.security.windows.clear()
    login(private)
    guard = private.app.state.security
    now = guard.clock()
    guard.clock = lambda:now+8*60*60+1
    assert private.post("/api/session").status_code == 401


def test_body_limit_before_session_mutation(private):
    login(private)
    response = private.post("/api/session",content=b"x"*(MAX_BODY+1))
    assert response.status_code == 413
    assert private.app.state.sessions == {}


@pytest.mark.parametrize("host", ["[invalid","127.0.0.1:999999","user@127.0.0.1","127.0.0.1/extra"])
def test_malformed_host_is_rejected_without_server_error(private,host):
    assert private.get("/api/health",headers={"Host":host}).status_code == 403


def test_local_mode_denies_non_loopback_clients(tmp_path):
    client = TestClient(create_app(data_dir=tmp_path,serve_frontend=False),client=("192.0.2.10",1234))
    assert client.get("/api/health").status_code == 403


def test_rate_window_recovers_and_expensive_operations_are_limited(private,monkeypatch):
    guard = private.app.state.security
    now = guard.clock()
    guard.clock = lambda:now
    assert not guard.limited("test","category",2)
    assert not guard.limited("test","category",2)
    assert guard.limited("test","category",2)
    guard.clock = lambda:now+61
    assert not guard.limited("test","category",2)
    login(private)
    monkeypatch.setattr("stock_engine.api.compare_workload",lambda *args:[])
    for _ in range(2):
        assert private.post("/api/experiments",json={"count":100,"workload":"deep"}).status_code == 200
    assert private.post("/api/experiments",json={"count":100,"workload":"deep"}).status_code == 429


def test_private_websocket_requires_auth_and_checks_origin(private):
    with pytest.raises(WebSocketDisconnect) as denied:
        with private.websocket_connect("/api/live?session_id=invalid"):
            pytest.fail("Unauthenticated socket was accepted")
    assert denied.value.code == 1008
    login(private)
    sid = private.post("/api/session").json()["session_id"]
    bearer = {"Authorization":f"Bearer {KEY}","Host":"tradevelocity.test","Origin":ORIGIN}
    with private.websocket_connect(f"/api/live?session_id={sid}",headers=bearer) as socket:
        assert socket.receive_json() == {"type":"connected","revision":0}
    with pytest.raises(WebSocketDisconnect):
        with private.websocket_connect(f"/api/live?session_id={sid}",headers={**bearer,"Origin":"https://evil.test"}):
            pytest.fail("Cross-origin socket was accepted")


def test_websocket_cookie_revocation_before_next_update(private):
    login(private)
    sid = private.post("/api/session").json()["session_id"]
    headers = {"Host":"tradevelocity.test","Origin":ORIGIN,"Cookie":f"{COOKIE}={private.cookies.get(COOKIE)}"}
    with private.websocket_connect(f"/api/live?session_id={sid}",headers=headers) as socket:
        assert socket.receive_json()["type"] == "connected"
        assert private.post("/api/auth/logout").status_code == 200
        private.post("/api/lab/orders",headers={"Authorization":f"Bearer {KEY}","X-Session-ID":sid},
                     json={"order_id":"S","symbol":"RELIANCE","side":"SELL","quantity":1,"price":"100"})
        with pytest.raises(WebSocketDisconnect):
            socket.receive_json()
