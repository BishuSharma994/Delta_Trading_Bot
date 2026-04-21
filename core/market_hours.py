import logging
from datetime import datetime, time as dtime

import pytz

logger = logging.getLogger(__name__)
NYSE_TZ = pytz.timezone("America/New_York")

XSTOCK_SYMBOLS = frozenset({
    "GOOGLXUSD", "METAXUSD", "AAPLXUSD", "AMZNXUSD",
    "TSLAXUSD",  "NVDAXUSD", "COINXUSD", "CRCLXUSD",
    "QQQXUSD",   "SPYXUSD",
})

MARKET_OPEN = dtime(9, 30)
MARKET_CLOSE = dtime(16, 0)


def is_us_market_hours() -> bool:
    now_est = datetime.now(NYSE_TZ)
    if now_est.weekday() >= 5:
        return False
    return MARKET_OPEN <= now_est.time() <= MARKET_CLOSE


def symbol_tradeable(symbol: str) -> bool:
    if symbol not in XSTOCK_SYMBOLS:
        return True
    allowed = is_us_market_hours()
    if not allowed:
        logger.debug(f"SKIP {symbol} — outside NYSE hours")
    return allowed
