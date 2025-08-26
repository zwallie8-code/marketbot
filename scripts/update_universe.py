import yfinance as yf
import time
import random

def fetch_stock_data(tickers):
    valid_stocks = {}
    batch_size = 10  # Keep batches small to avoid 429
    total = len(tickers)

    for i in range(0, total, batch_size):
        batch = tickers[i:i + batch_size]
        print(f"📌 Fetching batch {i // batch_size + 1}: {len(batch)} tickers...")

        for ticker in batch:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info

                if "regularMarketPrice" in info and info["regularMarketPrice"] is not None:
                    valid_stocks[ticker] = {
                        "price": info["regularMarketPrice"],
                        "marketCap": info.get("marketCap"),
                        "volume": info.get("volume"),
                    }
                    print(f"✅ {ticker} fetched")
                else:
                    print(f"⚠️ {ticker} skipped — missing price")
            except Exception as e:
                print(f"❌ Failed {ticker}: {e}")

            # Sleep between requests to avoid hitting the 429 limit
            time.sleep(random.uniform(1, 3))

        # Cooldown after each batch
        print("⏳ Cooling down for 5 seconds...")
        time.sleep(5)

    return valid_stocks
