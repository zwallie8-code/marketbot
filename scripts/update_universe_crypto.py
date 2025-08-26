import os
import json
import requests

# Output path
OUTPUT_FILE = "data/crypto.json"

def fetch_top_crypto():
    """Fetches top crypto assets from CoinGecko."""
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 50,
        "page": 1,
        "sparkline": False
    }
    print(f"Fetching top crypto from {url}...")
    response = requests.get(url, params=params)

    if response.status_code != 200:
        raise RuntimeError(f"CoinGecko API failed! Status {response.status_code}: {response.text}")

    crypto_data = response.json()
    if not crypto_data:
        raise RuntimeError("No crypto data received from CoinGecko.")

    # Clean & normalize data
    cleaned_crypto = []
    for coin in crypto_data:
        cleaned_crypto.append({
            "id": coin.get("id"),
            "symbol": coin.get("symbol").upper(),
            "name": coin.get("name"),
            "current_price": coin.get("current_price"),
            "market_cap": coin.get("market_cap"),
            "volume": coin.get("total_volume")
        })

    # Save to file
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(cleaned_crypto, f, indent=4)

    print(f"✅ Saved {len(cleaned_crypto)} crypto assets to {OUTPUT_FILE}")


if __name__ == "__main__":
    try:
        fetch_top_crypto()
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)
