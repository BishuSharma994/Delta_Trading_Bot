# Feature pipeline
# Derives features from recorded market memory
# No execution. No evaluator. No thresholds.

import json
from pathlib import Path

from intelligence.features import (
    pre_volatility_5m,
    pre_volatility_15m,
    pre_trend_slope_15m,
    bid_ask_spread_pct,
    time_to_funding_sec,
)

EVENTS_DIR = Path("data/events")


def _load_events(event_type: str):
    file = EVENTS_DIR / f"{event_type}.jsonl"
    if not file.exists():
        return []

    with open(file) as f:
        return [json.loads(line) for line in f]


def build_feature_vector(symbol: str):
    """
    Build feature vector for a symbol using recent market memory.
    """

    price_events = _load_events("price_snapshot")
    funding_events = _load_events("funding_snapshot")

    # Filter by symbol
    price_events = [
        e for e in price_events if e["payload"]["symbol"] == symbol
    ]
    funding_events = [
        e for e in funding_events if e["payload"]["symbol"] == symbol
    ]

    if len(price_events) < 15 or len(funding_events) < 1:
        return None

    # --- PRICE FEATURES ---
    prices_5m = [
        e["payload"]["mark_price"] for e in price_events[-5:]
    ]
    prices_15m = [
        e["payload"]["mark_price"] for e in price_events[-15:]
    ]

    latest_price = price_events[-1]["payload"]
    bid = latest_price["best_bid"]
    ask = latest_price["best_ask"]

    # --- FUNDING FEATURES ---
    latest_funding = funding_events[-1]["payload"]

    now_utc = price_events[-1]["timestamp_utc"]
    next_funding_time = latest_funding["next_funding_time_utc"]

    tts = time_to_funding_sec(
        next_funding_time_utc=next_funding_time,
        now_utc=now_utc,
    )

    features = {
        "pre_volatility_5m": pre_volatility_5m(prices_5m),
        "pre_volatility_15m": pre_volatility_15m(prices_15m),
        "pre_trend_slope_15m": pre_trend_slope_15m(prices_15m),
        "bid_ask_spread_pct": bid_ask_spread_pct(bid, ask),
        "funding_rate_abs": abs(latest_funding["funding_rate_pct"]),
        "time_to_funding_sec": tts,
    }

    return features

