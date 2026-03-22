zigzag_len = 9
fib_factor = 0.273


def _recent_retest(candles, ob):
    for candle in candles:
        if candle["high"] >= ob["low"] and candle["low"] <= ob["high"]:
            return True
    return False


def process_structure(candles):
    if len(candles) < 20:
        return {"signal": None, "market": 0, "ob": None}

    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    closes = [c["close"] for c in candles]
    opens = [c["open"] for c in candles]

    h0 = max(highs[-zigzag_len:])
    h1 = max(highs[-2 * zigzag_len : -zigzag_len])

    l0 = min(lows[-zigzag_len:])
    l1 = min(lows[-2 * zigzag_len : -zigzag_len])

    market = 0

    if h0 > h1 and h0 > h1 + abs(h1 - l0) * fib_factor:
        market = 1
    elif l0 < l1 and l0 < l1 - abs(h0 - l1) * fib_factor:
        market = -1

    ob = None

    if market == 1:
        for i in range(len(candles) - 2, len(candles) - zigzag_len, -1):
            if opens[i] > closes[i]:
                ob = {
                    "type": "BU_OB",
                    "high": highs[i],
                    "low": lows[i],
                }
                break

    elif market == -1:
        for i in range(len(candles) - 2, len(candles) - zigzag_len, -1):
            if opens[i] < closes[i]:
                ob = {
                    "type": "BE_OB",
                    "high": highs[i],
                    "low": lows[i],
                }
                break

    if ob is None:
        return {"signal": None, "market": market, "ob": None}

    price = closes[-1]
    # The prompt's in-zone and beyond-boundary checks cannot both be true at once,
    # so we require a recent retest before the current close confirms the break.
    recent_retest = _recent_retest(candles[-3:-1], ob)

    if market == 1 and recent_retest and price > ob["high"]:
        return {
            "signal": "LONG",
            "sl": ob["low"],
            "reason": "OB_retest_confirmation",
            "market": market,
            "ob": ob,
        }

    if market == -1 and recent_retest and price < ob["low"]:
        return {
            "signal": "SHORT",
            "sl": ob["high"],
            "reason": "OB_retest_confirmation",
            "market": market,
            "ob": ob,
        }

    return {"signal": None, "market": market, "ob": ob}
