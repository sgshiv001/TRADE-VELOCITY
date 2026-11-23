"""Point the Android WebView at the same server that serves the UI and API."""

import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


def configure(server_url: str, root: Path = ROOT):
    parsed = urlsplit(server_url)
    if (not parsed.hostname or parsed.username or parsed.password
            or parsed.path not in ("", "/") or parsed.query or parsed.fragment):
        raise ValueError("Use the backend origin without credentials, a path, query or fragment")
    if parsed.scheme != "https" and not (
            parsed.scheme == "http" and parsed.hostname in ("localhost", "127.0.0.1", "::1")):
        raise ValueError("Use HTTPS for a hosted backend, or HTTP localhost with adb reverse for local testing")
    _ = parsed.port
    path = root / "capacitor.config.json"
    config = json.loads(path.read_text(encoding="utf-8"))
    config["server"] = {"url": server_url.rstrip("/"), "cleartext": parsed.scheme == "http"}
    config.setdefault("android", {})["allowMixedContent"] = False
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=os.environ.get("TRADEVELOCITY_SERVER_URL", "http://localhost:8000"))
    arguments = parser.parse_args()
    try:
        configure(arguments.url)
    except ValueError as exc:
        parser.error(str(exc))
    print("Android backend configured. Run npx cap sync android before building the APK.")


if __name__ == "__main__":
    main()
