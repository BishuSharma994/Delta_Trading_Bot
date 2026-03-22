# app/strategy/msb_ob_engine.py

# Stateful MSB + Order Block engine (aligned with Pine logic)

zigzag_len = 9
fib_factor = 0.273

# --- persistent per-symbol state
_SYMBOL_STATE = {}


def _get_state(symbol: str) -> dict:
    if symbol not in _SYMBOL_STATE:
        _SYMBOL_STATE[symbol] = {
            "was_inside_ob": False,
            "last_ob": None,
        }
    return _SYMBOL_STATE[symbol]


def process_structure(symbol: str, candles: list[dict]) -> dict:
    if not candles or len(candles) < 20:
        return {"signal": None, "market": 0, "ob": None}

    highs = [float(c["high"]) for c in candles]
    lows = [float(c["low"]) for c in candles]
    closes = [float(c["close"]) for c in candles]
    opens = [float(c["open"]) for c in candles]

    # --- simple swing approximation (same as before)
    h0 = max(highs[-zigzag_len:])
    h1 = max(highs[-2 * zigzag_len : -zigzag_len])

    l0 = min(lows[-zigzag_len:])
    l1 = min(lows[-2 * zigzag_len : -zigzag_len])

    market = 0

    # --- MSB detection
    if h0 > h1 and h0 > h1 + abs(h1 - l0) * fib_factor:
        market = 1
    elif l0 < l1 and l0 < l1 - abs(h0 - l1) * fib_factor:
        market = -1

    # --- detect OB
    ob = None

    if market == 1:
        for i in range(len(candles) - 2, len(candles) - zigzag_len, -1):
            if opens[i] > closes[i]:  # bearish candle
                ob = {
                    "type": "BU_OB",
                    "high": highs[i],
                    "low": lows[i],
                }
                break

    elif market == -1:
        for i in range(len(candles) - 2, len(candles) - zigzag_len, -1):
            if opens[i] < closes[i]:  # bullish candle
                ob = {
                    "type": "BE_OB",
                    "high": highs[i],
                    "low": lows[i],
                }
                break

    if ob is None:
        return {"signal": None, "market": market, "ob": None}

    price = closes[-1]

    # --- STATE
    state = _get_state(symbol)

    # reset state if OB changes
    if state["last_ob"] != ob:
        state["was_inside_ob"] = False
        state["last_ob"] = ob

    inside_ob = ob["low"] <= price <= ob["high"]

    # --- STEP 1: mark entry into OB
    if inside_ob:
        state["was_inside_ob"] = True
        return {
            "signal": None,
            "market": market,
            "ob": ob,
        }

    # --- STEP 2: trigger after leaving OB

    # SHORT
    if market == -1 and state["was_inside_ob"] and price < ob["low"]:
        state["was_inside_ob"] = False
        return {
            "signal": "SHORT",
            "sl": ob["high"],
            "reason": "OB_retest_breakdown",
            "market": market,
            "ob": ob,
        }

    # LONG
    if market == 1 and state["was_inside_ob"] and price > ob["high"]:
        state["was_inside_ob"] = False
        return {
            "signal": "LONG",
            "sl": ob["low"],
            "reason": "OB_retest_breakout",
            "market": market,
            "ob": ob,
        }

    return {
        "signal": None,
        "market": market,
        "ob": ob,
    }