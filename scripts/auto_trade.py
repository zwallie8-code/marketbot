#!/usr/bin/env python3
"""
Autonomous trading loop:
- loads merged recommendations (data/merged_recommendations.json)
- exits positions that no longer meet threshold or have whale_sell signals
- enters new positions according to risk policy
"""

import os
import json
from pathlib import Path
from typing import Dict, Any

# ✅ Use merged file as default
RECS_FILE = os.getenv("RECS_FILE", "data/merged_recommendations.json")
RECS_PATH = Path(RECS_FILE)

# ----- Config -----
try:
    from scripts.config import (
        MAX_PORTFOLIO_SIZE, MAX_POSITION_USD, MIN_CONFIDENCE,
        EXIT_BELOW_CONFIDENCE, STOP_LOSS_PCT, TAKE_PROFIT_PCT, DRY_RUN
    )
except Exception:
    MAX_PORTFOLIO_SIZE = int(os.getenv("MAX_PORTFOLIO_SIZE", "5"))
    MAX_POSITION_USD = float(os.getenv("MAX_POSITION_USD", "1000"))
    MIN_CONFIDENCE = float(os.getenv("MIN_CONFIDENCE", "0.7"))
    EXIT_BELOW_CONFIDENCE = float(os.getenv("EXIT_BELOW_CONFIDENCE", "0.5"))
    STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", "0.05"))
    TAKE_PROFIT_PCT = float(os.getenv("TAKE_PROFIT_PCT", "0.10"))
    DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

# ----- Broker -----
try:
    from scripts.broker_alpaca import BrokerAlpaca
except Exception as e:
    raise RuntimeError(f"Failed to import BrokerAlpaca: {e}")


def load_recommendations(path: Path) -> Dict[str, Dict[str, Any]]:
    """Load recommendations JSON and normalize to {SYMBOL: {score, signal, meta}}"""
    if not path.exists():
        raise FileNotFoundError(f"Recommendations file not found: {path}")

    with open(path, "r") as f:
        raw = json.load(f)

    items = None
    if isinstance(raw, dict):
        items = raw.get("ranked") or raw.get("top") or raw.get("data") or raw.get("recommendations")
    if items is None and isinstance(raw, list):
        items = raw

    if not items:
        raise ValueError("No valid recommendations found in file")

    normalized: Dict[str, Dict[str, Any]] = {}
    for entry in items:
        if not isinstance(entry, dict):
            continue
        sym = entry.get("symbol") or entry.get("ticker")
        if not sym:
            continue
        score = None
        try:
            score = float(entry.get("score")) if entry.get("score") is not None else None
        except Exception:
            pass
        signal = entry.get("signal") or entry.get("reason") or ""
        normalized[sym.upper()] = {"score": score, "signal": signal, "meta": entry}
    return normalized


def get_cash_from_broker(broker) -> float:
    try:
        return float(broker.get_cash())
    except Exception:
        try:
            acct = broker.api.get_account()  # type: ignore
            return float(getattr(acct, "cash", 0.0))
        except Exception:
            return 0.0


def get_active_positions(broker) -> Dict[str, Any]:
    try:
        positions = broker.get_positions()
        return {p.symbol: p for p in positions} if isinstance(positions, list) else positions or {}
    except Exception:
        return {}


def position_qty_from_cash(cash: float, price: float) -> int:
    if price <= 0:
        return 0
    usd_alloc = min(cash, MAX_POSITION_USD)
    qty = int(usd_alloc // price)
    return max(qty, 0)


def main():
    print(f"📥 Loading recommendations from {RECS_FILE}...")
    try:
        recs = load_recommendations(RECS_PATH)
    except Exception as e:
        print(f"❌ Failed to load recommendations: {e}")
        return
    if not recs:
        print("❌ No recommendations found. Exiting.")
        return

    broker = BrokerAlpaca()
    try:
        broker.authenticate()
    except Exception as e:
        print(f"❌ Broker authentication failed: {e}")
        return

    cash = get_cash_from_broker(broker)
    active = get_active_positions(broker)
    print(f"💵 Cash=${cash:.2f} | Active positions={list(active.keys())}")

    # --- EXIT LOOP ---
    for sym, pos in list(active.items()):
        rec = recs.get(sym.upper())
        score = rec["score"] if rec else None
        signal = rec["signal"] if rec else ""
        exit_reason = None

        if "sell" in signal.lower():
            exit_reason = f"signal={signal}"
        elif score is None or score < EXIT_BELOW_CONFIDENCE:
            exit_reason = f"score={score}"

        if exit_reason:
            print(f"🔻 Exiting {sym} ({exit_reason})")
            try:
                broker.market_sell_all(sym)
            except Exception as e:
                print(f"⚠️ Sell failed for {sym}: {e}")
        else:
            print(f"✓ Holding {sym} (score={score}, signal={signal})")

    # --- ENTRY LOOP ---
    cash = get_cash_from_broker(broker)
    active = get_active_positions(broker)
    active_syms = {s.upper() for s in active.keys()}

    candidates = sorted(
        [(sym, info["score"] or 0, info) for sym, info in recs.items()],
        key=lambda x: x[1],
        reverse=True,
    )

    for sym, score, info in candidates:
        if sym in active_syms:
            continue
        if score is None or score < MIN_CONFIDENCE:
            if "whale_buy" not in (info.get("signal") or "").lower():
                continue
        price = info.get("meta", {}).get("price")
        if not price:
            continue
        qty = position_qty_from_cash(cash, price)
        if qty <= 0 or len(active_syms) >= MAX_PORTFOLIO_SIZE:
            continue

        print(f"🟢 Buying {sym} | qty={qty} | price=${price:.2f} | score={score}")
        try:
            broker.market_buy_qty(
                sym,
                qty,
                bracket=True,
                entry_price=price,
                stop_loss_pct=STOP_LOSS_PCT,
                take_profit_pct=TAKE_PROFIT_PCT,
            )
            cash -= qty * price
            active_syms.add(sym)
        except Exception as e:
            print(f"⚠️ Failed to buy {sym}: {e}")

    print("✅ Trading pass complete.")


if __name__ == "__main__":
    main()
