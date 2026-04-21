# Decision loop
# Connects feature pipeline → evaluator → market memory
# No execution. Reject-first.

import time
from datetime import datetime, timezone

from core.feature_pipeline import build_feature_vector
from core.market_hours import symbol_tradeable
from intelligence.evaluator import evaluate
from data.events import log_event
from config.settings import ACTIVE_SYMBOLS, DECISION_LOOP_SLEEP_SECONDS



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
        for symbol in ACTIVE_SYMBOLS:
            if not symbol_tradeable(symbol):
                continue
            run_once(symbol)

        time.sleep(DECISION_LOOP_SLEEP_SECONDS)



if __name__ == "__main__":
    run_loop()
