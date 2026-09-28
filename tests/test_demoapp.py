"""Verify that the presentation file exercises the real matching engine."""

import importlib.util
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("tradevelocity_demo", ROOT / "demoapp.py")
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)


def test_walkthrough_verifies_actual_trades_fifo_and_cancellation():
    report = demo.run_engine_walkthrough()
    assert report["matched_shares"] == 250
    assert report["executions"] == [(50, "105.00"), (100, "106.00"), (100, "107.00")]
    assert report["vwap"] == "106.20"
    assert report["partial_remaining"] == 50
    assert report["fifo_executions"] == [("FIRST-SELL", 20), ("SECOND-SELL", 5)]
    assert report["fifo_remaining"] == 25
    assert report["cancelled"]


def test_terminal_demo_runs_without_starting_the_app():
    result = subprocess.run([sys.executable, str(ROOT / "demoapp.py"), "--terminal-only"],
                            cwd=ROOT, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert "ALL ENGINE DEMO CHECKS PASSED" in result.stdout
    assert "TERMINAL DEMO COMPLETE" in result.stdout
    assert "Starting" not in result.stdout


def test_demo_forwards_launch_options_to_the_single_app_launcher(monkeypatch):
    import app

    received = []
    monkeypatch.setattr(app, "main", lambda arguments: received.append(arguments) or 0)
    assert demo.main(["--port", "8010", "--browser", "chrome", "--skip-build"]) == 0
    assert received == [["--port", "8010", "--browser", "chrome", "--skip-build"]]
