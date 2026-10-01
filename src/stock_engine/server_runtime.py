"""One supported network loop/configuration for web, desktop, and QA servers."""
import asyncio


def create_loop():
    # Selector transports avoid the Windows Proactor shutdown/socket-reset
    # callback failure. This one-worker app does not launch subprocesses from
    # its event loop and caps concurrent connections below selector limits.
    return asyncio.SelectorEventLoop()


def server_options():
    return {"loop":"stock_engine.server_runtime:create_loop", "ws":"websockets-sansio",
            "workers":1, "limit_concurrency":100, "timeout_keep_alive":5,
            "timeout_graceful_shutdown":10, "ws_max_size":4096}
