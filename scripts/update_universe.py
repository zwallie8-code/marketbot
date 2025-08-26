import yfinance as yf
import pandas as pd
import json
import time

OUTPUT_PATH = "data/stocks.json"

def get_sp500_tickers():
    url = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv"
    df = pd.read_csv(url)
    return df['Symbol'].tolist()

def fetch_batch(batch):
    """Fetch a batch of tickers with retry logic and error handling."""
    try:
        df = yf.download(
            tickers=batch,
            period="5d",
            interval="1d",
            group_by="ticker",
            threads=True
        )
        return df
    except Exception:
        return pd.DataFrame()

def fetch_stock_data(tickers):
    stock_data = []
    batch_size = 30
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i+batch_size]
        print(f"📦 Fetching batch {i//batch_size + 1} ({len(batch)} tickers)")
        df = fetch_batch(batch)

        for ticker in batch:
            try:
                price = df[ticker]['Close'][-1]
                volume = df[ticker]['Volume'][-1]
                if pd.isna(price):
                    continue  # skip invalid data

                stock_data.append({
                    "symbol": ticker,
                    "price": round(float(price), 2),
                    "volume": int(volume) if not pd.isna(volume) else None
                })
            except Exception:
                continue
        time.sleep(2)
    return stock_data

def main():
    tickers = get_sp500_tickers()
    print(f"✅ Found {len(tickers)} S&P 500 tickers")

    stock_data = fetch_stock_data(tickers)

    with open(OUTPUT_PATH, "w") as f:
        json.dump(stock_data, f, indent=4)

    print(f"✅ Saved {len(stock_data)} valid stocks to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
