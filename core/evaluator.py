# core/evaluator.py
# Institutional Evaluator — V2.3
# Execution GATED

from datetime import datetime, timezone
from Delta_Trading_Bot.data.memory import get_latest_strategy_vote


# Required features for base evaluation
REQUIRED_FEATURES = [
    "funding_rate_abs",
    "time_to_funding_sec",
    "pre_volatility_5m",
]


def _valid_vote(vote: dict) -> bool:
    """
    Defensive contract check.
    Ensures vote is a dict and contains a valid 'state'.
    """
    return (
        isinstance(vote, dict)
        and isinstance(vote.get("state"), str)
    )


def evaluate(features: dict, symbol: str | None = None) -> dict:
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
    funding_vote = get_latest_strategy_vote("funding_bias", symbol=symbol)
    vol_vote = get_latest_strategy_vote("volatility_regime", symbol=symbol)

    supporting_votes = []

    # -------- Funding Vote --------
    if _valid_vote(funding_vote):
        state = funding_vote["state"]
        if state not in ("NEUTRAL", "NO_DATA"):
            supporting_votes.append("funding_bias")

    # -------- Volatility Vote --------
    if _valid_vote(vol_vote):
        if (
            vol_vote.get("signal") in ("LONG", "SHORT")
            or vol_vote["state"] == "STRUCTURE_CONFIRMED"
        ):
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
        "state": "NO_EDGE",
        "score": 0.0,
        "notes": "Confluence not satisfied",
    }
