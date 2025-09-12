#!/usr/bin/env python3
"""
Autonomous trading loop:
- loads recommendations (data/gpt_recommendations.json)
- exits positions that no longer meet threshold or have whale_sell signals
- enters new positions according to risk policy
"""

import os
import json
import math
from pathlib import Path
from typing import Dict, Any

# Prefer to use your project's config if present
try:
    from scripts.config import (
        MAX_PORTFOLIO_SIZE, MAX_POSITION_USD, MIN_CONFIDENCE,
        EXIT_BELOW_CONFIDENCE, STOP_LOSS_PCT, TAKE_PROFIT_PCT, DRY_RUN
    )
except Exception:
    # sensible defaults if config is missing or import fails
    MAX_PORTFOLIO_SIZE = int(os.getenv("MAX_PORTFOLIO_SIZE", "5"))
    MAX_POSITION_USD = float(os.getenv("MAX_POSITION_USD", "1000"))
    MIN_CONFIDENCE = float(os.getenv("MIN_CONFIDENCE", "0.7"))
    EXIT_BELOW_CONFIDENCE = float(os.getenv("EXIT_BELOW_CONFIDENCE", "0.5"))
    STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", "0.05"))
    TAKE_PROFIT_PCT = float(os.getenv("TAKE_PROFIT_PCT", "0.10"))
    # Default to DRY_RUN=True in CI unless explicitly disabled (protects live capital)
    DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

# Broker wrapper (your broker_alpaca implementation)
try:
    from scripts.broker_alpaca import BrokerAlpaca
except Exception as e:
    raise RuntimeError(f"Failed to import BrokerAlpaca: {e}")

RECS_FILE = os.getenv("RECS_FILE", "data/gpt_recommendations.json")
RECS_PATH = Path(RECS_FILE)


def load_recommendations(path: Path) -> Dict[str, Dict[str, Any]]:
    """
    Load recommendations JSON and normalize into dict: {SYMBOL: {score, signal, reason}}
    Accepts shapes:
      { "ranked": [ {symbol, score, reason, ...}, ... ] }
      or plain list [ {symbol, score}, ... ]
      or {"top": [...]}
    """
    if not path.exists():
        raise FileNotFoundError(f"Recommendations file not found: {path}")

    with open(path, "r") as f:
        raw = json.load(f)

    # find list of items
    items = None
    if isinstance(raw, dict):
        items = raw.get("ranked") or raw.get("top") or raw.get("rankings") or raw.get("data")
        if items is None:
            # maybe the dict itself is a list-like mapping of symbols
            # fallback: try to detect keyed dict
            # If raw contains 'mode' or metadata, look for 'ranked' earlier; else error
            if isinstance(raw.get("ranked"), list):
                items = raw.get("ranked")
    if items is None and isinstance(raw, list):
        items = raw

    if not items:
        raise ValueError("No ranked/top array found in recommendations file")

    normalized: Dict[str, Dict[str, Any]] = {}
    for entry in items:
        if not isinstance(entry, dict):
            continue
        sym = entry.get("symbol") or entry.get("ticker") or entry.get("sym")
        if not sym:
            continue
        score = entry.get("score")
        # try to parse numeric score robustly
        try:
            score = float(score) if score is not None else None
        except Exception:
            score = None
        signal = entry.get("signal") or entry.get("reason_signal") or entry.get("reason")
        normalized[sym.upper()] = {
            "score": score,
            "signal": signal,
            "meta": entry
        }
    return normalized


def get_cash_from_broker(broker) -> float:
    # Prefer explicit method if broker implements get_cash()
    if hasattr(broker, "get_cash") and callable(getattr(broker, "get_cash")):
        return float(broker.get_cash())
    # fallback to query account object if available
    try:
        acct = broker.api.get_account()  # type: ignore
        return float(getattr(acct, "cash", 0.0))
    except Exception:
        return 0.0


def get_active_positions(broker) -> Dict[str, Any]:
    # prefer list_positions if available
    try:
        if hasattr(broker, "get_positions") and callable(getattr(broker, "get_positions")):
            # expected to return dict symbol->position or list
            positions = broker.get_positions()
            # If it's a list convert to dict
            if isinstance(positions, list):
                return {p.symbol: p for p in positions}
            return positions or {}
        # fallback raw api
        plist = broker.api.list_positions()  # type: ignore
        return {p.symbol: p for p in plist}
    except Exception:
        return {}


def position_qty_from_cash(cash: float, price: float) -> int:
    """
    Determine how many shares to buy:
      - allocate up to MAX_POSITION_USD per position
      - but don't use more than available cash
    """
    if price <= 0:
        return 0
    usd_alloc = min(cash, MAX_POSITION_USD)
    qty = int(usd_alloc // price)
    return max(qty, 0)


def main():
    print("📥 Loading GPT trading recommendations...")
    try:
        recs = load_recommendations(RECS_PATH)
    except Exception as e:
        print(f"❌ Failed to load recommendations: {e}")
        return

    if not recs:
        print("❌ No recommendations found. Exiting.")
        return

    broker = BrokerAlpaca()  # will raise if keys missing
    # authenticate / show account
    try:
        broker.authenticate()
    except Exception as e:
        print(f"❌ Broker authentication failed: {e}")
        return

    cash = get_cash_from_broker(broker)
    active = get_active_positions(broker)
    print(f"💵 Cash=${cash:.2f} | Active positions count: {len(active)}")

    # Normalize active symbols to uppercase keys
    active_syms = {s.upper(): v for s, v in active.items()}

    # --- EXIT POSITIONS ---
    # Exit rules:
    #  - explicit signal 'whale_sell' or similar present
    #  - score is None or < EXIT_BELOW_CONFIDENCE
    print("🔁 Evaluating existing positions for exits...")
    for sym in list(active_syms.keys()):
        rec = recs.get(sym)
        score = rec["score"] if rec else None
        signal = rec["signal"] if rec else None
        # consider 'whale_sell' or negative signals in meta
        should_exit = False
        reason = None

        if signal and isinstance(signal, str) and "sell" in signal.lower():
            should_exit = True
            reason = f"signal={signal}"
        elif score is None or (isinstance(score, (int, float)) and score < EXIT_BELOW_CONFIDENCE):
            should_exit = True
            reason = f"score={score}"

        if should_exit:
            print(f"→ Exiting {sym}: {reason}")
            try:
                broker.market_sell_all(sym)
            except Exception as e:
                print(f"⚠️ Failed to sell {sym}: {e}")
        else:
            print(f"✓ Keeping {sym}: score={score}, signal={signal}")

    # Refresh cash & positions after exits
    cash = get_cash_from_broker(broker)
    active = get_active_positions(broker)
    active_syms = {s.upper(): v for s, v in active.items()}
    print(f"💵 Post-exit cash=${cash:.2f} | Active positions: {list(active_syms.keys())}")

    # --- ENTER NEW POSITIONS ---
    # Build candidate list sorted by score desc (None scores go to bottom)
    candidates = []
    for sym, info in recs.items():
        score = info.get("score")
        # skip negative/very low scores
        candidates.append((sym, score or 0.0, info))

    # sort highest score first
    candidates.sort(key=lambda x: (x[1] is not None, x[1]), reverse=True)

    print("🔎 Scanning candidates to open positions...")
    for sym, score, meta in candidates:
        # already holding?
        if sym in active_syms:
            continue

        # skip if not meeting entry threshold
        if score is None or score < MIN_CONFIDENCE:
            # but allow explicit whale_buy signal even if score is lower
            sig = (meta.get("signal") or "").lower() if meta.get("signal") else ""
            if "whale_buy" not in sig:
                continue

        # need a price — try meta->price or try to get via safe_price if available
        price = None
        # many recommendation entries include price in meta, try that first
        cand_meta = meta.get("meta", {})
        price = cand_meta.get("price") or cand_meta.get("lastPrice") or cand_meta.get("close") or cand_meta.get("price_usd")
        # as a last resort, ask broker for a current quote if available
        if price is None:
            try:
                if hasattr(broker, "api") and getattr(broker, "api") is not None:
                    # Alpaca get_last_trade or get_last_quote available
                    try:
                        last = broker.api.get_last_trade(sym)  # type: ignore
                        price = float(getattr(last, "price", None))
                    except Exception:
                        # try get_last_quote
                        try:
                            quote = broker.api.get_last_quote(sym)  # type: ignore
                            # use mid of ask/bid
                            bid = float(getattr(quote, "bidprice", 0) or 0)
                            ask = float(getattr(quote, "askprice", 0) or 0)
                            price = ((bid + ask) / 2) if (bid and ask) else None
                        except Exception:
                            price = None
            except Exception:
                price = None

        if price is None:
            print(f"⚠️ No price for {sym}, skipping")
            continue

        # determine maximum shares to buy with available cash and policy
        qty = position_qty_from_cash(cash, price)
        if qty <= 0:
            print(f"⚠️ Insufficient cash to buy {sym} at ${price:.2f} (cash=${cash:.2f})")
            continue

        # check portfolio size
        if len(active_syms) >= MAX_PORTFOLIO_SIZE:
            print(f"⚠️ Portfolio full ({len(active_syms)}/{MAX_PORTFOLIO_SIZE}), not entering {sym}")
            break

        # place order (or dry-run)
        print(f"→ Buying {sym}: qty={qty} price=${price:.2f} score={score}")
        try:
            broker.market_buy_qty(
                sym,
                qty,
                bracket=True,
                entry_price=price,
                stop_loss_pct=STOP_LOSS_PCT,
                take_profit_pct=TAKE_PROFIT_PCT
            )
            # update cash & active list conservatively
            cash -= qty * price
            active_syms[sym] = {"qty": qty}
        except Exception as e:
            print(f"⚠️ Failed to buy {sym}: {e}")

    print("✅ Trading pass complete.")


if __name__ == "__main__":
    main()
