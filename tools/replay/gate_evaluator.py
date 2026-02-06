"""
Gate Evaluator Logic
V2.4 — Offline Replay Only

Applies execution gate rules deterministically.
No execution. No live imports.
"""

from typing import Dict, List, Any, TypedDict, Literal
from statistics import mean


GateState = Literal["ALLOW", "DENY"]


class GateDecision(TypedDict):
    timestamp_utc: str
    symbol: str
    state: GateState
    reasons: List[str]
    evidence: Dict[str, Any]


class GateInputs(TypedDict):
    timestamp_utc: str
    symbol: str
    confluence: Dict[str, Any]
    persistence: Dict[str, Any]
    votes: List[Dict[str, Any]]
    virtual_state: Dict[str, Any]


def _same_bias(votes: List[Dict[str, Any]]) -> bool:
    biases = {v["vote"]["bias"] for v in votes if v["vote"]["bias"] != 0}
    return len(biases) == 1


def evaluate_gate(
    inputs: GateInputs,
    gate_config: Dict[str, Any],
) -> GateDecision:

    reasons: List[str] = []
    evidence: Dict[str, Any] = {}

    ts = inputs["timestamp_utc"]
    symbol = inputs["symbol"]
    votes = inputs["votes"]
    state = inputs["virtual_state"]

    # 1) Cooldown check
    if state.get("cooldown_remaining_sec", 0) > 0:
        reasons.append("cooldown_active")

    # 2) Require no open position (virtual)
    if state.get("open_position", False):
        reasons.append("virtual_position_open")

    # 3) Non-neutral votes
    non_neutral = [v for v in votes if v["vote"]["bias"] != 0]
    if len(non_neutral) < gate_config["requirements"]["confluence"]["min_strategies"]:
        reasons.append("insufficient_strategy_confluence")

    # 4) Same bias requirement
    if non_neutral and not _same_bias(non_neutral):
        reasons.append("conflicting_strategy_bias")

    # 5) Confidence check
    confidences = [v["vote"]["confidence"] for v in non_neutral]
    if confidences:
        avg_conf = mean(confidences)
        evidence["avg_confidence"] = avg_conf
        if avg_conf < gate_config["requirements"]["confidence"]["min_average"]:
            reasons.append("confidence_below_threshold")
    else:
        reasons.append("no_confidence_data")

    # 6) Persistence check (precomputed)
    persistence = inputs["persistence"]
    min_persist = gate_config["requirements"]["persistence"]["min_consecutive_votes"]
    if persistence.get("max_consecutive_non_neutral", 0) < min_persist:
        reasons.append("insufficient_persistence")

    # FINAL DECISION
    if reasons:
        decision_state: GateState = gate_config["outputs"]["deny_state"]
    else:
        decision_state = gate_config["outputs"]["allow_state"]

    return {
        "timestamp_utc": ts,
        "symbol": symbol,
        "state": decision_state,
        "reasons": reasons,
        "evidence": evidence,
    }
