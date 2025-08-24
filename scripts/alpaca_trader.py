import os
import json
import alpaca_trade_api as tradeapi

# Load credentials from environment variables (GitHub Secrets)
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_API_SECRET = os.getenv("ALPACA_API_SECRET")
ALPACA_ENDPOINT = os.getenv("ALPACA_ENDPOINT", "https://paper-api.alpaca.markets")

# Initialize Alpaca API client
api = tradeapi.REST(ALPACA_API_KEY, ALPACA_API_SECRET, ALPACA_ENDPOINT)

def get_recommendations():
    """Read GPT stock recommendations from JSON"""
    try:
        with open("data/gpt_recommendations.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print("⚠️ No GPT recommendations found.")
        return []

def execute_trades():
    """Place buy/sell trades based on GPT recommendations"""
    recommendations = get_recommendations()

    if not recommendations:
        print("No recommendations available. Exiting...")
        return

    for stock in recommendations:
        symbol = stock.get("symbol")
        action = stock.get("action")
        qty = stock.get("quantity", 1)  # Default to 1 share if missing

        try:
            if action.lower() == "buy":
                api.submit_order(
                    symbol=symbol,
                    qty=qty,
                    side="buy",
                    type="market",
                    time_in_force="gtc"
                )
                print(f"✅ Placed BUY order for {qty} shares of {symbol}")
            elif action.lower() == "sell":
                api.submit_order(
                    symbol=symbol,
                    qty=qty,
                    side="sell",
                    type="market",
                    time_in_force="gtc"
                )
                print(f"✅ Placed SELL order for {qty} shares of {symbol}")
            else:
                print(f"⚠️ Skipping {symbol} — Unknown action: {action}")
        except Exception as e:
            print(f"❌ Error trading {symbol}: {e}")

if __name__ == "__main__":
    execute_trades()
