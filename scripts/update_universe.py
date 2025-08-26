#!/usr/bin/env python3
import os
import json
import time
import requests

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
STOCKS_FILE = "data/stocks.json"
MAX_LIMIT = 100  # Free API limit per call

def fetch_stocks(limit=MAX_LIMIT):
    """Fetch stock tickers using Polygon Free API"""
    url = f"https://api.polygon.io/v3/reference/tickers?market=stocks&active=true&limit={limit}&apiKey={POLYGON_API_KEY}"
    print(f"🚀 Fetching {limit} stocks from Polygon Free API...")
    response = requests.get(url)

    if response.status_code == 429:
        print("⚠️ Rate limit hit, sleeping 15s...")
        time.sleep(15)
        return fetch_stocks(limit)

    if response.status_code == 403:
        print("❌ ERROR: Your Polygon API key doesn't have snapshot access. Using free ticker data only.")
        return []

    if response.status_code != 200:
        print(f"❌ API error {response.status_code}: {response.text}")
        return []

    data = response.json().get("results", [])
    stocks = []

    for t in data:
        stocks.append({
            "symbol": t.get("ticker"),
            "name": t.get("name", "Unknown"),
            "market": t.get("market", "stocks"),
            "price": None,          # Free endpoint does not include prices
            "marketCap": None       # We’ll enrich this later if needed
        })

    return stocks

def save_stocks(stocks):
    """Save fetched stocks to JSON file"""
    os.makedirs(os.path.dirname(STOCKS_FILE), exist_ok=True)
    with open(STOCKS_FILE, "w") as f:
        json.dump(stocks, f, indent=2)
    print(f"✅ Saved {len(stocks)} stocks → {STOCKS_FILE}")

def main():
    print("🚀 Updating stock universe from Polygon Free API...")
    stocks = fetch_stocks(limit=MAX_LIMIT)

    if not stocks:
        print("⚠️ WARNING: No stock data fetched! Your stocks.json may remain empty.")
    else:
        save_stocks(stocks)

if __name__ == "__main__":
    main()
