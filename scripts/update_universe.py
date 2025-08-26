#!/usr/bin/env python3
import os
import json
import requests
import time

# Load Polygon API key from environment variables
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
if not POLYGON_API_KEY:
    raise ValueError("❌ Missing POLYGON_API_KEY in environment variables.")

# File to store results
STOCKS_FILE = "data/stocks.json"
SNAPSHOT_URL = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers?apiKey={POLYGON_API_KEY}"

def fetch_stocks():
    """Fetches stock snapshot from Polygon, includes price & market cap."""
    print("🚀 Fetching stock snapshot from Polygon...")

    try:
        response = requests.get(SNAPSHOT_URL)
        if response.status_code == 429:
            print("⚠️ Rate limit hit. Waiting 15 seconds...")
            time.sleep(15)
            return fetch_stocks()

        if response.status_code != 200:
            print(f"❌ Error fetching data: {response.status_code} - {response.text}")
            return []

        data = response.json()
        tickers = data.get("tickers", [])
        stocks = []

        for t in tickers:
            try:
                symbol = t.get("ticker")
                name = t.get("name", "Unknown")
                price = t.get("lastTrade", {}).get("p") or t.get("day", {}).get("c")
                market_cap = t.get("marketCap")

                stocks.append({
                    "symbol": symbol,
                    "name": name,
                    "price": price if price is not None else None,
                    "marketCap": market_cap if market_cap is not None else None
                })
            except Exception as e:
                print(f"⚠️ Error parsing ticker: {e}")
                continue

        return stocks

    except Exception as e:
        print(f"❌ Failed to fetch snapshot: {e}")
        return []

def save_stocks(stocks):
    """Save fetched stock data to JSON."""
    os.makedirs(os.path.dirname(STOCKS_FILE), exist_ok=True)
    with open(STOCKS_FILE, "w") as f:
        json.dump(stocks, f, indent=2)
    print(f"✅ Saved {len(stocks)} stocks → {STOCKS_FILE}")

def main():
    stocks = fetch_stocks()
    if not stocks:
        print("❌ No stocks fetched. Exiting.")
        return
    save_stocks(stocks)

if __name__ == "__main__":
    main()
