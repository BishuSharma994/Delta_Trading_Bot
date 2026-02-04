# Backtest engine
# Replays market memory and evaluates decisions deterministically
# No execution. No PnL. No fills.

import json
from pathlib import Path
from datetime import datetime

from core.feature_pipeline import build_feature_vector
from intelligence.evaluator import evaluate
from data.events import log_event

EVENTS_DIR = Path("data/events")


def _load_events(event_type: str):
    file = EVENTS_DIR / f"{event_type}.jsonl"
    if not file.exists():
        return []

    with open(file) as f:
        return [json.loads(line) for line in f]


def run_backtest(symbol: str):
    """
    Replay memory chronologically and evaluate decisions.
    """

    price_events = _load_events("price_snapshot")
    funding_events = _load_events("funding_snapshot")

    # Filter by symbol
    price_events = [e for e in price_events if e["payload"]["symbol"] == symbol]
    funding_events = [e for e in funding_events if e["payload"]["symbol"] == symbol]

    # Sort by time
    price_events.sort(key=lambda e: e["timestamp_utc"])
    funding_events.sort(key=lambda e: e["timestamp_utc"])

    if not price_events or not funding_events:
        print("Insufficient memory for backtest")
        return

    print(f"Running backtest for {symbol}")
    print(f"Price events: {len(price_events)}")
    print(f"Funding events: {len(funding_events)}")

    for i in range(len(price_events)):
        # Truncate memory to time i
        truncated_price = price_events[: i + 1]

        # Temporarily write truncated price memory
        tmp_file = EVENTS_DIR / "_tmp_price.jsonl"
        with open(tmp_file, "w") as f:
            for e in truncated_price:
                f.write(json.dumps(e) + "\n")

        # Swap in truncated memory
        original = EVENTS_DIR / "price_snapshot.jsonl"
        original.rename(EVENTS_DIR / "_price_backup.jsonl")
        tmp_file.rename(original)

        features = build_feature_vector(symbol)
        if features is None:
            continue

        decision = evaluate(features)

        log_event(
            "backtest_decision",
            {
                "symbol": symbol,
                "decision": decision,
                "features": features,
                "at_time": price_events[i]["timestamp_utc"],
            },
        )

        # Restore original memory
        original.rename(tmp_file)
        (EVENTS_DIR / "_price_backup.jsonl").rename(original)

    print("Backtest complete")
