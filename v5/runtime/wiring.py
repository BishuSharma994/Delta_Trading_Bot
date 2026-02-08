"""
V5 Runtime Wiring
NO EXECUTION
Evidence + Authorization + Governance + Kill-Switch + Audit + Diagnostics + Dry-Run Intent
"""

import json
from pathlib import Path

from v5.runtime.evidence_validator import validate_evidence
from v5.runtime.authorization import authorization_valid
from v5.runtime.governance import is_armed
from v5.runtime.kill_switch import kill_switch_triggered
from v5.runtime.audit import log_gate
from v5.runtime.intents import emit_intent
from v5.runtime.diagnostics import log_alignment_diagnostic

ALIGNMENT_FILE = Path("data/events/alignment_state.jsonl")


def load_latest_alignment():
    if not ALIGNMENT_FILE.exists():
        return None
    latest = None
    with ALIGNMENT_FILE.open() as f:
        for line in f:
            latest = json.loads(line)
    return latest


def main():
    # -------- EVIDENCE --------
    ok, reason = validate_evidence()
    log_gate("evidence_check", {"ok": ok, "reason": reason})
    if not ok:
        print(f"EVIDENCE DENY: {reason}")
        return

    # -------- AUTHORIZATION --------
    auth_ok, auth_reason = authorization_valid()
    log_gate("authorization_check", {"ok": auth_ok, "reason": auth_reason})
    if not auth_ok:
        print(f"AUTHORIZATION DENY: {auth_reason}")
        return

    # -------- GOVERNANCE --------
    armed, state = is_armed()
    log_gate("governance_check", {"armed": armed, "state": state})
    if not armed:
        print(f"GOVERNANCE DENY: {state}")
        return

    # -------- KILL SWITCH --------
    triggered, which = kill_switch_triggered()
    log_gate("kill_switch_check", {"triggered": triggered, "which": which})
    if triggered:
        print(f"KILL SWITCH TRIGGERED: {which}")
        return

    # -------- ALIGNMENT --------
    alignment = load_latest_alignment()
    if not alignment:
        log_gate("alignment_missing", {})
        print("ALIGNMENT DENY: missing")
        return

    if alignment.get("alignment_state") != "ALIGNED":
        log_gate(
            "alignment_not_aligned",
            {
                "state": alignment.get("alignment_state"),
                "reason": alignment.get("reason"),
            },
        )

        log_alignment_diagnostic(
            symbol=alignment.get("symbol"),
            payload={
                "alignment_state": alignment.get("alignment_state"),
                "reason": alignment.get("reason"),
                "volatility_vote": alignment.get("volatility_vote"),
                "funding_vote": alignment.get("funding_vote"),
                "time_to_funding_sec": alignment.get("time_to_funding_sec"),
                "confidence": alignment.get("confidence"),
                "evidence_present": bool(alignment.get("evidence")),
            },
        )

        print("ALIGNMENT DENY: not aligned")
        return

    # -------- DRY-RUN INTENT --------
    emit_intent(
        symbol=alignment["symbol"],
        direction=alignment["direction"],
        confidence=alignment["confidence"],
        reason=alignment["reason"],
    )

    log_gate("intent_emitted", {"symbol": alignment["symbol"], "mode": "dry_run"})
    print("DRY-RUN INTENT EMITTED")


if __name__ == "__main__":
    main()
