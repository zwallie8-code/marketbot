import json
import sys
from pathlib import Path

DATA_PATH = Path("data/stocks.json")

def rank_stocks(limit=20):
    # Check if stocks.json exists
    if not DATA_PATH.exists():
        print("❌ ERROR: stocks.json not found. Run update_universe first.")
        sys.exit(1)

    # Load JSON safely
    with open(DATA_PATH, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print("❌ ERROR: Invalid JSON format in stocks.json")
            sys.exit(1)

    # Validate data format
    if not isinstance(data, list) or not data:
        print("❌ ERROR: stocks.json is empty or not in list format. Run update_universe first.")
        sys.exit(1)

    # Clean data — remove stocks without price or market cap
    cleaned = []
    skipped = 0
    for stock in data:
        price = stock.get("price")
        market_cap = stock.get("marketCap")

        # If neither price nor market cap is usable, skip
        if price is None and market_cap is None:
            skipped += 1
            continue

        cleaned.append(stock)

    if skipped:
        print(f"⚠️ Skipped {skipped} stocks with missing price/marketCap")

    if not cleaned:
        print("❌ ERROR: No valid stock data to rank after cleaning")
        sys.exit(1)

    # Sort by marketCap first, fallback to price if missing
    ranked = sorted(
        cleaned,
        key=lambda x: (
            x.get("marketCap") if isinstance(x.get("marketCap"), (int, float)) else
            x.get("price") if isinstance(x.get("price"), (int, float)) else 0
        ),
        reverse=True
    )

    # Return top N results
    return ranked[:limit]

if __name__ == "__main__":
    # Get top limit from args
    try:
        top = int(sys.argv[sys.argv.index("--top") + 1]) if "--top" in sys.argv else 20
    except (ValueError, IndexError):
        top = 20

    ranked = rank_stocks(top)

    print(f"✅ Ranked {len(ranked)} stocks:")
    for stock in ranked:
        symbol = stock.get("symbol", "N/A")
        price = stock.get("price", "N/A")
        market_cap = stock.get("marketCap", "N/A")
        print(f"{symbol}: ${price} | Market Cap: {market_cap}")
