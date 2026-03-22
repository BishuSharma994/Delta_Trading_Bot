# core/state_engine.py

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from utils.io import write_event

STATE_FILE = Path("execution_state.json")


class SymbolState:
    def __init__(self):
        self.state = "FLAT"
        self.trade_type = None  # FUNDING / VOL
        self.side = None  # LONG / SHORT

        self.entry_time = None
        self.entry_price = None

        self.peak_price = None
        self.trough_price = None

        self.exit_funding_ts = None

        self.trade_date = None
        self.daily_trade_count = 0

        self.funding_trade_taken = False
        self.vol_long_taken = False
        self.vol_short_taken = False

        self.last_ttf = None


class StateEngine:
    def __init__(self):
        self.symbols = {}
        self._load()

    def _load(self):
        if STATE_FILE.exists():
            with open(STATE_FILE) as f:
                raw = json.load(f)

            for symbol, data in raw.items():
                s = SymbolState()
                s.__dict__.update(data)
                self.symbols[symbol] = s

    def _save(self):
        raw = {k: v.__dict__ for k, v in self.symbols.items()}
        with open(STATE_FILE, "w") as f:
            json.dump(raw, f, indent=2)

    def _log(self, symbol, action, trade_type, side, price, reason):
        write_event("paper_trades.jsonl", {
            "symbol": symbol,
            "action": action,
            "trade_type": trade_type,
            "side": side,
            "price": float(price),
            "reason": reason,
        })

    def process(self, symbol, decision, features, price, funding_vote, vol_vote):

        now = datetime.now(timezone.utc)

        if symbol not in self.symbols:
            self.symbols[symbol] = SymbolState()

        s = self.symbols[symbol]

        ttf = features.get("time_to_funding_sec")
        funding_rate = features.get("funding_rate")

        # ---------------- DAILY RESET ----------------
        today = now.date().isoformat()
        if s.trade_date != today:
            s.trade_date = today
            s.daily_trade_count = 0
            s.funding_trade_taken = False
            s.vol_long_taken = False
            s.vol_short_taken = False

        if s.daily_trade_count >= 3:
            s.last_ttf = ttf
            self._save()
            return

        # =================================================
        # ENTRY LOGIC
        # =================================================
        if s.state == "FLAT":
            vol_signal = vol_vote.get("signal") if isinstance(vol_vote, dict) else None
            vol_reason = (
                vol_vote.get("reason", "OB_retest_confirmation")
                if isinstance(vol_vote, dict)
                else "OB_retest_confirmation"
            )

            vol_long_entry_ready = vol_signal == "LONG"
            vol_short_entry_ready = vol_signal == "SHORT"

            # ---------- FUNDING ----------
            if (
                not s.funding_trade_taken
                and isinstance(ttf, (int, float))
                and ttf <= 120
                and funding_rate is not None
            ):

                side = "SHORT" if funding_rate > 0 else "LONG"

                s.state = "IN_FUNDING_TRADE"
                s.trade_type = "FUNDING"
                s.side = side
                s.entry_time = now.isoformat()
                s.entry_price = price
                s.peak_price = price
                s.trough_price = price

                s.exit_funding_ts = (now + timedelta(seconds=ttf)).isoformat()

                s.daily_trade_count += 1
                s.funding_trade_taken = True

                print(f"[FUNDING_ENTRY] {symbol} {side}")

                self._log(symbol, "ENTRY", "FUNDING", side, price, "funding_entry")

            # ---------- VOL LONG ----------
            elif (
                not s.vol_long_taken
                and vol_long_entry_ready
            ):
                s.state = "IN_VOL_TRADE"
                s.trade_type = "VOL"
                s.side = "LONG"
                s.entry_time = now.isoformat()
                s.entry_price = price
                s.peak_price = price
                s.trough_price = price

                s.daily_trade_count += 1
                s.vol_long_taken = True

                print(f"[VOL_LONG_ENTRY] {symbol}")

                self._log(symbol, "ENTRY", "VOL", "LONG", price, vol_reason)

            # ---------- VOL SHORT ----------
            elif (
                not s.vol_short_taken
                and vol_short_entry_ready
            ):
                s.state = "IN_VOL_TRADE"
                s.trade_type = "VOL"
                s.side = "SHORT"
                s.entry_time = now.isoformat()
                s.entry_price = price
                s.peak_price = price
                s.trough_price = price

                s.daily_trade_count += 1
                s.vol_short_taken = True

                print(f"[VOL_SHORT_ENTRY] {symbol}")

                self._log(symbol, "ENTRY", "VOL", "SHORT", price, vol_reason)

        # =================================================
        # FUNDING MANAGEMENT
        # =================================================
        elif s.state == "IN_FUNDING_TRADE":

            if s.side == "LONG":
                move = (price - s.entry_price) / s.entry_price
            else:
                move = (s.entry_price - price) / s.entry_price

            exit_reason = None

            if move <= -0.005:
                exit_reason = "funding_stop"

            if not exit_reason and s.exit_funding_ts:
                if now >= datetime.fromisoformat(s.exit_funding_ts):
                    exit_reason = "funding_time"

            if not exit_reason and s.last_ttf and ttf:
                if ttf > s.last_ttf:
                    exit_reason = "funding_rollover"

            if exit_reason:
                print(f"[FUNDING_EXIT] {symbol} {exit_reason}")

                self._log(symbol, "EXIT", "FUNDING", s.side, price, exit_reason)

                s.state = "FLAT"
                s.trade_type = None
                s.side = None

        # =================================================
        # VOL MANAGEMENT (FIXED)
        # =================================================
        elif s.state == "IN_VOL_TRADE":

            TP = 0.006
            SL = 0.005
            MIN_ACTIVATION = 0.003

            if s.side == "LONG":

                move = (price - s.entry_price) / s.entry_price

                if price > s.peak_price:
                    s.peak_price = price

                if move >= TP:
                    exit_reason = "take_profit"

                elif move <= -SL:
                    exit_reason = "hard_stop"

                elif move >= MIN_ACTIVATION:
                    trail = s.peak_price * (1 - 0.005)
                    exit_reason = "trailing_stop" if price <= trail else None
                else:
                    exit_reason = None

            else:  # SHORT

                move = (s.entry_price - price) / s.entry_price

                if price < s.trough_price:
                    s.trough_price = price

                if move >= TP:
                    exit_reason = "take_profit"

                elif move <= -SL:
                    exit_reason = "hard_stop"

                elif move >= MIN_ACTIVATION:
                    trail = s.trough_price * (1 + 0.005)
                    exit_reason = "trailing_stop" if price >= trail else None
                else:
                    exit_reason = None

            entry_time = datetime.fromisoformat(s.entry_time)

            if not exit_reason and (now - entry_time).seconds > 900:
                exit_reason = "timeout"

            if exit_reason:
                print(f"[VOL_EXIT] {symbol} {exit_reason}")

                self._log(symbol, "EXIT", "VOL", s.side, price, exit_reason)

                s.state = "FLAT"
                s.trade_type = None
                s.side = None

        s.last_ttf = ttf
        self._save()
