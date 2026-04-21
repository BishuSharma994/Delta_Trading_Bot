"""
brain/pattern_detector.py
Pure statistical pattern detection — no ML, no named candle patterns.
Detects recurring price behavior from raw OHLCV data.

4 pattern types:
    VOLATILITY_COMPRESSION_BREAKOUT   — compression → expansion
    MEAN_REVERSION_AFTER_EXTENSION    — Z-score overextension → revert
    TREND_CONTINUATION_PULLBACK       — trend → pullback → resume
    RANGE_BOUNDARY_REJECTION          — price hits range edge → reject
"""

import logging
import math

logger = logging.getLogger(__name__)


def _range(candle) -> float:
    return float(candle["high"]) - float(candle["low"])


def _body(candle) -> float:
    return abs(float(candle["close"]) - float(candle["open"]))


def _dir(candle) -> str:
    return "BULL" if float(candle["close"]) >= float(candle["open"]) else "BEAR"


def _pct(a, b) -> float:
    return (b - a) / a if a else 0.0


def _sma(vals: list, n: int) -> list:
    result = []
    for i in range(len(vals)):
        window = vals[max(0, i - n + 1): i + 1]
        result.append(sum(window) / len(window))
    return result


def _std(vals: list) -> float:
    if len(vals) < 2:
        return 0.0
    mean = sum(vals) / len(vals)
    return math.sqrt(sum((x - mean) ** 2 for x in vals) / len(vals))


def _atr(candles: list, period: int = 14) -> list:
    trs = []
    for i in range(1, len(candles)):
        high = float(candles[i]["high"])
        low = float(candles[i]["low"])
        prev_close = float(candles[i - 1]["close"])
        trs.append(max(high - low, abs(high - prev_close), abs(low - prev_close)))
    atrs = _sma(trs, period)
    return [0.0] * (len(candles) - len(atrs)) + atrs


def _ts(candle):
    return candle.get("time") or candle.get("timestamp")


# ── Pattern 1 ─────────────────────────────────────────────────────────────────

def detect_vol_compression_breakouts(
    candles: list,
    lookback: int = 20,
    compress_factor: float = 0.5,
) -> list:
    if len(candles) < lookback + 2:
        return []
    ranges = [_range(candle) for candle in candles]
    avg_ranges = _sma(ranges, lookback)
    results = []
    for i in range(lookback, len(candles) - 1):
        avg = avg_ranges[i]
        if not avg:
            continue
        compressed = ranges[i] < avg * compress_factor
        breakout = ranges[i + 1] > avg * 1.5
        if compressed and breakout:
            direction = _dir(candles[i + 1])
            outcome_pct = _pct(
                float(candles[i]["close"]),
                float(candles[i + 1]["close"]),
            )
            if direction == "BEAR":
                outcome_pct = -outcome_pct
            results.append(
                {
                    "pattern": "VOLATILITY_COMPRESSION_BREAKOUT",
                    "index": i,
                    "timestamp": _ts(candles[i]),
                    "direction": direction,
                    "compression_ratio": round(ranges[i] / avg, 4),
                    "breakout_ratio": round(ranges[i + 1] / avg, 4),
                    "outcome_pct": round(outcome_pct, 6),
                    "success": outcome_pct > 0,
                }
            )
    return results


# ── Pattern 2 ─────────────────────────────────────────────────────────────────

def detect_mean_reversion_after_extension(
    candles: list,
    lookback: int = 20,
    extension_z: float = 2.0,
) -> list:
    if len(candles) < lookback + 2:
        return []
    closes = [float(candle["close"]) for candle in candles]
    results = []
    for i in range(lookback, len(candles) - 1):
        window = closes[i - lookback: i]
        mean = sum(window) / len(window)
        std = _std(window)
        if not std:
            continue
        z_score = (closes[i] - mean) / std
        if abs(z_score) < extension_z:
            continue
        expected = "BEAR" if z_score > 0 else "BULL"
        outcome_pct = _pct(closes[i], closes[i + 1])
        if expected == "BEAR":
            outcome_pct = -outcome_pct
        results.append(
            {
                "pattern": "MEAN_REVERSION_AFTER_EXTENSION",
                "index": i,
                "timestamp": _ts(candles[i]),
                "direction": expected,
                "z_score": round(z_score, 4),
                "outcome_pct": round(outcome_pct, 6),
                "success": outcome_pct > 0,
            }
        )
    return results


# ── Pattern 3 ─────────────────────────────────────────────────────────────────

def detect_trend_continuation_pullbacks(
    candles: list,
    trend_period: int = 50,
    pullback_period: int = 5,
) -> list:
    if len(candles) < trend_period + pullback_period + 2:
        return []
    closes = [float(candle["close"]) for candle in candles]
    ema_fast = _sma(closes, 20)
    ema_slow = _sma(closes, trend_period)
    results = []
    for i in range(trend_period, len(candles) - pullback_period - 1):
        trend_up = ema_fast[i] > ema_slow[i] * 1.001
        trend_down = ema_fast[i] < ema_slow[i] * 0.999
        if not (trend_up or trend_down):
            continue
        pullback_window = closes[i - pullback_period: i]
        if trend_up:
            pullback = all(
                pullback_window[j] >= pullback_window[j + 1]
                for j in range(len(pullback_window) - 1)
            )
            expected = "BULL"
        else:
            pullback = all(
                pullback_window[j] <= pullback_window[j + 1]
                for j in range(len(pullback_window) - 1)
            )
            expected = "BEAR"
        if not pullback:
            continue
        outcome_pct = _pct(closes[i], closes[i + 1])
        if expected == "BEAR":
            outcome_pct = -outcome_pct
        results.append(
            {
                "pattern": "TREND_CONTINUATION_PULLBACK",
                "index": i,
                "timestamp": _ts(candles[i]),
                "direction": expected,
                "trend": "UP" if trend_up else "DOWN",
                "outcome_pct": round(outcome_pct, 6),
                "success": outcome_pct > 0,
            }
        )
    return results


# ── Pattern 4 ─────────────────────────────────────────────────────────────────

def detect_range_boundary_rejections(
    candles: list,
    lookback: int = 30,
    tolerance: float = 0.002,
) -> list:
    if len(candles) < lookback + 2:
        return []
    results = []
    for i in range(lookback, len(candles) - 1):
        window = candles[i - lookback: i]
        range_high = max(float(candle["high"]) for candle in window)
        range_low = min(float(candle["low"]) for candle in window)
        range_size = range_high - range_low
        if not range_size:
            continue
        close = float(candles[i]["close"])
        near_high = (range_high - float(candles[i]["low"])) / range_size < tolerance
        near_low = (float(candles[i]["high"]) - range_low) / range_size < tolerance
        if not (near_high or near_low):
            continue
        expected = "BEAR" if near_high else "BULL"
        outcome_pct = _pct(close, float(candles[i + 1]["close"]))
        if expected == "BEAR":
            outcome_pct = -outcome_pct
        results.append(
            {
                "pattern": "RANGE_BOUNDARY_REJECTION",
                "index": i,
                "timestamp": _ts(candles[i]),
                "direction": expected,
                "boundary": "HIGH" if near_high else "LOW",
                "outcome_pct": round(outcome_pct, 6),
                "success": outcome_pct > 0,
            }
        )
    return results


# ── Master runner ─────────────────────────────────────────────────────────────

def run_all_detectors(candles: list, symbol: str, resolution: str) -> list:
    all_patterns = []
    detectors = [
        detect_vol_compression_breakouts,
        detect_mean_reversion_after_extension,
        detect_trend_continuation_pullbacks,
        detect_range_boundary_rejections,
    ]
    for detector in detectors:
        try:
            patterns = detector(candles)
            for pattern in patterns:
                pattern["symbol"] = symbol
                pattern["resolution"] = resolution
            all_patterns.extend(patterns)
            logger.info(
                f"  {detector.__name__}: {len(patterns)} on {symbol} {resolution}"
            )
        except Exception as exc:
            logger.error(
                f"  {detector.__name__} failed {symbol} {resolution}: {exc}"
            )
    return all_patterns
