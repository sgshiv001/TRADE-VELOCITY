"""Build a portable Windows app folder, including Python and the production UI."""
from pathlib import Path
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import shutil
import subprocess
import sys
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
        quick_start = ROOT / "docs/windows-start-here.txt"
        if quick_start.exists():
            output.write(quick_start,"START-HERE.txt")
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
    """Create a crisp multi-resolution TV monogram for the EXE and taskbar."""
    from PIL import Image, ImageDraw, ImageFilter

    size = 512
    icon = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    pixels = icon.load()
    for y in range(size):
        for x in range(size):
            mix = min(1.0, (x * .58 + y * .42) / size)
            teal_glow = max(0.0, 1 - (((x - 420) / 360) ** 2 + ((y - 125) / 350) ** 2) ** .5) * .2
            pixels[x, y] = tuple(round(start * (1 - mix) + end * mix + teal * teal_glow)
                                 for start, end, teal in zip((8, 20, 43), (37, 82, 205), (10, 130, 145))) + (255,)

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((8, 8, 504, 504), radius=112, fill=255)
    icon.putalpha(mask)

    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(glow).line([(236, 211), (302, 341), (361, 258), (413, 157)],
                              fill=(83, 239, 225, 165), width=48, joint="curve")
    glow = glow.filter(ImageFilter.GaussianBlur(23))
    icon = Image.alpha_composite(icon, glow)
    draw = ImageDraw.Draw(icon)
    draw.rounded_rectangle((8, 8, 504, 504), radius=112, outline=(180, 212, 255, 105), width=6)

    # The T is a stable white anchor; the rising V doubles as a market trace.
    draw.rounded_rectangle((70, 102, 279, 160), radius=24, fill=(247, 250, 255, 255))
    draw.rounded_rectangle((145, 134, 204, 370), radius=22, fill=(247, 250, 255, 255))
    draw.line([(236, 211), (302, 341), (361, 258), (413, 157)],
              fill=(94, 238, 222, 255), width=27, joint="curve")
    draw.polygon([(443, 110), (428, 177), (385, 151)], fill=(139, 255, 232, 255))
    draw.ellipse((287, 326, 317, 356), fill=(12, 30, 61, 255), outline=(139, 255, 232, 255), width=7)

    path.parent.mkdir(parents=True, exist_ok=True)
    icon.save(path, format="ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])


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
