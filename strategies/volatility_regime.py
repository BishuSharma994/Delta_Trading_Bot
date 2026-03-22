\# strategies/volatility_regime.py

import logging

from app.strategy.msb_ob_engine import process_structure
from app.strategy.regime_engine import detect_regime
from Delta_Trading_Bot.data.memory import get_recent_candles
from Delta_Trading_Bot.strategies.base import Strategy


def _fmt_metric(value):
    if isinstance(value, (int, float)):
        return f"{float(value):.6f}"
    return "n/a"


def evaluate_volatility(symbol: str, candles: list[dict]) -> tuple[dict, dict]:
    regime_data = detect_regime(candles)

    logging.info(
        "[REGIME] symbol=%s avg_range=%s dir_strength=%s trend_strength=%s regime=%s",
        symbol,
        _fmt_metric(regime_data.get("avg_range")),
        _fmt_metric(regime_data.get("dir_strength")),
        _fmt_metric(regime_data.get("trend_strength")),
        regime_data.get("regime"),
    )

    # --- HARD GATE (NO STRUCTURE PROCESSING)
    if regime_data["regime"] != "TRENDING":
        return regime_data, {"signal": None, "market": 0, "ob": None}

    # --- STRUCTURE ONLY AFTER REGIME PASS
    structure = process_structure(candles)

    if not structure:
        return regime_data, {"signal": None, "market": 0, "ob": None}

    logging.info("[MSB] symbol=%s market=%s", symbol, structure.get("market"))

    ob = structure.get("ob")
    if isinstance(ob, dict):
        logging.info(
            "[OB] symbol=%s type=%s range=%s-%s",
            symbol,
            ob.get("type"),
            _fmt_metric(ob.get("low")),
            _fmt_metric(ob.get("high")),
        )

    # --- STRICT SIGNAL VALIDATION (NO EARLY ENTRY)
    signal = structure.get("signal")

    if signal not in {"LONG", "SHORT"}:
        return regime_data, structure

    # --- FINAL ENTRY LOG (ONLY AFTER FULL VALIDATION)
    logging.info(
        "[ENTRY] symbol=%s signal=%s reason=%s",
        symbol,
        signal,
        structure.get("reason"),
    )

    return regime_data, structure


class VolatilityRegimeStrategy(Strategy):
    name = "volatility_regime"

    def vote(self, features: dict, symbol: str | None = None) -> dict:
        if not symbol:
            return {
                "state": "NO_DATA",
                "bias": 0,
                "confidence": 0.0,
                "reason": "Symbol required for volatility structure",
                "signal": None,
            }

        candles = get_recent_candles(symbol, limit=40)

        if not candles or len(candles) < 20:
            return {
                "state": "NO_DATA",
                "bias": 0,
                "confidence": 0.0,
                "reason": "Insufficient candle history",
                "signal": None,
            }

        regime_data, structure = evaluate_volatility(symbol, candles)

        # --- HARD BLOCK
        if regime_data["regime"] != "TRENDING":
            return {
                "state": "NO_TRADE",
                "bias": 0,
                "confidence": 0.0,
                "reason": "Regime filter blocked volatility trade",
                "signal": None,
                "regime": regime_data.get("regime"),
                "avg_range": regime_data.get("avg_range"),
                "dir_strength": regime_data.get("dir_strength"),
                "trend_strength": regime_data.get("trend_strength"),
                "market": structure.get("market"),
                "ob": structure.get("ob"),
            }

        signal = structure.get("signal")

        confidence = min(
            1.0,
            max(
                float(regime_data.get("dir_strength", 0.0)),
                float(regime_data.get("trend_strength", 0.0)) * 100,
            ),
        )

        # --- ONLY VALID STRUCTURE SIGNALS PASS
        if signal in {"LONG", "SHORT"}:
            return {
                "state": "STRUCTURE_CONFIRMED",
                "bias": 1 if signal == "LONG" else -1,
                "confidence": confidence,
                "reason": structure.get("reason", "OB_retest_confirmation"),
                "signal": signal,
                "sl": structure.get("sl"),
                "regime": regime_data.get("regime"),
                "avg_range": regime_data.get("avg_range"),
                "dir_strength": regime_data.get("dir_strength"),
                "trend_strength": regime_data.get("trend_strength"),
                "market": structure.get("market"),
                "ob": structure.get("ob"),
            }

        # --- TRENDING BUT NO ENTRY
        return {
            "state": "TRENDING_NO_SIGNAL",
            "bias": 0,
            "confidence": 0.0,
            "reason": "No OB confirmation",
            "signal": None,
            "regime": regime_data.get("regime"),
            "avg_range": regime_data.get("avg_range"),
            "dir_strength": regime_data.get("dir_strength"),
            "trend_strength": regime_data.get("trend_strength"),
            "market": structure.get("market"),
            "ob": structure.get("ob"),
        }