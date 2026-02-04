# Decision loop
# Connects feature pipeline → evaluator → market memory
# No execution. Reject-first.

import time
from datetime import datetime, timezone

from core.feature_pipeline import build_feature_vector
from intelligence.evaluator import evaluate
from data.events import log_event


SYMBOLS = ["BTCUSD"]
SLEEP_SECONDS = 60


def run_once(symbol: str):
    features = build_feature_vector(symbol)

    if features is None:
        log_event(
            "decision",
            {
                "symbol": symbol,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "status": "insufficient_data",
            },
        )
        return

    decision = evaluate(features)

    log_event(
        "decision",
        {
            "symbol": symbol,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "features": features,
            "decision": decision,
        },
    )


def run_loop():
    while True:
        for symbol in SYMBOLS:
            run_once(symbol)

        time.sleep(SLEEP_SECONDS)


if __name__ == "__main__":
    run_loop()
