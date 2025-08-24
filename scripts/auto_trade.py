import os
import json
from scripts.broker_alpaca import BrokerAlpaca
from scripts.policy_engine import should_buy, calculate_position_size

RECOMMENDATIONS_FILE = "data/gpt_recommendations.json"

def main():
    # Load GPT stock recommendations
    if not os.path.exists(RECOMMENDATIONS_FILE):
        raise FileNotFoundError(f"Missing GPT recommendations file: {RECOMMENDATIONS_FILE}")

    with open(RECOMMENDATIONS_FILE, "r") as f:
        recommendations = json.load(f)

    # Initialize broker
    broker = BrokerAlpaca()
    broker.authenticate()
    balance = broker.get_balance()
    active_positions = broker.get_positions()

    # Process each recommended stock
    for stock in recommendations:
        ticker = stock["ticker"]
        price = stock["price"]
        confidence = stock["confidence"]

        print(f"Considering {ticker} | Price: {price} | Confidence: {confidence}")

        if should_buy(stock, active_positions):
            qty = calculate_position_size(balance, price)
            broker.place_order(ticker, qty, side="buy")
        else:
            print(f"Skipping {ticker} (low confidence or portfolio full)")

if __name__ == "__main__":
    main()
