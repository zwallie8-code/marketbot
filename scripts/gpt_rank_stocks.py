import os
import json
import pandas as pd
import openai

# ---- CONFIG ----
STOCKS_FILE = "data/stocks.json"
GPT_OUTPUT_FILE = "data/gpt_recommendations.json"
CSV_OUTPUT = "output/ranked_stocks.csv"

# Load API key from environment
openai.api_key = os.getenv("OPENAI_API_KEY")

def load_stocks():
    """Load the stock dataset from JSON."""
    if not os.path.exists(STOCKS_FILE):
        raise FileNotFoundError(f"Missing file: {STOCKS_FILE}")
    with open(STOCKS_FILE, "r") as f:
        return json.load(f)

def ask_gpt_for_ranking(stocks):
    """Ask GPT to rank stocks based on fundamentals, sentiment, and growth potential."""
    # Prepare stock symbols for context
    stock_symbols = [s.get("symbol") for s in stocks[:50]]  # Limit to 50 to avoid token limits

    prompt = f"""
    You are a financial analyst. Here is a list of stock symbols:
    {', '.join(stock_symbols)}

    Rank these stocks based on:
    - Growth potential
    - Stability and fundamentals
    - Market sentiment
    - Risk vs reward

    Return ONLY a valid JSON array where each element has:
    {{
        "symbol": "AAPL",
        "score": 92,
        "reason": "Strong growth potential, strong earnings, and solid fundamentals."
    }}
    """

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "You are a financial analyst."},
                  {"role": "user", "content": prompt}],
        temperature=0.3,
    )

    try:
        recommendations = json.loads(response["choices"][0]["message"]["content"])
    except json.JSONDecodeError:
        raise ValueError("GPT did not return valid JSON. Check the API response.")
    
    return recommendations

def save_rankings(recommendations):
    """Save GPT recommendations to JSON and CSV."""
    # Save JSON
    os.makedirs(os.path.dirname(GPT_OUTPUT_FILE), exist_ok=True)
    with open(GPT_OUTPUT_FILE, "w") as f:
        json.dump(recommendations, f, indent=4)

    # Convert to CSV
    df = pd.DataFrame(recommendations)
    os.makedirs(os.path.dirname(CSV_OUTPUT), exist_ok=True)
    df.to_csv(CSV_OUTPUT, index=False)
    print(f"Rankings saved to {CSV_OUTPUT}")

def main():
    print("🔄 Loading stock data...")
    stocks = load_stocks()

    print("🤖 Asking GPT for stock rankings...")
    recommendations = ask_gpt_for_ranking(stocks)

    print("💾 Saving results...")
    save_rankings(recommendations)

    print("✅ Done! Rankings generated successfully.")

if __name__ == "__main__":
    main()

