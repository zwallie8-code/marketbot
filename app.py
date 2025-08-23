from flask import Flask, request, jsonify
import yfinance as yf

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "message": "Welcome to MarketBot Stock API! Use /stock?symbol=AAPL"
    })

@app.route('/stock', methods=['GET'])
def get_stock_price():
    try:
        # Get symbol from query params
        symbol = request.args.get('symbol')

        if not symbol:
            return jsonify({"error": "Please provide a stock symbol, e.g. /stock?symbol=AAPL"}), 400

        # Fetch stock data
        stock = yf.Ticker(symbol)
        data = stock.history(period="1d")

        if data.empty:
            return jsonify({"error": "Invalid stock symbol"}), 404

        # Get the latest closing price
        latest_price = round(data['Close'].iloc[-1], 2)

        return jsonify({
            "symbol": symbol.upper(),
            "latest_price": latest_price
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
