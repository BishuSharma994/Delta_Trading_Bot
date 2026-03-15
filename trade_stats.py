import json
from collections import defaultdict
import math

file = "data/events/paper_trades.jsonl"

open_trades = {}
returns = []

with open(file) as f:
    for line in f:
        t = json.loads(line)

        key = (t["symbol"], t["trade_type"])

        if t["action"] == "ENTRY":
            open_trades[key] = t

        elif t["action"] == "EXIT" and key in open_trades:
            entry = open_trades.pop(key)

            entry_price = entry["price"]
            exit_price = t["price"]

            r = (exit_price - entry_price) / entry_price
            returns.append(r)

# statistics
n = len(returns)
mean = sum(returns) / n

variance = sum((x - mean) ** 2 for x in returns) / n
std = math.sqrt(variance)

equity = 1
peak = 1
max_dd = 0

for r in returns:
    equity *= (1 + r)
    peak = max(peak, equity)
    dd = (peak - equity) / peak
    max_dd = max(max_dd, dd)

print("Trades:", n)
print("Mean return:", round(mean * 100, 3), "%")
print("Std dev:", round(std * 100, 3), "%")
print("Max drawdown:", round(max_dd * 100, 3), "%")
print("Total return:", round((equity - 1) * 100, 3), "%")
