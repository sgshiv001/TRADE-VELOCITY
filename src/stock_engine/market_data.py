"""Provider market history, explicit provenance, persistent cache, and analytics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
from pathlib import Path

import pandas as pd

from .companies import COMPANIES

SNAPSHOT_PATH = Path(__file__).parent / "data" / "market-history.json"
FIELDS = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]


@dataclass
class MarketData:
    histories: dict[str, pd.DataFrame]
    source: str
    fetched_at: str
    is_synthetic: bool = False
    message: str = ""

    @property
    def as_of(self) -> str:
        # The oldest last observation makes uneven provider coverage visible.
        return min(frame.index[-1] for frame in self.histories.values()).strftime("%d %b %Y") if self.histories else "Unavailable"

    def marks(self) -> dict[str, float]:
        return {symbol: float(frame["Close"].iloc[-1]) for symbol, frame in self.histories.items()}

    def to_dict(self) -> dict:
        return {
            "version": 1, "source": self.source, "fetched_at": self.fetched_at, "is_synthetic": self.is_synthetic,
            "histories": {symbol: [dict(Date=date.strftime("%Y-%m-%d"), **{field: float(row[field]) for field in FIELDS})
                                    for date, row in frame.iterrows()]
                          for symbol, frame in self.histories.items()},
        }


def clean_history(frame: pd.DataFrame) -> pd.DataFrame:
    """Require complete, finite OHLC bars and preserve corporate-action prices."""
    frame = frame.copy()
    if "Adj Close" not in frame:
        raise ValueError("adjusted closing prices are missing")
    frame = frame[FIELDS].apply(pd.to_numeric, errors="coerce").dropna()
    if not isinstance(frame.index, pd.DatetimeIndex):
        frame.index = pd.to_datetime(frame.index, errors="raise")
    if frame.index.tz is not None:
        frame.index = frame.index.tz_localize(None)
    frame.index = frame.index.normalize()
    frame = frame[~frame.index.duplicated(keep="last")].sort_index()
    finite = frame.map(math.isfinite).all(axis=1)
    positive = (frame[FIELDS[:-1]] > 0).all(axis=1) & (frame["Volume"] >= 0)
    valid_bar = (frame["High"] >= frame[["Open", "Close", "Low"]].max(axis=1)) & (
        frame["Low"] <= frame[["Open", "Close", "High"]].min(axis=1))
    frame = frame[finite & positive & valid_bar]
    if len(frame) < 2:
        raise ValueError("at least two complete trading days are required")
    frame.index.name = "Date"
    return frame


def download_market_data() -> MarketData:
    """Fetch five years of daily bars; never call this on every UI rerun."""
    import yfinance as yf

    tickers = [company.ticker for company in COMPANIES.values()]
    raw = yf.download(tickers, period="5y", interval="1d", auto_adjust=False,
                      group_by="ticker", threads=4, progress=False, timeout=10)
    histories = {}
    for symbol, company in COMPANIES.items():
        try:
            histories[symbol] = clean_history(raw[company.ticker])
        except (KeyError, TypeError, ValueError) as exc:
            # Retry only a failed ticker serially; concurrent provider cache
            # initialization can otherwise leave one ticker empty.
            try:
                histories[symbol] = clean_history(yf.Ticker(company.ticker).history(
                    period="5y", auto_adjust=False, timeout=10, raise_errors=True))
            except Exception as retry_error:
                raise ValueError(f"market history unavailable for {symbol}; previous snapshot was preserved") from retry_error
    return MarketData(histories, "Yahoo Finance · daily historical prices", datetime.now(timezone.utc).isoformat())


def save_snapshot(data: MarketData, path: Path = SNAPSHOT_PATH) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data.to_dict(), separators=(",", ":")), encoding="utf-8")
    temporary.replace(path)


def from_snapshot(payload: dict) -> MarketData:
    if payload.get("version") != 1 or not isinstance(payload.get("histories"), dict):
        raise ValueError("unsupported market snapshot")
    if payload.get("is_synthetic", False) or payload.get("is_demo", False):
        raise ValueError("synthetic market snapshots are not accepted")
    histories = {}
    for symbol in COMPANIES:
        frame = pd.DataFrame(payload["histories"][symbol]).set_index("Date")
        histories[symbol] = clean_history(frame)
    return MarketData(histories, str(payload["source"]), str(payload["fetched_at"]))


def load_market_data(path: Path = SNAPSHOT_PATH) -> MarketData:
    try:
        return from_snapshot(json.loads(Path(path).read_text(encoding="utf-8")))
    except (OSError, KeyError, TypeError, ValueError) as exc:
        return MarketData({}, "Market history unavailable", "", message=f"No usable provider snapshot. Refresh market data to download history. ({type(exc).__name__})")


def period_history(frame: pd.DataFrame, period: str) -> pd.DataFrame:
    offsets = {"1M": pd.DateOffset(months=1), "3M": pd.DateOffset(months=3), "6M": pd.DateOffset(months=6),
               "1Y": pd.DateOffset(years=1), "5Y": pd.DateOffset(years=5)}
    if period not in offsets:
        raise ValueError("unknown history period")
    if frame.empty:
        return frame.copy()
    return frame[frame.index >= frame.index[-1] - offsets[period]].copy()


def indicators(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    close = frame["Adj Close"]
    result["MA20"] = close.rolling(20).mean()
    result["MA50"] = close.rolling(50).mean()
    change = close.diff()
    gains = change.clip(lower=0).rolling(14).mean()
    losses = (-change.clip(upper=0)).rolling(14).mean()
    result["RSI14"] = 100 - 100 / (1 + gains / losses.where(losses != 0))
    result.loc[(losses == 0) & (gains > 0), "RSI14"] = 100
    result.loc[(losses == 0) & (gains == 0), "RSI14"] = 50
    result["Drawdown %"] = (close / close.cummax() - 1) * 100
    return result


def history_metrics(frame: pd.DataFrame) -> dict:
    if frame.empty:
        return dict.fromkeys(["last", "change_pct", "growth_pct", "cagr_pct", "volatility_pct", "drawdown_pct", "volume"])
    close = frame["Adj Close"]
    returns = close.pct_change().dropna()
    years = (frame.index[-1] - frame.index[0]).days / 365.25
    growth = (float(close.iloc[-1]) / float(close.iloc[0]) - 1) * 100
    return {
        "last": float(frame["Close"].iloc[-1]),
        "change_pct": (float(close.iloc[-1]) / float(close.iloc[-2]) - 1) * 100 if len(close) > 1 else None,
        "growth_pct": growth if len(close) > 1 else None,
        "cagr_pct": ((float(close.iloc[-1]) / float(close.iloc[0])) ** (1 / years) - 1) * 100 if years >= 1 else None,
        "volatility_pct": float(returns.std(ddof=0)) * math.sqrt(252) * 100 if len(returns) else None,
        "drawdown_pct": float(((close / close.cummax() - 1) * 100).min()),
        "volume": int(frame["Volume"].iloc[-1]),
    }


def market_rows(data: MarketData) -> list[dict]:
    rows = []
    for symbol, company in COMPANIES.items():
        if symbol not in data.histories or data.histories[symbol].empty:
            continue
        frame = data.histories[symbol]
        stats = history_metrics(period_history(frame, "1Y"))
        rows.append({"Symbol": symbol, "Company": company.name, "Sector": company.sector,
                     "Price (₹)": stats["last"], "Day %": stats["change_pct"], "1Y growth %": stats["growth_pct"],
                     "Volume": stats["volume"], "As of": frame.index[-1].strftime("%Y-%m-%d")})
    return rows
