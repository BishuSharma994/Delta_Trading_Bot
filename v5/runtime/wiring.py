"""
V5 Runtime Wiring
NO EXECUTION
Evidence + Authorization + Governance + Kill-Switch + Audit
"""

from v5.runtime.evidence_validator import validate_evidence
from v5.runtime.authorization import authorization_valid
from v5.runtime.governance import is_armed
from v5.runtime.kill_switch import kill_switch_triggered
from v5.runtime.audit import log_gate

def main():
    ok, reason = validate_evidence()
    log_gate("evidence_check", {"ok": ok, "reason": reason})
    if not ok:
        print(f"EVIDENCE DENY: {reason}")
        return

    auth_ok, auth_reason = authorization_valid()
    log_gate("authorization_check", {"ok": auth_ok, "reason": auth_reason})
    if not auth_ok:
        print(f"AUTHORIZATION DENY: {auth_reason}")
        return

    armed, state = is_armed()
    log_gate("governance_check", {"armed": armed, "state": state})
    if not armed:
        print(f"GOVERNANCE DENY: {state}")
        return

    triggered, which = kill_switch_triggered()
    log_gate("kill_switch_check", {"triggered": triggered, "which": which})
    if triggered:
        print(f"KILL SWITCH TRIGGERED: {which}")
        return

    log_gate("runtime_ready", {"status": "ready_no_execution"})
    print("V5 RUNTIME READY (DRY, NO EXECUTION)")

if __name__ == "__main__":
    main()
