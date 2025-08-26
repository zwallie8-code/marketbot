import requests
import pandas as pd
import yfinance as yf
import json
import time
from pathlib import Path

DATA_PATH = Path("data/stocks.json")
URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

# Add browser headers to bypass 403 Forbidden
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/115.0.0.0 Safari/537.36"
}

def get_sp500_tickers():
    """Fetch S&P 500 tickers from Wikipedia using requests instead of direct pandas read_html."""
    response = requests.get(URL, headers=HEADERS)
    response.raise_for_status()  # Throw exception if request fails

    tables = pd.read_html(response.text)
    sp500 = tables[0]
    tickers = sp500["Symbol"].tolist()
    return tickers

def fetch_stock_data(tickers):
    valid_stocks = {}
    for i, ticker in enumerate(tickers, start=1):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            if "regularMarketPrice" in info and info["regularMarketPrice"] is not None:
                valid_stocks[ticker] = {
                    "price": info["regularMarketPrice"],
                    "marketCap": info.get("marketCap"),
                    "volume": info.get("volume"),
                }
        except Exception as e:
            print(f"Failed to fetch {ticker}: {e}")
        time.sleep(0.2)  # Prevent rate-limiting

        if i % 50 == 0:
            print(f"Progress: {i}/{len(tickers)} tickers fetched")

    return valid_stocks

if __name__ == "__main__":
    print("🔹 Fetching S&P 500 tickers...")
    tickers = get_sp500_tickers()
    print(f"✅ Found {len(tickers)} S&P 500 tickers")

    stocks = fetch_stock_data(tickers)
    print(f"✅ Successfully fetched {len(stocks)} valid stocks")

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_PATH, "w") as f:
        json.dump(stocks, f, indent=4)

    print(f"💾 Saved {len(stocks)} stocks to {DATA_PATH}")
