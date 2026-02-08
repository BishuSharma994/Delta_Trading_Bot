import sys
from pathlib import Path

# ensure parent directory is on PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT.parent))
# =========================
# OBSERVER — INSTITUTIONAL V2.3 (FINAL)
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
BASE_DIR = Path(__file__).resolve().parent.parent
os.chdir(BASE_DIR)

# -------------------------
# LOAD ENV (ABSOLUTE PATH)
# -------------------------
# LOAD ENV (PROJECT ROOT)
PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")
assert os.getenv("DELTA_API_KEY"), "DELTA_API_KEY missing"
assert os.getenv("DELTA_API_SECRET"), "DELTA_API_SECRET missing"


# -------------------------
# INTERNAL IMPORTS
# -------------------------
from core.feature_pipeline import build_feature_vector
from core.evaluator import evaluate
from utils.io import write_event
from strategies.funding_bias import FundingBiasStrategy
from strategies.volatility_regime import VolatilityRegimeStrategy


# =========================
# CONFIG
# =========================
BASE_URL = "https://api.india.delta.exchange"

# ⚠️ EXECUTION UNIVERSE = PERPETUAL FUTURES ONLY
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
    filename="observer.log",
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
        "User-Agent": "delta-bot",
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
def get_product_info(product_id):
    r = requests.get(
        BASE_URL + f"/v2/products/{product_id}",
        timeout=HTTP_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()["result"]


def get_mark_price(symbol):
    r = requests.get(
        BASE_URL + f"/v2/tickers/{symbol}",
        timeout=HTTP_TIMEOUT,
    )
    r.raise_for_status()
    return float(r.json()["result"]["mark_price"])


# =========================
# MAIN LOOP
# =========================
def main():
    logging.info("OBSERVER STARTED")

    funding_strategy = FundingBiasStrategy()
    volatility_strategy = VolatilityRegimeStrategy()

    while True:
        try:
            now = datetime.now(timezone.utc)

            for symbol, product_id in SYMBOLS.items():
                # -------- PRICE --------
                mark_price = get_mark_price(symbol)

                write_event("price_snapshot.jsonl", {
                    "timestamp_utc": now.isoformat(),
                    "symbol": symbol,
                    "product_id": product_id,
                    "mark_price": mark_price,
                    "index_price": mark_price,
                    "best_bid": mark_price * 0.999,
                    "best_ask": mark_price * 1.001,
                })

                # -------- FUNDING (PERP ONLY) --------
                product = get_product_info(product_id)

                funding_rate = product.get("funding_rate")
                next_funding_ts = product.get("next_funding_time")

                if funding_rate is not None and next_funding_ts is not None:
                    next_funding_time = datetime.fromtimestamp(
                        next_funding_ts, tz=timezone.utc
                    )

                    write_event("funding_snapshot.jsonl", {
                        "timestamp_utc": now.isoformat(),
                        "symbol": symbol,
                        "product_id": product_id,
                        "funding_rate": float(funding_rate),
                        "next_funding_time_utc": next_funding_time.isoformat(),
                        "time_to_funding_sec": int(
                            (next_funding_time - now).total_seconds()
                        ),
                        "mark_price": product.get("mark_price"),
                        "index_price": product.get("index_price"),
                    })

                # -------- FEATURES --------
                features = build_feature_vector(symbol)

                # -------- STRATEGY VOTES --------
                funding_vote = funding_strategy.vote(features)
                volatility_vote = volatility_strategy.vote(features)

                write_event("strategy_votes.jsonl", {
                    "timestamp_utc": now.isoformat(),
                    "symbol": symbol,
                    "strategy": funding_strategy.name,
                    "vote": funding_vote,
                })

                write_event("strategy_votes.jsonl", {
                    "timestamp_utc": now.isoformat(),
                    "symbol": symbol,
                    "strategy": volatility_strategy.name,
                    "vote": volatility_vote,
                })

                # -------- EVALUATION --------
                decision = evaluate(features)

                write_event("decision.jsonl", {
                    "timestamp_utc": now.isoformat(),
                    "symbol": symbol,
                    "decision": decision,
                    "feature_states": features.get("_feature_states", {}),
                })

                logging.info(
                    "STATE | %s | %s",
                    symbol,
                    decision.get("state"),
                )

            time.sleep(LOOP_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            logging.info("MANUAL STOP")
            break

        except Exception as e:
            logging.exception("UNHANDLED ERROR")
            time.sleep(LOOP_INTERVAL_SECONDS)


# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    main()
