# Decision loop
# Single runtime loop: features -> evaluator -> state engine -> event memory.

import time
import traceback
from datetime import datetime, timezone

from core.evaluator import evaluate
from core.feature_pipeline import build_feature_vector
from core.market_hours import symbol_tradeable
from core.state_engine import StateEngine
from config.settings import ACTIVE_SYMBOLS, DECISION_LOOP_SLEEP_SECONDS
from utils.io import write_event


state_engine = StateEngine()


def normalize_decision(decision, features):
    if isinstance(decision, str):
        decision = {
            "state": decision,
            "direction": "LONG" if features.get("msb") == 1 else "SHORT",
        }

    return decision


def run_once(symbol: str):
    features = build_feature_vector(symbol)

    if features is None:
        print("TRACE_SKIPPED", symbol, "insufficient_features")
        write_event(
            "decision.jsonl",
            {
                "symbol": symbol,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "status": "insufficient_data",
            },
        )
        return

    print("TRACE_FEATURES", symbol)

    decision = evaluate(features, symbol=symbol)
    print("REAL_LOOP_ACTIVE", symbol, decision)
    print("TRACE_DECISION", symbol, decision, type(decision))

    decision = normalize_decision(decision, features)
    print("TRACE_DECISION_NORMALIZED", decision)

    print("TRACE_BEFORE_STATE_ENGINE", symbol, decision)
    state_engine.process(
        symbol=symbol,
        decision=decision,
        features=features,
    )

    write_event(
        "decision.jsonl",
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
            try:
                if not symbol_tradeable(symbol):
                    print("TRACE_SKIPPED", symbol, "symbol_not_tradeable")
                    continue

                run_once(symbol)
            except Exception as e:
                print("RUNTIME_ERROR", e)
                traceback.print_exc()
                print("TRACE_SKIPPED", symbol, "runtime_exception")
                continue

        time.sleep(DECISION_LOOP_SLEEP_SECONDS)


if __name__ == "__main__":
    run_loop()
