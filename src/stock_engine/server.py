"""Run a local database-backed API or an authenticated private hosted app."""
import argparse
import os
from pathlib import Path
import uvicorn
from .security import SecuritySettings
from .server_runtime import server_options


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local", action="store_true", help="run on loopback with local workspace access")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")))
    arguments = parser.parse_args()
    if not 1 <= arguments.port <= 65535:
        parser.error("port must be between 1 and 65535")
    settings = SecuritySettings.from_environment()
    if arguments.local and settings.mode != "local":
        parser.error("--local requires TRADEVELOCITY_MODE=local")
    if not arguments.local and settings.mode == "local":
        raise SystemExit("Hosting requires explicit private mode or accounts mode and an HTTPS origin")
    directory = os.environ.get("TRADEVELOCITY_DATA_DIR","")
    if not arguments.local and (not directory or not Path(directory).is_absolute()):
        raise SystemExit("Hosting requires an absolute, writable TRADEVELOCITY_DATA_DIR")
    from .api import create_app
    app = create_app(data_dir=Path(directory) if directory else None, security=settings)
    (app.state.accounts or app.state.store).check()
    uvicorn.run(app,host="127.0.0.1" if arguments.local else "0.0.0.0",port=arguments.port,
                proxy_headers=False,**server_options())


if __name__ == "__main__":
    main()
