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
        result = {
            "ts": now,
            "state": "INSUFFICIENT_DATA",
            "score": 0.0,
            "missing": missing,
            "notes": "Required features missing",
        }
        print("CHECK_EVAL", {
            "state": result["state"],
            "direction": direction if "direction" in locals() else None,
        })
        return result

    # -------------------------
    # STRATEGY CONFLUENCE
    # -------------------------
    funding_vote = get_latest_strategy_vote("funding_bias", symbol=symbol)
    vol_vote = get_latest_strategy_vote("volatility_regime", symbol=symbol)
    msb_vote = get_latest_strategy_vote("msb", symbol=symbol)
    ob_vote = get_latest_strategy_vote("order_block", symbol=symbol)

    supporting_votes = []

    def _extract_msb_direction(vote: dict | None) -> int:
        if isinstance(vote, dict):
            bias = vote.get("bias")
            market = vote.get("market")
            signal = vote.get("signal")

            if bias in (1, -1):
                return int(bias)
            if market in (1, -1):
                return int(market)
            if signal == "LONG":
                return 1
            if signal == "SHORT":
                return -1

        if isinstance(vol_vote, dict):
            market = vol_vote.get("market")
            signal = vol_vote.get("signal")

            if market in (1, -1):
                return int(market)
            if signal == "LONG":
                return 1
            if signal == "SHORT":
                return -1

        return 0

    def _extract_ob_type(vote: dict | None) -> str | None:
        if isinstance(vote, dict):
            if vote.get("type") in {"BU_OB", "BE_OB"}:
                return vote.get("type")
            ob_block = vote.get("ob")
            if isinstance(ob_block, dict) and ob_block.get("type") in {"BU_OB", "BE_OB"}:
                return ob_block.get("type")

        if isinstance(vol_vote, dict):
            ob_block = vol_vote.get("ob")
            if isinstance(ob_block, dict) and ob_block.get("type") in {"BU_OB", "BE_OB"}:
                return ob_block.get("type")

        return None

    regime = vol_vote.get("regime") if isinstance(vol_vote, dict) else None
    htf_bias = vol_vote.get("htf_bias") if isinstance(vol_vote, dict) else None
    chop_score = vol_vote.get("chop_score") if isinstance(vol_vote, dict) else None
    trend_strength = vol_vote.get("trend_strength") if isinstance(vol_vote, dict) else None

    print("CHECK_FEATURES", {
        "msb": msb_vote,
        "ob": ob_vote,
        "regime": regime
    })

    msb_direction = _extract_msb_direction(msb_vote)
    ob_type = _extract_ob_type(ob_vote)

    direction = None
    if msb_direction == 1 and ob_type == "BU_OB":
        direction = "LONG"
    elif msb_direction == -1 and ob_type == "BE_OB":
        direction = "SHORT"

    structure_aligned = direction in {"LONG", "SHORT"}

    # -------- Structural Vote --------
    if structure_aligned:
        supporting_votes.append("structure")

    # -------- Funding Vote (optional) --------
    if _valid_vote(funding_vote):
        state = funding_vote["state"]
        if state not in ("NEUTRAL", "NO_DATA"):
            supporting_votes.append("funding_bias")

    # -------- Volatility / Regime Vote (optional) --------
    relaxed_regime_ok = (
        regime == "TRENDING"
        or (
            isinstance(chop_score, (int, float))
            and isinstance(trend_strength, (int, float))
            and float(chop_score) < 0.7
            and float(trend_strength) > 0.0008
        )
    )
    if _valid_vote(vol_vote):
        if (
            vol_vote.get("signal") in ("LONG", "SHORT")
            or vol_vote["state"] == "STRUCTURE_CONFIRMED"
            or relaxed_regime_ok
        ):
            supporting_votes.append("volatility_regime")

    # -------------------------
    # EDGE DETECTION (NO EXECUTION)
    # -------------------------
    core_edge = regime == "TRENDING" and structure_aligned
    fallback_edge = structure_aligned

    if core_edge or fallback_edge or len(supporting_votes) >= 1:
        notes = "Confluence detected"
        if core_edge:
            notes = "Structural trend confluence detected"
        elif fallback_edge:
            notes = "MSB and order block aligned"

        score = 0.0
        if structure_aligned and relaxed_regime_ok:
            score = 1.0
        elif structure_aligned:
            score = 0.9
        elif supporting_votes:
            score = min(1.0, round(len(supporting_votes) / 2, 2))

        result = {
            "ts": now,
            "state": "EDGE_DETECTED",
            "score": score,
            "supporting_votes": supporting_votes,
            "notes": notes,
        }

        if direction:
            result["direction"] = direction
        if regime is not None:
            result["regime"] = regime
        if htf_bias is not None:
            result["htf_bias"] = htf_bias
        if isinstance(chop_score, (int, float)):
            result["chop_score"] = float(chop_score)
        if isinstance(trend_strength, (int, float)):
            result["trend_strength"] = float(trend_strength)
        if msb_direction in (1, -1):
            result["msb"] = msb_direction
        if ob_type in {"BU_OB", "BE_OB"}:
            result["ob_type"] = ob_type

        print("CHECK_EVAL", {
            "state": result["state"],
            "direction": direction if "direction" in locals() else None,
        })
        return result

    # -------------------------
    # DEFAULT SAFE STATE
    # -------------------------
    result = {
        "ts": now,
        "state": "NO_EDGE",
        "score": 0.0,
        "notes": "Confluence not satisfied",
    }
    print("CHECK_EVAL", {
        "state": result["state"],
        "direction": direction if "direction" in locals() else None,
    })
    return result
