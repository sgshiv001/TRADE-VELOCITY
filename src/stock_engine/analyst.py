"""Chronological one-session forecasts and explainable paper-trading signals."""

from datetime import datetime, timezone
from math import ceil

import numpy as np

from .analysis import analyze_history
from .market_data import MarketData


def _features(returns):
    return [returns[-1], np.mean(returns[-5:]), np.mean(returns[-20:]), np.std(returns[-20:])]


def _ridge(train, outcomes):
    centre = train.mean(axis=0)
    scale = train.std(axis=0)
    scale[scale == 0] = 1
    inputs = (train - centre) / scale
    baseline = outcomes.mean()
    penalty = np.eye(inputs.shape[1]) * 10
    weights = np.linalg.solve(inputs.T @ inputs + penalty, inputs.T @ (outcomes - baseline))

    def predict(values):
        return (values - centre) / scale @ weights + baseline

    return predict


def one_session_forecast(close, reference_price):
    """Split data chronologically into fitting, selection, and calibration windows."""
    prices = np.asarray(close, dtype=float)
    if len(prices) < 240 or not np.all(np.isfinite(prices) & (prices > 0)):
        return None
    returns = np.diff(np.log(prices))
    inputs = np.array([_features(returns[i - 20:i]) for i in range(20, len(returns))])
    targets = returns[20:]
    fit_end = int(len(targets) * 0.6)
    selection_end = int(len(targets) * 0.8)
    predict = _ridge(inputs[:fit_end], targets[:fit_end])
    validation = targets[fit_end:selection_end]
    ridge_errors = np.abs(validation - predict(inputs[fit_end:selection_end]))
    naive_errors = np.abs(validation)
    ridge_wins = ridge_errors.mean() < naive_errors.mean()
    calibrated = predict(inputs[selection_end:]) if ridge_wins else 0
    errors = np.sort(np.abs(targets[selection_end:] - calibrated))
    rank = min(len(errors), ceil((len(errors) + 1) * 0.8))
    radius = float(errors[rank - 1])
    movement = float(predict(np.array(_features(returns)))) if ridge_wins else 0.0
    return {
        "horizon": "Next trading session", "method": "Ridge regression" if ridge_wins else "Unchanged price baseline",
        "reference_price": round(reference_price, 2), "point": round(reference_price * np.exp(movement), 2),
        "lower": round(reference_price * np.exp(movement - radius), 2),
        "upper": round(reference_price * np.exp(movement + radius), 2),
        "change_pct": round(float(np.expm1(movement)) * 100, 3),
        "interval_target": 80, "fit_samples": fit_end, "selection_samples": len(validation),
        "calibration_samples": len(errors), "ridge_mae_pct": round(float(ridge_errors.mean()) * 100, 3),
        "baseline_mae_pct": round(float(naive_errors.mean()) * 100, 3),
    }


def stock_analysis(market: MarketData, symbol: str) -> dict:
    symbol = symbol.upper()
    frame = market.histories.get(symbol)
    if frame is None or len(frame) < 2:
        raise ValueError("A historical series is unavailable for this symbol")
    summary = analyze_history(symbol, market.histories)
    adjusted = frame["Adj Close"]
    forecast = one_session_forecast(adjusted, float(frame["Close"].iloc[-1]))
    now = datetime.now(timezone.utc)
    age = (now.date() - frame.index[-1].date()).days
    stale = age > 7 or age < 0
    macd = adjusted.ewm(span=12, adjust=False).mean() - adjusted.ewm(span=26, adjust=False).mean()
    histogram = float((macd - macd.ewm(span=9, adjust=False).mean()).iloc[-1])
    signal = "HOLD"
    if stale or forecast is None:
        signal = "INSUFFICIENT DATA"
    elif summary["signal"] == "Bullish" and histogram > 0 and forecast["change_pct"] > 0:
        signal = "BUY"
    elif summary["signal"] == "Bearish" and histogram < 0 and forecast["change_pct"] < 0:
        signal = "SELL"
    return {
        **summary, "source": market.source, "stale": stale, "forecast": forecast,
        "recommendation": signal, "macd_histogram": round(histogram, 3),
        "recommendation_reason": (
            "Refresh the market series before using this historical estimate." if stale else
            "At least 240 daily observations are required." if forecast is None else
            "The trend, MACD momentum and estimated direction agree." if signal in ("BUY", "SELL") else
            "The historical trend, MACD momentum and statistical forecast do not agree on a direction."
        ),
        "recent_closes": [{"date": date.strftime("%Y-%m-%d"), "price": round(float(value), 2)}
                          for date, value in frame["Close"].tail(20).items()],
    }
