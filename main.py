"""Small entry point for the Trade Velocity Phase 1 setup.

The production command-line interface remains available as
``python -m stock_engine.cli``. This root script is intentionally small so a
beginner can verify the project setup before learning the matching engine.
"""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config.settings import PROJECT_NAME, SUPPORTED_STOCKS  # noqa: E402


def main() -> None:
    """Print a setup confirmation and the configured market universe."""

    print(f"{PROJECT_NAME} setup is ready.")
    print("Configured stocks:", ", ".join(SUPPORTED_STOCKS))
    print("Next step: implement and study the Order model in Phase 2.")


if __name__ == "__main__":
    main()
