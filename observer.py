# =========================
# OBSERVER - INSTITUTIONAL V2.7
# Perpetual Restricted + Correct Funding + time_to_funding_sec
# =========================

import sys
import os
import time
import fcntl
import requests
import logging
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv


# -------------------------
# SINGLE INSTANCE LOCK
# -------------------------
_LOCK_FILE = open("/tmp/trading-bot.lock", "w")
try:
    fcntl.flock(_LOCK_FILE, fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError:
    print("Another instance is already running. Exiting.")
    sys.exit(0)


# -------------------------
# ENSURE PROJECT ROOT ON PATH
# -------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT.parent) not in sys.path:
    sys.path.append(str(PROJECT_ROOT.parent))
os.chdir(PROJECT_ROOT)

# -------------------------
# LOAD ENV
# -------------------------
load_dotenv(PROJECT_ROOT / ".env")

API_KEY = os.getenv("DELTA_API_KEY")
API_SECRET = os.getenv("DELTA_API_SECRET")

if not API_KEY or not API_SECRET:
    logging.warning(
        "DELTA API credentials not loaded; running in public market-data dry-run mode."
    )

# -------------------------
# INTERNAL IMPORTS
# -------------------------
from core.feature_pipeline import build_feature_vector
from core.evaluator import evaluate
from core.market_hours import is_nyse_hours
from core.state_engine import StateEngine
from config.settings import ACTIVE_SYMBOLS, XSTOCK_SYMBOLS
from utils.io import write_event
from strategies.funding_bias import FundingBiasStrategy
from strategies.volatility_regime import VolatilityRegimeStrategy
from v5.runtime.kill_switch import enforce, check_auto_arm

# =========================
# CONFIG
# =========================
BASE_URL = "https://api.india.delta.exchange"
LOOP_INTERVAL_SECONDS = 60
HTTP_TIMEOUT = 5
FUNDING_INTERVAL_SECONDS = 8 * 60 * 60  # 28800

TARGET_SYMBOLS = set(ACTIVE_SYMBOLS)

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
    perp_map = {}
    params = {
        "contract_types": "perpetual_futures",
        "page_size": 100,
    }

    while True:
        r = requests.get(
            BASE_URL + "/v2/products",
            params=params,
            timeout=HTTP_TIMEOUT,
        )
        r.raise_for_status()
        body = r.json()

        for p in body.get("result", []):
            symbol = p.get("symbol")
            if symbol in TARGET_SYMBOLS:
                perp_map[symbol] = p.get("id")

        after_cursor = body.get("meta", {}).get("after")
        if not after_cursor:
            break

        params["after"] = after_cursor

    if not perp_map:
        raise RuntimeError("No perpetual futures found — check TARGET_SYMBOLS and API endpoint")

    logging.info("PERPETUAL SYMBOL MAP LOADED: %s", perp_map)
    return perp_map


# =========================
# TICKER DATA
# =========================
def get_ticker(symbol):
    r = requests.get(BASE_URL + f"/v2/tickers/{symbol}", timeout=HTTP_TIMEOUT)
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

    state_engine = StateEngine()
    funding_strategy = FundingBiasStrategy()
    volatility_strategy = VolatilityRegimeStrategy()

    SYMBOLS = load_perpetual_products()
    logging.info("PERPETUAL SYMBOL MAP LOADED: %s", SYMBOLS)

    while True:
        if enforce(state_engine=state_engine):
            time.sleep(LOOP_INTERVAL_SECONDS)
            continue

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
                features["nyse_session"] = bool(
                    is_nyse_hours(loop_start) if symbol in XSTOCK_SYMBOLS else False
                )

                # -------- STRATEGY VOTES --------
                funding_vote = funding_strategy.vote(features)
                volatility_vote = volatility_strategy.vote(features, symbol=symbol)

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
                decision = evaluate(features, symbol=symbol)

                # -------- STATE ENGINE --------
                state_engine.process(
                    symbol,
                    decision,
                    features,
                    mark_price,
                    funding_vote,
                    volatility_vote,
                )

                write_event("decision.jsonl", {
                    "timestamp_utc": loop_start.isoformat(),
                    "symbol": symbol,
                    "decision": decision,
                    "features": {
                        "funding_rate_abs": features.get("funding_rate_abs"),
                        "time_to_funding_sec": features.get("time_to_funding_sec"),
                        "pre_volatility_5m": features.get("pre_volatility_5m"),
                    },
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

        total_daily_pnl = sum(s.daily_realized_return for s in state_engine.symbols.values())
        if check_auto_arm(total_daily_pnl, consecutive_losses=0, api_error_count=0):
            continue

        logging.info("HEARTBEAT | loop_complete")
        time.sleep(LOOP_INTERVAL_SECONDS)


# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    main()
