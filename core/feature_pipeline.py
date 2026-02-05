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
    """
    Build a pure feature vector from historical memory.
    Missing features are omitted by design.
    """
    features = {}

    # =====================================================
    # FUNDING FEATURES
    # =====================================================
    funding = get_latest_funding(symbol)

    if funding and "funding_rate" in funding and "next_funding_time_utc" in funding:
        # Absolute funding rate
        if isinstance(funding["funding_rate"], (int, float)):
            features["funding_rate_abs"] = abs(funding["funding_rate"])

        # Time to next funding (seconds)
        try:
            next_time = funding["next_funding_time_utc"].replace("Z", "+00:00")
            next_funding_time = datetime.fromisoformat(next_time)
            now_utc = datetime.now(timezone.utc)
            delta_sec = (next_funding_time - now_utc).total_seconds()

            if delta_sec >= 0:
                features["time_to_funding_sec"] = delta_sec
        except Exception:
            pass  # malformed timestamp → feature remains missing

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

    if book and "best_bid" in book and "best_ask" in book:
        bid = book["best_bid"]
        ask = book["best_ask"]

        if bid > 0 and ask > bid:
            mid = (bid + ask) / 2
            features["bid_ask_spread_pct"] = (ask - bid) / mid

    return features
