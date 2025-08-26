from __future__ import annotations
from dataclasses import dataclass
from typing import Dict
from .config import (
    MAX_PORTFOLIO_SIZE, MAX_POSITION_USD,
    MIN_CONFIDENCE, EXIT_BELOW_CONFIDENCE,
    STOP_LOSS_PCT, TAKE_PROFIT_PCT
)

@dataclass
class Decision:
    action: str          # 'buy' | 'hold' | 'exit' | 'skip'
    qty: int = 0
    stop_loss_pct: float = STOP_LOSS_PCT
    take_profit_pct: float = TAKE_PROFIT_PCT
    reason: str = ""

def should_enter(score: float) -> bool:
    return score is not None and score >= MIN_CONFIDENCE

def should_exit(score: float) -> bool:
    return score is None or score < EXIT_BELOW_CONFIDENCE

def position_size(cash: float, price: float) -> int:
    usd_alloc = min(cash / 10.0, MAX_POSITION_USD)
    return max(int(usd_alloc // price), 1)

def decide(ticker: str, score: float, price: float, active_positions: Dict[str, object], cash: float) -> Decision:
    if ticker in active_positions:
        if should_exit(score):
            return Decision(action="exit", reason=f"score {score} < exit_th={EXIT_BELOW_CONFIDENCE}")
        else:
            return Decision(action="hold", reason="already holding")
    else:
        if len(active_positions) >= MAX_PORTFOLIO_SIZE:
            return Decision(action="skip", reason=f"portfolio full ({len(active_positions)}/{MAX_PORTFOLIO_SIZE})")
        if should_enter(score):
            qty = position_size(cash, price)
            return Decision(action="buy", qty=qty, reason=f"enter score {score} >= {MIN_CONFIDENCE}")
        else:
            return Decision(action="skip", reason=f"score {score} < enter_th={MIN_CONFIDENCE}")
