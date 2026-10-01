import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sign_desktop",ROOT / "scripts/sign_desktop.py")
signing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(signing)


def test_signing_dry_plan_uses_store_identity_and_verifies(tmp_path,monkeypatch):
    monkeypatch.setattr(signing,"ROOT",tmp_path)
    executable = tmp_path / "dist/TradeVelocity/TradeVelocity.exe"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"test-only-placeholder")
    sign,verify = signing.commands(executable,"a"*40,"https://timestamp.test")
    assert "/sha1" in sign and "/fd" in sign and "/td" in sign
    assert "/p" not in sign and "/f" not in sign
    assert verify[1:4] == ["verify","/pa","/all"]


@pytest.mark.parametrize("target,thumb,url", [("outside.exe","a"*40,"https://timestamp.test"),
                                            ("dist/a.exe","wrong","https://timestamp.test"),
                                            ("dist/a.exe","a"*40,"http://timestamp.test")])
def test_signing_rejects_unsafe_targets_and_inputs(tmp_path,monkeypatch,target,thumb,url):
    monkeypatch.setattr(signing,"ROOT",tmp_path)
    executable = tmp_path / target
    executable.parent.mkdir(parents=True,exist_ok=True)
    executable.write_bytes(b"test-only-placeholder")
    with pytest.raises(ValueError):
        signing.commands(executable,thumb,url)


def test_portable_package_checks_integrity_and_stale_inputs(tmp_path,monkeypatch):
    import json
    import zipfile
    spec = importlib.util.spec_from_file_location("desktop_build",ROOT / "scripts/build_desktop.py")
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    monkeypatch.setattr(build,"ROOT",tmp_path)
    files = {"dist/TradeVelocity/TradeVelocity.exe":b"test-only-placeholder",
             "dist/TradeVelocity/_internal/frontend/dist/index.html":b"<html>test</html>",
             "frontend/dist/index.html":b"<html>test</html>",
             "dist/TradeVelocity/_internal/stock_engine/data/watchdog-calibration.json":b"{}",
             "src/stock_engine/data/watchdog-calibration.json":b"{}",
             "Launch_Desktop.vbs":b"test shortcut", "frontend/package.json":b'{"version":"test"}'}
    for name,content in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(content)
    receipt = build.package_desktop()
    assert receipt["crc"] == "passed"
    with zipfile.ZipFile(tmp_path / "dist/TradeVelocity-Windows-x64.zip") as archive:
        assert "Launch_Desktop.vbs" in archive.namelist()
        assert archive.testzip() is None
    (tmp_path / "frontend/dist/index.html").write_bytes(b"changed")
    with pytest.raises(ValueError,match="stale"):
        build.package_desktop()
