# =========================
# OBSERVER — INSTITUTIONAL V2.2
# Data + Intelligence Bridge (Execution GATED)
# =========================

import os
import time
import hmac
import hashlib
import json
import requests
import logging
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

# -------------------------
# HARD PIN WORKING DIRECTORY
# -------------------------
BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)

# -------------------------
# LOAD ENV (ABSOLUTE PATH)
# -------------------------
load_dotenv(dotenv_path=BASE_DIR / ".env")

# -------------------------
# INTERNAL IMPORTS (PACKAGE-ABSOLUTE)
# -------------------------
from Delta_Trading_Bot.core.feature_pipeline import build_feature_vector
from Delta_Trading_Bot.core.evaluator import evaluate
from Delta_Trading_Bot.utils.io import write_event

from Delta_Trading_Bot.strategies.funding_bias import FundingBiasStrategy
from Delta_Trading_Bot.strategies.volatility_regime import VolatilityRegimeStrategy

# =========================
# CONFIG
# =========================
BASE_URL = "https://api.india.delta.exchange"
SYMBOLS = {
    "BTCUSD": 84,
    "ETHUSD": 169,
    "BNBUSD": 321,
    "SOLUSD": 450,
}

LOOP_INTERVAL_SECONDS = 60
HTTP_TIMEOUT = 5

API_KEY = os.getenv("DELTA_API_KEY")
API_SECRET = os.getenv("DELTA_API_SECRET")

if not API_KEY or not API_SECRET:
    raise RuntimeError("API keys not loaded")

# =========================
# LOGGING
# =========================
logging.basicConfig(
    filename="bot.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

# =========================
# AUTH HELPERS
# =========================
def _sign(method, path, body=""):
    ts = str(int(time.time()))
    payload = method + ts + path + body
    sig = hmac.new(
        API_SECRET.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()

    return {
        "api-key": API_KEY,
        "timestamp": ts,
        "signature": sig,
        "User-Agent": "python-bot",
        "Content-Type": "application/json",
    }


def signed_get(path):
    headers = _sign("GET", path)
    r = requests.get(BASE_URL + path, headers=headers, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    return r.json()["result"]


# =========================
# MARKET DATA
# =========================
def get_mark_price(symbol):
    r = requests.get(
        BASE_URL + f"/v2/tickers/{symbol}",
        timeout=HTTP_TIMEOUT,
    )
    r.raise_for_status()
    return float(r.json()["result"]["mark_price"])


def get_funding_rate(product_id):
    try:
        r = requests.get(
            BASE_URL + f"/v2/products/{product_id}",
            timeout=HTTP_TIMEOUT,
        )
        r.raise_for_status()
        return r.json()["result"].get("funding_rate")
    except Exception:
        return None


# =========================
# MAIN LOOP
# =========================
def main():
    logging.info("OBSERVER STARTED")

    funding_strategy = FundingBiasStrategy()
    volatility_strategy = VolatilityRegimeStrategy()

    while True:
        try:
            now_utc = datetime.now(timezone.utc).isoformat()

            for symbol, product_id in SYMBOLS.items():
                price = get_mark_price(symbol)
                funding = get_funding_rate(product_id)

                # -------- EVENT INGESTION --------
                write_event("price_snapshot.jsonl", {
                    "timestamp_utc": now_utc,
                    "symbol": symbol,
                    "product_id": product_id,
                    "mark_price": price,
                    "index_price": price,
                    "best_bid": price * 0.999,
                    "best_ask": price * 1.001,
                })

                if funding is not None:
                    write_event("funding_snapshot.jsonl", {
                        "timestamp_utc": now_utc,
                        "symbol": symbol,
                        "product_id": product_id,
                        "funding_rate": funding,
                        "next_funding_time_utc": (
                            datetime.now(timezone.utc)
                            .replace(minute=0, second=0, microsecond=0)
                            .isoformat()
                        ),
                    })

                # -------- FEATURES --------
                features = build_feature_vector(symbol)

                # -------- STRATEGY VOTES --------
                funding_vote = funding_strategy.vote(features)
                volatility_vote = volatility_strategy.vote(features)

                write_event("strategy_votes.jsonl", {
                    "timestamp_utc": now_utc,
                    "symbol": symbol,
                    "strategy": funding_strategy.name,
                    "vote": funding_vote,
                })

                write_event("strategy_votes.jsonl", {
                    "timestamp_utc": now_utc,
                    "symbol": symbol,
                    "strategy": volatility_strategy.name,
                    "vote": volatility_vote,
                })

                # -------- EVALUATION --------
                decision = evaluate(features)

                logging.info("DECISION | %s | %s", symbol, decision.get("state"))

                write_event("decision.jsonl", {
                    "timestamp_utc": now_utc,
                    "symbol": symbol,
                    "decision": decision,
                    "feature_states": features.get("_feature_states", {}),
                })

            time.sleep(LOOP_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            logging.info("MANUAL STOP")
            break

        except Exception as e:
            logging.exception("Unhandled exception: %s", str(e))
            time.sleep(LOOP_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
