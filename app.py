from flask import Flask, jsonify

# Initialize Flask app
app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({
        "status": "success",
        "message": "🚀 MarketBot is live!"
    })

# Health check endpoint for Render
@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
