# core/state_engine.py

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.strategy.exit_manager import (
    build_vol_entry_context,
    evaluate_vol_exit,
    get_vol_trailing_stop,
    handle_vol_timeout,
)
from app.strategy.regime_filter import volatility_spike_detected
from config.asset_rules import get_asset_rules
from config.risk import RISK
from config.settings import SPREAD_MAX_PCT, XSTOCK_SYMBOLS
from utils.io import write_event

STATE_FILE = Path("execution_state.json")
XSTOCK_SYMBOL_SET = {symbol.upper() for symbol in XSTOCK_SYMBOLS}


def place_order(symbol, direction):
    print("ORDER_PLACED", symbol, direction)


def is_cooldown_active(last_trade_time, cooldown_duration):
    if last_trade_time is None:
        return False
    return (time.time() - last_trade_time) < cooldown_duration


def _parse_dt(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _coerce_float(value):
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _trade_return(side, entry_price, exit_price):
    if (
        side not in {"LONG", "SHORT"}
        or not isinstance(entry_price, (int, float))
        or not isinstance(exit_price, (int, float))
        or entry_price <= 0
    ):
        return 0.0

    if side == "LONG":
        return (float(exit_price) - float(entry_price)) / float(entry_price)

    return (float(entry_price) - float(exit_price)) / float(entry_price)


def _normalize_decision(decision):
    if isinstance(decision, dict):
        value = decision.get("state") or decision.get("decision") or ""
    else:
        value = decision or ""

    return str(value).upper().strip()


def _extract_decision_direction(decision):
    if not isinstance(decision, dict):
        return None

    direction = decision.get("direction")
    if isinstance(direction, str):
        direction = direction.upper().strip()
        if direction in {"LONG", "SHORT"}:
            return direction

    msb = decision.get("msb")
    if msb == 1:
        return "LONG"
    if msb == -1:
        return "SHORT"

    return None


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
        self.last_observed_at = None
        self.last_trade_time = None
        self.cooldown_until = None
        self.halted_until = None
        self.warmup_loops_remaining = 0
        self.daily_realized_return = 0.0
        self.loss_streak = 0
        self.consecutive_losses = 0
        self.last_exit_reason = None
        self.vol_context = None
        self.position_notional_usd = None
        self.position_size_units = None
        self.signal_confidence = None
        self.confidence_scale = None
        self.volatility_scale = None


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

    def _build_position_payload(self, state):
        payload = {}

        if isinstance(getattr(state, "position_notional_usd", None), (int, float)):
            payload["position_notional_usd"] = float(state.position_notional_usd)
        if isinstance(getattr(state, "position_size_units", None), (int, float)):
            payload["position_size_units"] = float(state.position_size_units)
        if isinstance(getattr(state, "signal_confidence", None), (int, float)):
            payload["signal_confidence"] = float(state.signal_confidence)
        if isinstance(getattr(state, "confidence_scale", None), (int, float)):
            payload["confidence_scale"] = float(state.confidence_scale)
        if isinstance(getattr(state, "volatility_scale", None), (int, float)):
            payload["volatility_scale"] = float(state.volatility_scale)

        return payload

    def _log(
        self,
        symbol,
        action,
        strategy_type,
        side,
        price,
        reason,
        now,
        spread_pct=None,
        nyse_session=False,
        position_payload=None,
    ):
        asset_trade_type = "xstock" if symbol.upper() in XSTOCK_SYMBOL_SET else "crypto"
        payload = {
            "symbol": symbol,
            "action": action,
            "trade_type": asset_trade_type,
            "strategy_type": strategy_type,
            "side": side,
            "price": float(price),
            "reason": reason,
            "timestamp_utc": now.isoformat(),
            "nyse_session": bool(nyse_session),
        }

        if isinstance(spread_pct, (int, float)):
            payload["spread_pct"] = float(spread_pct)

        if isinstance(position_payload, dict):
            payload.update(position_payload)

        write_event("paper_trades.jsonl", payload)

    def _log_rejection(
        self,
        symbol,
        side,
        reason,
        now,
        spread_pct=None,
        nyse_session=False,
        position_payload=None,
    ):
        payload = {
            "symbol": symbol,
            "action": "REJECT",
            "trade_type": "xstock" if symbol.upper() in XSTOCK_SYMBOL_SET else "crypto",
            "side": side,
            "reason": reason,
            "timestamp_utc": now.isoformat(),
            "nyse_session": bool(nyse_session),
        }

        if isinstance(spread_pct, (int, float)):
            payload["spread_pct"] = float(spread_pct)

        if isinstance(position_payload, dict):
            payload.update(position_payload)

        write_event("paper_trades.jsonl", payload)

    def _reset_position(self, state):
        state.state = "FLAT"
        state.trade_type = None
        state.side = None
        state.entry_time = None
        state.entry_price = None
        state.peak_price = None
        state.trough_price = None
        state.exit_funding_ts = None
        state.vol_context = None
        state.position_notional_usd = None
        state.position_size_units = None
        state.signal_confidence = None
        state.confidence_scale = None
        state.volatility_scale = None

    def _cooldown_seconds(self, exit_reason, realized_return):
        if exit_reason in {
            "hard_stop",
            "funding_stop",
            "stale_recovery_exit",
            "structure_break",
        }:
            return RISK.stop_loss_cooldown_sec

        if realized_return < 0:
            return RISK.losing_exit_cooldown_sec

        return RISK.win_cooldown_sec

    def _check_global_circuit_breaker(self):
        total_daily_loss = sum(
            float(getattr(state, "daily_realized_return", 0.0))
            for state in self.symbols.values()
        )

        if total_daily_loss <= -RISK.portfolio_max_daily_drawdown_pct:
            print(
                "[CRITICAL] GLOBAL CIRCUIT BREAKER: "
                f"portfolio daily loss {total_daily_loss:.4%} "
                f"<= {-RISK.portfolio_max_daily_drawdown_pct:.4%}"
            )
            return True

        return False

    def _position_count(self, state):
        return 0 if getattr(state, "state", "FLAT") == "FLAT" else 1

    def _has_capacity_for_entry(self, state):
        return self._position_count(state) < RISK.max_concurrent_positions_per_symbol

    def _extract_signal_confidence(self, decision, trade_type, funding_vote, vol_vote):
        values = []

        decision_score = _coerce_float((decision or {}).get("score"))
        if decision_score is not None:
            values.append(_clamp(decision_score, 0.0, 1.0))

        if trade_type == "FUNDING":
            funding_confidence = _coerce_float((funding_vote or {}).get("confidence"))
            if funding_confidence is not None:
                values.append(_clamp(funding_confidence, 0.0, 1.0))
        elif trade_type == "VOL":
            vol_confidence = _coerce_float((vol_vote or {}).get("confidence"))
            if vol_confidence is not None:
                values.append(_clamp(vol_confidence, 0.0, 1.0))

        if not values:
            return RISK.min_position_confidence

        return _clamp(
            sum(values) / len(values),
            RISK.min_position_confidence,
            RISK.max_position_confidence,
        )

    def _build_position_sizing(self, price, pre_volatility, signal_confidence):
        signal_confidence = _clamp(
            signal_confidence,
            RISK.min_position_confidence,
            RISK.max_position_confidence,
        )

        confidence_band = max(
            RISK.max_position_confidence - RISK.min_position_confidence,
            1e-9,
        )
        normalized_confidence = (
            signal_confidence - RISK.min_position_confidence
        ) / confidence_band
        confidence_scale = (
            RISK.position_confidence_floor_scale
            + normalized_confidence * (1.0 - RISK.position_confidence_floor_scale)
        )

        volatility_scale = 1.0
        if isinstance(pre_volatility, (int, float)) and pre_volatility > 0:
            volatility_scale = _clamp(
                RISK.position_volatility_target_pct / float(pre_volatility),
                RISK.position_volatility_floor_scale,
                RISK.position_volatility_ceiling_scale,
            )

        position_notional_usd = _clamp(
            RISK.base_position_notional_usd * confidence_scale * volatility_scale,
            RISK.min_position_notional_usd,
            RISK.max_position_notional_usd,
        )
        position_size_units = (
            position_notional_usd / float(price)
            if isinstance(price, (int, float)) and price > 0
            else 0.0
        )

        return {
            "position_notional_usd": round(position_notional_usd, 4),
            "position_size_units": round(position_size_units, 8),
            "signal_confidence": round(signal_confidence, 4),
            "confidence_scale": round(confidence_scale, 4),
            "volatility_scale": round(volatility_scale, 4),
        }

    def _close_trade(self, symbol, state, price, exit_reason, now, spread_pct=None, nyse_session=False):
        trade_type = state.trade_type
        side = state.side

        if trade_type in {"FUNDING", "VOL"} and side in {"LONG", "SHORT"}:
            print(f"[{trade_type}_EXIT] {symbol} {exit_reason}")
            self._log(
                symbol,
                "EXIT",
                trade_type,
                side,
                price,
                exit_reason,
                now,
                spread_pct=spread_pct,
                nyse_session=nyse_session,
                position_payload=self._build_position_payload(state),
            )

            realized_return = _trade_return(side, state.entry_price, price)
            state.daily_realized_return += realized_return

            if realized_return < 0:
                state.consecutive_losses = getattr(state, "consecutive_losses", 0) + 1
            else:
                state.consecutive_losses = 0

            if getattr(state, "consecutive_losses", 0) >= 3:
                state.halted_until = (now + timedelta(hours=1)).isoformat()

            if realized_return < 0:
                state.loss_streak += 1
            elif realized_return > 0:
                state.loss_streak = 0

            cooldown = self._cooldown_seconds(exit_reason, realized_return)
            state.cooldown_until = (now + timedelta(seconds=cooldown)).isoformat()
            state.last_exit_reason = exit_reason

        self._reset_position(state)

    def _position_is_stale(self, state, now):
        entry_time = _parse_dt(state.entry_time)
        if not entry_time:
            return False

        age_sec = (now - entry_time).total_seconds()
        if state.trade_type == "FUNDING":
            return age_sec > RISK.max_funding_trade_age_sec
        if state.trade_type == "VOL":
            return age_sec > RISK.max_vol_trade_age_sec
        return False

    def _can_attempt_entry(self, state, now):
        if state.daily_trade_count >= RISK.max_daily_trades_per_symbol:
            return False

        if state.daily_realized_return <= -RISK.max_daily_loss_pct:
            return False

        if state.loss_streak >= RISK.max_consecutive_losses:
            return False

        cooldown_until = _parse_dt(state.cooldown_until)
        if cooldown_until and now < cooldown_until:
            return False

        if state.warmup_loops_remaining > 0:
            state.warmup_loops_remaining -= 1
            return False

        return True

    def _entry_block_reason(self, state, now):
        if state.daily_trade_count >= RISK.max_daily_trades_per_symbol:
            return "daily_trade_cap_reject"

        if state.daily_realized_return <= -RISK.max_daily_loss_pct:
            return "daily_loss_limit_reject"

        if state.loss_streak >= RISK.max_consecutive_losses:
            return "loss_streak_reject"

        cooldown_until = _parse_dt(state.cooldown_until)
        if cooldown_until and now < cooldown_until:
            return "cooldown_active"

        if state.warmup_loops_remaining > 0:
            state.warmup_loops_remaining -= 1
            return "warmup_active"

        return None

    def _record_entry(
        self,
        state,
        trade_type,
        side,
        price,
        now,
        position_payload,
        exit_funding_ts=None,
        vol_context=None,
    ):
        state.state = f"IN_{trade_type}_TRADE"
        state.trade_type = trade_type
        state.side = side
        state.entry_time = now.isoformat()
        state.entry_price = float(price)
        state.peak_price = float(price)
        state.trough_price = float(price)
        state.exit_funding_ts = exit_funding_ts
        state.cooldown_until = None
        state.vol_context = vol_context
        state.position_notional_usd = position_payload.get("position_notional_usd")
        state.position_size_units = position_payload.get("position_size_units")
        state.signal_confidence = position_payload.get("signal_confidence")
        state.confidence_scale = position_payload.get("confidence_scale")
        state.volatility_scale = position_payload.get("volatility_scale")

    def process(self, symbol, decision, features, price, funding_vote, vol_vote, now=None):
        print("TRACE_STATE_ENGINE_ENTER", symbol, decision)

        now = now or datetime.now(timezone.utc)

        if symbol not in self.symbols:
            self.symbols[symbol] = SymbolState()

        s = self.symbols[symbol]

        halted_until = _parse_dt(getattr(s, "halted_until", None))
        if halted_until and now < halted_until:
            return

        if self._check_global_circuit_breaker():
            return

        if not isinstance(price, (int, float)):
            return

        asset_rules = get_asset_rules(symbol)
        is_xstock = symbol.upper() in XSTOCK_SYMBOL_SET

        ttf = features.get("time_to_funding_sec")
        funding_rate = features.get("funding_rate")
        funding_rate_abs = features.get("funding_rate_abs")
        pre_volatility = features.get("pre_volatility_5m")
        spread_pct = features.get("bid_ask_spread_pct")
        nyse_session = bool(features.get("nyse_session")) if is_xstock else False

        spread_limit_pct = SPREAD_MAX_PCT if is_xstock else RISK.max_bid_ask_spread_pct

        # ---------------- DAILY RESET ----------------
        today = now.date().isoformat()
        if s.trade_date != today:
            s.trade_date = today
            s.daily_trade_count = 0
            s.funding_trade_taken = False
            s.vol_long_taken = False
            s.vol_short_taken = False
            s.daily_realized_return = 0.0
            s.loss_streak = 0
            s.consecutive_losses = 0

        # ---------------- STALE DATA / RECOVERY ----------------
        last_seen = _parse_dt(s.last_observed_at)
        if last_seen and (now - last_seen).total_seconds() > RISK.max_stale_loop_gap_sec:
            if s.state != "FLAT":
                self._close_trade(
                    symbol,
                    s,
                    price,
                    "stale_recovery_exit",
                    now,
                    spread_pct=spread_pct,
                    nyse_session=nyse_session,
                )

            s.warmup_loops_remaining = max(
                s.warmup_loops_remaining,
                RISK.warmup_loops_after_stale_gap,
            )
            s.last_ttf = ttf
            s.last_observed_at = now.isoformat()
            self._save()
            return

        if s.state != "FLAT" and self._position_is_stale(s, now):
            self._close_trade(
                symbol,
                s,
                price,
                "stale_recovery_exit",
                now,
                spread_pct=spread_pct,
                nyse_session=nyse_session,
            )
            s.warmup_loops_remaining = max(
                s.warmup_loops_remaining,
                RISK.warmup_loops_after_stale_gap,
            )
            s.last_ttf = ttf
            s.last_observed_at = now.isoformat()
            self._save()
            return

        # =================================================
        # ENTRY LOGIC
        # =================================================
        if s.state == "FLAT":
            current_position = s.state
            last_trade_time = getattr(s, "last_trade_time", None)
            if last_trade_time == 0:
                last_trade_time = None
                s.last_trade_time = None
            cooldown_duration = RISK.win_cooldown_sec
            cooldown_active = is_cooldown_active(last_trade_time, cooldown_duration)
            decision_state = _normalize_decision(decision)
            decision_direction = _extract_decision_direction(decision)
            if isinstance(decision, dict):
                decision["state"] = decision_state
                if decision_direction in {"LONG", "SHORT"}:
                    decision["direction"] = decision_direction
            vol_signal = vol_vote.get("signal") if isinstance(vol_vote, dict) else None
            vol_reason = (
                vol_vote.get("reason", "OB_retest_confirmation")
                if isinstance(vol_vote, dict)
                else "OB_retest_confirmation"
            )
            vol_confidence = vol_vote.get("confidence") if isinstance(vol_vote, dict) else None

            funding_side = None
            if isinstance(funding_vote, dict):
                funding_side = funding_vote.get("side")
                if funding_side not in {"LONG", "SHORT"}:
                    bias = funding_vote.get("bias")
                    if bias == 1:
                        funding_side = "LONG"
                    elif bias == -1:
                        funding_side = "SHORT"

            funding_rate_safe = (
                not isinstance(funding_rate_abs, (int, float))
                or funding_rate_abs <= RISK.max_funding_rate_abs
            )
            spread_ok = isinstance(spread_pct, (int, float)) and spread_pct <= spread_limit_pct
            vol_setup_detected = (
                isinstance(vol_vote, dict)
                and vol_vote.get("state") == "STRUCTURE_CONFIRMED"
                and vol_signal in {"LONG", "SHORT"}
            )

            funding_entry_ready = (
                not is_xstock
                and not s.funding_trade_taken
                and isinstance(ttf, (int, float))
                and 0 <= ttf <= RISK.funding_entry_window_sec
                and isinstance(funding_rate, (int, float))
                and isinstance(funding_rate_abs, (int, float))
                and RISK.min_funding_rate_abs <= funding_rate_abs <= RISK.max_funding_rate_abs
                and isinstance(pre_volatility, (int, float))
                and pre_volatility <= RISK.max_funding_pre_volatility_5m
                and spread_ok
                and isinstance(funding_vote, dict)
                and funding_vote.get("state") == "BIAS_DETECTED"
                and funding_side in {"LONG", "SHORT"}
                and not volatility_spike_detected(vol_vote, asset_rules)
            )

            vol_entry_candidate = (
                vol_setup_detected
                and isinstance(vol_confidence, (int, float))
                and vol_confidence >= RISK.min_vol_confidence
                and isinstance(pre_volatility, (int, float))
                and pre_volatility <= RISK.max_vol_pre_volatility_5m
                and funding_rate_safe
                and not (
                    isinstance(ttf, (int, float))
                    and ttf <= RISK.funding_blackout_for_vol_sec
                )
            )
            vol_entry_ready = vol_entry_candidate and spread_ok
            is_entry_window = (
                (
                    isinstance(ttf, (int, float))
                    and 0 <= ttf <= RISK.funding_entry_window_sec
                )
                or not (
                    isinstance(ttf, (int, float))
                    and ttf <= RISK.funding_blackout_for_vol_sec
                )
            )

            print("CHECK_STATE", current_position)
            print("CHECK_COOLDOWN", cooldown_active)
            print("CHECK_WINDOW", is_entry_window)
            current_time = time.time()
            print("CHECK_COOLDOWN_DEBUG", {
                "cooldown_active": cooldown_active,
                "last_trade_time": last_trade_time,
                "current_time": current_time,
                "time_diff": current_time - last_trade_time if last_trade_time else None,
                "cooldown_duration": cooldown_duration,
            })
            print("TRACE_ENTRY_CHECK", {
                "state": decision.get("state") if isinstance(decision, dict) else decision,
                "position": current_position,
                "cooldown": cooldown_active,
            })

            intended_side = funding_side if funding_entry_ready else vol_signal
            entry_block_reason = None

            if (
                isinstance(decision, dict)
                and decision_direction in {"LONG", "SHORT"}
                and decision.get("state") == "EDGE_DETECTED"
            ):
                intended_side = decision_direction

                if decision["state"] == "EDGE_DETECTED":
                    if current_position == "FLAT" and not cooldown_active:
                        print("ENTRY_TRIGGERED", symbol)
                        print("TRACE_ORDER_EXECUTION", symbol, decision["direction"])
                        place_order(symbol, decision["direction"])
                        s.last_trade_time = time.time()

                        position_payload = self._build_position_sizing(
                            price=price,
                            pre_volatility=pre_volatility,
                            signal_confidence=self._extract_signal_confidence(
                                decision,
                                "VOL",
                                funding_vote,
                                vol_vote,
                            ),
                        )
                        self._record_entry(
                            s,
                            "VOL",
                            decision["direction"],
                            price,
                            now,
                            position_payload=position_payload,
                            vol_context=build_vol_entry_context(
                                decision["direction"],
                                vol_vote if isinstance(vol_vote, dict) else {},
                                asset_rules,
                            ),
                        )

                        s.daily_trade_count += 1
                        if decision["direction"] == "LONG":
                            s.vol_long_taken = True
                        else:
                            s.vol_short_taken = True

                        self._log(
                            symbol,
                            "ENTRY",
                            "VOL",
                            decision["direction"],
                            price,
                            "edge_detected_entry",
                            now,
                            spread_pct=spread_pct,
                            nyse_session=nyse_session,
                            position_payload=position_payload,
                        )
                    else:
                        self._log_rejection(
                            symbol,
                            decision_direction,
                            "cooldown_active",
                            now,
                            spread_pct=spread_pct,
                            nyse_session=nyse_session,
                        )
            elif (
                (entry_block_reason := self._entry_block_reason(s, now))
                and intended_side in {"LONG", "SHORT"}
            ):
                self._log_rejection(
                    symbol,
                    intended_side,
                    entry_block_reason,
                    now,
                    spread_pct=spread_pct,
                    nyse_session=nyse_session,
                )
            elif not funding_rate_safe and (funding_side in {"LONG", "SHORT"} or vol_signal in {"LONG", "SHORT"}):
                self._log_rejection(
                    symbol,
                    funding_side if funding_side in {"LONG", "SHORT"} else vol_signal,
                    "funding_rate_filter",
                    now,
                    spread_pct=spread_pct,
                    nyse_session=nyse_session,
                )
            elif vol_setup_detected and (
                not isinstance(vol_confidence, (int, float))
                or vol_confidence < RISK.min_vol_confidence
            ):
                self._log_rejection(
                    symbol,
                    vol_signal,
                    "confidence_too_low",
                    now,
                    spread_pct=spread_pct,
                    nyse_session=nyse_session,
                )
            elif vol_setup_detected and (
                not isinstance(pre_volatility, (int, float))
                or pre_volatility > RISK.max_vol_pre_volatility_5m
            ):
                self._log_rejection(
                    symbol,
                    vol_signal,
                    "volatility_too_high",
                    now,
                    spread_pct=spread_pct,
                    nyse_session=nyse_session,
                )
            elif vol_setup_detected and isinstance(ttf, (int, float)) and ttf <= RISK.funding_blackout_for_vol_sec:
                self._log_rejection(
                    symbol,
                    vol_signal,
                    "funding_blackout",
                    now,
                    spread_pct=spread_pct,
                    nyse_session=nyse_session,
                )
            elif vol_setup_detected and not spread_ok:
                self._log_rejection(
                    symbol,
                    vol_signal,
                    "spread_reject",
                    now,
                    spread_pct=spread_pct,
                    nyse_session=nyse_session,
                )
            elif vol_entry_ready and vol_signal == "LONG" and s.vol_long_taken:
                self._log_rejection(
                    symbol,
                    vol_signal,
                    "direction_already_taken",
                    now,
                    spread_pct=spread_pct,
                    nyse_session=nyse_session,
                )
            elif vol_entry_ready and vol_signal == "SHORT" and s.vol_short_taken:
                self._log_rejection(
                    symbol,
                    vol_signal,
                    "direction_already_taken",
                    now,
                    spread_pct=spread_pct,
                    nyse_session=nyse_session,
                )
            elif not self._has_capacity_for_entry(s):
                if intended_side in {"LONG", "SHORT"}:
                    self._log_rejection(
                        symbol,
                        intended_side,
                        "position_cap_reject",
                        now,
                        spread_pct=spread_pct,
                        nyse_session=nyse_session,
                    )
            elif funding_entry_ready:
                position_payload = self._build_position_sizing(
                    price=price,
                    pre_volatility=pre_volatility,
                    signal_confidence=self._extract_signal_confidence(
                        decision,
                        "FUNDING",
                        funding_vote,
                        vol_vote,
                    ),
                )
                print("CHECK_ENTRY_CALL", {
                    "symbol": symbol,
                    "decision": decision
                })
                self._record_entry(
                    s,
                    "FUNDING",
                    funding_side,
                    price,
                    now,
                    position_payload=position_payload,
                    exit_funding_ts=(now + timedelta(seconds=float(ttf))).isoformat(),
                )

                s.daily_trade_count += 1
                s.funding_trade_taken = True

                print(f"[FUNDING_ENTRY] {symbol} {funding_side}")
                self._log(
                    symbol,
                    "ENTRY",
                    "FUNDING",
                    funding_side,
                    price,
                    "funding_entry",
                    now,
                    spread_pct=spread_pct,
                    nyse_session=nyse_session,
                    position_payload=position_payload,
                )

            elif vol_entry_ready and vol_signal == "LONG":
                position_payload = self._build_position_sizing(
                    price=price,
                    pre_volatility=pre_volatility,
                    signal_confidence=self._extract_signal_confidence(
                        decision,
                        "VOL",
                        funding_vote,
                        vol_vote,
                    ),
                )
                print("CHECK_ENTRY_CALL", {
                    "symbol": symbol,
                    "decision": decision
                })
                self._record_entry(
                    s,
                    "VOL",
                    "LONG",
                    price,
                    now,
                    position_payload=position_payload,
                    vol_context=build_vol_entry_context(
                        "LONG",
                        vol_vote,
                        asset_rules,
                    ),
                )

                s.daily_trade_count += 1
                s.vol_long_taken = True

                print(f"[VOL_LONG_ENTRY] {symbol}")
                self._log(
                    symbol,
                    "ENTRY",
                    "VOL",
                    "LONG",
                    price,
                    vol_reason,
                    now,
                    spread_pct=spread_pct,
                    nyse_session=nyse_session,
                    position_payload=position_payload,
                )

            elif vol_entry_ready and vol_signal == "SHORT":
                position_payload = self._build_position_sizing(
                    price=price,
                    pre_volatility=pre_volatility,
                    signal_confidence=self._extract_signal_confidence(
                        decision,
                        "VOL",
                        funding_vote,
                        vol_vote,
                    ),
                )
                print("CHECK_ENTRY_CALL", {
                    "symbol": symbol,
                    "decision": decision
                })
                self._record_entry(
                    s,
                    "VOL",
                    "SHORT",
                    price,
                    now,
                    position_payload=position_payload,
                    vol_context=build_vol_entry_context(
                        "SHORT",
                        vol_vote,
                        asset_rules,
                    ),
                )

                s.daily_trade_count += 1
                s.vol_short_taken = True

                print(f"[VOL_SHORT_ENTRY] {symbol}")
                self._log(
                    symbol,
                    "ENTRY",
                    "VOL",
                    "SHORT",
                    price,
                    vol_reason,
                    now,
                    spread_pct=spread_pct,
                    nyse_session=nyse_session,
                    position_payload=position_payload,
                )

        # =================================================
        # FUNDING MANAGEMENT
        # =================================================
        elif s.state == "IN_FUNDING_TRADE":
            move = _trade_return(s.side, s.entry_price, price)
            exit_reason = None

            if move <= -RISK.funding_stop_pct:
                exit_reason = "funding_stop"

            exit_funding_ts = _parse_dt(s.exit_funding_ts)
            if not exit_reason and exit_funding_ts and now >= exit_funding_ts:
                exit_reason = "funding_time"

            if (
                not exit_reason
                and isinstance(s.last_ttf, (int, float))
                and isinstance(ttf, (int, float))
                and ttf > s.last_ttf
            ):
                exit_reason = "funding_rollover"

            if exit_reason:
                self._close_trade(
                    symbol,
                    s,
                    price,
                    exit_reason,
                    now,
                    spread_pct=spread_pct,
                    nyse_session=nyse_session,
                )

        # =================================================
        # VOL MANAGEMENT
        # =================================================
        elif s.state == "IN_VOL_TRADE":
            move = _trade_return(s.side, s.entry_price, price)
            exit_reason = None

            if s.side == "LONG":
                if price > s.peak_price:
                    s.peak_price = price

                if move >= RISK.vol_take_profit_pct:
                    exit_reason = "take_profit"
                elif move <= -RISK.vol_hard_stop_pct:
                    exit_reason = "hard_stop"
                elif isinstance((s.vol_context or {}).get("timeout_trailing_stop"), (int, float)):
                    trail = float(s.vol_context["timeout_trailing_stop"])
                    exit_reason = "trailing_stop" if price <= trail else None
                else:
                    trail = get_vol_trailing_stop(s)
                    if isinstance(trail, (int, float)):
                        exit_reason = "trailing_stop" if price <= trail else None
            else:
                if price < s.trough_price:
                    s.trough_price = price

                if move >= RISK.vol_take_profit_pct:
                    exit_reason = "take_profit"
                elif move <= -RISK.vol_hard_stop_pct:
                    exit_reason = "hard_stop"
                elif isinstance((s.vol_context or {}).get("timeout_trailing_stop"), (int, float)):
                    trail = float(s.vol_context["timeout_trailing_stop"])
                    exit_reason = "trailing_stop" if price >= trail else None
                else:
                    trail = get_vol_trailing_stop(s)
                    if isinstance(trail, (int, float)):
                        exit_reason = "trailing_stop" if price >= trail else None

            if not exit_reason:
                exit_reason, updated_context = evaluate_vol_exit(
                    symbol=symbol,
                    state=s,
                    price=price,
                    vol_vote=vol_vote if isinstance(vol_vote, dict) else {},
                    asset_rules=asset_rules,
                )
                s.vol_context = updated_context

            if not exit_reason:
                entry_time = _parse_dt(s.entry_time)
                if entry_time and (now - entry_time).total_seconds() >= RISK.vol_timeout_sec:
                    should_exit_timeout = handle_vol_timeout(s, move)
                    if should_exit_timeout:
                        exit_reason = "timeout"

            if exit_reason:
                self._close_trade(
                    symbol,
                    s,
                    price,
                    exit_reason,
                    now,
                    spread_pct=spread_pct,
                    nyse_session=nyse_session,
                )

        s.last_ttf = ttf
        s.last_observed_at = now.isoformat()
        self._save()
