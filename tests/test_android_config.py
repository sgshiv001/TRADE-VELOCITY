import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "configure_android", Path(__file__).resolve().parents[1] / "scripts/configure_android.py")
android = importlib.util.module_from_spec(spec)
spec.loader.exec_module(android)


def test_android_connects_to_same_origin_and_preserves_app_settings(tmp_path):
    path = tmp_path / "capacitor.config.json"
    path.write_text(json.dumps({"appId": "com.tradevelocity.app", "webDir": "frontend/dist",
                                "server": {"allowNavigation": ["*"]}}))
    android.configure("https://tradevelocity.test/", tmp_path)
    config = json.loads(path.read_text())
    assert config["appId"] == "com.tradevelocity.app"
    assert config["webDir"] == "frontend/dist"
    assert config["server"] == {"url": "https://tradevelocity.test", "cleartext": False}
    assert config["android"]["allowMixedContent"] is False
    android.configure("http://localhost:8000", tmp_path)
    assert json.loads(path.read_text())["server"] == {"url": "http://localhost:8000", "cleartext": True}


@pytest.mark.parametrize("url", ["http://public.test", "https://user:secret@server.test",
                                     "https://server.test/api", "https://server.test?key=secret"])
def test_invalid_android_backend_does_not_replace_configuration(tmp_path, url):
    path = tmp_path / "capacitor.config.json"
    path.write_text('{"appId":"com.tradevelocity.app"}')
    with pytest.raises(ValueError):
        android.configure(url, tmp_path)
    assert path.read_text() == '{"appId":"com.tradevelocity.app"}'
