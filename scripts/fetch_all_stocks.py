import yfinance as yf
import pandas as pd
import json
import os

# Load tickers from S&P 500 or custom list
sp500 = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]
tickers = sp500['Symbol'].tolist()

data = []

print(f"Fetching data for {len(tickers)} tickers...")

for ticker in tickers:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        data.append({
            "symbol": ticker,
            "name": info.get("shortName"),
            "sector": info.get("sector"),
            "marketCap": info.get("marketCap"),
            "price": info.get("currentPrice"),
            "peRatio": info.get("trailingPE"),
            "dividendYield": info.get("dividendYield"),
        })
    except Exception as e:
        print(f"Failed to fetch {ticker}: {e}")

# Save all stock data into JSON
os.makedirs("data", exist_ok=True)
with open("data/stocks.json", "w") as f:
    json.dump(data, f, indent=2)

print(f"✅ Saved stock data for {len(data)} companies!")
