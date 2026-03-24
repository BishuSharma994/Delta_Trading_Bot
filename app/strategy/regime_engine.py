def detect_regime(candles):
    try:
        if not candles or len(candles) < 15:
            return {
                "regime": "NO_TRADE",
                "avg_range": 0.0,
                "dir_strength": 0.0,
                "trend_strength": 0.0,
            }

        closes = []
        highs = []
        lows = []

        for c in candles:
            close = c.get("close") or c.get("c")
            high = c.get("high") or c.get("h")
            low = c.get("low") or c.get("l")

            if close is None or high is None or low is None:
                continue

            closes.append(float(close))
            highs.append(float(high))
            lows.append(float(low))

        if len(closes) < 15:
            return {
                "regime": "NO_TRADE",
                "avg_range": 0.0,
                "dir_strength": 0.0,
                "trend_strength": 0.0,
            }

        ranges = []
        for i in range(-10, 0):
            if closes[i] == 0:
                continue
            ranges.append((highs[i] - lows[i]) / closes[i])

        avg_range = sum(ranges) / len(ranges) if ranges else 0.0

        dir_score = 0
        for i in range(-5, -1):
            if closes[i] > closes[i - 1]:
                dir_score += 1
            elif closes[i] < closes[i - 1]:
                dir_score -= 1

        dir_strength = abs(dir_score) / 5

        sma5 = sum(closes[-5:]) / 5
        sma10 = sum(closes[-10:]) / 10

        last_price = closes[-1] if closes[-1] != 0 else 1e-9
        trend_strength = abs(sma5 - sma10) / last_price

        if (
            avg_range < 0.0007
            or dir_strength < 0.4
            or trend_strength < 0.0005
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

    except Exception as e:
        print(f"[REGIME_ERROR] {e}")
        return {
            "regime": "NO_TRADE",
            "avg_range": 0.0,
            "dir_strength": 0.0,
            "trend_strength": 0.0,
        }