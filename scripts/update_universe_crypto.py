import requests
import json
from pathlib import Path

OUTPUT_PATH = Path("data/crypto.json")
DEX_API = "https://api.dexscreener.com/latest/dex/tokens"

def fetch_top_tokens(limit=150):
    print(f"Fetching top {limit} crypto tokens from Dex Screener...")
    try:
        response = requests.get(DEX_API, timeout=15)
        response.raise_for_status()
        data = response.json()

        if "pairs" not in data:
            raise ValueError("Unexpected response format from Dex Screener")

        tokens = []
        for pair in data["pairs"][:limit]:
            tokens.append({
                "symbol": pair.get("baseToken", {}).get("symbol"),
                "name": pair.get("baseToken", {}).get("name"),
                "price_usd": float(pair.get("priceUsd", 0)),
                "volume_24h": float(pair.get("volume", 0)),
                "liquidity_usd": float(pair.get("liquidity", {}).get("usd", 0)),
                "chain": pair.get("chainId"),
                "dex_id": pair.get("dexId")
            })

        return tokens

    except Exception as e:
        print(f"⚠ Error fetching crypto tokens: {e}")
        return []

def save_tokens(tokens):
    if not tokens:
        print("⚠ No crypto data fetched. Skipping save.")
        return
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(tokens, f, indent=2)
    print(f"✅ Saved {len(tokens)} crypto tokens to {OUTPUT_PATH}")

def main():
    tokens = fetch_top_tokens()
    save_tokens(tokens)

if __name__ == "__main__":
    main()
