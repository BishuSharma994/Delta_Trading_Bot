def detect_regime(candles):
    if len(candles) < 15:
        return {"regime": "NO_TRADE"}

    closes = [c["close"] for c in candles]
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]

    ranges = [(highs[i] - lows[i]) / closes[i] for i in range(-10, 0)]
    avg_range = sum(ranges) / len(ranges)

    dir_score = 0
    for i in range(-5, -1):
        if closes[i] > closes[i - 1]:
            dir_score += 1
        elif closes[i] < closes[i - 1]:
            dir_score -= 1

    dir_strength = abs(dir_score) / 5

    sma5 = sum(closes[-5:]) / 5
    sma10 = sum(closes[-10:]) / 10

    trend_strength = abs(sma5 - sma10) / closes[-1]

    if (
        avg_range < 0.002
        or dir_strength < 0.6
        or trend_strength < 0.0015
    ):
        regime = "NO_TRADE"
    else:
        regime = "TRENDING"

    return {
        "regime": regime,
        "avg_range": avg_range,
        "dir_strength": dir_strength,
        "trend_strength": trend_strength,
    }
