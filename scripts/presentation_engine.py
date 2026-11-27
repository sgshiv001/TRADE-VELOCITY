"""Serve the bundled presentation workspace on an authenticated loopback socket."""

from argparse import ArgumentParser
import hmac
import json
import os
from pathlib import Path
import socket
import sys
from threading import Thread

from starlette.responses import JSONResponse
import uvicorn

from stock_engine.security import SecuritySettings
from stock_engine.server_runtime import server_options


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", required=True, type=Path)
    parser.add_argument("--frontend", required=True, type=Path)
    args = parser.parse_args()
    key = os.environ.pop("TRADEVELOCITY_OFFLINE_KEY", "").encode("ascii")
    if len(key) != 64 or not args.data_dir.is_absolute() or not (args.frontend / "app.html").is_file():
        parser.error("Start the engine from TradeVelocity with a bundled frontend and local data directory.")

    # The desktop child always uses a separate SQLite workspace.
    for name in ("DATABASE_URL", "TRADEVELOCITY_DATABASE_URL", "TRADEVELOCITY_ORIGIN", "TRADEVELOCITY_ACCESS_KEY"):
        os.environ.pop(name, None)
    os.environ["TRADEVELOCITY_MODE"] = "local"
    os.environ["TRADEVELOCITY_DATA_DIR"] = str(args.data_dir)
    os.environ["TRADEVELOCITY_WEB_DIR"] = str(args.frontend)
    from stock_engine.api import create_app

    application = create_app(data_dir=args.data_dir, security=SecuritySettings(), database_url="", offline=True)
    application.state.store.check()

    async def guarded(scope, receive, send):
        if scope["type"] in ("http", "websocket"):
            token = dict(scope["headers"]).get(b"x-tradevelocity-offline-key", b"")
            if not hmac.compare_digest(token, key):
                if scope["type"] == "websocket":
                    await send({"type": "websocket.close", "code": 1008})
                else:
                    await JSONResponse({"detail": "Open this workspace in TradeVelocity."}, status_code=403)(scope, receive, send)
                return
        await application(scope, receive, send)

    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        config = uvicorn.Config(guarded, port=port, http="h11", lifespan="on", proxy_headers=False, access_log=False,
                               log_level="warning", **server_options())
        server = uvicorn.Server(config)

        def watch_launcher():
            sys.stdin.buffer.read()
            server.should_exit = True

        print(json.dumps({"port": port}), flush=True)
        Thread(target=watch_launcher, daemon=True).start()
        server.run(sockets=[listener])


if __name__ == "__main__":
    main()
