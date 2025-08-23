from flask import Flask, jsonify, request
import yfinance as yf

app = Flask(__name__)

# Default home route
@app.route("/")
def home():
    return jsonify({
        "message": "Welcome to MarketBot Stock API! Use /stock?symbol=AAPL or /export/json"
    })

# Single stock fetch endpoint
@app.route("/stock", methods=["GET"])
def get_stock():
    symbol = request.args.get("symbol")

    if not symbol:
        return jsonify({"error": "Please provide a stock symbol, e.g., /stock?symbol=AAPL"}), 400

    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period="1d")  # Latest 1-day data

        if hist.empty:
            return jsonify({"error": f"No data found for symbol {symbol}"}), 404

        data = {
            "symbol": symbol.upper(),
            "current_price": hist["Close"].iloc[-1],
            "high": hist["High"].iloc[-1],
            "low": hist["Low"].iloc[-1],
            "volume": hist["Volume"].iloc[-1]
        }
        return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Export multiple stocks in JSON
@app.route("/export/json", methods=["GET"])
def export_stocks_json():
    symbols = request.args.get("symbols")

    if not symbols:
        return jsonify({
            "error": "Please provide stock symbols, e.g., /export/json?symbols=AAPL,MSFT,GOOGL"
        }), 400

    symbol_list = [s.strip().upper() for s in symbols.split(",")]
    results = []

    for symbol in symbol_list:
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period="1d")

            if hist.empty:
                results.append({"symbol": symbol, "error": "No data found"})
            else:
                results.append({
                    "symbol": symbol,
                    "current_price": hist["Close"].iloc[-1],
                    "high": hist["High"].iloc[-1],
                    "low": hist["Low"].iloc[-1],
                    "volume": hist["Volume"].iloc[-1]
                })
        except Exception as e:
            results.append({"symbol": symbol, "error": str(e)})

    return jsonify({"stocks": results})

# Run app locally (Render will override this)
if __name__ == "__main__":
    app.run(debug=True)
