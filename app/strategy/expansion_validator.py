from config.asset_rules import AssetRules


def _range_size(candle: dict) -> float:
    return max(0.0, float(candle["high"]) - float(candle["low"]))


def _range_pct(candle: dict) -> float:
    close = float(candle["close"])
    if close == 0:
        return 0.0
    return _range_size(candle) / abs(close)


def _body_ratio(candle: dict) -> float:
    total_range = _range_size(candle)
    if total_range <= 0:
        return 0.0
    body = abs(float(candle["close"]) - float(candle["open"]))
    return body / total_range


def _detect_liquidity_sweep(
    direction: str,
    candles: list[dict],
    lookback: int,
) -> bool:
    if len(candles) < lookback + 2:
        return False

    probe = candles[-2]
    reference = candles[-(lookback + 2):-2]

    if not reference:
        return False

    if direction == "LONG":
        prior_low = min(float(candle["low"]) for candle in reference)
        return (
            float(probe["low"]) < prior_low
            and float(probe["close"]) > prior_low
        )

    prior_high = max(float(candle["high"]) for candle in reference)
    return (
        float(probe["high"]) > prior_high
        and float(probe["close"]) < prior_high
    )


def validate_expansion(
    direction: str,
    candles: list[dict],
    structure_level: float,
    asset_rules: AssetRules,
) -> dict:
    if direction not in {"LONG", "SHORT"} or len(candles) < asset_rules.displacement_lookback + 1:
        return {
            "is_valid": False,
            "reason": "insufficient_displacement_context",
            "current_range": 0.0,
            "current_range_pct": 0.0,
            "avg_range": 0.0,
            "avg_range_pct": 0.0,
            "displacement_ratio": 0.0,
            "body_ratio": 0.0,
            "close_beyond_structure": False,
            "liquidity_sweep": False,
        }

    current = candles[-1]
    previous = candles[-(asset_rules.displacement_lookback + 1):-1]

    current_range = _range_size(current)
    current_range_pct = _range_pct(current)

    previous_ranges = [_range_size(candle) for candle in previous]
    previous_range_pcts = [_range_pct(candle) for candle in previous]

    avg_range = sum(previous_ranges) / len(previous_ranges) if previous_ranges else 0.0
    avg_range_pct = (
        sum(previous_range_pcts) / len(previous_range_pcts)
        if previous_range_pcts else 0.0
    )

    body_ratio = _body_ratio(current)
    close_price = float(current["close"])
    open_price = float(current["open"])
    displacement_ratio = current_range / avg_range if avg_range > 0 else 0.0
    liquidity_sweep = _detect_liquidity_sweep(
        direction,
        candles,
        asset_rules.liquidity_sweep_lookback,
    )

    if direction == "LONG":
        close_beyond_structure = close_price > structure_level * (
            1 + asset_rules.structure_close_buffer_pct
        )
        directional_body = close_price > open_price
    else:
        close_beyond_structure = close_price < structure_level * (
            1 - asset_rules.structure_close_buffer_pct
        )
        directional_body = close_price < open_price

    is_valid = (
        directional_body
        and avg_range > 0
        and current_range >= avg_range * asset_rules.displacement_range_multiplier
        and body_ratio >= asset_rules.min_body_ratio
        and close_beyond_structure
    )

    if is_valid:
        reason = "expansion_confirmed"
    elif not directional_body:
        reason = "directional_body_failed"
    elif avg_range <= 0:
        reason = "avg_range_unavailable"
    elif current_range < avg_range * asset_rules.displacement_range_multiplier:
        reason = "range_not_expanded"
    elif body_ratio < asset_rules.min_body_ratio:
        reason = "body_too_small"
    else:
        reason = "close_inside_structure"

    return {
        "is_valid": is_valid,
        "reason": reason,
        "current_range": current_range,
        "current_range_pct": current_range_pct,
        "avg_range": avg_range,
        "avg_range_pct": avg_range_pct,
        "displacement_ratio": displacement_ratio,
        "body_ratio": body_ratio,
        "close_beyond_structure": close_beyond_structure,
        "liquidity_sweep": liquidity_sweep,
    }
