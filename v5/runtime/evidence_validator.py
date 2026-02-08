"""
V5 Evidence Validator
NO EXECUTION
Spec-enforced validation only
"""

import json
from pathlib import Path
from datetime import datetime, timezone

SPEC_FILE = Path("v5/spec/evidence_contract.yaml")
ALIGNMENT_FILE = Path("data/events/alignment_state.jsonl")

REQUIRED_FIELDS = [
    "hypothesis_id",
    "rarity_index",
    "scenario_concurrence",
    "confidence_calibration",
]

def load_latest_alignment():
    if not ALIGNMENT_FILE.exists():
        return None
    latest = None
    with ALIGNMENT_FILE.open() as f:
        for line in f:
            latest = json.loads(line)
    return latest

def validate_evidence():
    alignment = load_latest_alignment()
    if alignment is None:
        return False, "missing_alignment_state"

    evidence = alignment.get("evidence", {})
    for field in REQUIRED_FIELDS:
        if field not in evidence:
            return False, f"missing_{field}"

    ts = alignment.get("timestamp_utc")
    if not ts:
        return False, "missing_timestamp"

    try:
        event_time = datetime.fromisoformat(ts)
    except Exception:
        return False, "invalid_timestamp"

    if event_time.tzinfo is None:
        return False, "timestamp_not_utc"

    return True, "evidence_valid"
