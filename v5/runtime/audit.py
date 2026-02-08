"""
V5 Audit Logging
Append-only, immutable intent
NO EXECUTION
"""

import json
from pathlib import Path
from datetime import datetime, timezone

AUDIT_DIR = Path("data/audit")
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

GATES_LOG = AUDIT_DIR / "gates.jsonl"

def log_gate(event_type, payload):
    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "payload": payload,
    }
    with GATES_LOG.open("a") as f:
        f.write(json.dumps(record) + "\n")
