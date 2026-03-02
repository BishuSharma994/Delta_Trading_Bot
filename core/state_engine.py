# core/state_engine.py
# Deterministic Execution State Machine (DRY-RUN ONLY)

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
                self.symbols[symbol] = s

    def _save(self):
        raw = {}
        for symbol, s in self.symbols.items():
            raw[symbol] = {
                "state": s.state,
                "entry_time": s.entry_time,
                "cooldown_until": s.cooldown_until,
                "last_decision_state": s.last_decision_state,
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

        # --- FLAT ---
        if s.state == "FLAT":
            if (
                current_decision_state == "EDGE_DETECTED"
                and s.last_decision_state != "EDGE_DETECTED"
                and features.get("time_to_funding_sec", 999999)
                < ENTRY_WINDOW_SECONDS
            ):
                s.state = "IN_POSITION"
                s.entry_time = now.isoformat()
                print(f"[DRY_RUN_ENTRY] {symbol} at {now.isoformat()}")

        # --- IN_POSITION ---
        elif s.state == "IN_POSITION":
            ttf = features.get("time_to_funding_sec", None)

            # Exit at funding settlement or missing funding
            if ttf is None or ttf <= 0:
                s.state = "COOLDOWN"
                s.cooldown_until = (now + timedelta(seconds=COOLDOWN_SECONDS)).isoformat()
                print(f"[DRY_RUN_EXIT] {symbol} at {now.isoformat()}")

        # --- COOLDOWN ---
        elif s.state == "COOLDOWN":
            if s.cooldown_until:
                cooldown_time = datetime.fromisoformat(s.cooldown_until)
                if now >= cooldown_time:
                    s.state = "FLAT"
                    s.cooldown_until = None

        s.last_decision_state = current_decision_state
        self._save()
