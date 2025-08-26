import os
import time
import json
import requests

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
STOCKS_FILE = "data/stocks.json"

def fetch_tickers(limit=100):
    """Fetch a list of tickers from Polygon API."""
    url = f"https://api.polygon.io/v3/reference/tickers?market=stocks&active=true&limit={limit}&apiKey={POLYGON_API_KEY}"
    print(f"🔹 Fetching tickers from: {url}")
    response = requests.get(url)

    if response.status_code != 200:
        print(f"❌ Failed to fetch tickers: {response.status_code} - {response.text}")
        return []

    data = response.json()
    return data.get("results", [])


def fetch_stock_details(symbol):
    """Fetch the latest price + market cap for a given stock symbol."""
    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev?apiKey={POLYGON_API_KEY}"
    try:
        response = requests.get(url)
        if response.status_code == 429:
            print("⚠️ Rate limit hit. Sleeping 12s...")
            time.sleep(12)
            return fetch_stock_details(symbol)

        if response.status_code != 200:
            print(f"⚠️ Failed {symbol}: {response.status_code}")
            return None

        data = response.json()
        results = data.get("results", [])
        if not results:
            return None

        # Get latest close price from previous day
        price = results[0].get("c", None)
        return price
    except Exception as e:
        print(f"⚠️ Error fetching {symbol}: {e}")
        return None


def build_stock_list(limit=100):
    """Fetch stocks and enrich with price + market cap."""
    tickers = fetch_tickers(limit)
    stocks = []

    for i, t in enumerate(tickers, start=1):
        symbol = t.get("ticker")
        name = t.get("name", "Unknown")
        market = t.get("market", "stocks")

        # Fetch price for each stock
        price = fetch_stock_details(symbol)

        stocks.append({
            "symbol": symbol,
            "name": name,
            "market": market,
            "price": price if price else None,
            "marketCap": t.get("market_cap", None)  # Fallback to Polygon field if available
        })

        if i % 10 == 0:
            print(f"📦 Processed {i}/{len(tickers)} stocks")

    return stocks


def save_stocks(stocks):
    """Save stocks to JSON file."""
    os.makedirs(os.path.dirname(STOCKS_FILE), exist_ok=True)
    with open(STOCKS_FILE, "w") as f:
        json.dump(stocks, f, indent=2)
    print(f"✅ Saved {len(stocks)} stocks → {STOCKS_FILE}")


def main():
    print("🚀 Updating stock universe...")
    stocks = build_stock_list(limit=100)

    if not stocks:
        print("❌ No stock data fetched. Exiting.")
        return

    save_stocks(stocks)


if __name__ == "__main__":
    main()
