# core/evaluator.py
# Evaluates feature vectors. NO execution logic.

REQUIRED_FEATURES = [
    "funding_rate_abs",
    "time_to_funding_sec",
    "pre_volatility_5m",
    "bid_ask_spread_pct",
]


def evaluate(features: dict):
    missing = [f for f in REQUIRED_FEATURES if f not in features]

    if missing:
        return {
            "status": "insufficient_data",
            "allow": False,
            "missing": missing,
        }

    return {
        "status": "rejected",
        "allow": False,
        "reason": "baseline_v1_guardrail",
    }
