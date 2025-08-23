import os, json, math, pytz, statistics
from datetime import datetime
from policy_engine import within_trade_window, size_position, accept_buy, stop_take, PolicyConfig
from broker_alpaca import Broker

def load_inputs():
    with open("gpt_recommendations.json","r") as f: recs = json.load(f)
    with open("output/market_metrics.json","r") as f: mkt = json.load(f)   # your ATRs, DMAs, sectors, prices
    return recs, mkt

def dollars_to_shares(dollars, price): 
    return max(0, math.floor(dollars / price))

def main():
    tz = pytz.timezone("America/New_York")
    dry_run = os.getenv("DRY_RUN","true").lower()=="true"
    paper   = os.getenv("PAPER_TRADING","true").lower()=="true"
    kill    = os.getenv("KILL_SWITCH","false").lower()=="true"
    if kill: 
        print("KILL_SWITCH engaged. Exiting."); return

    now = datetime.utcnow().replace(tzinfo=pytz.utc)
    if not within_trade_window(now, tz):
        print("Outside trade window. Exiting."); return

    recs, mkt = load_inputs()
    assert (now - datetime.fromisoformat(recs["as_of"].replace("Z","+00:00"))).total_seconds() < 24*3600, "Stale recs"

    broker = Broker(paper=paper)
    acct = broker.account()
    equity = float(acct["equity"])
    max_invested = equity * PolicyConfig.max_portfolio_alloc

    # compute current exposure
    positions = broker.positions()
    invested = sum(float(p["market_value"]) for p in positions)
    room = max(0.0, max_invested - invested)

    orders=[]
    for rec in recs["recommendations"]:
        sym = rec["symbol"]
        px  = mkt["prices"][sym]
        above_50dma = px > mkt["dma50"][sym]
        atr_pct = mkt["atr_pct"][sym]               # e.g., ATR/Price
        sector  = mkt["sector"][sym]

        if not accept_buy(rec, rec["confidence"], above_50dma): 
            continue

        symbol_cap = min(PolicyConfig.max_symbol_alloc, rec.get("max_alloc_pct", 1.0))
        dollar_size = min(size_position(equity, symbol_cap, atr_pct), room)
        qty = dollars_to_shares(dollar_size, px)
        if qty <= 0: 
            continue

        stop_pct, tp_pct = stop_take(rec)
        stop_price = round(px*(1.0 - stop_pct), 2)
        tp_price   = round(px*(1.0 + tp_pct), 2)
        limit_price= round(px*(1.0 + PolicyConfig.max_slippage), 2)

        if dry_run:
            orders.append({"symbol":sym, "qty":qty, "limit":limit_price, "stop":stop_price, "tp":tp_price})
        else:
            resp = broker.place_order(sym, qty, "buy", limit_price=limit_price, stop_loss=stop_price, take_profit=tp_price)
            orders.append(resp)

    with open("output/placed_orders.json","w") as f: json.dump(orders, f, indent=2)
    print(json.dumps(orders, indent=2))

if __name__ == "__main__":
    main()
