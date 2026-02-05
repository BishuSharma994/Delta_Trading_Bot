# Intelligence Feature Registry
# Read-only declarations. No logic. No imports.

FEATURE_SET_VERSION = "v1.11"

FEATURES = [
    # Pre-funding
    "pre_volatility_5m",
    "pre_volatility_15m",
    "pre_trend_slope_15m",
    "spread_stress_avg_1m",

    # Funding context
    "funding_rate_abs",
    "funding_rate_delta",
    "time_to_funding_sec",

    # Post-funding (backtest-only)
    "post_max_adverse_excursion_1m",
    "post_drawdown_5m",
    "post_reversion_speed",

    # Liquidity & stability
    "bid_ask_spread_pct",
    "volume_1m_norm",
    "gap_risk_score",
]
