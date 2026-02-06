"""
Gate Evaluator Interface
V2.4 — Offline Replay Only

Purpose:
- Apply execution gate rules to historical evidence
- Return ALLOW / DENY decisions with explicit reasons
- Never place trades
- Never import live systems
- Never mutate real state

This module is configuration-driven and read-only.
"""

from typing import Dict, List, Any, TypedDict, Literal


GateState = Literal["ALLOW", "DENY"]


class GateDecision(TypedDict):
    """
    Immutable record of a gate evaluation outcome.
    """
    timestamp_utc: str
    symbol: str
    state: GateState
    reasons: List[str]
    evidence: Dict[str, Any]


class GateInputs(TypedDict):
    """
    Evidence bundle provided by the replay runner.
    """
    timestamp_utc: str
    symbol: str
    confluence: Dict[str, Any]
    persistence: Dict[str, Any]
    votes: List[Dict[str, Any]]
    virtual_state: Dict[str, Any]


def evaluate_gate(
    inputs: GateInputs,
    gate_config: Dict[str, Any],
) -> GateDecision:
    """
    Evaluate execution permission using offline evidence.

    Rules are read from gate_config (execution_gate.yaml).

    This function:
    - Does NOT execute trades
    - Does NOT access live data
    - Does NOT modify persistent state
    - Does NOT infer missing data

    Returns:
        GateDecision:
            state: ALLOW or DENY
            reasons: explicit list of gate failures or approvals
            evidence: minimal supporting context
    """
    raise NotImplementedError("Gate evaluation logic implemented in Step 4")
