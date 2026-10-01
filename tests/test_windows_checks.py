import asyncio
import os
import pytest
from stock_engine import windows_checks
from stock_engine.server_runtime import create_loop, server_options


def test_server_uses_selector_transport_and_bounded_connections():
    loop = create_loop()
    try:
        assert isinstance(loop,asyncio.SelectorEventLoop)
        assert server_options()["limit_concurrency"] == 100
        assert server_options()["ws"] == "websockets-sansio"
    finally:
        loop.close()


@pytest.mark.skipif(os.name != "nt",reason="Windows registry preflight")
def test_missing_runtime_is_reported_without_installing(monkeypatch):
    monkeypatch.setattr(windows_checks,"registry_value",lambda path,name:None)
    result = windows_checks.check_windows()
    assert result["ready"] is False
    assert any("WebView2" in problem for problem in result["problems"])
    assert any(".NET" in problem for problem in result["problems"])
    assert result["setup_links"]["webview2"].startswith("https://developer.microsoft.com/")


@pytest.mark.skipif(os.name != "nt",reason="Windows registry preflight")
def test_installed_windows_prerequisites(monkeypatch):
    monkeypatch.setattr(windows_checks,"registry_value",lambda path,name:"145.0.0.0" if name == "pv" else 533325)
    result = windows_checks.check_windows()
    assert result["ready"]
    assert result["webview2_version"] == "145.0.0.0"
