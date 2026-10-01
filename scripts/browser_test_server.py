"""Serve the built application with disposable storage for browser tests only."""

import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

import uvicorn
from stock_engine.api import create_app
from stock_engine.server_runtime import server_options


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8804)
    arguments = parser.parse_args()
    with TemporaryDirectory(prefix="tradevelocity-e2e-") as directory:
        uvicorn.run(create_app(data_dir=Path(directory) / "sessions"),
                    host="127.0.0.1", port=arguments.port,
                    log_level="warning", **server_options())


if __name__ == "__main__":
    main()
