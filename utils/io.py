import json
from pathlib import Path
from datetime import datetime, timezone

BASE_EVENT_DIR = Path("data/events")


def write_event(filename: str, payload: dict) -> None:
    """
    Append-only JSONL writer.
    No reads. No mutation. No overwrite.
    """
    BASE_EVENT_DIR.mkdir(parents=True, exist_ok=True)
    path = BASE_EVENT_DIR / filename

    # enforce UTC timestamp if missing
    if "timestamp_utc" not in payload:
        payload["timestamp_utc"] = datetime.now(timezone.utc).isoformat()

    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, separators=(",", ":")) + "\n")
