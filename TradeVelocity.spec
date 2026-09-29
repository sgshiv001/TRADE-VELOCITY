# Build with: .venv\Scripts\python.exe -m PyInstaller TradeVelocity.spec
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files

root = Path(SPECPATH)
a = Analysis([str(root / "app.py")], pathex=[str(root / "src")],
             datas=[(str(root / "frontend" / "dist"), "frontend/dist"),
                    (str(root / "scenarios"), "scenarios")] + collect_data_files("stock_engine"),
             hiddenimports=["webview.platforms.edgechromium", "uvicorn.logging", "uvicorn.loops.auto",
                            "uvicorn.protocols.http.auto", "uvicorn.protocols.websockets.auto", "uvicorn.lifespan.on"],
             excludes=["PyQt5", "PyQt6", "PySide2", "PySide6", "matplotlib", "IPython", "pytest"],
             noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="TradeVelocity",
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False, console=False,
          icon=str(root / "build" / "desktop-icon.ico") if (root / "build" / "desktop-icon.ico").exists() else None)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="TradeVelocity")
