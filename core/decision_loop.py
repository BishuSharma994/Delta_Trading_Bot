# Decision loop
# Single runtime loop: features -> evaluator -> state engine -> event memory.

import time
import logging
from datetime import datetime, timezone

from core.evaluator import evaluate
from core.feature_pipeline import build_feature_vector
from core.market_hours import symbol_tradeable
from core.state_engine import StateEngine
from config.settings import ACTIVE_SYMBOLS, DECISION_LOOP_SLEEP_SECONDS
from utils.io import write_event


logger = logging.getLogger()
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
        logger.info("TRACE_SKIPPED %s insufficient_features", symbol)
        write_event(
            "decision.jsonl",
            {
                "symbol": symbol,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "status": "insufficient_data",
            },
        )
        return

    logger.info("TRACE_FEATURES %s", symbol)

    decision = evaluate(features, symbol=symbol)
    logger.info("REAL_LOOP_ACTIVE %s %s", symbol, decision)
    logger.info("TRACE_DECISION %s %s %s", symbol, decision, type(decision))

    decision = normalize_decision(decision, features)
    logger.info("TRACE_DECISION_NORMALIZED %s", decision)

    logger.info("TRACE_BEFORE_STATE_ENGINE %s %s", symbol, decision)
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
                    logger.info("TRACE_SKIPPED %s symbol_not_tradeable", symbol)
                    continue

                run_once(symbol)
            except Exception as e:
                logger.exception("RUNTIME_ERROR %s", e)
                logger.info("TRACE_SKIPPED %s runtime_exception", symbol)
                continue

        time.sleep(DECISION_LOOP_SLEEP_SECONDS)


if __name__ == "__main__":
    run_loop()
