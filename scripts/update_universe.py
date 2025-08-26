import yfinance as yf
import pandas as pd
import json

OUTPUT_PATH = "data/stocks.json"

def get_sp500_tickers():
    # Use a GitHub-hosted static CSV instead of scraping Wikipedia directly
    url = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv"
    df = pd.read_csv(url)
    return df['Symbol'].tolist()

def fetch_stock_data(tickers):
    data = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            data.append({
                "symbol": ticker,
                "name": info.get("shortName", ""),
                "sector": info.get("sector", ""),
                "price": info.get("currentPrice", None),
                "volume": info.get("volume", None),
                "market_cap": info.get("marketCap", None),
                "pe_ratio": info.get("trailingPE", None),
                "dividend_yield": info.get("dividendYield", None),
            })
        except Exception:
            continue
    return data

def main():
    tickers = get_sp500_tickers()
    stock_data = fetch_stock_data(tickers)

    with open(OUTPUT_PATH, "w") as f:
        json.dump(stock_data, f, indent=4)
    print(f"✅ Saved {len(stock_data)} stocks to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
