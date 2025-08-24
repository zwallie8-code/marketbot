#!/usr/bin/env python3
import os, json, argparse, sys
from pathlib import Path
import pandas as pd
from openai import OpenAI

def die(msg, code=1):
    print(f"ERROR: {msg}", file=sys.stderr); sys.exit(code)

def load_universe(path):
    if not Path(path).exists():
        die(f"input file not found: {path}")
    with open(path, "r") as f:
        data = json.load(f)
    # accept either {"rows":[...]} or just [...]
    return data["rows"] if isinstance(data, dict) and "rows" in data else data

def build_prompt(rows, top_n):
    # keep the payload light for the model
    cols = ["symbol","return_1d","change_1d","volume","close"]
    slim = []
    for r in rows:
        slim.append({k: r.get(k) for k in cols})
    return f"""
You are a quantitative assistant. Rank US tickers using momentum (return_1d / change_1d) with basic liquidity/price sanity (prefer higher volume, avoid sub-$1).
Input (JSON list of objects with symbol, return_1d, change_1d, volume, close):
{json.dumps(slim)[:120000]}  # truncated if huge

Return STRICT JSON only:
{{
  "as_of": "<UTC ISO8601>",
  "method": "momentum_v1",
  "top": [
    {{"symbol": "TICK", "score": <float>, "reason": "<short reason>"}}
  ]
}}
Include at most {top_n} items in "top".
"""

def call_gpt(prompt, model="gpt-4o-mini"):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    if not client.api_key:
        die("OPENAI_API_KEY is not set in the environment")
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role":"system","content":"You output only valid JSON. No prose."},
            {"role":"user","content":prompt}
        ],
        temperature=0.2
    )
    return resp.choices[0].message.content.strip()

def parse_json_strict(txt):
    # try to locate first/last brace in case model adds whitespace
    start = txt.find("{"); end = txt.rfind("}")
    if start == -1 or end == -1:
        die("Model did not return JSON.")
    return json.loads(txt[start:end+1])

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="data/stocks.json")
    p.add_argument("--out-json", default="data/gpt_recommendations.json")
    p.add_argument("--out-csv", default="output/ranked_stocks.csv")
    p.add_argument("--top", type=int, default=50)
    args = p.parse_args()

    Path("output").mkdir(parents=True, exist_ok=True)
    rows = load_universe(args.input)
    if not rows:
        die("input universe is empty")

    print("📥 Loading stock data...")
    prompt = build_prompt(rows, args.top)
    print("🤖 Asking GPT for stock rankings...")
    txt = call_gpt(prompt)
    payload = parse_json_strict(txt)

    # Save JSON
    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_json, "w") as f:
        json.dump(payload, f, indent=2)

    # CSV for artifact
    df = pd.DataFrame(payload.get("top", []))
    if "rank" not in df.columns:
        df.insert(0, "rank", range(1, len(df)+1))
    df.to_csv(args.out_csv, index=False)

    print(f"✅ Wrote: {args.out_json}")
    print(f"✅ Wrote: {args.out_csv}")

if __name__ == "__main__":
    main()
