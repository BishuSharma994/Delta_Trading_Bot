"""
brain/data_collector.py
Fetches 1.5 years of OHLCV candle data from Delta Exchange India API.
Resolutions: 15m and 1h
Symbols: all 14 (crypto + xStock)
Saves to: brain/data/historical/{SYMBOL}_{resolution}.jsonl
"""

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
BASE_URL = "https://api.india.delta.exchange"
API_KEY = os.getenv("DELTA_API_KEY", "")

ALL_SYMBOLS = [
    "BTCUSD", "ETHUSD", "SOLUSD", "BNBUSD",
    "GOOGLXUSD", "METAXUSD", "AAPLXUSD", "AMZNXUSD",
    "TSLAXUSD", "NVDAXUSD", "COINXUSD", "CRCLXUSD",
    "QQQXUSD", "SPYXUSD",
]
RESOLUTIONS = ["15m", "1h"]
LOOKBACK_DAYS = 540
MAX_PER_REQUEST = 500
DATA_DIR = Path(__file__).parent / "data" / "historical"
DATA_DIR.mkdir(parents=True, exist_ok=True)

RESOLUTION_SECONDS = {"15m": 900, "1h": 3600, "4h": 14400, "1d": 86400}


def _fetch_page(symbol: str, resolution: str, start_ts: int, end_ts: int) -> list:
    try:
        response = requests.get(
            f"{BASE_URL}/v2/history/candles",
            headers={"api-key": API_KEY},
            params={
                "resolution": resolution,
                "symbol": symbol,
                "start": start_ts,
                "end": end_ts,
            },
            timeout=15,
        )
        data = response.json()
        if not data.get("success"):
            logger.warning(
                f"API error {symbol} {resolution}: {data.get('error')}"
            )
            return []
        return data.get("result", [])
    except Exception as exc:
        logger.error(f"Request failed {symbol} {resolution}: {exc}")
        return []


def fetch_full_history(symbol: str, resolution: str) -> list:
    step = RESOLUTION_SECONDS.get(resolution, 3600)
    end_ts = int(datetime.now(timezone.utc).timestamp())
    start_ts = end_ts - LOOKBACK_DAYS * 86400
    cursor = start_ts
    candles = []

    logger.info(
        f"Fetching {symbol} {resolution} "
        f"{datetime.utcfromtimestamp(start_ts).date()} → "
        f"{datetime.utcfromtimestamp(end_ts).date()}"
    )

    while cursor < end_ts:
        page_end = min(cursor + step * MAX_PER_REQUEST, end_ts)
        page = _fetch_page(symbol, resolution, cursor, page_end)
        candles.extend(page)
        cursor = page_end + 1
        time.sleep(0.25)

    seen = set()
    unique = []
    for candle in candles:
        ts = candle.get("time") or candle.get("timestamp")
        if ts not in seen:
            seen.add(ts)
            unique.append(candle)

    unique.sort(key=lambda candle: candle.get("time") or candle.get("timestamp", 0))
    logger.info(f"  {symbol} {resolution}: {len(unique)} candles")
    return unique


def save_candles(symbol: str, resolution: str, candles: list) -> Path:
    path = DATA_DIR / f"{symbol}_{resolution}.jsonl"
    with open(path, "w", encoding="utf-8") as handle:
        for candle in candles:
            handle.write(json.dumps(candle) + "\n")
    return path


def load_candles(symbol: str, resolution: str) -> list:
    path = DATA_DIR / f"{symbol}_{resolution}.jsonl"
    if not path.exists():
        return []
    result = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                result.append(json.loads(line))
    return result


def collect_all(force_refresh: bool = False) -> dict:
    """
    Fetches all symbol+resolution combinations.
    Skips if cached file exists and force_refresh=False.
    Returns dict keyed by 'SYMBOL_resolution'.
    """
    result = {}
    for symbol in ALL_SYMBOLS:
        for resolution in RESOLUTIONS:
            key = f"{symbol}_{resolution}"
            path = DATA_DIR / f"{key}.jsonl"
            if path.exists() and not force_refresh:
                candles = load_candles(symbol, resolution)
                logger.info(f"Cache hit {key}: {len(candles)} candles")
            else:
                candles = fetch_full_history(symbol, resolution)
                if candles:
                    save_candles(symbol, resolution, candles)
            result[key] = candles
    return result


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    collect_all(force_refresh=True)
    print("Data collection complete.")
