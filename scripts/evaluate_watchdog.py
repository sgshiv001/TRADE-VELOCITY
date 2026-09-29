"""Reproduce the classroom watchdog's separate synthetic training/test experiment."""
import argparse
import json
from pathlib import Path
import platform

import sklearn

from stock_engine.watchdog import classroom_demo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=Path("benchmarks/watchdog-evaluation.json"))
    args = parser.parse_args()
    _, demo = classroom_demo(args.seed)
    payload = {"python": platform.python_version(), "scikit_learn": sklearn.__version__,
               "platform": platform.platform(), "evaluation": demo["evaluation"], "steps": demo["steps"]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
