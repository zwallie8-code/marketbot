import yfinance as yf

def safe_price(symbol: str) -> float | None:
    yf_symbol = symbol.replace('.', '-')  # Yahoo format
    try:
        t = yf.Ticker(yf_symbol)
        px = getattr(t, "fast_info", {}).get("last_price") if hasattr(t, "fast_info") else None
        if not px:
            hist = t.history(period="1d")
            if not hist.empty:
                px = float(hist["Close"].iloc[-1])
        return float(px) if px else None
    except Exception:
        return None
