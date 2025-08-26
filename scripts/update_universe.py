import os
import json
import requests

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
STOCKS_FILE = "data/stocks.json"

SNAPSHOT_URL = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers?apiKey={POLYGON_API_KEY}"

def fetch_stocks():
    """Fetch full snapshot of all US stocks with price + market cap."""
    print(f"🚀 Fetching stock snapshot from Polygon...")
    response = requests.get(SNAPSHOT_URL)

    if response.status_code == 429:
        print("⚠️ Rate limit hit — retrying in 15 seconds...")
        import time
        time.sleep(15)
        return fetch_stocks()

    if response.status_code != 200:
        print(f"❌ Error fetching snapshot: {response.status_code} - {response.text}")
        return []

    data = response.json()
    results = data.get("tickers", [])
    stocks = []

    for item in results:
        try:
            symbol = item.get("ticker")
            name = item.get("name", "Unknown")
            price = item.get("lastTrade", {}).get("p") or item.get("day", {}).get("c")
            market_cap = item.get("marketCap", None)

            stocks.append({
                "symbol": symbol,
                "name": name,
                "price": price if price is not None else None,
                "marketCap": market_cap if market_cap is not None else None
            })
        except Exception as e:
            print(f"⚠️ Error parsing {item.get('ticker')}: {e}")
            continue

    return stocks

def save_stocks(stocks):
    """Save stocks data to JSON."""
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
