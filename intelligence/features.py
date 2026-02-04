# Feature computation functions
# Pure functions only. No I/O. No API. No state.

import math
from statistics import stdev


def _log_returns(prices):
    if len(prices) < 2:
        raise ValueError("At least two prices required")

    returns = []
    for i in range(1, len(prices)):
        if prices[i - 1] <= 0 or prices[i] <= 0:
            raise ValueError("Prices must be positive")
        returns.append(math.log(prices[i] / prices[i - 1]))
    return returns


def pre_volatility_5m(prices_5m):
    """
    prices_5m: list of mark prices sampled over last 5 minutes
    """
    returns = _log_returns(prices_5m)
    return stdev(returns)


def pre_volatility_15m(prices_15m):
    """
    prices_15m: list of mark prices sampled over last 15 minutes
    """
    returns = _log_returns(prices_15m)
    return stdev(returns)

def pre_trend_slope_15m(prices_15m):
    """
    Linear slope of price over 15 minutes.
    Positive = uptrend, Negative = downtrend
    """
    n = len(prices_15m)
    if n < 2:
        raise ValueError("At least two prices required")

    x = list(range(n))
    y = prices_15m

    x_mean = sum(x) / n
    y_mean = sum(y) / n

    numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

    if denominator == 0:
        raise ValueError("Degenerate trend window")

    return numerator / denominator

def bid_ask_spread_pct(bid_price, ask_price):
    """
    Percentage bid-ask spread relative to mid price
    """
    if bid_price <= 0 or ask_price <= 0:
        raise ValueError("Prices must be positive")

    if ask_price < bid_price:
        raise ValueError("Ask price cannot be lower than bid price")

    mid = (bid_price + ask_price) / 2
    return (ask_price - bid_price) / mid

def pre_trend_slope_15m(prices_15m):
    """
    Linear slope of price over 15 minutes.
    Positive = uptrend, Negative = downtrend
    """
    n = len(prices_15m)
    if n < 2:
        raise ValueError("At least two prices required")

    x = list(range(n))
    y = prices_15m

    x_mean = sum(x) / n
    y_mean = sum(y) / n

    numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

    if denominator == 0:
        raise ValueError("Degenerate trend window")

    return numerator / denominator

def bid_ask_spread_pct(bid_price, ask_price):
    """
    Percentage bid-ask spread relative to mid price
    """
    if bid_price <= 0 or ask_price <= 0:
        raise ValueError("Prices must be positive")

    if ask_price < bid_price:
        raise ValueError("Ask price cannot be lower than bid price")

    mid = (bid_price + ask_price) / 2
    return (ask_price - bid_price) / mid
