"""Smoke tests for the Phase 1 project setup."""

from config.settings import (
    AI_PARAMETERS,
    BENCHMARK_PARAMETERS,
    PROJECT_NAME,
    SUPPORTED_STOCKS,
)


def test_phase1_configuration_is_available():
    assert PROJECT_NAME == "Trade Velocity"
    assert len(SUPPORTED_STOCKS) >= 2
    assert 0 < AI_PARAMETERS["contamination"] < 1
    assert BENCHMARK_PARAMETERS["sizes"]


def test_existing_engine_package_can_be_imported():
    from stock_engine import MatchingEngine

    engine = MatchingEngine()
    assert engine.symbols() == []
