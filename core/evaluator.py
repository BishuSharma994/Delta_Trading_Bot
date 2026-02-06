# core/evaluator.py
# Institutional Evaluator — V2.2
# Execution GATED

from datetime import datetime, timezone
from data.memory import get_latest_strategy_vote

# Required features for base evaluation
REQUIRED_FEATURES = [
    "funding_rate_abs",
    "time_to_funding_sec",
    "pre_volatility_5m",
]


def evaluate(features: dict) -> dict:
    now = datetime.now(timezone.utc).isoformat()

    # -------------------------
    # FEATURE PRESENCE CHECK
    # -------------------------
    missing = [f for f in REQUIRED_FEATURES if f not in features]

    if missing:
        return {
            "ts": now,
            "state": "INSUFFICIENT_DATA",
            "score": 0.0,
            "missing": missing,
            "notes": "Required features missing",
        }

    # -------------------------
    # STRATEGY CONFLUENCE
    # -------------------------
    funding_vote = get_latest_strategy_vote("funding_bias")
    vol_vote = get_latest_strategy_vote("volatility_regime")

    supporting_votes = []

    if funding_vote and funding_vote["state"] not in ("NEUTRAL", "NO_DATA"):
        supporting_votes.append("funding_bias")

    if vol_vote and vol_vote["state"] == "EXPANSION_DETECTED":
        supporting_votes.append("volatility_regime")

    # -------------------------
    # EDGE DETECTION (NO EXECUTION)
    # -------------------------
    if len(supporting_votes) >= 2:
        return {
            "ts": now,
            "state": "EDGE_DETECTED",
            "score": round(len(supporting_votes) / 2, 2),
            "supporting_votes": supporting_votes,
            "notes": "Multi-strategy confluence detected",
        }

    # -------------------------
    # DEFAULT SAFE STATE
    # -------------------------
    return {
        "ts": now,
        "state": "INSUFFICIENT_DATA",
        "score": 0.0,
        "notes": "Confluence not satisfied",
    }
