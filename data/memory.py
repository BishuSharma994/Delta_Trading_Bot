# data/memory.py
# Read-only event memory layer
# Institutional V2.2 — COMPLETE CONTRACT SET

import json
from pathlib import Path

# -------------------------
# PATH SETUP
# -------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
EVENTS_DIR = BASE_DIR / "data" / "events"


# -------------------------
# CORE EVENT READER
# -------------------------
def read_events(filename: str):
    """
    Reads JSONL event files safely.
    """
    path = EVENTS_DIR / filename
    if not path.exists():
        return []

    events = []
    with open(path, "r") as f:
        for line in f:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


# -------------------------
# FUNDING MEMORY
# -------------------------
def get_latest_funding(symbol: str):
    events = read_events("funding_snapshot.jsonl")

    for event in reversed(events):
        if event.get("symbol") == symbol:
            return event
    return None


# -------------------------
# PRICE MEMORY
# -------------------------
def get_recent_prices(symbol: str, minutes: int = 5):
    """
    Returns recent mark prices for volatility calculations.
    """
    events = read_events("price_snapshot.jsonl")

    prices = []
    for event in reversed(events):
        if event.get("symbol") == symbol:
            price = event.get("mark_price")
            if price is not None:
                prices.append(price)

        if len(prices) >= minutes:
            break

    return list(reversed(prices))


# -------------------------
# ORDER BOOK MEMORY
# -------------------------
def get_latest_book(symbol: str):
    """
    Returns the most recent best bid / ask snapshot.
    Required by feature_pipeline.py
    """
    events = read_events("price_snapshot.jsonl")

    for event in reversed(events):
        if event.get("symbol") == symbol:
            bid = event.get("best_bid")
            ask = event.get("best_ask")

            if bid is not None and ask is not None:
                return {
                    "best_bid": bid,
                    "best_ask": ask,
                }

    return None

# -------------------------
# STRATEGY VOTES MEMORY
# -------------------------
def get_latest_strategy_vote(strategy_name: str):
    """
    Returns the most recent vote emitted by a strategy.
    """
    events = read_events("strategy_votes.jsonl")

    for event in reversed(events):
        if event.get("strategy") == strategy_name:
            return event.get("vote")

    return None
# -------------------------
# FEATURE HISTORY MEMORY
# -------------------------
def get_recent_feature_values(feature_name: str, limit: int = 60):
    """
    Returns recent numeric feature values from decision events.
    """
    events = read_events("decision.jsonl")

    values = []
    for event in reversed(events):
        feature_block = event.get("features", {})
        value = feature_block.get(feature_name)

        if isinstance(value, (int, float)):
            values.append(float(value))

        if len(values) >= limit:
            break

    return list(reversed(values))

