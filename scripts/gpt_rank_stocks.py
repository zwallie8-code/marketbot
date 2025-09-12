import json
import sys
import requests
from pathlib import Path

DATA_PATH = Path("data/stocks.json")
OUTPUT_PATH = Path("data/gpt_recommendations.json")

DEX_API = "https://api.dexscreener.com/latest/dex/search?q=ETH"  # you can expand query to multiple tokens

def fetch_whale_signals():
    """Fetch whale activity from Dexscreener."""
    try:
        resp = requests.get(DEX_API, timeout=10)
        data = resp.json().get("pairs", [])
    except Exception as e:
        print(f"⚠️ Dexscreener fetch failed: {e}")
        return {}

    signals = {}
    for pair in data:
        symbol = pair.get("baseToken", {}).get("symbol")
        buys = pair.get("txns", {}).get("h24", {}).get("buys", 0)
        sells = pair.get("txns", {}).get("h24", {}).get("sells", 0)
        volume = float(pair.get("volume", {}).get("h24", 0))

        if not symbol:
            continue

        # Heuristic whale detection
        if volume > 1_000_000 and buys > sells * 2:
            signals[symbol] = {"signal": "whale_buy", "boost": 0.3}
        elif volume > 1_000_000 and sells > buys * 2:
            signals[symbol] = {"signal": "whale_sell", "boost": -0.3}

    print(f"🐋 Whale signals detected: {len(signals)}")
    return signals


def rank_stocks(limit=20):
    if not DATA_PATH.exists():
        print("❌ ERROR: stocks.json not found. Run update_universe first.")
        sys.exit(1)

    with open(DATA_PATH, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print("❌ ERROR: Invalid JSON format in stocks.json")
            sys.exit(1)

    if not isinstance(data, list) or not data:
        print("❌ ERROR: stocks.json is empty or not in list format.")
        sys.exit(1)

    whale_signals = fetch_whale_signals()

    ranked = []
    for stock in data:
        symbol = stock.get("symbol")
        price = stock.get("price")
        market_cap = stock.get("marketCap")

        if price is None or market_cap is None:
            continue

        # Base score heuristic (normalize marketCap a bit)
        score = (market_cap / 1e9) ** 0.5 if market_cap else 0

        # Apply whale boost if available
        if symbol in whale_signals:
            score += whale_signals[symbol]["boost"]

        ranked.append({
            "symbol": symbol,
            "price": price,
            "marketCap": market_cap,
            "score": round(score, 3),
            "reason": whale_signals.get(symbol, {}).get("signal", "marketCap heuristic")
        })

    ranked = sorted(ranked, key=lambda x: x["score"], reverse=True)[:limit]

    with open(OUTPUT_PATH, "w") as f:
        json.dump({"ranked": ranked}, f, indent=2)

    print(f"✅ Ranked {len(ranked)} stocks with whale signals merged")
    return ranked


if __name__ == "__main__":
    try:
        top = int(sys.argv[sys.argv.index("--top") + 1]) if "--top" in sys.argv else 20
    except (ValueError, IndexError):
        top = 20

    rank_stocks(top)
