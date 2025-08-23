from flask import Flask, jsonify, request, send_file
import os, io, json, gzip, threading, time
import requests
import numpy as np
import yfinance as yf

app = Flask(__name__)

CACHE_JSON = "/tmp/latest_stocks.json"
CACHE_GZ   = "/tmp/latest_stocks.json.gz"
STATUS     = {"running": False, "updated_at": None, "symbols": 0, "batches": 0, "error": None}

# ------------ helpers ------------
def to_py(v):
    if isinstance(v, np.generic):
        return v.item()
    return v

def get_all_us_tickers(exclude_etf=True):
    """
    Pulls NASDAQ + NYSE/AMEX lists from NASDAQ Trader.
    """
    urls = [
        "https://nasdaqtrader.com/dynamic/symboldirectory/nasdaqlisted.txt",
        "https://nasdaqtrader.com/dynamic/symboldirectory/otherlisted.txt"
    ]
    tickers = set()
    for url in urls:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        lines = r.text.strip().splitlines()
        # Pipe-delimited header; last few lines are footers
        for line in lines[1:]:
            if "|" not in line:
                continue
            parts = line.split("|")
            symbol = parts[0].strip()
            if not symbol or symbol in ("Symbol", "File Creation Time"):
                continue
            # Exclusions
            if exclude_etf:
                # ETF flag: NASDAQ file has "ETF" column, otherlisted has "ETF"
                # Try to detect simple Y flag near end of row
                if "Y|" in line and "ETF" in lines[0]:
                    # NASDAQ format: ...|ETF|...
                    pass
            # Remove test issues, rights, units, etc.
            if any(suffix in symbol for suffix in (".W", ".U", ".R", ".P", "^", "$")):
                continue
            if symbol.isalpha():
                tickers.add(symbol.upper())
    # Reasonable cap to avoid abuse on free tier
    return sorted(tickers)

def chunked(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i+n]

def fetch_snapshot_batch(symbols):
    """
    Returns list of dicts with: symbol, close, prev_close, change_1d, return_1d, volume.
    """
    joined = " ".join(symbols)  # yfinance tolerates space/comma
    tk = yf.Tickers(joined)
    out = []
    for s in symbols:
        try:
            t = tk.tickers[s]
            hist = t.history(period="5d", interval="1d", auto_adjust=True, prepost=False)
            if hist.empty or hist.shape[0] < 2:
                out.append({"symbol": s, "error": "no_bars"})
                continue
            last = hist.iloc[-1]
            prev = hist.iloc[-2]
            close = to_py(last["Close"])
            prevc = to_py(prev["Close"])
            vol   = int(to_py(last.get("Volume", 0))) if not np.isnan(last.get("Volume", 0)) else None
            chg   = close - prevc
            ret1d = None if prevc in (None, 0) else chg / prevc
            out.append({
                "symbol": s,
                "close": close,
                "prev_close": prevc,
                "change_1d": chg,
                "return_1d": ret1d,
                "volume": vol
            })
        except Exception as e:
            out.append({"symbol": s, "error": f"{type(e).__name__}: {e}"})
    return out

def build_cache(max_symbols=None, batch_size=200, sleep_sec=0.5):
    STATUS.update({"running": True, "error": None, "symbols": 0, "batches": 0})
    try:
        symbols = get_all_us_tickers(exclude_etf=True)
        if max_symbols:
            symbols = symbols[:max_symbols]
        all_rows = []
        batch_idx = 0
        for batch in chunked(symbols, batch_size):
            batch_idx += 1
            rows = fetch_snapshot_batch(batch)
            all_rows.extend(rows)
            STATUS.update({"symbols": len(all_rows), "batches": batch_idx})
            time.sleep(sleep_sec)  # be nice to Yahoo
        payload = {
            "universe": "US_equities",
            "count": len(all_rows),
            "generated_at": int(time.time()),
            "rows": all_rows
        }
        # Write plain JSON
        with open(CACHE_JSON, "w") as f:
            json.dump(payload, f)
        # Write gzip too
        with gzip.open(CACHE_GZ, "wb") as f:
            f.write(json.dumps(payload).encode("utf-8"))
        STATUS.update({"running": False, "updated_at": int(time.time())})
        return payload
    except Exception as e:
        STATUS.update({"running": False, "error": f"{type(e).__name__}: {e}"})
        raise

def ensure_cache_exists():
    return os.path.exists(CACHE_JSON)

# ------------ routes ------------
@app.route("/")
def home():
    return jsonify({
        "message": "MarketBot US Market API",
        "endpoints": {
            "/export/all": "Build/refresh cache (sync). Optional: ?max=500 to limit, ?async=1 for background",
            "/data/latest": "Download latest JSON (or ?gzip=1)",
            "/rank/top": "Ranks from cache. Params: ?n=50&metric=return_1d",
            "/health": "Service status",
            "/status": "Build status"
        }
    })

@app.route("/health")
def health():
    return jsonify({"ok": True, "cache_exists": ensure_cache_exists(), "status": STATUS})

@app.route("/status")
def status():
    return jsonify(STATUS)

@app.route("/export/all")
def export_all():
    """
    Build the full-market snapshot and cache it.
    - ?max=1000   -> limit symbols (useful on free tier)
    - ?async=1    -> start in background, return status immediately
    - ?batch=200  -> batch size
    """
    max_symbols = request.args.get("max", type=int)
    batch_size  = request.args.get("batch", default=200, type=int)
    async_flag  = request.args.get("async", default=0, type=int) == 1

    if async_flag:
        if STATUS.get("running"):
            return jsonify({"started": False, "message": "already running", "status": STATUS}), 202
        def _worker():
            try:
                build_cache(max_symbols=max_symbols, batch_size=batch_size)
            except Exception:
                pass
        threading.Thread(target=_worker, daemon=True).start()
        return jsonify({"started": True, "status": STATUS}), 202

    payload = build_cache(max_symbols=max_symbols, batch_size=batch_size)
    return jsonify({"ok": True, "count": payload["count"], "updated_at": payload["generated_at"]})

@app.route("/data/latest")
def data_latest():
    """
    Serve cached JSON (or gzip).
    - ?gzip=1 -> serve gzip
    """
    if not ensure_cache_exists():
        return jsonify({"error": "no cache yet. Hit /export/all first (use ?async=1)."}), 404
    if request.args.get("gzip", default=0, type=int) == 1 and os.path.exists(CACHE_GZ):
        return send_file(CACHE_GZ, mimetype="application/gzip", as_attachment=True, download_name="latest_stocks.json.gz")
    return send_file(CACHE_JSON, mimetype="application/json", as_attachment=True, download_name="latest_stocks.json")

@app.route("/rank/top")
def rank_top():
    """
    Rank from cached data.
    - ?metric=return_1d|volume|change_1d
    - ?n=50
    - ?desc=1 (default) or 0
    """
    if not ensure_cache_exists():
        return jsonify({"error": "no cache yet. Hit /export/all first."}), 404

    metric = request.args.get("metric", default="return_1d")
    n      = request.args.get("n", default=50, type=int)
    desc   = request.args.get("desc", default=1, type=int) == 1

    with open(CACHE_JSON, "r") as f:
        payload = json.load(f)

    rows = [r for r in payload["rows"] if metric in r and isinstance(r.get(metric), (int, float)) and not np.isnan(r.get(metric))]
    rows.sort(key=lambda x: x.get(metric, 0), reverse=desc)
    return jsonify({
        "metric": metric,
        "desc": desc,
        "n": n,
        "total": len(rows),
        "results": rows[:n]
    })

# gunicorn entrypoint
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
