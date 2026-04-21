"""
tools/fetch_product_ids.py
Fetches real product IDs for all symbols from Delta Exchange India.
Run once. Copy output into config/symbols.py.

Usage (Windows VS Code terminal):
    python tools/fetch_product_ids.py
"""

import os

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.india.delta.exchange"
API_KEY = os.getenv("DELTA_API_KEY", "")

TARGET_SYMBOLS = [
    "BTCUSD", "ETHUSD", "SOLUSD", "BNBUSD",
    "GOOGLXUSD", "METAXUSD", "AAPLXUSD", "AMZNXUSD",
    "TSLAXUSD", "NVDAXUSD", "COINXUSD", "CRCLXUSD",
    "QQQXUSD", "SPYXUSD",
]


def fetch_product_ids():
    headers = {"api-key": API_KEY}
    response = requests.get(
        f"{BASE_URL}/v2/products",
        headers=headers,
        timeout=15,
    )

    if response.status_code != 200:
        print(f"ERROR {response.status_code}: {response.text[:300]}")
        return

    products = response.json().get("result", [])
    found = {}

    for product in products:
        symbol = product.get("symbol", "")
        if symbol in TARGET_SYMBOLS:
            found[symbol] = product.get("id")

    print("\n" + "=" * 50)
    print("SYMBOL ID MAP — paste into config/symbols.py")
    print("=" * 50)
    print("SYMBOL_ID_MAP = {")
    for sym in TARGET_SYMBOLS:
        pid = found.get(sym, "NOT_FOUND")
        print(f'    "{sym}": {pid},')
    print("}")
    print("=" * 50)

    missing = [s for s in TARGET_SYMBOLS if s not in found]
    if missing:
        print(f"\nNOT FOUND ({len(missing)} symbols):")
        for sym in missing:
            print(f"  {sym} — check symbol name on Delta Exchange")


if __name__ == "__main__":
    fetch_product_ids()
