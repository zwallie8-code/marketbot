import os
import alpaca_trade_api as tradeapi

class BrokerAlpaca:
    def __init__(self):
        self.api_key = os.getenv("ALPACA_API_KEY")
        self.secret_key = os.getenv("ALPACA_SECRET_KEY")
        self.base_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

        if not self.api_key or not self.secret_key:
            raise RuntimeError(
                f"Missing Alpaca keys. "
                f"ALPACA_API_KEY={'SET' if self.api_key else 'MISSING'}, "
                f"ALPACA_SECRET_KEY={'SET' if self.secret_key else 'MISSING'}"
            )

        # Initialize Alpaca API client
        self.api = tradeapi.REST(self.api_key, self.secret_key, self.base_url, api_version="v2")

    def authenticate(self):
        """Verify connection and print account cash."""
        account = self.api.get_account()
        print(f"✅ Connected to Alpaca | Cash Available: ${account.cash}")

    def get_cash(self) -> float:
        """Return available cash balance as float."""
        account = self.api.get_account()
        return float(account.cash)

    def get_positions(self) -> dict:
        """Return open positions as {symbol: qty}."""
        positions = self.api.list_positions()
        return {p.symbol: float(p.qty) for p in positions}

    def market_buy_qty(self, symbol: str, qty: float):
        """Place a market buy order for given quantity."""
        return self.api.submit_order(
            symbol=symbol,
            qty=qty,
            side="buy",
            type="market",
            time_in_force="gtc"
        )

    def market_sell_all(self, symbol: str):
        """Sell all shares of a given symbol (if any)."""
        positions = self.get_positions()
        qty = positions.get(symbol)
        if qty:
            return self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side="sell",
                type="market",
                time_in_force="gtc"
            )
        else:
            print(f"⚠️ No open position for {symbol}")
            return None
