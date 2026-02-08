"""
V5 Order Intent Generator
DRY-RUN ONLY
NO EXECUTION
"""

import json
from pathlib import Path
from datetime import datetime, timezone

INTENT_LOG = Path("data/audit/orders.jsonl")

def emit_intent(symbol, direction, confidence, reason):
    intent = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "symbol": symbol,
        "direction": direction,
        "confidence": confidence,
        "reason": reason,
        "mode": "DRY_RUN",
    }
    with INTENT_LOG.open("a") as f:
        f.write(json.dumps(intent) + "\n")
