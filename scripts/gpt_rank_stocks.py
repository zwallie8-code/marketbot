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
    return data["rows"] if isinstance(data, dict) and "rows" in data else data

def build_prompt(rows, top_n):
    cols = ["symbol","return_1d","change_1d","volume","close"]
    slim = [{k: r.get(k) for k in cols} for r in rows]
    return f"""
You are a quantitative assistant. Rank US tickers using momentum (return_1d / change_1d) with basic liquidity/price sanity (prefer higher volume, avoid sub-$1).
Input (JSON list of objects with symbol, return_1d, change_1d, volume, close):
{json.dumps(slim)[:120000]}

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
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    client = OpenAI(api_key=key)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role":"system","content":"You output only valid JSON. No prose."},
                  {"role":"user","content":prompt}],
        temperature=0.2
    )
    return resp.choices[0].message.content.strip()

def parse_json_strict(txt):
    if txt is None: return None
    start = txt.find("{"); end = txt.rfind("}")
    if start == -1 or end == -1: return None
    try:
        return json.loads(txt[start:end+1])
    except Exception:
        return None

def heuristic_rank(rows, top_n):
    import math
    scored = []
    for r in rows:
        ret = r.get("return_1d") or 0.0
        vol = r.get("volume") or 0.0
        sc = (ret or 0.0) * (math.log(max(vol,1))+1)
        scored.append({"symbol": r["symbol"], "score": round(float(sc),4), "reason":"heuristic momentum x liquidity"})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return {"as_of":"local", "method":"heuristic_v1", "top": scored[:top_n]}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="data/stocks.json")
    p.add_argument("--out-json", default="data/gpt_recommendations.json")
    p.add_argument("--out-csv", default="output/ranked_stocks.csv")
    p.add_argument("--top", type=int, default=20)
    p.add_argument("--model", default=os.getenv("OPENAI_MODEL","gpt-4o-mini"))
    args = p.parse_args()

    Path("output").mkdir(parents=True, exist_ok=True)
    rows = load_universe(args.input)
    if not rows: die("input universe is empty")

    txt = call_gpt(build_prompt(rows, args.top), model=args.model)
    payload = parse_json_strict(txt) or heuristic_rank(rows, args.top)

    with open(args.out_json, "w") as f:
        json.dump(payload, f, indent=2)

    df = pd.DataFrame(payload.get("top", []))
    if "rank" not in df.columns:
        df.insert(0, "rank", range(1, len(df)+1))
    df.to_csv(args.out_csv, index=False)

    print(f"✅ Wrote: {args.out_json}")
    print(f"✅ Wrote: {args.out_csv}")

if __name__ == "__main__":
    main()
