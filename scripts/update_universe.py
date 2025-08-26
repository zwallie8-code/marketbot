#!/usr/bin/env python3
import os
import json
import yfinance as yf

STOCKS_FILE = "data/stocks.json"

# You can adjust how many stocks to fetch (max recommended: 2000)
MAX_STOCKS = 500  

# Predefined major tickers list from S&P 500 + Nasdaq + NYSE + ETF universes
# You can extend this list if you want more coverage
def load_ticker_list():
    """Load a big list of tradable tickers from Yahoo."""
    # Fetch top S&P 500 tickers as a start
    sp500 = yf.Ticker("^GSPC").history(period="1d")
    tickers = yf.download("^GSPC", period="1d")
    del sp500, tickers  # Just a sanity check on API
    # For now, we’ll start from a static list
    # For full automation, we can integrate a Nasdaq ticker list fetcher later
    return [
        "AAPL", "MSFT", "GOOG", "AMZN", "META", "TSLA", "NVDA", "NFLX", "AMD", "INTC",
        "BA", "DIS", "WMT", "PG", "XOM", "CVX", "JPM", "V", "MA", "KO"
    ]  # Expandable manually or dynamically later


def fetch_stock_details(symbol):
    """Fetch the latest price + market cap from Yahoo Finance."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        price = info.get("currentPrice") or info.get("regularMarketPrice")
        market_cap = info.get("marketCap")

        if price is None or market_cap is None:
            print(f"⚠️ Skipping {symbol}: Missing price or market cap")
            return None

        return {
            "symbol": symbol,
            "name": info.get("shortName", "Unknown"),
            "market": "stocks",
            "price": price,
            "marketCap": market_cap
        }
    except Exception as e:
        print(f"⚠️ Error fetching {symbol}: {e}")
        return None


def build_stock_list():
    """Build a full stock universe enriched with price & market cap."""
    symbols = load_ticker_list()
    stocks = []

    for i, symbol in enumerate(symbols[:MAX_STOCKS], start=1):
        data = fetch_stock_details(symbol)
        if data:
            stocks.append(data)
        if i % 10 == 0:
            print(f"📦 Processed {i}/{len(symbols)} stocks")

    return stocks


def save_stocks(stocks):
    """Save valid stocks to JSON."""
    os.makedirs(os.path.dirname(STOCKS_FILE), exist_ok=True)
    with open(STOCKS_FILE, "w") as f:
        json.dump(stocks, f, indent=2)
    print(f"✅ Saved {len(stocks)} stocks → {STOCKS_FILE}")


def main():
    print("🚀 Building stock universe...")
    stocks = build_stock_list()

    if not stocks:
        print("❌ No valid stock data. Exiting.")
        return

    save_stocks(stocks)


if __name__ == "__main__":
    main()
