import logging

logger = logging.getLogger()


def detect_regime(candles):
    try:
        # --- safety
        if not candles or len(candles) < 15:
            return {
                "regime": "RANGE",
                "avg_range": 0.0,
                "dir_strength": 0.0,
                "trend_strength": 0.0,
            }

        closes = []
        highs = []
        lows = []

        # --- normalize input
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
                "regime": "RANGE",
                "avg_range": 0.0,
                "dir_strength": 0.0,
                "trend_strength": 0.0,
            }

        # --- avg range (volatility / expansion)
        ranges = []
        for i in range(-10, 0):
            price = closes[i]
            if price == 0:
                continue
            ranges.append((highs[i] - lows[i]) / price)

        avg_range = sum(ranges) / len(ranges) if ranges else 0.0

        # --- directional strength
        dir_score = 0
        for i in range(-5, -1):
            if closes[i] > closes[i - 1]:
                dir_score += 1
            elif closes[i] < closes[i - 1]:
                dir_score -= 1

        dir_strength = abs(dir_score) / 5

        # --- trend strength
        sma5 = sum(closes[-5:]) / 5
        sma10 = sum(closes[-10:]) / 10

        last_price = closes[-1] if closes[-1] != 0 else 1e-9
        trend_strength = abs(sma5 - sma10) / last_price

        regime = "TRENDING" if trend_strength > 0.00005 else "RANGE"

        return {
            "regime": regime,
            "avg_range": avg_range,
            "dir_strength": dir_strength,
            "trend_strength": trend_strength,
        }

    except Exception as e:
        logger.info("[REGIME_ERROR] %s", e)
        return {
            "regime": "RANGE",
            "avg_range": 0.0,
            "dir_strength": 0.0,
            "trend_strength": 0.0,
        }
