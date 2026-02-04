# Funding snapshot ingestion
# Observation-only. No decisions. No execution.

from datetime import datetime, timezone
from data.events import log_event


def normalize_funding_snapshot(raw: dict) -> dict:
    """
    Normalize funding data into canonical schema.
    """

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "symbol": raw["symbol"],
        "product_id": raw["product_id"],
        "funding_rate_pct": float(raw["funding_rate"]),
        "next_funding_time_utc": raw["next_funding_time"],
        "mark_price": float(raw["mark_price"]),
        "index_price": float(raw["index_price"]),
    }


def ingest_funding_snapshot(raw: dict):
    """
    Accepts raw exchange response and logs normalized funding snapshot.
    """

    snapshot = normalize_funding_snapshot(raw)

    log_event(
        event_type="funding_snapshot",
        payload=snapshot
    )

    return snapshot
