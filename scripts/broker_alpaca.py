import os
import alpaca_trade_api as tradeapi

class BrokerAlpaca:
    def __init__(self):
        self.api_key = os.getenv("ALPACA_API_KEY")
        self.secret_key = os.getenv("ALPACA_SECRET_KEY")
        self.base_url = "https://paper-api.alpaca.markets"  # switch to live if ready

        if not self.api_key or not self.secret_key:
            raise RuntimeError(
                f"Missing Alpaca keys. ALPACA_API_KEY={'SET' if self.api_key else 'MISSING'}, "
                f"ALPACA_SECRET_KEY={'SET' if self.secret_key else 'MISSING'}"
            )

        self.api = tradeapi.REST(self.api_key, self.secret_key, self.base_url)

    def authenticate(self):
        account = self.api.get_account()
        print(f"✅ Connected to Alpaca | Cash=${account.cash} | Buying power=${account.buying_power}")
        return account

    def get_cash(self) -> float:
        return float(self.api.get_account().cash)

    def get_positions(self):
        positions = self.api.list_positions()
        return {p.symbol: p for p in positions}

    def market_buy_qty(self, symbol: str, qty: int, bracket=True, entry_price=None,
                       stop_loss_pct=0.05, take_profit_pct=0.1):
        print(f"🟢 Submitting BUY order: {symbol} qty={qty}")
        if bracket and entry_price:
            stop_loss = round(entry_price * (1 - stop_loss_pct), 2)
            take_profit = round(entry_price * (1 + take_profit_pct), 2)
            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side="buy",
                type="market",
                time_in_force="gtc",
                order_class="bracket",
                stop_loss={"stop_price": stop_loss},
                take_profit={"limit_price": take_profit}
            )
        else:
            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side="buy",
                type="market",
                time_in_force="gtc"
            )
        return order

    def market_sell_all(self, symbol: str):
        pos = self.api.get_position(symbol)
        if not pos or float(pos.qty) == 0:
            print(f"⚠️ No active position in {symbol}")
            return
        qty = abs(int(float(pos.qty)))
        print(f"🔻 Submitting SELL order: {symbol} qty={qty}")
        return self.api.submit_order(
            symbol=symbol,
            qty=qty,
            side="sell",
            type="market",
            time_in_force="gtc"
        )
