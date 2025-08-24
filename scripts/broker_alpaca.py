import os
import alpaca_trade_api as tradeapi

class BrokerAlpaca:
    def __init__(self):
        self.api_key = os.getenv("BROKER_KEY")
        self.api_secret = os.getenv("BROKER_SECRET")
        self.base_url = "https://paper-api.alpaca.markets"
        self.api = None

    def authenticate(self):
        self.api = tradeapi.REST(self.api_key, self.api_secret, self.base_url)
        try:
            account = self.api.get_account()
            print(f"[Alpaca] Authenticated. Buying power: {account.buying_power}")
        except Exception as e:
            raise RuntimeError(f"Authentication failed: {e}")

    def get_positions(self):
        return self.api.list_positions()

    def get_balance(self):
        return float(self.api.get_account().cash)

    def place_order(self, ticker: str, qty: int, side: str = "buy"):
        try:
            order = self.api.submit_order(
                symbol=ticker,
                qty=qty,
                side=side,
                type="market",
                time_in_force="gtc"
            )
            print(f"[Alpaca] Placed {side} order: {qty} x {ticker}")
            return order
        except Exception as e:
            print(f"[Alpaca] Order failed for {ticker}: {e}")
            return None

    def cancel_order(self, order_id: str):
        try:
            self.api.cancel_order(order_id)
            print(f"[Alpaca] Canceled order {order_id}")
        except Exception as e:
            print(f"[Alpaca] Failed to cancel order {order_id}: {e}")
