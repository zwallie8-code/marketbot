import os

# ----- Broker -----
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

# Dry-run: don't actually place orders (still prints actions)
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"

# ----- Policy / Risk -----
MAX_PORTFOLIO_SIZE = int(os.getenv("MAX_PORTFOLIO_SIZE", "5"))
MAX_POSITION_USD  = float(os.getenv("MAX_POSITION_USD", "1000"))
MIN_CONFIDENCE    = float(os.getenv("MIN_CONFIDENCE", "0.7"))
EXIT_BELOW_CONFIDENCE = float(os.getenv("EXIT_BELOW_CONFIDENCE", "0.5"))

# Stops / targets for bracket orders
STOP_LOSS_PCT   = float(os.getenv("STOP_LOSS_PCT", "0.05"))  # 5%
TAKE_PROFIT_PCT = float(os.getenv("TAKE_PROFIT_PCT", "0.10"))  # 10%

# Universe / ranking
UNIVERSE_SOURCE = os.getenv("UNIVERSE_SOURCE", "sp500")  # or 'file'
UNIVERSE_FILE   = os.getenv("UNIVERSE_FILE", "data/stocks.json")
GPT_TOP_N       = int(os.getenv("GPT_TOP_N", "20"))
GPT_RANK_MAX_ROWS = int(os.getenv("GPT_RANK_MAX_ROWS", "400"))
OPENAI_MODEL    = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
