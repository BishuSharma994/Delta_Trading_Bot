from config.asset_rules import AssetRules


CHOP_SCORE_THRESHOLD = 0.95
TREND_STRENGTH_THRESHOLD = 0.00005


def _range_pct(candle: dict) -> float:
    close = float(candle["close"])
    if close == 0:
        return 0.0
    return (float(candle["high"]) - float(candle["low"])) / abs(close)


def _true_ranges(candles: list[dict]) -> list[float]:
    values = []
    prev_close = None

    for candle in candles:
        high = float(candle["high"])
        low = float(candle["low"])
        close = float(candle["close"])

        if prev_close is None:
            values.append(high - low)
        else:
            values.append(max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close),
            ))

        prev_close = close

    return values


def evaluate_regime_filter(candles: list[dict], asset_rules: AssetRules) -> dict:
    minimum = max(asset_rules.regime_lookback + 1, 12)
    if not candles or len(candles) < minimum:
        return {
            "regime": "RANGE",
            "allow_trade": False,
            "reason": "insufficient_regime_context",
            "avg_range": 0.0,
            "atr_pct": 0.0,
            "dir_strength": 0.0,
            "trend_strength": 0.0,
            "chop_score": 1.0,
        }

    recent = candles[-minimum:]
    closes = [float(candle["close"]) for candle in recent]
    last_close = closes[-1] if closes[-1] != 0 else 1e-9

    range_pcts = [_range_pct(candle) for candle in recent[-asset_rules.regime_lookback:]]
    avg_range = sum(range_pcts) / len(range_pcts) if range_pcts else 0.0

    true_ranges = _true_ranges(recent[-asset_rules.regime_lookback:])
    atr = sum(true_ranges) / len(true_ranges) if true_ranges else 0.0
    atr_pct = atr / abs(last_close)

    price_path = sum(
        abs(curr - prev)
        for prev, curr in zip(closes, closes[1:])
    )
    directional_efficiency = (
        abs(closes[-1] - closes[0]) / price_path
        if price_path > 0 else 0.0
    )

    fast_window = closes[-5:]
    slow_window = closes[-10:]
    fast_sma = sum(fast_window) / len(fast_window)
    slow_sma = sum(slow_window) / len(slow_window)
    trend_strength = abs(fast_sma - slow_sma) / abs(last_close)
    chop_score = 1.0 - directional_efficiency

    if trend_strength > TREND_STRENGTH_THRESHOLD:
        regime = "TRENDING"
        reason = "trend_strength_pass"
    else:
        regime = "RANGE"
        reason = "range"

    if chop_score > CHOP_SCORE_THRESHOLD:
        regime = "RANGE"
        reason = "high_chop_soft_range"

    return {
        "regime": regime,
        "allow_trade": True,
        "reason": reason,
        "avg_range": avg_range,
        "atr_pct": atr_pct,
        "dir_strength": directional_efficiency,
        "trend_strength": trend_strength,
        "chop_score": chop_score,
    }


def volatility_spike_detected(metrics: dict, asset_rules: AssetRules) -> bool:
    if not isinstance(metrics, dict):
        return False

    atr_pct = metrics.get("atr_pct")
    avg_range = metrics.get("avg_range")

    return bool(
        isinstance(atr_pct, (int, float))
        and atr_pct >= asset_rules.max_prefunding_atr_pct
    ) or bool(
        isinstance(avg_range, (int, float))
        and avg_range >= asset_rules.max_prefunding_avg_range_pct
    )
