"""Build a portable Windows app folder, including Python and the production UI."""
from pathlib import Path
import os
import shutil
import struct
import subprocess
import sys
import zlib

ROOT = Path(__file__).resolve().parents[1]


def make_icon(path: Path) -> None:
    """Generate a small code-native TV icon, without external image tooling."""
    size = 64
    rows = []
    for y in range(size):
        row = bytearray([0])
        for x in range(size):
            rounded = ((x < 10 or x >= 54) and (y < 10 or y >= 54) and
                       (x - (10 if x < 10 else 53)) ** 2 + (y - (10 if y < 10 else 53)) ** 2 > 100)
            t = (12 <= x < 33 and 19 <= y < 25) or (20 <= x < 26 and 19 <= y < 45)
            v = 19 <= y < 45 and (abs(x - (35 + (y - 19) / 3)) < 3 or abs(x - (53 - (y - 19) / 3)) < 3)
            row.extend((255, 255, 255, 255) if t or v else (49, 93, 232, 0 if rounded else 255))
        rows.append(bytes(row))
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(b"".join(rows))) + chunk(b"IEND", b"")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(struct.pack("<HHH", 0, 1, 1) + struct.pack("<BBBBHHII", size, size, 0, 0, 1, 32, len(png), 22) + png)


def main():
    if os.name != "nt":
        raise SystemExit("Build the Windows executable on Windows.")
    npm = shutil.which("npm.cmd")
    if not npm:
        raise SystemExit("Node.js/npm is required on the build machine.")
    if not (ROOT / "frontend" / "node_modules").exists():
        subprocess.run([npm, "ci"], cwd=ROOT / "frontend", check=True)
    subprocess.run([npm, "run", "build"], cwd=ROOT / "frontend", check=True)
    make_icon(ROOT / "build" / "desktop-icon.ico")
    # Only replace this build's generated output, never source or saved sessions.
    destination = (ROOT / "dist" / "TradeVelocity").resolve()
    if destination.parent != (ROOT / "dist").resolve():
        raise SystemExit("Refusing to overwrite a desktop output outside this project's dist folder.")
    subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "TradeVelocity.spec"], cwd=ROOT, check=True)
    print(f"Ready: {ROOT / 'dist' / 'TradeVelocity' / 'TradeVelocity.exe'}")
    print("Copy the whole TradeVelocity folder, not just the EXE. WebView2 Runtime is required.")


if __name__ == "__main__":
    main()
