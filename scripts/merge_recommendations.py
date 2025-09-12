#!/usr/bin/env python3
import json
from pathlib import Path

FILES = [
    "data/gpt_recommendations.json",   # stock/crypto rankings
    "data/whale_recs.json",            # whale trades (adjust if different)
]
OUT = "data/merged_recommendations.json"

def load_json(path: str):
    p = Path(path)
    if not p.exists():
        print(f"⚠️ Missing file: {path}")
        return []
    try:
        with open(p, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Could not load {path}: {e}")
        return []

def main():
    merged = []
    for f in FILES:
        data = load_json(f)
        if isinstance(data, dict) and "ranked" in data:
            merged.extend(data["ranked"])
        elif isinstance(data, dict) and "top" in data:
            merged.extend(data["top"])
        elif isinstance(data, list):
            merged.extend(data)

    if not merged:
        print("❌ No recommendations found to merge")
        return

    # remove duplicates by symbol (keep highest score)
    by_symbol = {}
    for rec in merged:
        sym = rec.get("symbol") or rec.get("ticker")
        score = rec.get("score") or rec.get("confidence") or 0
        if not sym:
            continue
        if sym not in by_symbol or score > by_symbol[sym]["score"]:
            by_symbol[sym] = {"symbol": sym, "score": score}

    final = list(by_symbol.values())
    with open(OUT, "w") as f:
        json.dump(final, f, indent=2)

    print(f"✅ Merged {len(final)} unique recommendations → {OUT}")

if __name__ == "__main__":
    main()
