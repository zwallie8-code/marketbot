import json
import sys
from pathlib import Path

DATA_PATH = Path("data/stocks.json")

def rank_stocks(limit=20):
    if not DATA_PATH.exists():
        print("ERROR: stocks.json not found")
        sys.exit(1)

    with open(DATA_PATH, "r") as f:
        data = json.load(f)

    if not data:
        print("ERROR: No valid stock data found. Run update_universe first.")
        sys.exit(1)

    ranked = sorted(data.items(), key=lambda x: x[1].get("marketCap", 0), reverse=True)
    return ranked[:limit]

if __name__ == "__main__":
    top = int(sys.argv[sys.argv.index("--top") + 1]) if "--top" in sys.argv else 20
    ranked = rank_stocks(top)
    print(f"✅ Ranked {len(ranked)} stocks:")
    for ticker, info in ranked:
        print(f"{ticker}: ${info['price']} | Market Cap: {info['marketCap']}")
