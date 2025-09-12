#!/usr/bin/env python3
import os
import json
import requests

DEXSCREENER_URL = "https://api.dexscreener.com/latest/dex/trades"
OUTPUT_FILE = "data/whales.json"

def fetch_whale_trades(limit=50):
    url = f"{DEXSCREENER_URL}?limit={limit}"
    resp = requests.get(url)

    if resp.status_code != 200:
        print(f"❌ Dexscreener API error: {resp.status_code}")
        return []

    data = resp.json()
    trades = data.get("trades", [])
    whales = []

    for t in trades:
        whales.append({
            "symbol": t.get("baseToken", {}).get("symbol"),
            "side": t.get("type"),  # buy/sell
            "amountUSD": t.get("amountUsd"),
            "txHash": t.get("txHash"),
            "timestamp": t.get("blockTimestamp"),
            "dex": t.get("dex", {}).get("name")
        })

    return whales

def save_whales(whales):
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(whales, f, indent=2)
    print(f"✅ Saved {len(whales)} whale trades → {OUTPUT_FILE}")

def main():
    print("🚀 Fetching whale trades from Dexscreener...")
    whales = fetch_whale_trades()
    if whales:
        save_whales(whales)
    else:
        print("⚠️ No whale trades fetched")

if __name__ == "__main__":
    main()
