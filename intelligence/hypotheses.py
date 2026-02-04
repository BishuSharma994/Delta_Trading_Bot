# Hypotheses and rejection rules
# Read-only declarations. No execution. No thresholds tied to capital.

HYPOTHESES_VERSION = "v1.12"

# Each hypothesis returns PASS/FAIL with reason codes
HYPOTHESES = [
    {
        "name": "stable_pre_funding_structure",
        "description": "Pre-funding price action is stable and non-chaotic",
        "reject_if": [
            "pre_volatility_5m_high",
            "pre_volatility_15m_high",
            "gap_risk_score_high",
        ],
    },
    {
        "name": "liquidity_sufficient",
        "description": "Order book and volume sufficient to avoid slippage traps",
        "reject_if": [
            "bid_ask_spread_pct_high",
            "volume_1m_norm_low",
        ],
    },
    {
        "name": "funding_edge_not_crowded",
        "description": "Funding is elevated but not signaling crowded positioning",
        "reject_if": [
            "funding_rate_abs_extreme",
            "funding_rate_delta_spike",
        ],
    },
    {
        "name": "historical_post_funding_survivability",
        "description": "Past funding events did not cause unacceptable drawdowns",
        "reject_if": [
            "post_max_adverse_excursion_high",
            "post_drawdown_5m_high",
        ],
    },
]
