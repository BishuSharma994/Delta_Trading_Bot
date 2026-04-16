from config.asset_rules import AssetRules


def _aggregate_candles(candles: list[dict], group_size: int) -> list[dict]:
    aggregated = []

    for index in range(0, len(candles), group_size):
        block = candles[index:index + group_size]
        if len(block) < group_size:
            continue

        aggregated.append({
            "open": float(block[0]["open"]),
            "high": max(float(candle["high"]) for candle in block),
            "low": min(float(candle["low"]) for candle in block),
            "close": float(block[-1]["close"]),
        })

    return aggregated


def detect_htf_bias(candles: list[dict], asset_rules: AssetRules) -> dict:
    required_candles = asset_rules.htf_group_size * asset_rules.htf_slow_blocks
    if not candles or len(candles) < required_candles:
        return {
            "bias": "NEUTRAL",
            "reason": "insufficient_htf_data",
            "trend_pct": 0.0,
            "fast_sma": 0.0,
            "slow_sma": 0.0,
        }

    recent = candles[-required_candles:]
    htf_candles = _aggregate_candles(recent, asset_rules.htf_group_size)

    if len(htf_candles) < asset_rules.htf_slow_blocks:
        return {
            "bias": "NEUTRAL",
            "reason": "insufficient_htf_blocks",
            "trend_pct": 0.0,
            "fast_sma": 0.0,
            "slow_sma": 0.0,
        }

    closes = [float(candle["close"]) for candle in htf_candles]
    highs = [float(candle["high"]) for candle in htf_candles]
    lows = [float(candle["low"]) for candle in htf_candles]

    fast_window = closes[-asset_rules.htf_fast_blocks:]
    slow_window = closes[-asset_rules.htf_slow_blocks:]

    fast_sma = sum(fast_window) / len(fast_window)
    slow_sma = sum(slow_window) / len(slow_window)
    last_close = closes[-1] if closes[-1] != 0 else 1e-9
    trend_pct = abs(fast_sma - slow_sma) / abs(last_close)

    higher_high = highs[-1] >= highs[-2]
    higher_low = lows[-1] >= lows[-2]
    lower_high = highs[-1] <= highs[-2]
    lower_low = lows[-1] <= lows[-2]

    if (
        fast_sma > slow_sma
        and closes[-1] > closes[0]
        and higher_high
        and higher_low
        and trend_pct >= asset_rules.min_htf_trend_pct
    ):
        bias = "LONG"
        reason = "htf_uptrend"
    elif (
        fast_sma < slow_sma
        and closes[-1] < closes[0]
        and lower_high
        and lower_low
        and trend_pct >= asset_rules.min_htf_trend_pct
    ):
        bias = "SHORT"
        reason = "htf_downtrend"
    else:
        bias = "NEUTRAL"
        reason = "htf_bias_unclear"

    return {
        "bias": bias,
        "reason": reason,
        "trend_pct": trend_pct,
        "fast_sma": fast_sma,
        "slow_sma": slow_sma,
    }
