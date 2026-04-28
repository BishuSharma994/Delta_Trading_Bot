import json
import logging
import os
from pathlib import Path
from datetime import datetime, timezone

BASE_EVENT_DIR = Path("data/events")
PAPER_TRADE_PATH = "/root/Delta_Trading_Bot/paper_trades.json"


def record_trade(trade: dict):
    symbol = trade.get("symbol")
    action = trade.get("action")
    logging.info(f"WRITING_TRADE {symbol} {action}")

    os.makedirs(os.path.dirname(PAPER_TRADE_PATH), exist_ok=True)

    if not os.path.exists(PAPER_TRADE_PATH):
        with open(PAPER_TRADE_PATH, "w") as f:
            json.dump([], f)

    with open(PAPER_TRADE_PATH, "r+") as f:
        data = json.load(f)
        data.append(trade)
        f.seek(0)
        json.dump(data, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
        f.truncate()


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
