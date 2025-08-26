import yfinance as yf
import json
import pandas as pd
import time
from pathlib import Path

DATA_PATH = Path("data/stocks.json")

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
            print(f"Failed to get {ticker}: {e}")
        time.sleep(0.2)  # Avoid 429 rate-limit errors

        if i % 50 == 0:
            print(f"Progress: {i}/{len(tickers)} tickers fetched")

    return valid_stocks

if __name__ == "__main__":
    # Pull S&P 500 list
    sp500 = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]
    tickers = sp500["Symbol"].tolist()

    stocks = fetch_stock_data(tickers)
    print(f"✅ Successfully fetched {len(stocks)} valid stocks")

    # Save results
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_PATH, "w") as f:
        json.dump(stocks, f, indent=4)
