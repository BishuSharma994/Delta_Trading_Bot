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

    # --- HARD GATE
    if regime_data["regime"] != "TRENDING":
        return regime_data, {"signal": None, "market": 0, "ob": None}

    # --- STRUCTURE (STATEFUL)
    structure = process_structure(symbol, candles)

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

    signal = structure.get("signal")

    # --- FINAL ENTRY LOG (ONLY AFTER VALID SIGNAL)
    if signal in {"LONG", "SHORT"}:
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
                "reason": "Symbol required",
                "signal": None,
            }

        candles = get_recent_candles(symbol, limit=40)

        if not candles or len(candles) < 20:
            return {
                "state": "NO_DATA",
                "bias": 0,
                "confidence": 0.0,
                "reason": "Insufficient candles",
                "signal": None,
            }

        regime_data, structure = evaluate_volatility(symbol, candles)

        # --- REGIME BLOCK
        if regime_data["regime"] != "TRENDING":
            return {
                "state": "NO_TRADE",
                "bias": 0,
                "confidence": 0.0,
                "reason": "Regime blocked",
                "signal": None,
                "regime": regime_data.get("regime"),
            }

        signal = structure.get("signal")

        confidence = min(
            1.0,
            max(
                float(regime_data.get("dir_strength", 0.0)),
                float(regime_data.get("trend_strength", 0.0)) * 100,
            ),
        )

        # --- VALID ENTRY
        if signal in {"LONG", "SHORT"}:
            return {
                "state": "STRUCTURE_CONFIRMED",
                "bias": 1 if signal == "LONG" else -1,
                "confidence": confidence,
                "reason": structure.get("reason"),
                "signal": signal,
                "sl": structure.get("sl"),
                "regime": regime_data.get("regime"),
                "market": structure.get("market"),
                "ob": structure.get("ob"),
            }

        # --- NO ENTRY YET (WAITING FOR OB BREAK)
        return {
            "state": "TRENDING_NO_SIGNAL",
            "bias": 0,
            "confidence": 0.0,
            "reason": "Waiting for OB breakout",
            "signal": None,
            "regime": regime_data.get("regime"),
            "market": structure.get("market"),
            "ob": structure.get("ob"),
        }