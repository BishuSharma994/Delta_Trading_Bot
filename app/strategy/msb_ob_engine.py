# Stateful MSB + OB engine with continuation filter (FINAL FIX)

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

    # --- swing detection
    h0 = max(highs[-zigzag_len:])
    h1 = max(highs[-2 * zigzag_len : -zigzag_len])

    l0 = min(lows[-zigzag_len:])
    l1 = min(lows[-2 * zigzag_len : -zigzag_len])

    market = 0

    # --- MSB
    if h0 > h1 and h0 > h1 + abs(h1 - l0) * fib_factor:
        market = 1
    elif l0 < l1 and l0 < l1 - abs(h0 - l1) * fib_factor:
        market = -1

    # --- OB detection
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

    # --- STATE
    state = _get_state(symbol)

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

    # --- CONTINUATION FILTER (CRITICAL FIX)
    recent_range = (max(highs[-3:]) - min(lows[-3:])) / closes[-1]

    if recent_range < 0.0012:
        return {
            "signal": None,
            "market": market,
            "ob": ob,
        }

    # --- CONFIRMATION CANDLE
    momentum_confirm = closes[-1] > closes[-2]

    # --- SHORT ENTRY
    if market == -1 and state["was_inside_ob"]:
        if price < ob["low"] and closes[-1] < closes[-2]:
            state["was_inside_ob"] = False
            return {
                "signal": "SHORT",
                "sl": ob["high"],
                "reason": "OB_retest_breakdown_confirmed",
                "market": market,
                "ob": ob,
            }

    # --- LONG ENTRY
    if market == 1 and state["was_inside_ob"]:
        if price > ob["high"] and momentum_confirm:
            state["was_inside_ob"] = False
            return {
                "signal": "LONG",
                "sl": ob["low"],
                "reason": "OB_retest_breakout_confirmed",
                "market": market,
                "ob": ob,
            }

    return {
        "signal": None,
        "market": market,
        "ob": ob,
    }