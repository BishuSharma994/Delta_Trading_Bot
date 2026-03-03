# core/state_engine.py

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path


STATE_FILE = Path("execution_state.json")


# =====================================================
# Symbol State
# =====================================================

class SymbolState:
    def __init__(self):
        self.state = "FLAT"  # FLAT | IN_FUNDING_TRADE | IN_VOL_TRADE
        self.trade_type = None  # None | FUNDING | VOL

        self.entry_time = None
        self.entry_price = None

        self.exit_funding_ts = None

        self.trade_date = None
        self.daily_trade_count = 0
        self.funding_trade_taken = False
        self.vol_trade_taken = False

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
                s.exit_funding_ts = data.get("exit_funding_ts")
                s.trade_date = data.get("trade_date")
                s.daily_trade_count = data.get("daily_trade_count", 0)
                s.funding_trade_taken = data.get("funding_trade_taken", False)
                s.vol_trade_taken = data.get("vol_trade_taken", False)
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
                "exit_funding_ts": s.exit_funding_ts,
                "trade_date": s.trade_date,
                "daily_trade_count": s.daily_trade_count,
                "funding_trade_taken": s.funding_trade_taken,
                "vol_trade_taken": s.vol_trade_taken,
                "last_decision_state": s.last_decision_state,
                "last_ttf": s.last_ttf,
            }

        with open(STATE_FILE, "w") as f:
            json.dump(raw, f, indent=2)

    # =====================================================
    # Core Process
    # =====================================================

    def process(
        self,
        symbol,
        decision,
        features,
        current_price,
        funding_vote,
        volatility_vote,
    ):
        now = datetime.now(timezone.utc)

        if symbol not in self.symbols:
            self.symbols[symbol] = SymbolState()

        s = self.symbols[symbol]

        current_decision_state = decision.get("state")
        current_ttf = features.get("time_to_funding_sec")

        # -------------------------
        # Daily Reset
        # -------------------------
        today = now.date().isoformat()

        if s.trade_date != today:
            s.trade_date = today
            s.daily_trade_count = 0
            s.funding_trade_taken = False
            s.vol_trade_taken = False

        # -------------------------
        # Hard Cap: 2 trades per day
        # -------------------------
        if s.daily_trade_count >= 2:
            s.last_decision_state = current_decision_state
            s.last_ttf = current_ttf
            self._save()
            return

        # =====================================================
        # ENTRY LOGIC
        # =====================================================

        if s.state == "FLAT":

            # -------------------------
            # 1️⃣ Funding Priority Entry
            # -------------------------
            FUNDING_WINDOW_SECONDS = 120

            if (
                not s.funding_trade_taken
                and isinstance(current_ttf, (int, float))
                and current_ttf <= FUNDING_WINDOW_SECONDS
                and current_decision_state == "EDGE_DETECTED"
            ):
                s.state = "IN_FUNDING_TRADE"
                s.trade_type = "FUNDING"
                s.entry_time = now.isoformat()
                s.entry_price = current_price

                funding_ts = now + timedelta(seconds=float(current_ttf))
                s.exit_funding_ts = funding_ts.isoformat()

                s.daily_trade_count += 1
                s.funding_trade_taken = True

                print(f"[FUNDING_ENTRY] {symbol} at {now.isoformat()}")

            # -------------------------
            # 2️⃣ Volatility Entry
            # -------------------------
            elif (
                not s.vol_trade_taken
                and volatility_vote == "EDGE_DETECTED"
            ):
                s.state = "IN_VOL_TRADE"
                s.trade_type = "VOL"
                s.entry_time = now.isoformat()
                s.entry_price = current_price

                s.daily_trade_count += 1
                s.vol_trade_taken = True

                print(f"[VOL_ENTRY] {symbol} at {now.isoformat()}")

        # =====================================================
        # FUNDING TRADE MANAGEMENT
        # =====================================================

        elif s.state == "IN_FUNDING_TRADE":

            # Hard stop-loss (0.3%)
            if s.entry_price:
                if abs(current_price - s.entry_price) / s.entry_price >= 0.003:
                    print(f"[FUNDING_STOP] {symbol} at {now.isoformat()}")

                    s.state = "FLAT"
                    s.trade_type = None
                    s.entry_time = None
                    s.entry_price = None
                    s.exit_funding_ts = None

            # Funding timestamp exit
            elif s.exit_funding_ts:
                funding_time = datetime.fromisoformat(s.exit_funding_ts)

                if now >= funding_time:
                    print(f"[FUNDING_EXIT] {symbol} at {now.isoformat()}")

                    s.state = "FLAT"
                    s.trade_type = None
                    s.entry_time = None
                    s.entry_price = None
                    s.exit_funding_ts = None

        # =====================================================
        # VOLATILITY TRADE MANAGEMENT
        # =====================================================

        elif s.state == "IN_VOL_TRADE":

            if s.entry_price:

                move_pct = (current_price - s.entry_price) / s.entry_price

                # Take-profit (0.25%)
                if move_pct >= 0.0025:
                    print(f"[VOL_TP] {symbol} at {now.isoformat()}")

                    s.state = "FLAT"
                    s.trade_type = None
                    s.entry_time = None
                    s.entry_price = None

                # Stop-loss (0.3%)
                elif move_pct <= -0.003:
                    print(f"[VOL_STOP] {symbol} at {now.isoformat()}")

                    s.state = "FLAT"
                    s.trade_type = None
                    s.entry_time = None
                    s.entry_price = None

        # -------------------------
        # Diagnostics
        # -------------------------
        s.last_decision_state = current_decision_state
        s.last_ttf = current_ttf

        self._save()