from flask import Flask, jsonify, request
import yfinance as yf
import numpy as np

try:
    import pandas as pd
except Exception:  # Render will install pandas via yfinance; this is just a safe import
    pd = None

app = Flask(__name__)

# Default watchlist (used if ?symbols= is omitted)
DEFAULT_TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "BRK-B", "JPM", "NFLX"]


# ---------- utils ----------

def to_native(v):
    """Convert numpy/pandas scalars/timestamps to plain Python/JSON-safe."""
    # numpy generic (int64, float64, etc.)
    if isinstance(v, np.generic):
        return v.item()
    # pandas Timestamp
    if pd is not None and isinstance(v, pd.Timestamp):
        return v.to_pydatetime().isoformat()
    # plain python already
    return v


def quote_for(symbol: str):
    """Fetch latest daily OHLCV for a single symbol."""
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="1d")  # last completed bar
    if hist.empty:
        return None

    row = hist.iloc[-1]
    # Some fields may be NaN; guard + convert
    def field(name):
        val = row.get(name)
        if pd is not None and pd.isna(val):
            return None
        return to_native(val)

    ts = row.name  # index may be pandas.Timestamp
    ts_iso = to_native(ts)

    return {
        "symbol": symbol.upper(),
        "timestamp": ts_iso,
        "open": field("Open"),
        "high": field("High"),
        "low": field("Low"),
        "close": field("Close"),
        "volume": int(field("Volume")) if field("Volume") is not None else None,
    }


# ---------- routes ----------

@app.route("/")
def root():
    return jsonify({
        "message": "Welcome to MarketBot Stock API",
        "endpoints": {
            "/stock?symbol=AAPL": "Single symbol snapshot (OHLCV for latest day)",
            "/export/json?symbols=AAPL,MSFT,GOOGL": "Multiple symbols (comma-separated). If omitted, uses default watchlist.",
            "/health": "Service health check"
        },
        "default_watchlist": DEFAULT_TICKERS
    })


@app.route("/health")
def health():
    return jsonify({"ok": True})


@app.route("/stock")
def stock():
    symbol = (request.args.get("symbol") or "").strip()
    if not symbol:
        return jsonify({"error": "Missing required query param 'symbol', e.g. /stock?symbol=AAPL"}), 400

    try:
        data = quote_for(symbol)
        if data is None:
            return jsonify({"error": f"No data found for symbol '{symbol}'"}), 404
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": f"{type(e).__name__}: {e}"}), 500


@app.route("/export/json")
def export_json():
    # Accepts ?symbols=AAPL,MSFT  (optional; uses default list if omitted)
    raw = request.args.get("symbols")
    symbols = [s.strip().upper() for s in raw.split(",")] if raw else DEFAULT_TICKERS

    out = []
    for s in symbols:
        try:
            q = quote_for(s)
            out.append(q if q is not None else {"symbol": s, "error": "No data"})
        except Exception as e:
            out.append({"symbol": s, "error": f"{type(e).__name__}: {e}"})

    return jsonify({"symbols": symbols, "results": out})


# Local run (Render uses your Start Command: `gunicorn app:app`)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
