# NOTE: Delta Exchange xStock perpetuals trade 24/7.
# NYSE hours are tracked for spread-tightening only, not session gating.

import logging
from datetime import datetime, time as dtime, timezone

logger = logging.getLogger(__name__)

XSTOCK_SYMBOLS = frozenset({
    "GOOGLXUSD", "METAXUSD", "AAPLXUSD", "AMZNXUSD",
    "TSLAXUSD",  "NVDAXUSD", "COINXUSD", "CRCLXUSD",
    "QQQXUSD",   "SPYXUSD",
})

NYSE_OPEN_UTC = dtime(13, 30)
NYSE_CLOSE_UTC = dtime(20, 0)


def is_nyse_hours(now_utc: datetime) -> bool:
    if now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=timezone.utc)
    else:
        now_utc = now_utc.astimezone(timezone.utc)

    if now_utc.weekday() >= 5:
        return False

    now_time = now_utc.time().replace(tzinfo=None)
    return NYSE_OPEN_UTC <= now_time < NYSE_CLOSE_UTC


def is_us_market_hours() -> bool:
    return is_nyse_hours(datetime.now(timezone.utc))


def symbol_tradeable(symbol: str, now_utc: datetime | None = None) -> bool:
    """Delta Exchange xStocks trade 24/7. No session gate required."""
    del symbol, now_utc
    return True
