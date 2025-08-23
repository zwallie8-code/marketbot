import os, time
import requests

class Broker:
    def __init__(self, paper=True):
        self.key = os.environ["BROKER_KEY"]
        self.secret = os.environ["BROKER_SECRET"]
        base = "https://paper-api.alpaca.markets" if paper else "https://api.alpaca.markets"
        self.base = base
        self.h = {"APCA-API-KEY-ID": self.key, "APCA-API-SECRET-KEY": self.secret}

    def account(self):
        return requests.get(self.base+"/v2/account", headers=self.h).json()

    def positions(self):
        return requests.get(self.base+"/v2/positions", headers=self.h).json()

    def place_order(self, symbol, qty, side, limit_price=None, stop_loss=None, take_profit=None):
        o = {
          "symbol": symbol, "qty": qty, "side": side, "type": "limit" if limit_price else "market",
          "time_in_force": "day"
        }
        if limit_price: o["limit_price"]=str(limit_price)
        if stop_loss or take_profit:
            o["order_class"]="bracket"
            if stop_loss:    o["stop_loss"]= {"stop_price": str(stop_loss)}
            if take_profit:  o["take_profit"]={"limit_price": str(take_profit)}
        r = requests.post(self.base+"/v2/orders", json=o, headers=self.h)
        return r.json()
