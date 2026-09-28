import csv
from pathlib import Path
import subprocess
import sys

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "compare_engines.py"


def test_comparison_cli_writes_reproducible_results_with_memory(tmp_path):
    output = tmp_path / "nested" / "comparison.csv"
    result = subprocess.run([
        sys.executable, str(SCRIPT), "--sizes", "20,40", "--workloads", "mixed,deep,cancel",
        "--symbols", "2", "--repeats", "1", "--trace-memory", "--output", str(output),
    ], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    with output.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    assert len(rows) == 12
    for row in rows:
        assert row["engine"] in {"indexed", "linear"}
        assert row["python"] and row["platform"]
        assert float(row["seconds"]) > 0
        assert float(row["commands_per_second"]) > 0
        assert float(row["peak_traced_mb"]) >= 0
        if row["workload"] == "deep":
            assert int(row["trades"]) == int(row["commands"]) // 2
        if row["workload"] in {"deep", "cancel"}:
            assert int(row["open_orders"]) == 0


@pytest.mark.parametrize("args", [
    ["--sizes", "1"], ["--workloads", "unknown"], ["--symbols", "0"],
    ["--repeats", "0"], ["--workloads", "deep,deep"],
])
def test_invalid_cli_arguments_do_not_write_results(tmp_path, args):
    output = tmp_path / "comparison.csv"
    result = subprocess.run([sys.executable, str(SCRIPT), *args, "--output", str(output)],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 2
    assert "error:" in result.stderr
    assert not output.exists()
