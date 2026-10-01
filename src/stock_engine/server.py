"""Opt-in private single-operator hosting entry; local app.py stays loopback."""
import os
from pathlib import Path
import uvicorn
from .security import SecuritySettings
from .server_runtime import server_options


def main():
    settings = SecuritySettings.from_environment()
    if settings.mode != "private":
        raise SystemExit("Hosting entry refuses to start without explicit private mode, HTTPS origin and access key")
    directory = os.environ.get("TRADEVELOCITY_DATA_DIR","")
    if not directory or not Path(directory).is_absolute():
        raise SystemExit("Hosting requires an absolute, writable TRADEVELOCITY_DATA_DIR")
    from .api import create_app
    uvicorn.run(create_app(data_dir=Path(directory),security=settings),host="0.0.0.0",port=8000,
                proxy_headers=False,**server_options())


if __name__ == "__main__":
    main()
