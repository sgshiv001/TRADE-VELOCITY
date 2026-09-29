"""Build and run the complete TradeVelocity app with browser selection.

Run ``python app.py``. Ctrl+C stops the server. Use demoapp.py for verified examples.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import threading
import urllib.error
import urllib.request
import webbrowser


ROOT = Path(__file__).resolve().parent
HOST = "127.0.0.1"
APP_ID = "trade-velocity"


def use_project_python(arguments: list[str]) -> int | None:
    """Prefer this project's environment even when launched with system Python."""
    environment = ROOT / ".venv"
    if getattr(sys, "frozen", False):
        return None
    executable = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if executable.exists() and Path(sys.prefix).resolve() != environment.resolve():
        print(f"Using project Python: {executable}", flush=True)
        # Popen quotes paths with spaces correctly on Windows and keeps this
        # terminal waiting for the project's Python, including its exit status.
        process = subprocess.Popen([str(executable), str(ROOT / "app.py"), *arguments], cwd=ROOT)
        try:
            return process.wait()
        except KeyboardInterrupt:
            # Both interpreters share the console; let Uvicorn handle Ctrl+C.
            try:
                return process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                return 0
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
    return None


def browser_path(name: str) -> str | None:
    """Find Windows browsers, including per-user Chrome installations."""
    executable, directory = {
        "edge": ("msedge", "Microsoft/Edge/Application/msedge.exe"),
        "chrome": ("chrome", "Google/Chrome/Application/chrome.exe"),
        "firefox": ("firefox", "Mozilla Firefox/firefox.exe"),
    }[name]
    candidates = [shutil.which(executable)]
    for variable in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        if os.environ.get(variable):
            candidates.append(str(Path(os.environ[variable]) / directory))
    return next((path for path in candidates if path and Path(path).is_file()), None)


def select_browser() -> str:
    print("\nSelect a browser for TradeVelocity:")
    print("  1. Microsoft Edge")
    print("  2. Google Chrome")
    print("  3. System default browser")
    print("  4. Mozilla Firefox")
    while True:
        try:
            choice = input("Enter 1, 2, 3, or 4 [1]: ").strip() or "1"
        except EOFError:
            print("No interactive input; using the system default browser.")
            return "default"
        if choice in ("1", "2", "3", "4"):
            return {"1": "edge", "2": "chrome", "3": "default", "4": "firefox"}[choice]
        print("Please enter a number from 1 to 4.")


def open_browser(browser: str, url: str) -> None:
    try:
        if browser != "default":
            executable = browser_path(browser)
            if executable:
                opened = webbrowser.BackgroundBrowser(executable).open(url)
            else:
                print(f"{browser.title()} was not found; using the system default browser.")
                opened = webbrowser.open(url)
        else:
            opened = webbrowser.open(url)
        if not opened:
            print(f"Open this address manually in your browser: {url}")
    except (OSError, webbrowser.Error) as exc:
        print(f"Could not open the browser ({exc}). Open {url} manually.")


def app_is_running(port: int) -> bool:
    """Only reuse a server that identifies itself as this application."""
    # Loopback requests must not go through a configured HTTP proxy.
    client = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with client.open(f"http://{HOST}:{port}/api/health", timeout=1) as response:
            payload = json.load(response)
            return response.status == 200 and isinstance(payload, dict) and (
                payload.get("status") == "ok" and payload.get("application") == APP_ID
            )
    except (OSError, urllib.error.URLError, ValueError):
        return False


def check_dependencies() -> None:
    modules = ("uvicorn", "fastapi", "numpy", "pandas", "sklearn", "yfinance")
    missing = [module for module in modules if importlib.util.find_spec(module) is None]
    if missing:
        raise RuntimeError(
            f"Missing Python dependencies: {', '.join(missing)}.\n"
            f'Run in PowerShell from the project folder:\n& "{sys.executable}" '
            '-m pip install -e ".[app]"'
        )


def build_frontend(skip_build: bool) -> None:
    frontend = ROOT / "frontend"
    if not skip_build:
        npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
        if npm is None:
            raise RuntimeError("Node.js/npm was not found. Install Node.js, then reopen the terminal.")
        if not (frontend / "node_modules").is_dir():
            print("Installing frontend dependencies...", flush=True)
            subprocess.run([npm, "ci"], cwd=frontend, check=True)
        print("Building the frontend...", flush=True)
        subprocess.run([npm, "run", "build"], cwd=frontend, check=True)
    if not (frontend / "dist" / "index.html").is_file():
        raise RuntimeError("The frontend build is missing. Run again without --skip-build.")


def serve(port: int, browser: str | None, skip_build: bool) -> int:
    url = f"http://{HOST}:{port}/"
    if app_is_running(port):
        print(f"TradeVelocity is already running at {url}")
        if browser:
            open_browser(browser, url)
        print("Stop the existing server from the terminal that started it.")
        return 0

    # Reserve the port before building; a second launch cannot race this one.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        if os.name == "nt":
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        else:
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            listener.bind((HOST, port))
        except OSError as exc:
            raise RuntimeError(
                f"Cannot use {url}: {exc}\n"
                "If another program uses this port, run: python app.py --port 8001"
            ) from exc

        check_dependencies()
        build_frontend(skip_build)
        sys.path.insert(0, str(ROOT / "src"))
        import uvicorn
        from stock_engine.api import app as application

        server = uvicorn.Server(uvicorn.Config(application, host=HOST, port=port, workers=1))
        finished = threading.Event()

        def announce_when_ready() -> None:
            while not finished.wait(0.1):
                if server.started:
                    print(f"\nTradeVelocity is ready: {url}", flush=True)
                    print("Press Ctrl+C to stop. Paper sessions are saved in .marketlab/sessions.", flush=True)
                    if browser:
                        open_browser(browser, url)
                    return

        announcer = threading.Thread(target=announce_when_ready, daemon=True)
        announcer.start()
        try:
            # Running in this process prevents orphan servers when VS Code stops.
            server.run(sockets=[listener])
        finally:
            finished.set()
            announcer.join(timeout=2)
        return 0 if server.started else 1


def main(arguments: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if arguments is None else arguments)
    if getattr(sys, "frozen", False) and "--desktop" not in arguments:
        arguments.append("--desktop")
    parser = argparse.ArgumentParser(description="Launch the complete TradeVelocity app")
    parser.add_argument("--port", type=int, default=8000, help="local port (default: 8000)")
    parser.add_argument("--browser", choices=("edge", "chrome", "firefox", "default"),
                        help="choose a browser without the interactive prompt")
    parser.add_argument("--no-browser", action="store_true", help="run without opening a browser")
    parser.add_argument("--skip-build", action="store_true", help="reuse frontend/dist")
    parser.add_argument("--desktop", action="store_true", help="open a native desktop window")
    parser.add_argument("--smoke-test", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(arguments)
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    if args.no_browser and args.browser:
        parser.error("--browser and --no-browser cannot be combined")

    try:
        delegated_exit = use_project_python(arguments)
        if delegated_exit is not None:
            return delegated_exit
        if args.desktop:
            check_dependencies()
            build_frontend(args.skip_build or getattr(sys, "frozen", False))
            sys.path.insert(0, str(ROOT / "src"))
            from stock_engine.desktop import run_desktop
            return run_desktop(args.smoke_test)
        print("TRADEVELOCITY / COMPLETE APP LAUNCHER", flush=True)
        browser = None if args.no_browser else args.browser or select_browser()
        return serve(args.port, browser, args.skip_build)
    except KeyboardInterrupt:
        print("\nTradeVelocity stopped.")
        return 0
    except subprocess.CalledProcessError as exc:
        print(f"\nFrontend build/install failed (exit {exc.returncode}). See the error above.", file=sys.stderr)
        return exc.returncode
    except (RuntimeError, OSError, ImportError) as exc:
        if args.desktop and not args.smoke_test:
            from tkinter import Tk, messagebox
            root = Tk()
            root.withdraw()
            messagebox.showerror("TradeVelocity could not start", f"{exc}\n\nFor desktop setup, run:\n.venv\\Scripts\\python.exe -m pip install -e \".[app,desktop]\"\n\nThen run npm.cmd run build inside frontend.")
            root.destroy()
        else:
            if sys.stderr is not None:
                print(f"\nLaunch failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    raise SystemExit(main())
