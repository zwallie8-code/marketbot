import os
import alpaca_trade_api as tradeapi

class BrokerAlpaca:
    def __init__(self):
        self.api_key = os.getenv("ALPACA_API_KEY")
        self.secret_key = os.getenv("ALPACA_SECRET_KEY")
        self.base_url = "https://paper-api.alpaca.markets"  # Paper trading by default

        if not self.api_key or not self.secret_key:
            raise RuntimeError("Missing ALPACA_API_KEY/ALPACA_SECRET_KEY")

        self.api = tradeapi.REST(self.api_key, self.secret_key, self.base_url)

    def authenticate(self):
        account = self.api.get_account()
        print(f"✅ Connected to Alpaca | Cash Available: ${account.cash}")
