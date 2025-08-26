import json
import os
import alpaca_trade_api as tradeapi
from pathlib import Path

DATA_PATH = Path("data/stocks.json")

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
BASE_URL = "https://paper-api.alpaca.markets"

def paper_trade():
    with open(DATA_PATH, "r") as f:
        stocks = json.load(f)

    top_picks = sorted(stocks.items(), key=lambda x: x[1].get("marketCap", 0), reverse=True)[:5]
    api = tradeapi.REST(API_KEY, SECRET_KEY, BASE_URL, api_version="v2")

    for ticker, info in top_picks:
        try:
            api.submit_order(
                symbol=ticker,
                qty=1,
                side="buy",
                type="market",
                time_in_force="gtc"
            )
            print(f"✅ Paper traded: Bought 1 share of {ticker}")
        except Exception as e:
            print(f"❌ Failed to trade {ticker}: {e}")

if __name__ == "__main__":
    paper_trade()
