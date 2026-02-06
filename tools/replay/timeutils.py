from datetime import datetime, timezone
from typing import List, Dict, Any


def _to_ts(ts: str) -> float:
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()


def within_window(
    base_ts: str,
    events: List[Dict[str, Any]],
    window_seconds: int,
) -> List[Dict[str, Any]]:
    base = _to_ts(base_ts)
    lo = base - window_seconds
    hi = base + window_seconds
    out: List[Dict[str, Any]] = []
    for e in events:
        t = _to_ts(e["timestamp_utc"])
        if lo <= t <= hi:
            out.append(e)
    return out
