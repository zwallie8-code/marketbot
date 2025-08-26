#!/usr/bin/env python3
import os
import json
from pathlib import Path
from typing import Dict

# ✅ FIX: Use absolute imports instead of relative ones for GitHub Actions
from scripts.broker_alpaca import BrokerAlpaca
from scripts.policy_engine import decide
from scripts.utils import safe_price

# Configurations
RECS_FILE = os.getenv("RECS_FILE", "data/gpt_recommendations.json")
EXIT_TH = float(os.getenv("EXIT_BELOW_CONFIDENCE", "0.5"))


def load_recommendations(path: str) -> Dict[str, float]:
    """Load GPT-based trading recommendations from JSON file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"❌ Missing recommendations file: {path}")

    with open(p, "r") as f:
        data = json.load(f)

    # Support multiple potential key formats
    rows = data.get("top") or data.get("ranked") or data
    norm = {}

    for r in rows:
        sym = r.get("symbol") or r.get("ticker")
        sc = r.get("score") or r.get("confidence")
        if sym:
            norm[sym] = float(sc) if sc is not None else None

    return norm


def main():
    print("📥 Loading GPT trading recommendations...")
    recs: Dict[str, float] = load_recommendations(RECS_FILE)

    if not recs:
        print("⚠️ No recommendations found. Exiting.")
        return

    # Initialize broker
    broker = BrokerAlpaca()
    broker.authenticate()

    cash = broker.get_cash()
    active = broker.get_positions()
    print(f"💵 Cash=${cash:.2f} | Active positions: {list(active.keys())}")

    # === EXIT POSITIONS BELOW THRESHOLD ===
    for sym in list(active.keys()):
        score = recs.get(sym)
        if score is None or score < EXIT_TH:
            print(f"🔻 Exiting {sym}: score={score} < threshold={EXIT_TH}")
            broker.market_sell_all(sym)

    # === ENTER NEW POSITIONS ===
    for sym, score in recs.items():
        price = safe_price(sym)
        if not price:
            print(f"⚠️ No price found for {sym}, skipping.")
            continue

        d = decide(sym, score, price, active, cash)
        if d.action == "buy" and d.qty > 0:
            print(f"🟢 Buying {sym} | Qty={d.qty} | Price=${price} | Score={score}")
            broker.market_buy_qty(
                sym,
                d.qty,
                bracket=True,
                entry_price=price,
                stop_loss_pct=d.stop_loss_pct,
                take_profit_pct=d.take_profit_pct,
            )
        else:
            print(f"{sym}: {d.action.upper()} ({d.reason})")


if __name__ == "__main__":
    main()
