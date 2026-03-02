# core/state_engine.py
# Deterministic Execution State Machine (DRY-RUN ONLY)
# Funding Rollover Safe Version

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path


STATE_FILE = Path("execution_state.json")

ENTRY_WINDOW_SECONDS = 1800
COOLDOWN_SECONDS = 3600


class SymbolState:
    def __init__(self):
        self.state = "FLAT"
        self.entry_time = None
        self.cooldown_until = None
        self.last_decision_state = None
        self.last_ttf = None  # track previous funding countdown


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
                s.entry_time = data.get("entry_time")
                s.cooldown_until = data.get("cooldown_until")
                s.last_decision_state = data.get("last_decision_state")
                s.last_ttf = data.get("last_ttf")
                self.symbols[symbol] = s

    def _save(self):
        raw = {}
        for symbol, s in self.symbols.items():
            raw[symbol] = {
                "state": s.state,
                "entry_time": s.entry_time,
                "cooldown_until": s.cooldown_until,
                "last_decision_state": s.last_decision_state,
                "last_ttf": s.last_ttf,
            }

        with open(STATE_FILE, "w") as f:
            json.dump(raw, f, indent=2)

    # -------------------------
    # Core Transition Logic
    # -------------------------
    def process(self, symbol: str, decision: dict, features: dict):
        now = datetime.now(timezone.utc)

        if symbol not in self.symbols:
            self.symbols[symbol] = SymbolState()

        s = self.symbols[symbol]
        current_decision_state = decision.get("state")
        current_ttf = features.get("time_to_funding_sec")

        # -------------------------
        # FLAT → IN_POSITION
        # -------------------------
        if s.state == "FLAT":
            if (
                current_decision_state == "EDGE_DETECTED"
                and s.last_decision_state != "EDGE_DETECTED"
                and isinstance(current_ttf, (int, float))
                and current_ttf < ENTRY_WINDOW_SECONDS
            ):
                s.state = "IN_POSITION"
                s.entry_time = now.isoformat()
                print(f"[DRY_RUN_ENTRY] {symbol} at {now.isoformat()}")

        # -------------------------
        # IN_POSITION → COOLDOWN
        # Detect funding rollover
        # -------------------------
        elif s.state == "IN_POSITION":

            # Fail-safe: if timing missing, exit
            if current_ttf is None:
                s.state = "COOLDOWN"
                s.cooldown_until = (now + timedelta(seconds=COOLDOWN_SECONDS)).isoformat()
                print(f"[DRY_RUN_EXIT - MISSING_TTF] {symbol} at {now.isoformat()}")

            else:
                # Detect rollover: countdown resets upward
                if s.last_ttf is not None:
                    if current_ttf > s.last_ttf:
                        s.state = "COOLDOWN"
                        s.cooldown_until = (
                            now + timedelta(seconds=COOLDOWN_SECONDS)
                        ).isoformat()
                        print(f"[DRY_RUN_EXIT - FUNDING_ROLLOVER] {symbol} at {now.isoformat()}")

        # -------------------------
        # COOLDOWN → FLAT
        # -------------------------
        elif s.state == "COOLDOWN":
            if s.cooldown_until:
                cooldown_time = datetime.fromisoformat(s.cooldown_until)
                if now >= cooldown_time:
                    s.state = "FLAT"
                    s.cooldown_until = None
                    print(f"[COOLDOWN_COMPLETE] {symbol} at {now.isoformat()}")

        # Track for next loop
        s.last_decision_state = current_decision_state
        s.last_ttf = current_ttf

        self._save()