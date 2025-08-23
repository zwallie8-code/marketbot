import math, datetime as dt

class PolicyConfig:
    min_conf = 0.65
    max_portfolio_alloc = 0.70
    max_symbol_alloc = 0.10
    max_sector_alloc = 0.25
    target_frac = 0.05
    vol_ref = 0.02
    vol_floor = 0.01
    max_slippage = 0.0025
    trade_start = (10, 5)   # hh, mm
    trade_end   = (15, 50)

def within_trade_window(now, tz):
    local = now.astimezone(tz)
    s_h,s_m = PolicyConfig.trade_start
    e_h,e_m = PolicyConfig.trade_end
    start = local.replace(hour=s_h, minute=s_m, second=0, microsecond=0)
    end   = local.replace(hour=e_h, minute=e_m, second=0, microsecond=0)
    return start <= local <= end

def size_position(equity, symbol_cap, atr_pct):
    base = equity * PolicyConfig.target_frac
    scale = PolicyConfig.vol_ref / max(atr_pct, PolicyConfig.vol_floor)
    return min(base * scale, equity * symbol_cap)

def accept_buy(rec, conf, price_above_50dma):
    return rec["action"]=="BUY" and conf>=PolicyConfig.min_conf and price_above_50dma

def stop_take(rec):
    stop = max(0.06, rec.get("stop_loss_pct", 0.06))
    tp   = min(0.15, rec.get("take_profit_pct", 0.15))
    return stop, tp
