import json
from typing import List, Dict, Any


def load_votes(path: str) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            events.append(json.loads(line))
    events.sort(key=lambda e: e["timestamp_utc"])
    return events


def load_confluence(path: str) -> List[Dict[str, Any]]:
    with open(path, "r") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def load_persistence(path: str) -> Dict[str, Any]:
    with open(path, "r") as f:
        return json.load(f)
