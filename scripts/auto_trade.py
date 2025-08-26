#!/usr/bin/env python3
import os, json
from pathlib import Path
from typing import Dict
from .broker_alpaca import BrokerAlpaca
from .policy_engine import decide
from .utils import safe_price

RECS_FILE = os.getenv("RECS_FILE", "data/gpt_recommendations.json")
EXIT_TH = float(os.getenv("EXIT_BELOW_CONFIDENCE", "0.5"))

def load_recommendations(path: str):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Missing recommendations file: {path}")
    with open(p, "r") as f:
        data = json.load(f)
    rows = data.get("top") or data.get("ranked") or data
    norm = {}
    for r in rows:
        sym = r.get("symbol") or r.get("ticker")
        sc  = r.get("score") or r.get("confidence")
        if sym:
            norm[sym] = float(sc) if sc is not None else None
    return norm

def main():
    print("📥 Loading recommendations...")
    recs: Dict[str, float] = load_recommendations(RECS_FILE)
    if not recs:
        print("No recommendations found. Exiting."); return

    broker = BrokerAlpaca()
    broker.authenticate()
    cash = broker.get_cash()
    active = broker.get_positions()
    print(f"💵 Cash=${cash:.2f} | Active positions: {list(active.keys())}")

    # Exit positions no longer meeting threshold
    for sym in list(active.keys()):
        score = recs.get(sym)
        if score is None or score < EXIT_TH:
            print(f"→ Exiting {sym}: score={score} < {EXIT_TH}")
            broker.market_sell_all(sym)

    # Enter new positions
    for sym, score in recs.items():
        price = safe_price(sym)
        if not price:
            print(f"⚠️ No price for {sym}, skipping."); continue
        d = decide(sym, score, price, active, cash)
        if d.action == "buy" and d.qty > 0:
            broker.market_buy_qty(
                sym, d.qty, bracket=True, entry_price=price,
                stop_loss_pct=d.stop_loss_pct, take_profit_pct=d.take_profit_pct
            )
        else:
            print(f"{sym}: {d.action} ({d.reason})")

if __name__ == "__main__":
    main()
