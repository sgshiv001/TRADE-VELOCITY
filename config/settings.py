"""Central configuration for the Trade Velocity project.

Keeping defaults in one module makes experiments reproducible and avoids
scattering magic numbers across the matching engine, simulator, and UI.
"""

from __future__ import annotations

from pathlib import Path

PROJECT_NAME = "Trade Velocity"
PROJECT_TITLE = (
    "Trade Velocity: High-Performance Stock Market Order Matching Engine "
    "Using Advanced Data Structures and Artificial Intelligence"
)
TAGLINE = "Where Every Order Meets Its Match."

SUPPORTED_STOCKS = (
    "AAPL",
    "MSFT",
    "NVDA",
    "TSLA",
    "AMZN",
    "GOOGL",
    "META",
)

DEFAULT_PRICE = 100.00
DEFAULT_ORDER_QUANTITY = 100
SIMULATION_SIZE = 10_000
BUY_PROBABILITY = 0.50
MARKET_ORDER_PROBABILITY = 0.10
PRICE_VARIATION = 0.05
QUANTITY_RANGE = (1, 100)

AI_PARAMETERS = {
    "contamination": 0.05,
    "random_state": 42,
}

BENCHMARK_PARAMETERS = {
    "sizes": (10_000, 100_000, 1_000_000, 5_000_000, 10_000_000),
    "workers": (1, 2, 4, 8),
}

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"
BENCHMARK_RESULTS_DIR = PROJECT_ROOT / "benchmarks" / "results"
