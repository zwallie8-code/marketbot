#!/usr/bin/env python3
import json, time
from pathlib import Path
import pandas as pd
import yfinance as yf

OUT = Path("data/stocks.json")

def load_sp500():
    tables = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
    df = tables[0]
    syms = df["Symbol"].astype(str).tolist()
    syms_yf = [s.replace(".", "-") for s in syms]
    return syms, syms_yf, df

def fetch_prices(symbols_yf):
    return yf.download(
        symbols_yf, period="6mo", interval="1d",
        auto_adjust=True, threads=True, group_by="ticker", progress=False
    )

def latest_val(series):
    try:
        return float(series.dropna().iloc[-1])
    except Exception:
        return None

def compute_rows(sp_syms, yf_syms, meta_df, px):
    rows = []
    for orig, yfs in zip(sp_syms, yf_syms):
        try:
            df = px[yfs]
        except Exception:
            continue
        close  = latest_val(df["Close"]) if isinstance(df, pd.DataFrame) else None
        volume = latest_val(df["Volume"]) if isinstance(df, pd.DataFrame) else None

        def ret(days):
            try:
                s = df["Close"].dropna()
                c0 = float(s.iloc[-1])
                cN = float(s.iloc[-days])
                return round((c0 - cN) / cN, 4)
            except Exception:
                return None

        rows.append({
            "symbol": orig,
            "yf_symbol": yfs,
            "close": close,
            "volume": volume,
            "return_1d": ret(2),
            "change_1d": ret(2),
            "r_5d": ret(5),
            "r_1m": ret(21),
            "r_3m": ret(63),
            "sector": str(meta_df.loc[meta_df['Symbol']==orig, 'GICS Sector'].values[0]) if orig in meta_df['Symbol'].values else "",
            "industry": str(meta_df.loc[meta_df['Symbol']==orig, 'GICS Sub-Industry'].values[0]) if orig in meta_df['Symbol'].values else ""
        })
    return rows

def main():
    sp_syms, yf_syms, meta_df = load_sp500()
    px = fetch_prices(yf_syms)
    rows = compute_rows(sp_syms, yf_syms, meta_df, px)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        json.dump({"rows": rows, "updated_at": int(time.time())}, f, indent=2)
    print(f"✅ Wrote {OUT.resolve()} with {len(rows)} rows")

if __name__ == "__main__":
    main()
