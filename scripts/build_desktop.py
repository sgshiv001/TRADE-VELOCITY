"""Build a portable Windows app folder, including Python and the production UI."""
from pathlib import Path
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import zlib
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda:source.read(1024*1024),b""):
            result.update(chunk)
    return result.hexdigest()


def package_desktop():
    folder = (ROOT / "dist/TradeVelocity").resolve()
    if folder.parent != (ROOT / "dist").resolve():
        raise ValueError("Desktop folder must stay in this project's dist directory")
    executable = folder / "TradeVelocity.exe"
    calibration = folder / "_internal/stock_engine/data/watchdog-calibration.json"
    entry = folder / "_internal/frontend/dist/index.html"
    if not executable.is_file() or not entry.is_file() or not calibration.is_file():
        raise ValueError("Build the complete Windows application before packaging")
    if (entry.read_bytes() != (ROOT / "frontend/dist/index.html").read_bytes()
            or calibration.read_bytes() != (ROOT / "src/stock_engine/data/watchdog-calibration.json").read_bytes()):
        raise ValueError("Packaged frontend/calibration is stale; rebuild before packaging")
    archive = ROOT / "dist/TradeVelocity-Windows-x64.zip"
    with zipfile.ZipFile(archive,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as output:
        output.write(ROOT / "Launch_Desktop.vbs","Launch_Desktop.vbs")
        instructions = ROOT / "docs/windows-release.md"
        if instructions.exists():
            output.write(instructions,"WINDOWS-README.md")
        for path in sorted(folder.rglob("*")):
            if not path.resolve().is_relative_to(folder):
                raise ValueError("Refusing to package a link outside the generated desktop folder")
            if path.is_file():
                output.write(path,path.relative_to(folder.parent).as_posix())
    with zipfile.ZipFile(archive) as output:
        if output.testzip() is not None:
            raise ValueError("Portable archive CRC integrity failed")
        count = len(output.namelist())
    result = {"version":json.loads((ROOT / "frontend/package.json").read_text())["version"],
              "generated_at":datetime.now(timezone.utc).isoformat(),"archive":archive.name,
              "bytes":archive.stat().st_size,"entries":count,"crc":"passed",
              "sha256":digest(archive),"exe_sha256":digest(executable),
              "calibration_sha256":digest(calibration),"frontend_matches":True,
              "signature":"Not established by this manifest; check Authenticode separately"}
    (ROOT / "dist/TradeVelocity-release.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(f"Verified ZIP: {archive}")
    return result


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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-only",action="store_true",help="repackage an existing build, e.g. after certificate signing")
    args = parser.parse_args()
    if args.package_only:
        package_desktop()
        return
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
    package_desktop()


if __name__ == "__main__":
    main()
