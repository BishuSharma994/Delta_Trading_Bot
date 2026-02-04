import os
import time
import hmac
import hashlib
import json
import requests
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

# =========================
# LOAD ENV
# =========================
load_dotenv()

API_KEY = os.getenv("DELTA_API_KEY")
API_SECRET = os.getenv("DELTA_API_SECRET")

if not API_KEY or not API_SECRET:
    raise Exception("API keys not loaded")

# =========================
# CONFIG
# =========================
BASE_URL = "https://api.india.delta.exchange"
SYMBOL = "BTCUSD"
PRODUCT_ID = 84

ORDER_SIZE = 1
FUNDING_THRESHOLD = 0.0002
LOOP_INTERVAL_SECONDS = 60
MAX_HOLD_SECONDS = 60 * 30
HTTP_TIMEOUT = 5
position_entry_time = None
KILL_SWITCH = False  # SET TO True TO HALT ALL TRADING
print("KILL_SWITCH VALUE AT START:", KILL_SWITCH)


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
        hashlib.sha256
    ).hexdigest()

    headers = {
        "api-key": API_KEY,
        "timestamp": ts,
        "signature": sig,
        "User-Agent": "python-bot",
        "Content-Type": "application/json",
    }
    return headers


def signed_get(path):
    headers = _sign("GET", path)
    r = requests.get(BASE_URL + path, headers=headers, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    return r.json()["result"]


def signed_post(path, body_dict):
    body = json.dumps(body_dict)
    headers = _sign("POST", path, body)
    r = requests.post(
        BASE_URL + path,
        headers=headers,
        data=body,
        timeout=HTTP_TIMEOUT
    )
    if not r.ok:
        print("STATUS:", r.status_code)
        print("RESPONSE:", r.text)
    r.raise_for_status()
    return r.json()["result"]

# =========================
# API FUNCTIONS
# =========================
def get_wallet():
    return signed_get("/v2/wallet/balances")


def get_positions():
    return signed_get("/v2/positions/margined")



def get_mark_price():
    r = requests.get(
        BASE_URL + f"/v2/tickers/{SYMBOL}",
        timeout=HTTP_TIMEOUT
    )
    r.raise_for_status()
    return float(r.json()["result"]["mark_price"])


def get_funding_rate():
    try:
        r = requests.get(
            BASE_URL + f"/v2/products/{PRODUCT_ID}",
            timeout=HTTP_TIMEOUT
        )
        r.raise_for_status()
        product = r.json()["result"]

        funding = product.get("funding_rate")
        if funding is None:
            return None

        return float(funding)

    except Exception:
        return None



def place_market_order(side):
    print("KILL SWITCH CHECK:", KILL_SWITCH)
    if KILL_SWITCH:
        print("KILL SWITCH ACTIVE → ORDER BLOCKED")
        logging.critical("KILL SWITCH ACTIVE → ORDER BLOCKED")
        raise RuntimeError("KILL SWITCH PREVENTED ORDER")
    body = {
        "product_id": PRODUCT_ID,
        "size": ORDER_SIZE,
        "side": side,
        "order_type": "market_order",
    }
    print("ORDER PAYLOAD:", body)
    order = signed_post("/v2/orders", body)
    logging.info("ORDER PLACED | %s", order)
    return order


def close_position():
    if KILL_SWITCH:
        print("KILL SWITCH ACTIVE → CLOSE BLOCKED")
        logging.warning("KILL SWITCH ACTIVE → CLOSE BLOCKED")
        return
    positions = get_positions()
    for p in positions:
        if p["product_symbol"] == SYMBOL and int(p["size"]) != 0:
            side = "sell" if p["side"] == "buy" else "buy"
            body = {
                "product_id": PRODUCT_ID,
                "size": abs(int(p["size"])),
                "side": side,
                "order_type": "market_order",
                "reduce_only": True,
            }
            result = signed_post("/v2/orders", body)
            logging.info("POSITION CLOSED | %s", result)
            print("POSITION CLOSED")
            return

# =========================
# MAIN LOOP
# =========================
def main():
    if KILL_SWITCH:
     logging.warning("KILL SWITCH ENABLED — BOT IN READ-ONLY MODE")

    global position_entry_time
    logging.info("BOT STARTED")

    while True:
        try:
            print("-" * 60)
            print("UTC:", datetime.now(timezone.utc).isoformat())

            wallet = get_wallet()
            balance = 0.0
            for a in wallet:
                if a["asset_symbol"] in ("INR", "USD"):
                    balance = float(a["available_balance"])
                    break

            price = get_mark_price()
            funding = get_funding_rate()

            print("Available Margin:", balance)
            print("Symbol:", SYMBOL)
            print("Mark Price:", price)
            print("Funding Rate:", funding)

            logging.info(
                "Heartbeat | Margin=%s | Price=%s | Funding=%s",
                balance, price, funding
            )

            positions = get_positions()
            open_positions = [
                p for p in positions
                if p["product_symbol"] == SYMBOL and int(p["size"]) != 0
            ]

            print("Open Positions:", len(open_positions))

            if not open_positions:
                position_entry_time = None

                if funding is None:
                    print("NO FUNDING DATA → STANDING BY")

                elif funding >= FUNDING_THRESHOLD:
                    print("FUNDING HIGH → ENTER SHORT")
                    place_market_order("sell")
                    position_entry_time = time.time()

                elif funding <= -FUNDING_THRESHOLD:
                    print("FUNDING LOW → ENTER LONG")
                    place_market_order("buy")
                    position_entry_time = time.time()

                else:
                    print("FUNDING NEUTRAL → NO TRADE")

            else:
                if position_entry_time is None:
                    position_entry_time = time.time()

                held = time.time() - position_entry_time
                print(f"POSITION HELD FOR {int(held)} seconds")

                if held >= MAX_HOLD_SECONDS:
                    print("MAX HOLD TIME REACHED → CLOSING POSITION")
                    close_position()
                    position_entry_time = None
                else:
                    print("HOLDING POSITION")

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
