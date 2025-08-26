from __future__ import annotations
from typing import Optional
import alpaca_trade_api as tradeapi
from .config import ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL, DRY_RUN

class BrokerAlpaca:
    def __init__(self):
        self.api: Optional[tradeapi.REST] = None

    def authenticate(self):
        if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
            raise RuntimeError("Missing ALPACA_API_KEY/ALPACA_SECRET_KEY")
        self.api = tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL)
        acct = self.api.get_account()
        print(f"[Alpaca] Auth ok. Equity=${acct.equity}, BP=${acct.buying_power}")

    def get_positions(self):
        return {p.symbol: p for p in self.api.list_positions()} if self.api else {}

    def get_cash(self) -> float:
        return float(self.api.get_account().cash)

    def market_buy_qty(self, symbol: str, qty: int, bracket: bool = True, entry_price: float | None = None,
                       stop_loss_pct: float = 0.05, take_profit_pct: float = 0.10):
        if DRY_RUN:
            print(f"[DRY-RUN] BUY {qty} {symbol} bracket={bracket}")
            return None
        if bracket and entry_price:
            stop_price = round(entry_price * (1 - stop_loss_pct), 2)
            tp_price   = round(entry_price * (1 + take_profit_pct), 2)
            order = self.api.submit_order(
                symbol=symbol, qty=qty, side="buy", type="market", time_in_force="gtc",
                order_class="bracket",
                take_profit={"limit_price": tp_price},
                stop_loss={"stop_price": stop_price},
            )
        else:
            order = self.api.submit_order(symbol=symbol, qty=qty, side="buy", type="market", time_in_force="gtc")
        print(f"[Alpaca] BUY {qty} {symbol}")
        return order

    def market_sell_all(self, symbol: str):
        if DRY_RUN:
            print(f"[DRY-RUN] SELL-ALL {symbol}")
            return None
        try:
            pos = self.api.get_position(symbol)
            qty = pos.qty
        except Exception:
            print(f"[Alpaca] No position for {symbol}")
            return None
        order = self.api.submit_order(symbol=symbol, qty=qty, side="sell", type="market", time_in_force="gtc")
        print(f"[Alpaca] SELL {qty} {symbol}")
        return order
