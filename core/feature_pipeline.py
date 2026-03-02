# core/feature_pipeline.py
# Pure feature derivation. No API calls. No side effects.
# Institutional Stable Version

from datetime import datetime, timezone
from statistics import stdev
import math

from Delta_Trading_Bot.data.memory import (
    get_latest_funding,
    get_recent_prices,
    get_latest_book,
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

        # -------- funding_rate_abs --------
        fr = funding.get("funding_rate")
        if isinstance(fr, (int, float)):
            features["funding_rate_abs"] = abs(float(fr))

        # -------- time_to_funding_sec (PRIMARY PATH) --------
        ttf = funding.get("time_to_funding_sec")
        if isinstance(ttf, (int, float)):
            # Guard against negative timing drift
            if ttf >= 0:
                features["time_to_funding_sec"] = float(ttf)

        # -------- Fallback: derive from next_funding_time_utc --------
        elif funding.get("next_funding_time_utc"):
            try:
                nft = funding["next_funding_time_utc"].replace("Z", "+00:00")
                next_time = datetime.fromisoformat(nft)
                now = datetime.now(timezone.utc)
                delta_sec = (next_time - now).total_seconds()

                if delta_sec >= 0:
                    features["time_to_funding_sec"] = float(delta_sec)
            except Exception:
                pass

    # =====================================================
    # PRICE VOLATILITY (5 MIN)
    # =====================================================
    prices_5m = get_recent_prices(symbol, minutes=5)

    if prices_5m and len(prices_5m) >= 2:
        returns = _log_returns(prices_5m)
        if returns and len(returns) >= 2:
            try:
                features["pre_volatility_5m"] = float(stdev(returns))
            except Exception:
                pass

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
                features["bid_ask_spread_pct"] = float((ask - bid) / mid)

    # =====================================================
    # FEATURE READINESS STATES
    # =====================================================
    required = [
        "funding_rate_abs",
        "time_to_funding_sec",
        "pre_volatility_5m",
    ]

    feature_states = {}
    for name in required:
        feature_states[name] = "hot" if name in features else "cold"

    features["_feature_states"] = feature_states

    return features