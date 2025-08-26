#!/usr/bin/env python3
# Emits a mock whale-driven recommendations file compatible with auto_trade.py
import json, time, random
from pathlib import Path

OUT = Path("data/gpt_recommendations.json")
CANDS = ["AAPL","MSFT","NVDA","AMZN","META","TSLA"]

def main():
    ranked = []
    for s in CANDS:
        size = random.uniform(0, 1)  # pretend whale size -> score
        ranked.append({"symbol": s, "score": round(0.5 + size/2, 3), "reason": f"mock_whale size={size:.2f}"})
    payload = {"as_of": int(time.time()), "method":"mock_whale", "top": ranked}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2))
    print(f"✅ Wrote {OUT.resolve()}")

if __name__ == "__main__":
    main()
