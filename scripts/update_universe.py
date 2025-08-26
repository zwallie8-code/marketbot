import os
import requests
import json

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
STOCKS_FILE = "data/stocks.json"

def fetch_stocks():
    url = f"https://api.polygon.io/v3/reference/tickers?market=stocks&active=true&limit=100&apiKey={POLYGON_API_KEY}"
    print(f"🔹 Using Polygon API URL: {url}")

    response = requests.get(url)
    print(f"🔹 Status Code: {response.status_code}")

    # Print first 300 chars for debugging
    print(f"🔹 Response snippet: {response.text[:300]}")

    if response.status_code != 200:
        print(f"❌ Error fetching stocks: {response.status_code} - {response.text}")
        return []

    data = response.json()
    tickers = []
    for item in data.get("results", []):
        tickers.append({
            "symbol": item.get("ticker"),
            "name": item.get("name"),
            "market": item.get("market")
        })
    return tickers

def save_stocks(stocks):
    with open(STOCKS_FILE, "w") as f:
        json.dump(stocks, f, indent=2)

def main():
    print("🚀 Fetching stock universe from Polygon...")
    stocks = fetch_stocks()

    if not stocks:
        print("❌ No stock data fetched, exiting.")
        return

    save_stocks(stocks)
    print(f"✅ Successfully saved {len(stocks)} stocks to {STOCKS_FILE}")

if __name__ == "__main__":
    main()
