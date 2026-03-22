```python
def detect_regime(candles):
    """
    Regime detection for volatility gating.

    Output:
    {
        "regime": "TRENDING" | "NO_TRADE",
        "avg_range": float,
        "dir_strength": float,
        "trend_strength": float,
    }
    """

    # --- safety check
    if not candles or len(candles) < 15:
        return {
            "regime": "NO_TRADE",
            "avg_range": 0.0,
            "dir_strength": 0.0,
            "trend_strength": 0.0,
        }

    try:
        closes = [float(c["close"]) for c in candles]
        highs = [float(c["high"]) for c in candles]
        lows = [float(c["low"]) for c in candles]

        # --- avg_range (last 10 candles)
        ranges = []
        for i in range(-10, 0):
            price = closes[i]
            if price == 0:
                continue
            ranges.append((highs[i] - lows[i]) / price)

        avg_range = sum(ranges) / len(ranges) if ranges else 0.0

        # --- directional strength (last 5 candles)
        dir_score = 0
        for i in range(-5, -1):
            if closes[i] > closes[i - 1]:
                dir_score += 1
            elif closes[i] < closes[i - 1]:
                dir_score -= 1

        dir_strength = abs(dir_score) / 5

        # --- SMA calculations
        sma5 = sum(closes[-5:]) / 5
        sma10 = sum(closes[-10:]) / 10

        last_price = closes[-1] if closes[-1] != 0 else 1e-9
        trend_strength = abs(sma5 - sma10) / last_price

        # --- UPDATED THRESHOLDS (FIXED)
        if (
            avg_range < 0.0012
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

    except Exception:
        # fail-safe
        return {
            "regime": "NO_TRADE",
            "avg_range": 0.0,
            "dir_strength": 0.0,
            "trend_strength": 0.0,
        }
```
