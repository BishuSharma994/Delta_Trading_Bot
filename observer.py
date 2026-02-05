# =========================
# OBSERVER — INSTITUTIONAL V2.1
# Trading + Intelligence Bridge (Execution GATED)
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
print("OBSERVER CWD:", os.getcwd())

# -------------------------
# LOAD ENV (ABSOLUTE PATH)
# -------------------------
load_dotenv(dotenv_path=BASE_DIR / ".env")
print("OBSERVER BOOTSTRAP COMPLETE")

# -------------------------
# IMPORT INTERNAL MODULES
# -------------------------
from core.feature_pipeline import build_feature_vector
from core.evaluator import evaluate
from utils.io import write_event
from strategies.funding_bias import FundingBiasStrategy

# =========================
# CONFIG
# =========================
BASE_URL = "https://api.india.delta.exchange"
SYMBOL = "BTCUSD"
PRODUCT_ID = 84

LOOP_INTERVAL_SECONDS = 60
HTTP_TIMEOUT = 5
KILL_SWITCH = False

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
def get_mark_price():
    r = requests.get(
        BASE_URL + f"/v2/tickers/{SYMBOL}",
        timeout=HTTP_TIMEOUT,
    )
    r.raise_for_status()
    return float(r.json()["result"]["mark_price"])


def get_funding_rate():
    try:
        r = requests.get(
            BASE_URL + f"/v2/products/{PRODUCT_ID}",
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

    while True:
        try:
            print("-" * 60)
            now_utc = datetime.now(timezone.utc).isoformat()
            print("UTC:", now_utc)

            price = get_mark_price()
            funding = get_funding_rate()

            print("Symbol:", SYMBOL)
            print("Mark Price:", price)
            print("Funding Rate:", funding)

            # -------- EVENT INGESTION --------
            write_event("price_snapshot.jsonl", {
                "timestamp_utc": now_utc,
                "symbol": SYMBOL,
                "product_id": PRODUCT_ID,
                "mark_price": price,
                "index_price": price,
                "best_bid": price * 0.999,
                "best_ask": price * 1.001,
            })

            if funding is not None:
                write_event("funding_snapshot.jsonl", {
                    "timestamp_utc": now_utc,
                    "symbol": SYMBOL,
                    "product_id": PRODUCT_ID,
                    "funding_rate": funding,
                    "next_funding_time_utc": (
                        datetime.now(timezone.utc)
                        .replace(minute=0, second=0, microsecond=0)
                        .isoformat()
                    ),
                })

            # -------- INTELLIGENCE --------
            features = build_feature_vector(SYMBOL)
            decision = evaluate(features)

            print("DECISION:", decision)
            logging.info("DECISION | %s", decision)
            logging.info("NO EXECUTION — STATE: %s", decision.get("state"))

            write_event("decision.jsonl", {
                "timestamp_utc": now_utc,
                "symbol": SYMBOL,
                "decision": decision,
                "feature_states": features.get("_feature_states", {}),
            })

            # -------- STRATEGY VOTES (V2.1) --------
            funding_vote = funding_strategy.vote(features)

            write_event("strategy_votes.jsonl", {
                "timestamp_utc": now_utc,
                "symbol": SYMBOL,
                "strategy": funding_strategy.name,
                "vote": funding_vote,
            })

            print("SLEEPING:", LOOP_INTERVAL_SECONDS, "seconds")
            time.sleep(LOOP_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            logging.info("MANUAL STOP")
            break

        except Exception as e:
            print("ERROR:", str(e))
            logging.exception("Unhandled exception")
            time.sleep(LOOP_INTERVAL_SECONDS)


# =========================
if __name__ == "__main__":
    main()
