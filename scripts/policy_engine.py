MAX_POSITION_SIZE = 1000      # USD allocated per stock
MAX_PORTFOLIO_SIZE = 5        # Limit of simultaneous positions
MIN_CONFIDENCE = 0.7          # Minimum GPT confidence required

def should_buy(stock: dict, active_positions: list) -> bool:
    """Decide if a stock should be bought based on GPT confidence & portfolio size."""
    if len(active_positions) >= MAX_PORTFOLIO_SIZE:
        return False
    return stock["confidence"] >= MIN_CONFIDENCE

def calculate_position_size(balance: float, price: float) -> int:
    """Determine how many shares to buy based on risk policy."""
    usd_allocated = min(balance / 10, MAX_POSITION_SIZE)
    return max(int(usd_allocated / price), 1)
