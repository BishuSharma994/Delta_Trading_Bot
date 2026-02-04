# Price snapshot ingestion
# Observation-only. No decisions. No execution.

from datetime import datetime, timezone
from data.events import log_event


def normalize_price_snapshot(raw: dict) -> dict:
    """
    Normalize raw price data into canonical schema.
    """

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "symbol": raw["symbol"],
        "product_id": raw["product_id"],
        "mark_price": float(raw["mark_price"]),
        "index_price": float(raw["index_price"]),
        "best_bid": float(raw["best_bid"]),
        "best_ask": float(raw["best_ask"]),
    }


def ingest_price_snapshot(raw: dict):
    """
    Accepts raw exchange price response and logs normalized price snapshot.
    """

    snapshot = normalize_price_snapshot(raw)

    log_event(
        event_type="price_snapshot",
        payload=snapshot
    )

    return snapshot
