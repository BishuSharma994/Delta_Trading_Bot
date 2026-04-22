import logging
from datetime import datetime, time as dtime, timezone

logger = logging.getLogger(__name__)

XSTOCK_SYMBOLS = frozenset({
    "GOOGLXUSD", "METAXUSD", "AAPLXUSD", "AMZNXUSD",
    "TSLAXUSD",  "NVDAXUSD", "COINXUSD", "CRCLXUSD",
    "QQQXUSD",   "SPYXUSD",
})

NYSE_OPEN_UTC = dtime(13, 30)  # ← NEW
NYSE_CLOSE_UTC = dtime(20, 0)  # ← NEW


def is_nyse_hours(now_utc: datetime) -> bool:  # ← NEW
    if now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=timezone.utc)
    else:
        now_utc = now_utc.astimezone(timezone.utc)

    if now_utc.weekday() >= 5:
        return False

    now_time = now_utc.time().replace(tzinfo=None)
    return NYSE_OPEN_UTC <= now_time < NYSE_CLOSE_UTC


def is_us_market_hours() -> bool:
    return is_nyse_hours(datetime.now(timezone.utc))  # ← CHANGED


def symbol_tradeable(symbol: str, now_utc: datetime | None = None) -> bool:  # ← CHANGED
    if symbol not in XSTOCK_SYMBOLS:
        return True

    allowed = is_nyse_hours(now_utc or datetime.now(timezone.utc))
    if not allowed:
        logger.info("SKIP %s - outside NYSE hours", symbol)  # ← CHANGED
    return allowed
