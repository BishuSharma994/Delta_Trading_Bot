# core/feature_pipeline.py
# Pure feature derivation. No API calls. No side effects.

from datetime import datetime, timezone
from statistics import stdev
import math

from data.memory import (
    get_latest_funding,
    get_recent_prices,
    get_latest_book
)

# -------------------------
# Helpers
# -------------------------
def _log_returns(prices):
    returns = []
    for i in range(1, len(prices)):
        if prices[i - 1] <= 0 or prices[i] <= 0:
            return None
        returns.append(math.log(prices[i] / prices[i - 1]))
    return returns


# -------------------------
# Feature Builder
# -------------------------
def build_feature_vector(symbol: str):
    features = {}

    # =====================================================
    # FUNDING FEATURES
    # =====================================================
    funding = get_latest_funding(symbol)

    if funding:
        # Absolute funding rate
        fr = funding.get("funding_rate")
        if isinstance(fr, (int, float)):
            features["funding_rate_abs"] = abs(fr)

        # Time to next funding
        nft = funding.get("next_funding_time_utc")
        if nft:
            try:
                nft = nft.replace("Z", "+00:00")
                next_time = datetime.fromisoformat(nft)
                now = datetime.now(timezone.utc)
                delta_sec = (next_time - now).total_seconds()
                if delta_sec >= 0:
                    features["time_to_funding_sec"] = delta_sec
            except Exception:
                pass

    # =====================================================
    # PRICE VOLATILITY (5 MIN)
    # =====================================================
    prices_5m = get_recent_prices(symbol, minutes=5)

    if prices_5m and len(prices_5m) >= 2:
        returns = _log_returns(prices_5m)
        if returns and len(returns) >= 2:
            features["pre_volatility_5m"] = stdev(returns)

    # =====================================================
    # BID / ASK SPREAD
    # =====================================================
    book = get_latest_book(symbol)

    if book:
        bid = book.get("best_bid")
        ask = book.get("best_ask")

        if isinstance(bid, (int, float)) and isinstance(ask, (int, float)):
            if bid > 0 and ask > bid:
                mid = (bid + ask) / 2
                features["bid_ask_spread_pct"] = (ask - bid) / mid

    # =====================================================
    # FEATURE READINESS STATES (STEP 2)
    # =====================================================
    feature_states = {}

    for name in [
        "funding_rate_abs",
        "time_to_funding_sec",
        "pre_volatility_5m",
    ]:
        feature_states[name] = "hot" if name in features else "cold"

    features["_feature_states"] = feature_states

    return features
