import yfinance as yf
import pandas as pd
import json
import time

OUTPUT_PATH = "data/stocks.json"

def get_sp500_tickers():
    url = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv"
    df = pd.read_csv(url)
    return df['Symbol'].tolist()

def fetch_stock_data(tickers):
    # Bulk download for better rate limits
    df = yf.download(
        tickers=tickers,
        period="5d",
        interval="1d",
        group_by="ticker",
        threads=True
    )
    
    stock_data = []
    for ticker in tickers:
        try:
            if ticker not in df.columns.levels[0]:
                continue

            price = df[ticker]['Close'][-1]
            volume = df[ticker]['Volume'][-1]

            stock_data.append({
                "symbol": ticker,
                "price": round(float(price), 2),
                "volume": int(volume) if not pd.isna(volume) else None
            })
        except Exception:
            continue
    return stock_data

def main():
    tickers = get_sp500_tickers()
    print(f"✅ Found {len(tickers)} S&P 500 tickers")

    stock_data = []
    batch_size = 50  # Avoids hitting Yahoo's rate limits
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i+batch_size]
        print(f"Fetching batch {i//batch_size + 1}: {len(batch)} tickers")
        stock_data.extend(fetch_stock_data(batch))
        time.sleep(2)  # Prevents throttling

    with open(OUTPUT_PATH, "w") as f:
        json.dump(stock_data, f, indent=4)
    print(f"✅ Saved {len(stock_data)} stocks to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
