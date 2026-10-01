"""Reproduce offline AI calibration without reading or modifying user sessions."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from stock_engine.calibration import evaluate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("benchmarks/ai-calibration.json"))
    arguments = parser.parse_args()
    result = evaluate(lambda message:print(message,flush=True))
    result["generated_at"] = datetime.now(timezone.utc).isoformat()
    arguments.output.parent.mkdir(parents=True,exist_ok=True)
    arguments.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"selected_settings":result["selected_settings"],"heldout":result["heldout"],"legacy_heldout":result["legacy_heldout"],"output":str(arguments.output)},indent=2))


if __name__ == "__main__":
    main()
