# core/evaluator.py
# Deterministic finite-state evaluator (institutional grade)

from datetime import datetime, timezone

REQUIRED_FEATURES = {
    "funding_rate_abs",
    "time_to_funding_sec",
    "pre_volatility_5m",
}

EDGE_SCORE_THRESHOLD = 0.75
PERSISTENCE_REQUIRED = 3

_state = "INSUFFICIENT_DATA"
_persist = 0


def _now():
    return datetime.now(timezone.utc).isoformat()


def evaluate(features: dict):
    global _state, _persist

    # ---------------------------
    # MISSING FEATURES
    # ---------------------------
    missing = [k for k in REQUIRED_FEATURES if k not in features]

    decision = {
        "ts": _now(),
        "state": None,
        "score": 0.0,
        "missing": missing,
        "notes": "",
    }

    # ---------------------------
    # INSUFFICIENT DATA
    # ---------------------------
    if missing:
        _state = "INSUFFICIENT_DATA"
        _persist = 0
        decision["state"] = _state
        decision["notes"] = "Required features missing"
        return decision

    # ---------------------------
    # SCORE (DEFENSIVE)
    # ---------------------------
    score = 0.0

    fr = features.get("funding_rate_abs")
    if isinstance(fr, (int, float)):
        score += min(fr * 10, 0.4)

    vol = features.get("pre_volatility_5m")
    if isinstance(vol, (int, float)):
        score += min(vol * 5, 0.4)

    ttf = features.get("time_to_funding_sec")
    if isinstance(ttf, (int, float)) and ttf < 3600:
        score += 0.1

    score = round(min(score, 1.0), 4)
    decision["score"] = score

    # ---------------------------
    # NO EDGE
    # ---------------------------
    if score < EDGE_SCORE_THRESHOLD:
        _state = "NO_EDGE"
        _persist = 0
        decision["state"] = _state
        decision["notes"] = "Composite below threshold"
        return decision

    # ---------------------------
    # EDGE DETECTED
    # ---------------------------
    if _state != "EDGE_DETECTED":
        _persist = 0

    _state = "EDGE_DETECTED"
    _persist += 1

    decision["state"] = _state
    decision["notes"] = f"Edge persistence {_persist}/{PERSISTENCE_REQUIRED}"

    # ---------------------------
    # EDGE APPROVED (STILL GATED)
    # ---------------------------
    if _persist >= PERSISTENCE_REQUIRED:
        _state = "EDGE_APPROVED"
        decision["state"] = _state
        decision["notes"] = "Edge persisted; execution gated"

    return decision
