# core/feature_pipeline.py
# Pure feature derivation. No API calls. No side effects.

from datetime import timezone
from data.memory import (
    get_latest_funding,
    get_recent_prices,
    get_latest_book
)
from statistics import stdev
import math


def _log_returns(prices):
    returns = []
    for i in range(1, len(prices)):
        if prices[i - 1] <= 0 or prices[i] <= 0:
            return None
        returns.append(math.log(prices[i] / prices[i - 1]))
    return returns


def build_feature_vector(symbol: str):
    features = {}

    # --- FUNDING FEATURES ---
    funding = get_latest_funding(symbol)
    if funding:
        features["funding_rate_abs"] = abs(funding["funding_rate"])
        features["time_to_funding_sec"] = funding["time_to_funding_sec"]

    # --- PRICE VOLATILITY (5m) ---
    prices_5m = get_recent_prices(symbol, minutes=5)
    if prices_5m and len(prices_5m) >= 2:
        returns = _log_returns(prices_5m)
        if returns and len(returns) >= 2:
            features["pre_volatility_5m"] = stdev(returns)

    # --- BID ASK SPREAD ---
    book = get_latest_book(symbol)
    if book:
        bid = book["best_bid"]
        ask = book["best_ask"]
        if bid > 0 and ask > bid:
            mid = (bid + ask) / 2
            features["bid_ask_spread_pct"] = (ask - bid) / mid

    return features
