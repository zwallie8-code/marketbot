import requests
import json
from pathlib import Path
import os

API_KEY = os.getenv("FMP_API_KEY")  # Set in GitHub secrets
OUTPUT_PATH = Path("data/stocks.json")

def fetch_sp500(limit=500):
    print("Fetching S&P 500 stocks from FMP API...")
    url = f"https://financialmodelingprep.com/api/v3/sp500_constituent?apikey={API_KEY}"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        if not data:
            raise ValueError("Empty response from FMP API")

        stocks = []
        for stock in data[:limit]:
            stocks.append({
                "symbol": stock["symbol"],
                "name": stock["name"],
                "sector": stock.get("sector", "N/A")
            })

        return stocks

    except Exception as e:
        print(f"⚠ Error fetching stocks: {e}")
        return []

def save_stocks(stocks):
    if not stocks:
        print("⚠ No stock data fetched. Skipping save.")
        return
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(stocks, f, indent=2)
    print(f"✅ Saved {len(stocks)} stocks to {OUTPUT_PATH}")

def main():
    stocks = fetch_sp500()
    save_stocks(stocks)

if __name__ == "__main__":
    main()
