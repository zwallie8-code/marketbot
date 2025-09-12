#!/usr/bin/env python3
import os
import json
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

WHALES_FILE = "data/whales.json"
OUTPUT_FILE = "data/gpt_recommendations.json"

def load_whales():
    if not os.path.exists(WHALES_FILE):
        print("❌ whales.json not found. Run fetch_whales.py first.")
        return []
    with open(WHALES_FILE, "r") as f:
        return json.load(f)

def analyze_with_gpt(whales):
    """Send whale trades to GPT and get ranked signals."""
    prompt = f"""
You are a crypto trading AI. Analyze whale trades and assign confidence scores
between 0.0 and 1.0 for BUY signals only. Higher = stronger conviction.

Trades:
{json.dumps(whales[:20], indent=2)}

Return JSON array with objects:
[{{"symbol": "XXX", "score": 0.85, "reason": "Whales aggressively buying"}}]
    """

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    try:
        return json.loads(response.choices[0].message["content"])
    except Exception:
        print("⚠️ GPT output parse error")
        return []

def save_recommendations(recs):
    with open(OUTPUT_FILE, "w") as f:
        json.dump(recs, f, indent=2)
    print(f"✅ Saved GPT recommendations → {OUTPUT_FILE}")

def main():
    whales = load_whales()
    if not whales:
        return
    recs = analyze_with_gpt(whales)
    if recs:
        save_recommendations(recs)

if __name__ == "__main__":
    main()
