# =========================
# OBSERVER — INSTITUTIONAL V2.7
# Perpetual Restricted + Correct Funding + time_to_funding_sec
# =========================

import sys
import os
import time
import requests
import logging
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

# -------------------------
# ENSURE PROJECT ROOT ON PATH
# -------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT.parent))
os.chdir(PROJECT_ROOT)

# -------------------------
# LOAD ENV
# -------------------------
load_dotenv(PROJECT_ROOT / ".env")

API_KEY = os.getenv("DELTA_API_KEY")
API_SECRET = os.getenv("DELTA_API_SECRET")

if not API_KEY or not API_SECRET:
    raise RuntimeError("API keys not loaded")

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
LOOP_INTERVAL_SECONDS = 60
HTTP_TIMEOUT = 5
FUNDING_INTERVAL_SECONDS = 8 * 60 * 60  # 28800

TARGET_SYMBOLS = {"BTCUSD", "ETHUSD", "SOLUSD", "BNBUSD"}

# =========================
# LOGGING
# =========================
logging.basicConfig(
    filename="bot.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logging.info("OBSERVER BOOTSTRAP OK")

# =========================
# PERPETUAL PRODUCT LOADER
# =========================
def load_perpetual_products():
    r = requests.get(
        BASE_URL + "/v2/products",
        timeout=HTTP_TIMEOUT,
    )
    r.raise_for_status()

    products = r.json()["result"]
    perp_map = {}

    for p in products:
        if p.get("contract_type") == "perpetual_futures":
            symbol = p.get("symbol")
            if symbol in TARGET_SYMBOLS:
                perp_map[symbol] = p.get("id")

    if not perp_map:
        raise RuntimeError("No perpetual futures found")

    return perp_map

# =========================
# TICKER DATA
# =========================
def get_ticker(symbol):
    r = requests.get(
        BASE_URL + f"/v2/tickers/{symbol}",
        timeout=HTTP_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()["result"]

# =========================
# FUNDING TIMER
# =========================
def compute_time_to_funding(loop_start):
    now_ts = int(loop_start.timestamp())
    next_funding_ts = ((now_ts // FUNDING_INTERVAL_SECONDS) + 1) * FUNDING_INTERVAL_SECONDS
    return next_funding_ts - now_ts

# =========================
# MAIN LOOP
# =========================
def main():
    logging.info("OBSERVER STARTED")

    funding_strategy = FundingBiasStrategy()
    volatility_strategy = VolatilityRegimeStrategy()

    SYMBOLS = load_perpetual_products()
    logging.info("PERPETUAL SYMBOL MAP LOADED: %s", SYMBOLS)

    while True:
        loop_start = datetime.now(timezone.utc)

        for symbol, product_id in SYMBOLS.items():
            try:
                ticker = get_ticker(symbol)

                mark_price = float(ticker.get("mark_price"))
                funding_rate = ticker.get("funding_rate")
                spot_price = ticker.get("spot_price")

                # -------- PRICE SNAPSHOT --------
                write_event("price_snapshot.jsonl", {
                    "timestamp_utc": loop_start.isoformat(),
                    "symbol": symbol,
                    "product_id": product_id,
                    "mark_price": mark_price,
                    "index_price": float(spot_price) if spot_price else mark_price,
                    "best_bid": float(ticker["quotes"]["best_bid"]),
                    "best_ask": float(ticker["quotes"]["best_ask"]),
                })

                # -------- FUNDING SNAPSHOT --------
                if funding_rate is not None:
                    time_to_funding_sec = compute_time_to_funding(loop_start)

                    write_event("funding_snapshot.jsonl", {
                        "timestamp_utc": loop_start.isoformat(),
                        "symbol": symbol,
                        "product_id": product_id,
                        "funding_rate": float(funding_rate),
                        "time_to_funding_sec": time_to_funding_sec,
                        "mark_price": mark_price,
                        "index_price": float(spot_price) if spot_price else mark_price,
                    })

                # -------- FEATURES --------
                features = build_feature_vector(symbol)

                # -------- STRATEGY VOTES --------
                funding_vote = funding_strategy.vote(features)
                volatility_vote = volatility_strategy.vote(features)

                write_event("strategy_votes.jsonl", {
                    "timestamp_utc": loop_start.isoformat(),
                    "symbol": symbol,
                    "strategy": funding_strategy.name,
                    "vote": funding_vote,
                })

                write_event("strategy_votes.jsonl", {
                    "timestamp_utc": loop_start.isoformat(),
                    "symbol": symbol,
                    "strategy": volatility_strategy.name,
                    "vote": volatility_vote,
                })

                # -------- EVALUATION --------
                decision = evaluate(features)

                write_event("decision.jsonl", {
                    "timestamp_utc": loop_start.isoformat(),
                    "symbol": symbol,
                    "decision": decision,
                    "feature_states": features.get("_feature_states", {}),
                })

                logging.info(
                    "DECISION | %s | %s",
                    symbol,
                    decision.get("state"),
                )

            except Exception:
                logging.exception("SYMBOL ERROR | %s", symbol)
                continue

        logging.info("HEARTBEAT | loop_complete")
        time.sleep(LOOP_INTERVAL_SECONDS)

# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    main()
