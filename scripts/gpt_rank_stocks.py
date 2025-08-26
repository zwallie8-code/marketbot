import json
import sys
from pathlib import Path

DATA_PATH = Path("data/stocks.json")

def rank_stocks(limit=20):
    if not DATA_PATH.exists():
        print("ERROR: stocks.json not found")
        sys.exit(1)

    with open(DATA_PATH, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print("ERROR: Invalid JSON format in stocks.json")
            sys.exit(1)

    if not isinstance(data, list) or not data:
        print("ERROR: stocks.json is empty or not a list. Run update_universe first.")
        sys.exit(1)

    # Sort by marketCap if available, otherwise fallback to price
    ranked = sorted(
        data,
        key=lambda x: x.get("marketCap", x.get("price", 0)),
        reverse=True
    )

    return ranked[:limit]

if __name__ == "__main__":
    top = int(sys.argv[sys.argv.index("--top") + 1]) if "--top" in sys.argv else 20
    ranked = rank_stocks(top)

    print(f"✅ Ranked {len(ranked)} stocks:")
    for stock in ranked:
        symbol = stock.get("symbol", "N/A")
        price = stock.get("price", "N/A")
        market_cap = stock.get("marketCap", "N/A")
        print(f"{symbol}: ${price} | Market Cap: {market_cap}")
