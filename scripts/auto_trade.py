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
    from config import (
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
    from broker_alpaca import BrokerAlpaca
except Exception as e:
    raise RuntimeError(f"Failed to import BrokerAlpaca: {e}")
