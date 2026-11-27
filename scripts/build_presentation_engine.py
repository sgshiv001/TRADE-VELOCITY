"""Freeze the local FastAPI matching engine for the Windows presentation EXE."""

from pathlib import Path
import subprocess
import sys


def main():
    root = Path(__file__).resolve().parents[1]
    subprocess.run([
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--onedir", "--paths", "src",
        "--exclude-module", "yfinance", "--exclude-module", "psycopg", "--exclude-module", "sqlalchemy",
        "--collect-data", "stock_engine", "--hidden-import", "uvicorn.lifespan.on",
        "--hidden-import", "uvicorn.protocols.http.h11_impl", "--hidden-import",
        "uvicorn.protocols.websockets.websockets_sansio_impl", "--distpath", "build/presentation-engine",
        "--workpath", "build/presentation-pyinstaller", "--specpath", "build", "--name",
        "TradeVelocityEngine", "scripts/presentation_engine.py",
    ], cwd=root, check=True)


if __name__ == "__main__":
    main()
