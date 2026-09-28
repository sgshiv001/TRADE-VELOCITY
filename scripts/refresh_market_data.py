"""Download a dated local snapshot for MarketLab; keeps previous data on failure."""

from stock_engine.market_data import download_market_data, save_snapshot
import sys


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    data = download_market_data()
    save_snapshot(data)
    print(f"Saved {data.source}; coverage through {data.as_of}")
    for symbol, frame in data.histories.items():
        print(f"{symbol}: {len(frame)} daily bars, last close INR {frame['Close'].iloc[-1]:.2f}, date {frame.index[-1]:%Y-%m-%d}")


if __name__ == "__main__":
    main()
