"""
V5 Alignment Diagnostics
LOGGING ONLY
NO DECISIONS
NO EXECUTION
"""

import json
from pathlib import Path
from datetime import datetime, timezone

DIAG_DIR = Path("data/audit")
DIAG_DIR.mkdir(parents=True, exist_ok=True)

ALIGNMENT_DIAG = DIAG_DIR / "alignment_diagnostics.jsonl"

def log_alignment_diagnostic(symbol, payload):
    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "symbol": symbol,
        "diagnostic": payload,
    }
    with ALIGNMENT_DIAG.open("a") as f:
        f.write(json.dumps(record) + "\n")
