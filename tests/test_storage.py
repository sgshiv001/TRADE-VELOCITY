import sqlite3
import pytest
from stock_engine.storage import SessionStore


def test_database_failure_rolls_back_commands_metadata_and_receipt(tmp_path):
    store = SessionStore(tmp_path)
    store.save("session",[],{"reviews":{}},0)
    connection = store.connect()
    connection.execute("CREATE TRIGGER fail_command BEFORE INSERT ON commands BEGIN SELECT RAISE(ABORT,'disk failure'); END")
    connection.commit()
    connection.close()
    with pytest.raises(sqlite3.IntegrityError):
        store.save("session",[{"type":"cancel","order_id":"A"}],{"reviews":{"1":{"status":"reviewed"}}},1,receipt=("key","fingerprint",{}))
    assert store.load("session")["lab"]["events"] == []
    assert store.load("session")["reviews"] == {}
    assert store.load("session")["revision"] == 0
    assert store.receipt("session","key") is None
