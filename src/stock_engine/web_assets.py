"""Trusted app-shell paths and CSP hashes for the static frontend export."""

from base64 import b64encode
from hashlib import sha256
from pathlib import Path
import re

INLINE_SCRIPT = re.compile(rb"<script\b[^>]*>(.*?)</script\s*>", flags=re.IGNORECASE | re.DOTALL)


def app_pages(frontend: Path) -> dict[str, Path]:
    pages = {"/": frontend / "index.html"}
    for name in ("app", "login", "signup"):
        page = frontend / f"{name}.html"
        pages[f"/{name}"] = page if page.is_file() else pages["/"]
    return pages


def inline_script_hashes(frontend: Path, pages: dict[str, Path]) -> dict[str, str]:
    routes = {f"/{path.name}": path for path in frontend.glob("*.html")}
    routes.update(pages)
    hashes = {}
    for route, path in routes.items():
        if not path.is_file():
            continue
        content = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        values = set()
        for script in INLINE_SCRIPT.findall(content):
            if script.strip():
                digest = b64encode(sha256(script).digest()).decode("ascii")
                values.add(f"'sha256-{digest}'")
        if values:
            hashes[route] = " ".join(sorted(values))
    return hashes
