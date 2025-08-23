# scripts/gpt_rank_stocks.py
import os, json, math, time, random, pathlib
from datetime import datetime
import pandas as pd

DATA_PATH = pathlib.Path("data/stocks.json")
OUT_DIR = pathlib.Path("data")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "gpt_recommendations.json"

# ---- Helpers ----------------------------------------------------------------
def pct(a, b):
    try:
        if b in (0, None) or pd.isna(a) or pd.isna(b): return None
        return round((a - b) / b * 100, 3)
    except Exception:
        return None

def compute_features(df):
    # Expect columns like: close, close_1d_ago, close_5d_ago, close_21d_ago, etc.
    # If your JSON schema is different, adjust here.
    feats = []
    for _, r in df.iterrows():
        sym = r.get("symbol") or r.get("ticker") or r.get("Symbol")
        if not sym: 
            continue
        row = {
            "symbol": sym,
            "name": r.get("name") or r.get("Name") or "",
            "last": r.get("close") or r.get("Close"),
            "r_1d": pct(r.get("close"), r.get("close_1d_ago")),
            "r_5d": pct(r.get("close"), r.get("close_5d_ago")),
            "r_1m": pct(r.get("close"), r.get("close_21d_ago")),   # ~21 trading days
            "r_3m": pct(r.get("close"), r.get("close_63d_ago")),   # ~63 trading days
            "vol30": r.get("volatility_30d"),
            "vol": r.get("volume") or r.get("Volume"),
            "sector": r.get("sector") or "",
            "industry": r.get("industry") or ""
        }
        feats.append(row)
    return pd.DataFrame(feats)

def compact_csv(df):
    cols = ["symbol","last","r_1d","r_5d","r_1m","r_3m","vol30","vol","sector","industry"]
    df2 = df[cols].copy()
    # keep numbers small; fillna for compactness
    for c in ["last","r_1d","r_5d","r_1m","r_3m","vol30","vol"]:
        if c in df2:
            df2[c] = df2[c].fillna("").astype(str)
    return df2.to_csv(index=False)

def chunk_rows(df, max_rows):
    for i in range(0, len(df), max_rows):
        yield df.iloc[i:i+max_rows]

def local_heuristic_rank(df, top_n=20):
    # Cheap, no-API fallback: momentum / volatility combo
    sc = (
        (df["r_1m"].fillna(0) * 0.4) +
        (df["r_3m"].fillna(0) * 0.4) +
        (df["r_5d"].fillna(0) * 0.15) +
        (df["r_1d"].fillna(0) * 0.05) -
        (df["vol30"].fillna(0) * 0.05)
    )
    tmp = df.copy()
    tmp["score"] = sc
    top = tmp.sort_values("score", ascending=False).head(top_n)
    return [
        {
            "symbol": r.symbol,
            "score": round(float(r.score), 4),
            "reason": "Momentum/volatility heuristic (no GPT key).",
        }
        for _, r in top.iterrows()
    ]

# ---- GPT call (optional) -----------------------------------------------------
def call_openai_rank(rows_csv, model=None, top_n=20):
    """
    Sends compact CSV features to GPT and asks for JSON ranking.
    If OPENAI_API_KEY is not set, returns None.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    # Use the modern SDK if available; fall back to legacy if not.
    try:
        # Newer SDK (2024+)
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        mdl = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        system = (
            "You are a disciplined equity analyst. "
            "Given CSV rows with features for many tickers, pick the top stocks. "
            "Return STRICT JSON with this schema: "
            "{ 'ranked': [ { 'symbol': 'AAPL', 'score': number, 'reason': 'short explanation' } ] } "
            f"Limit to top {top_n}. Prefer higher multi-horizon momentum and reasonable volatility."
        )
        user = (
            "Columns: symbol,last,r_1d,r_5d,r_1m,r_3m,vol30,vol,sector,industry\n"
            "Rows:\n" + rows_csv
        )

        resp = client.chat.completions.create(
            model=mdl,
            messages=[
                {"role":"system","content":system},
                {"role":"user","content":user}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        txt = resp.choices[0].message.content
        return json.loads(txt).get("ranked", [])
    except Exception:
        # Legacy SDK fallback
        try:
            import openai
            openai.api_key = api_key
            mdl = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            system = (
                "You are a disciplined equity analyst. "
                "Return JSON only with key 'ranked'."
            )
            user = (
                "Columns: symbol,last,r_1d,r_5d,r_1m,r_3m,vol30,vol,sector,industry\n"
                "Rows:\n" + rows_csv + "\nTop 20 JSON please."
            )
            resp = openai.ChatCompletion.create(
                model=mdl,
                messages=[{"role":"system","content":system},{"role":"user","content":user}],
                temperature=0.2
            )
            return json.loads(resp.choices[0].message["content"]).get("ranked", [])
        except Exception:
            return None

# ---- Main --------------------------------------------------------------------
def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Missing {DATA_PATH}. Run the dataset updater first.")

    raw = json.loads(DATA_PATH.read_text())
    # Accept list or dict-with-list
    if isinstance(raw, dict) and "data" in raw:
        df = pd.DataFrame(raw["data"])
    else:
        df = pd.DataFrame(raw)

    feats = compute_features(df)

    # Keep payload compact: pick most analyzable subset (e.g., top by volume) to send to GPT
    # If you truly want *all* tickers, the script will chunk them.
    subset = feats.copy()
    if "vol" in subset and pd.api.types.is_numeric_dtype(subset["vol"]):
        subset = subset.sort_values("vol", ascending=False)
    # Optional hard cap to keep token usage sane
    subset = subset.head(int(os.getenv("GPT_RANK_MAX_ROWS", "600")))

    ranked_all = []
    api_available = bool(os.getenv("OPENAI_API_KEY"))

    if api_available:
        # Chunk 200 rows at a time for token safety
        for part in chunk_rows(subset, max_rows=200):
            csv_part = compact_csv(part)
            ranked = call_openai_rank(csv_part, top_n=int(os.getenv("GPT_TOP_N", "20")))
            if ranked:
                ranked_all.extend(ranked)
            time.sleep(1)  # gentle rate limiting

        # De-dup by symbol, keep best score
        best = {}
        for r in ranked_all:
            sym = r.get("symbol")
            if not sym: 
                continue
            sc = r.get("score")
            if sym not in best or (isinstance(sc, (int,float)) and sc > best[sym].get("score", -1e9)):
                best[sym] = r
        ranked_final = sorted(best.values(), key=lambda x: x.get("score", 0), reverse=True)[:int(os.getenv("GPT_TOP_N", "20"))]
        mode = "gpt"
    else:
        ranked_final = local_heuristic_rank(subset, top_n=int(os.getenv("GPT_TOP_N", "20")))
        mode = "heuristic"

    output = {
        "mode": mode,
        "updated_at": int(time.time()),
        "count_input": int(len(subset)),
        "ranked": ranked_final
    }
    OUT_FILE.write_text(json.dumps(output, indent=2))
    print(f"Saved rankings to {OUT_FILE.resolve()} (mode={mode}, input={len(subset)})")

if __name__ == "__main__":
    main()
