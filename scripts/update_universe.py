import os
import json
import requests

# Load API key from environment variable
FMP_API_KEY = os.getenv("FMP_API_KEY")
if not FMP_API_KEY:
    raise ValueError("Missing FMP_API_KEY. Set it in GitHub Secrets.")

# Output path
OUTPUT_FILE = "data/stocks.json"

def fetch_sp500_stocks():
    """Fetches S&P 500 stock list from Financial Modeling Prep API."""
    url = f"https://financialmodelingprep.com/api/v3/sp500_constituent?apikey={FMP_API_KEY}"
    print(f"Fetching stocks from {url}...")
    response = requests.get(url)

    if response.status_code != 200:
        raise RuntimeError(f"FMP API failed! Status {response.status_code}: {response.text}")

    stocks = response.json()
    if not stocks:
        raise RuntimeError("No stock data received from FMP API.")

    # Clean & normalize data
    cleaned_stocks = []
    for stock in stocks:
        cleaned_stocks.append({
            "symbol": stock.get("symbol"),
            "name": stock.get("name"),
            "sector": stock.get("sector", "Unknown")
        })

    # Save to file
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(cleaned_stocks, f, indent=4)

    print(f"✅ Saved {len(cleaned_stocks)} stocks to {OUTPUT_FILE}")


if __name__ == "__main__":
    try:
        fetch_sp500_stocks()
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)
