"""
V5 Runtime Wiring
NO EXECUTION
Evidence + Governance + Kill-Switch enforcement
"""

from v5.runtime.evidence_validator import validate_evidence
from v5.runtime.governance import is_armed
from v5.runtime.kill_switch import kill_switch_triggered

def main():
    ok, reason = validate_evidence()
    if not ok:
        print(f"EVIDENCE DENY: {reason}")
        return

    armed, state = is_armed()
    if not armed:
        print(f"GOVERNANCE DENY: {state}")
        return

    triggered, which = kill_switch_triggered()
    if triggered:
        print(f"KILL SWITCH TRIGGERED: {which}")
        return

    print("V5 RUNTIME READY (DRY, NO EXECUTION)")

if __name__ == "__main__":
    main()
