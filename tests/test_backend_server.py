import sys

import pytest

from stock_engine import server
from stock_engine.storage import StorageError


def test_local_backend_checks_database_and_binds_loopback(tmp_path, monkeypatch):
    monkeypatch.setenv("TRADEVELOCITY_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("TRADEVELOCITY_DATABASE_URL", "")
    monkeypatch.setattr(sys, "argv", ["server", "--local", "--port", "8123"])
    captured = {}

    def run(app, **options):
        captured.update(options)
        assert app.state.store.path.is_file()

    monkeypatch.setattr(server.uvicorn, "run", run)
    server.main()
    assert captured["host"] == "127.0.0.1"
    assert captured["port"] == 8123
    assert captured["workers"] == 1


def test_hosted_entry_requires_explicit_configuration(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["server"])
    monkeypatch.delenv("TRADEVELOCITY_MODE", raising=False)
    with pytest.raises(SystemExit, match="private mode"):
        server.main()


def test_unavailable_database_prevents_backend_start(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["server", "--local"])

    def unavailable(self):
        raise StorageError("Database unavailable")

    monkeypatch.setattr("stock_engine.storage.SessionStore.check", unavailable)
    with pytest.raises(StorageError):
        server.main()
