"""Feature engineering and Isolation Forest anomaly detection.

The matching engine remains deterministic. This module only analyses market
observations after they have been generated. Historical OHLCV data does not
contain order-level buy/sell messages, so order-flow fields are explicitly
documented proxies rather than claims about an exchange's hidden order book.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .companies import COMPANIES
from .market_data import indicators, period_history

FEATURE_NAMES = (
    "price",
    "price_change",
    "volume",
    "volatility",
    "spread",
    "buy_volume",
    "sell_volume",
    "order_imbalance",
    "order_arrival_rate",
    "trade_frequency",
    "vwap",
    "vwap_deviation",
    "market_depth",
)

FEATURE_EXPLANATIONS = {
    "price": "Adjusted closing price.",
    "price_change": "One-session percentage price change.",
    "volume": "Observed daily volume.",
    "volatility": "Rolling 20-session return volatility.",
    "spread": "High-low percentage range used as a historical spread proxy.",
    "buy_volume": "Estimated buy pressure from the close position inside the daily range.",
    "sell_volume": "Estimated sell pressure from the close position inside the daily range.",
    "order_imbalance": "Buy-pressure proxy minus sell-pressure proxy.",
    "order_arrival_rate": "Rolling five-session volume used as an arrival-rate proxy.",
    "trade_frequency": "Rolling five-session observation activity proxy.",
    "vwap": "Rolling 20-session volume-weighted average price.",
    "vwap_deviation": "Percentage distance of price from rolling VWAP.",
    "market_depth": "Rolling 20-session volume used as a historical depth proxy.",
}


def build_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Create clean anomaly features from one symbol's OHLCV history."""

    result = indicators(frame)
    close = result["Adj Close"].astype(float)
    volume = result["Volume"].astype(float)
    returns = close.pct_change()
    rolling_volume = volume.rolling(20, min_periods=5).mean()
    rolling_arrivals = volume.rolling(5, min_periods=3).mean()
    rolling_vwap = (close * volume).rolling(20, min_periods=5).sum() / volume.rolling(20, min_periods=5).sum()
    daily_range = ((result["High"] - result["Low"]) / close * 100).replace([np.inf, -np.inf], np.nan)
    range_size = (result["High"] - result["Low"]).replace(0, np.nan)
    close_position = ((close - result["Low"]) / range_size).clip(0, 1).fillna(0.5)
    buy_volume = volume * close_position
    sell_volume = volume * (1 - close_position)

    features = pd.DataFrame(index=result.index)
    features["price"] = close
    features["price_change"] = returns * 100
    features["volume"] = volume
    features["volatility"] = returns.rolling(20, min_periods=5).std() * math.sqrt(252) * 100
    features["spread"] = daily_range
    features["buy_volume"] = buy_volume
    features["sell_volume"] = sell_volume
    features["order_imbalance"] = ((buy_volume - sell_volume) / volume.replace(0, np.nan)).clip(-1, 1)
    features["order_arrival_rate"] = rolling_arrivals
    features["trade_frequency"] = volume.rolling(5, min_periods=3).count()
    features["vwap"] = rolling_vwap
    features["vwap_deviation"] = (close / rolling_vwap - 1) * 100
    features["market_depth"] = rolling_volume
    return features.replace([np.inf, -np.inf], np.nan).dropna()


def _score_to_unit_interval(raw_scores: np.ndarray) -> np.ndarray:
    """Convert Isolation Forest unusualness into a display score in [0, 1]."""

    unusualness = -raw_scores
    low, high = float(unusualness.min()), float(unusualness.max())
    if math.isclose(low, high):
        return np.full(len(unusualness), 0.5)
    return np.clip((unusualness - low) / (high - low), 0, 1)


def detect_anomalies(histories: dict[str, pd.DataFrame], symbol: str, period: str = "1Y") -> dict:
    """Fit an Isolation Forest and return a serializable anomaly report."""

    symbol = symbol.upper()
    if symbol not in COMPANIES:
        raise ValueError("company was not found")
    historical = period_history(histories[symbol], period)
    features = build_features(historical)
    if len(features) < 10:
        raise ValueError("not enough complete observations for anomaly detection")

    contamination = min(0.20, max(0.05, 1 / len(features)))
    model = Pipeline([
        ("scaler", StandardScaler()),
        ("isolation_forest", IsolationForest(
            n_estimators=150,
            contamination=contamination,
            random_state=42,
        )),
    ])
    matrix = features.loc[:, FEATURE_NAMES]
    model.fit(matrix)
    forest = model.named_steps["isolation_forest"]
    raw_scores = model.decision_function(matrix)
    scores = _score_to_unit_interval(raw_scores)
    predictions = model.predict(matrix)

    timeline = []
    for date, score, prediction in zip(features.index[-90:], scores[-90:], predictions[-90:]):
        timeline.append({
            "date": date.strftime("%Y-%m-%d"),
            "anomaly_score": round(float(score), 4),
            "is_anomalous": bool(prediction == -1),
        })

    latest = features.iloc[-1]
    latest_values = {name: round(float(latest[name]), 4) for name in FEATURE_NAMES}
    latest_score = float(scores[-1])
    latest_prediction = int(predictions[-1])
    standardized = np.abs(StandardScaler().fit_transform(matrix)[-1])
    top_features = [
        FEATURE_NAMES[index]
        for index in np.argsort(standardized)[::-1][:3]
    ] if len(standardized) else []

    return {
        "symbol": symbol,
        "company": COMPANIES[symbol].name,
        "period": period,
        "method": "StandardScaler + Isolation Forest",
        "model": "Isolation Forest",
        "contamination": round(float(contamination), 4),
        "observations": len(features),
        "anomaly_count": int((predictions == -1).sum()),
        "latest": {
            "date": features.index[-1].strftime("%Y-%m-%d"),
            "anomaly_score": round(latest_score, 4),
            "is_anomalous": bool(latest_prediction == -1),
            "features": latest_values,
            "top_features": top_features,
        },
        "timeline": timeline,
        "feature_explanations": FEATURE_EXPLANATIONS,
        "note": "Anomaly scores indicate unusual activity within this feature window. They are not fraud probabilities or causal explanations.",
        "trees": forest.n_estimators,
    }
