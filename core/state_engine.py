# core/state_engine.py
# Dual-Mode Structured State Engine (FOUNDATION ONLY)

import json
from datetime import datetime, timezone
from pathlib import Path


STATE_FILE = Path("execution_state.json")


# =====================================================
# Symbol State Structure (Dual Mode Ready)
# =====================================================

class SymbolState:
    def __init__(self):
        # -------------------------
        # Core State
        # -------------------------
        self.state = "FLAT"
        # "FLAT"
        # "IN_FUNDING_TRADE"
        # "IN_VOL_TRADE"

        self.trade_type = None
        # None | "FUNDING" | "VOL"

        # -------------------------
        # Trade Lifecycle
        # -------------------------
        self.entry_time = None
        self.entry_price = None

        self.stop_price = None
        self.take_profit_price = None

        self.exit_funding_ts = None  # used only for funding trades

        # -------------------------
        # Daily Controls
        # -------------------------
        self.trade_date = None  # YYYY-MM-DD
        self.daily_trade_count = 0

        self.funding_trade_taken = False
        self.vol_trade_taken = False

        # -------------------------
        # Optional Cooldown
        # -------------------------
        self.cooldown_until = None

        # -------------------------
        # Diagnostics
        # -------------------------
        self.last_decision_state = None
        self.last_ttf = None


# =====================================================
# State Engine
# =====================================================

class StateEngine:
    def __init__(self):
        self.symbols = {}
        self._load()

    # -------------------------
    # Persistence
    # -------------------------

    def _load(self):
        if STATE_FILE.exists():
            with open(STATE_FILE, "r") as f:
                raw = json.load(f)

            for symbol, data in raw.items():
                s = SymbolState()

                s.state = data.get("state", "FLAT")
                s.trade_type = data.get("trade_type")

                s.entry_time = data.get("entry_time")
                s.entry_price = data.get("entry_price")

                s.stop_price = data.get("stop_price")
                s.take_profit_price = data.get("take_profit_price")

                s.exit_funding_ts = data.get("exit_funding_ts")

                s.trade_date = data.get("trade_date")
                s.daily_trade_count = data.get("daily_trade_count", 0)

                s.funding_trade_taken = data.get("funding_trade_taken", False)
                s.vol_trade_taken = data.get("vol_trade_taken", False)

                s.cooldown_until = data.get("cooldown_until")

                s.last_decision_state = data.get("last_decision_state")
                s.last_ttf = data.get("last_ttf")

                self.symbols[symbol] = s

    def _save(self):
        raw = {}

        for symbol, s in self.symbols.items():
            raw[symbol] = {
                "state": s.state,
                "trade_type": s.trade_type,

                "entry_time": s.entry_time,
                "entry_price": s.entry_price,

                "stop_price": s.stop_price,
                "take_profit_price": s.take_profit_price,

                "exit_funding_ts": s.exit_funding_ts,

                "trade_date": s.trade_date,
                "daily_trade_count": s.daily_trade_count,
                "funding_trade_taken": s.funding_trade_taken,
                "vol_trade_taken": s.vol_trade_taken,

                "cooldown_until": s.cooldown_until,

                "last_decision_state": s.last_decision_state,
                "last_ttf": s.last_ttf,
            }

        with open(STATE_FILE, "w") as f:
            json.dump(raw, f, indent=2)

    # -------------------------
    # Core Process (STRUCTURE ONLY)
    # -------------------------

    def process(self, symbol: str, decision: dict, features: dict):
    now = datetime.now(timezone.utc)

    if symbol not in self.symbols:
        self.symbols[symbol] = SymbolState()

    s = self.symbols[symbol]

    current_decision_state = decision.get("state")
    current_ttf = features.get("time_to_funding_sec")

    # -------------------------------------------------
    # Daily Reset Logic
    # -------------------------------------------------
    today = now.date().isoformat()

    if s.trade_date != today:
        s.trade_date = today
        s.daily_trade_count = 0
        s.funding_trade_taken = False
        s.vol_trade_taken = False

    # -------------------------------------------------
    # Hard Trade Cap (Max 2 per day)
    # -------------------------------------------------
    if s.daily_trade_count >= 2:
        s.last_decision_state = current_decision_state
        s.last_ttf = current_ttf
        self._save()
        return

    # =================================================
    # FUNDING ENTRY LOGIC (PRIORITY MODE)
    # =================================================
    if s.state == "FLAT":

        # Funding window: 2 minutes before funding
        FUNDING_WINDOW_SECONDS = 120

        if (
            not s.funding_trade_taken
            and isinstance(current_ttf, (int, float))
            and current_ttf <= FUNDING_WINDOW_SECONDS
            and current_decision_state == "EDGE_DETECTED"
        ):
            # Enter funding trade
            s.state = "IN_FUNDING_TRADE"
            s.trade_type = "FUNDING"
            s.entry_time = now.isoformat()

            # Lock funding timestamp
            funding_ts = now + timedelta(seconds=float(current_ttf))
            s.exit_funding_ts = funding_ts.isoformat()

            s.daily_trade_count += 1
            s.funding_trade_taken = True

            print(f"[FUNDING_ENTRY] {symbol} at {now.isoformat()}")

    # =================================================
    # FUNDING EXIT LOGIC (TIME-BASED ONLY FOR NOW)
    # =================================================
    elif s.state == "IN_FUNDING_TRADE":

        if s.exit_funding_ts:
            funding_time = datetime.fromisoformat(s.exit_funding_ts)

            if now >= funding_time:
                print(f"[FUNDING_EXIT] {symbol} at {now.isoformat()}")

                # Reset to flat
                s.state = "FLAT"
                s.trade_type = None
                s.entry_time = None
                s.exit_funding_ts = None

    # -------------------------------------------------
    # Diagnostics
    # -------------------------------------------------
    s.last_decision_state = current_decision_state
    s.last_ttf = current_ttf

    self._save()