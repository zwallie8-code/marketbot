import os
import json
import openai
import pandas as pd

# Load API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Load stock data
with open("data/stocks.json", "r") as f:
    stocks = json.load(f)

def ask_gpt_for_ranking(stocks):
    # Convert stock data into a simple string for GPT
    stock_list = "\n".join([f"{s['symbol']}: {s['price']}" for s in stocks])

    prompt = f"""
    You are a financial analyst. Based on the following stock prices, rank the top 10 stocks to invest in today.
    Return the results in JSON format with keys: symbol, rank, and reasoning.

    Stock Data:
    {stock_list}
    """

    # Updated OpenAI API call
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful financial assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    reply = response.choices[0].message.content

    try:
        return json.loads(reply)
    except:
        # If GPT doesn't return clean JSON, wrap into one
        return {"error": "Invalid GPT response", "raw": reply}

def main():
    print("📈 Loading stock data...")
    print("🤖 Asking GPT for stock rankings...")

    recommendations = ask_gpt_for_ranking(stocks)

    # Save GPT recommendations
    os.makedirs("data", exist_ok=True)
    with open("data/gpt_recommendations.json", "w") as f:
        json.dump(recommendations, f, indent=2)

    print("✅ Saved GPT recommendations to data/gpt_recommendations.json")

if __name__ == "__main__":
    main()
