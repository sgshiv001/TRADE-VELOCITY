"""Deterministic, explainable market insights for the TradeVelocity application."""

from datetime import datetime, timezone
import math

from .companies import COMPANIES
from .market_data import history_metrics, indicators, period_history


def _round(value, places=2):
    return round(float(value), places) if value is not None and math.isfinite(float(value)) else None


def analyze_history(symbol: str, histories: dict, period: str = "1Y") -> dict:
    symbol = symbol.upper()
    if symbol not in COMPANIES:
        raise ValueError("company was not found")
    full = indicators(histories[symbol])
    frame = period_history(full, period)
    if len(frame) < 2:
        raise ValueError("At least two observations are needed for historical analysis. Choose a longer period.")
    metrics = history_metrics(frame)
    latest = full.iloc[-1]
    close = float(latest["Adj Close"])
    ma20 = float(latest["MA20"]) if math.isfinite(float(latest["MA20"])) else None
    ma50 = float(latest["MA50"]) if math.isfinite(float(latest["MA50"])) else None
    rsi = float(latest["RSI14"]) if math.isfinite(float(latest["RSI14"])) else 50.0
    recent_volume = float(full["Volume"].tail(20).mean())
    volume_ratio = float(latest["Volume"]) / recent_volume if recent_volume else 1.0
    trend_points = [close > ma for ma in (ma20, ma50) if ma is not None]
    trend_up = sum(trend_points) >= max(1, len(trend_points)) / 2
    positive = metrics["growth_pct"] >= 0
    signal = "Bullish" if positive and trend_up and rsi < 72 else "Bearish" if not positive and not trend_up and rsi > 28 else "Mixed"
    bullets = [
        f"{period} adjusted return is {_round(metrics['growth_pct']):+.2f}% with an annualized volatility of {_round(metrics['volatility_pct']):.2f}%.",
        f"The latest adjusted close is {'above' if trend_up else 'below'} the available moving-average trend.",
        f"RSI14 is {_round(rsi):.1f}, which is {'near an overbought zone' if rsi >= 70 else 'near an oversold zone' if rsi <= 30 else 'inside a neutral range'}.",
    ]
    risk_flags = []
    if abs(metrics["drawdown_pct"]) >= 20:
        risk_flags.append(f"Historical drawdown reached {_round(metrics['drawdown_pct']):.2f}% in this window.")
    if volume_ratio >= 1.75:
        risk_flags.append(f"The latest volume is {volume_ratio:.1f}× its 20-session average.")
    if not risk_flags:
        risk_flags.append("No rule-based risk flag crossed the configured threshold.")
    return {
        "symbol": symbol,
        "company": COMPANIES[symbol].name,
        "sector": COMPANIES[symbol].sector,
        "period": period,
        "as_of": full.index[-1].strftime("%Y-%m-%d"),
        "signal": signal,
        "headline": f"{COMPANIES[symbol].name} has a {signal.lower()} rule-based setup over {period}.",
        "snapshot": {"price": float(full["Close"].iloc[-1]), "return_pct": _round(metrics["growth_pct"]),
                     "rsi": _round(rsi), "volatility_pct": _round(metrics["volatility_pct"]),
                     "drawdown_pct": _round(metrics["drawdown_pct"]), "volume_ratio": _round(volume_ratio),
                     "moving_average": "above" if trend_up else "below"},
        "evidence": bullets,
        "risk_flags": risk_flags,
        "method": "TradeVelocity Rules v1 · indicators only · no order execution",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
