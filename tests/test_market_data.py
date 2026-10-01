import json
import math

import pandas as pd
import pytest

from stock_engine.companies import COMPANIES
from stock_engine.market_data import (
    FIELDS, MarketData, clean_history, from_snapshot, history_metrics,
    indicators, load_market_data, period_history, save_snapshot,
)


def frame():
    return pd.DataFrame([[100, 102, 98, 100, 100, 1000]] * 80,
                        index=pd.bdate_range("2025-01-01", periods=80), columns=FIELDS)


def test_snapshot_preserves_prices_and_provenance_without_network(tmp_path):
    data = MarketData({symbol: frame() for symbol in COMPANIES}, "Fixture provider", "2025-06-01T00:00:00Z")
    path = tmp_path / "market.json"
    save_snapshot(data, path)
    restored = load_market_data(path)
    assert restored.source == "Fixture provider"
    assert not restored.is_synthetic
    for symbol in COMPANIES:
        pd.testing.assert_frame_equal(restored.histories[symbol], clean_history(frame()), check_freq=False, check_dtype=False)
    assert json.loads(path.read_text())["is_synthetic"] is False


def test_missing_or_broken_snapshot_has_no_fabricated_prices(tmp_path):
    path = tmp_path / "market.json"
    missing = load_market_data(path)
    assert missing.histories == {} and missing.marks() == {}
    assert missing.as_of == "Unavailable"
    path.write_text("{}")
    broken = load_market_data(path)
    assert broken.histories == {}
    assert "unavailable" in broken.source.lower()
    payload = MarketData({symbol: frame() for symbol in COMPANIES}, "Synthetic", "", True).to_dict()
    with pytest.raises(ValueError, match="synthetic"):
        from_snapshot(payload)


def test_cleaning_removes_invalid_bars_and_sorts_unique_days():
    source = frame().iloc[:5].copy()
    source.iloc[1, source.columns.get_loc("Close")] = math.nan
    source.iloc[2, source.columns.get_loc("High")] = 1
    source.iloc[3, source.columns.get_loc("Volume")] = -1
    result = clean_history(source.iloc[::-1])
    assert len(result) == 2
    assert result.index.is_monotonic_increasing
    with pytest.raises(ValueError):
        clean_history(source.iloc[:3])


def test_flat_rsi_drawdown_and_adjusted_growth():
    source = frame()
    result = indicators(source)
    assert result["RSI14"].iloc[-1] == 50
    assert result["Drawdown %"].iloc[-1] == 0
    assert history_metrics(source)["growth_pct"] == 0
    assert history_metrics(source)["volatility_pct"] == 0
    # A raw price split must not create an artificial adjusted-price loss.
    split = source.copy()
    split.iloc[-1, split.columns.get_loc("Close")] = 50
    assert history_metrics(split)["growth_pct"] == 0
    assert history_metrics(split)["last"] == 50


def test_history_filter_is_relative_to_data_date():
    source = frame()
    subset = period_history(source, "1M")
    assert subset.index.min() >= source.index[-1] - pd.DateOffset(months=1)
    with pytest.raises(ValueError):
        period_history(source, "invalid")
