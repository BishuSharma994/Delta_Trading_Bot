import logging

from config.asset_rules import get_asset_rules
from app.strategy.htf_bias import detect_htf_bias
from app.strategy.msb_ob_engine import process_structure
from app.strategy.regime_filter import evaluate_regime_filter
from Delta_Trading_Bot.data.memory import get_recent_candles
from Delta_Trading_Bot.strategies.base import Strategy


def _fmt_metric(value):
    if isinstance(value, (int, float)):
        return f"{float(value):.6f}"
    return "n/a"


def evaluate_volatility(symbol: str, candles: list[dict]) -> tuple[dict, dict]:
    asset_rules = get_asset_rules(symbol)
    regime_data = evaluate_regime_filter(candles, asset_rules)

    logging.info(
        "[REGIME] symbol=%s avg_range=%s atr_pct=%s dir_strength=%s trend_strength=%s chop_score=%s regime=%s reason=%s",
        symbol,
        _fmt_metric(regime_data.get("avg_range")),
        _fmt_metric(regime_data.get("atr_pct")),
        _fmt_metric(regime_data.get("dir_strength")),
        _fmt_metric(regime_data.get("trend_strength")),
        _fmt_metric(regime_data.get("chop_score")),
        regime_data.get("regime"),
        regime_data.get("reason"),
    )

    # --- HARD GATE
    if not regime_data.get("allow_trade"):
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

    htf_bias = detect_htf_bias(candles, asset_rules)
    structure["htf_bias"] = htf_bias.get("bias")
    structure["htf_bias_reason"] = htf_bias.get("reason")

    logging.info(
        "[HTF] symbol=%s bias=%s trend_pct=%s",
        symbol,
        htf_bias.get("bias"),
        _fmt_metric(htf_bias.get("trend_pct")),
    )

    signal = structure.get("signal")
    market = structure.get("market")

    if market == 1 and htf_bias.get("bias") != "LONG":
        structure["signal"] = None
        structure["reason"] = "HTF bias misaligned"
    elif market == -1 and htf_bias.get("bias") != "SHORT":
        structure["signal"] = None
        structure["reason"] = "HTF bias misaligned"

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
                "reason": regime_data.get("reason", "Regime blocked"),
                "signal": None,
                "regime": regime_data.get("regime"),
                "avg_range": regime_data.get("avg_range"),
                "atr_pct": regime_data.get("atr_pct"),
                "dir_strength": regime_data.get("dir_strength"),
                "trend_strength": regime_data.get("trend_strength"),
                "chop_score": regime_data.get("chop_score"),
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
                "avg_range": regime_data.get("avg_range"),
                "atr_pct": regime_data.get("atr_pct"),
                "dir_strength": regime_data.get("dir_strength"),
                "trend_strength": regime_data.get("trend_strength"),
                "chop_score": regime_data.get("chop_score"),
                "market": structure.get("market"),
                "ob": structure.get("ob"),
                "expansion": structure.get("expansion"),
                "htf_bias": structure.get("htf_bias"),
            }

        # --- NO ENTRY YET (WAITING FOR OB BREAK)
        return {
            "state": "TRENDING_NO_SIGNAL",
            "bias": 0,
            "confidence": 0.0,
            "reason": structure.get("reason", "Waiting for OB breakout"),
            "signal": None,
            "regime": regime_data.get("regime"),
            "avg_range": regime_data.get("avg_range"),
            "atr_pct": regime_data.get("atr_pct"),
            "dir_strength": regime_data.get("dir_strength"),
            "trend_strength": regime_data.get("trend_strength"),
            "chop_score": regime_data.get("chop_score"),
            "market": structure.get("market"),
            "ob": structure.get("ob"),
            "expansion": structure.get("expansion"),
            "htf_bias": structure.get("htf_bias"),
        }
