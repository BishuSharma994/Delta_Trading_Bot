from config.asset_rules import AssetRules
from app.strategy.post_entry_validation import (
    initialize_post_entry_validation,
    evaluate_post_entry_validation,
)
from app.strategy.regime_filter import evaluate_regime_filter
from Delta_Trading_Bot.data.memory import get_recent_candles
from config.risk import RISK


def _coerce_float(value):
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _favorable_move(side: str, entry_price: float, reference_price: float) -> float:
    if entry_price <= 0:
        return 0.0

    if side == "LONG":
        return (reference_price - entry_price) / entry_price
    if side == "SHORT":
        return (entry_price - reference_price) / entry_price
    return 0.0


def _structure_invalidation(side: str, vol_vote: dict) -> float | None:
    if not isinstance(vol_vote, dict):
        return None

    ob = vol_vote.get("ob")
    if not isinstance(ob, dict):
        return None

    if side == "LONG":
        return _coerce_float(ob.get("low"))
    if side == "SHORT":
        return _coerce_float(ob.get("high"))
    return None


def build_vol_entry_context(
    side: str,
    vol_vote: dict,
    asset_rules: AssetRules,
) -> dict:
    atr_pct = _coerce_float(vol_vote.get("atr_pct")) or 0.0
    context = initialize_post_entry_validation(atr_pct, asset_rules)

    context.update({
        "structure_invalidation": _structure_invalidation(side, vol_vote),
        "entry_reason": vol_vote.get("reason"),
        "entry_htf_bias": vol_vote.get("htf_bias"),
        "entry_displacement_ratio": _coerce_float(
            (vol_vote.get("expansion") or {}).get("displacement_ratio")
        ) or 0.0,
    })

    return context


def build_legacy_vol_context(
    side: str,
    vol_vote: dict,
    asset_rules: AssetRules,
) -> dict:
    context = build_vol_entry_context(side, vol_vote, asset_rules)
    context["validation_remaining"] = 0
    context["validation_passed"] = True
    return context


def get_vol_trailing_stop(state) -> float | None:
    current_pnl_pct = _favorable_move(
        state.side,
        float(state.entry_price),
        float(state.peak_price if state.side == "LONG" else state.trough_price),
    )
    if current_pnl_pct < 0.0010:
        return None

    # trailing stop activates only after +0.10% profit (prevents premature stop-out)
    if state.side == "LONG":
        return float(state.peak_price) * (1 - RISK.vol_trailing_stop_pct)
    return float(state.trough_price) * (1 + RISK.vol_trailing_stop_pct)


def handle_vol_timeout(state, current_pnl_pct: float, log_func=print) -> bool:
    if current_pnl_pct > 0.0010:
        if not isinstance(state.vol_context, dict):
            state.vol_context = {}

        state.vol_context["timeout_trailing_mode"] = True
        state.vol_context["timeout_trailing_stop"] = (
            float(state.entry_price) * 1.0005
            if state.side == "LONG"
            else float(state.entry_price) * 0.9995
        )
        log_func("timeout suppressed — trade profitable, switching to trailing stop mode")
        # timeout suppressed for profitable trades — let winners run
        return False

    return True


def _structure_break(state, candles: list[dict], asset_rules: AssetRules) -> bool:
    context = state.vol_context if isinstance(state.vol_context, dict) else {}
    level = _coerce_float(context.get("structure_invalidation"))

    if level is None or not candles:
        return False

    close_price = float(candles[-1]["close"])

    if state.side == "LONG":
        return close_price <= level * (1 - asset_rules.structure_buffer_pct)

    return close_price >= level * (1 + asset_rules.structure_buffer_pct)


def _momentum_failure(state, price: float, candles: list[dict], asset_rules: AssetRules) -> bool:
    context = state.vol_context if isinstance(state.vol_context, dict) else {}
    if not context.get("validation_passed"):
        return False

    lookback = max(2, asset_rules.momentum_failure_lookback)
    if len(candles) < lookback:
        return False

    best_price = state.peak_price if state.side == "LONG" else state.trough_price
    if not isinstance(best_price, (int, float)):
        return False

    favorable_move = _favorable_move(state.side, state.entry_price, float(best_price))
    current_move = _favorable_move(state.side, state.entry_price, float(price))

    if favorable_move <= 0:
        return False

    retracement = favorable_move - current_move
    if retracement < max(favorable_move * 0.5, float(context.get("entry_atr_pct", 0.0)) * 0.25):
        return False

    recent = candles[-lookback:]

    if state.side == "LONG":
        return all(float(candle["close"]) <= float(candle["open"]) for candle in recent)

    return all(float(candle["close"]) >= float(candle["open"]) for candle in recent)


def _volatility_collapse(candles: list[dict], state, asset_rules: AssetRules) -> bool:
    context = state.vol_context if isinstance(state.vol_context, dict) else {}
    if not context.get("validation_passed"):
        return False

    regime_data = evaluate_regime_filter(candles, asset_rules)
    atr_pct = _coerce_float(regime_data.get("atr_pct")) or 0.0
    entry_atr_pct = _coerce_float(context.get("entry_atr_pct")) or 0.0
    collapse_threshold = max(
        asset_rules.min_atr_pct,
        entry_atr_pct * asset_rules.volatility_collapse_ratio,
    )

    return (
        regime_data.get("regime") == "NO_TRADE"
        and regime_data.get("reason") in {"low_atr", "low_avg_range", "choppy"}
        and atr_pct < collapse_threshold
    )


def evaluate_vol_exit(
    symbol: str,
    state,
    price: float,
    vol_vote: dict,
    asset_rules: AssetRules,
) -> tuple[str | None, dict]:
    context = state.vol_context if isinstance(state.vol_context, dict) else {}
    if not context:
        context = build_legacy_vol_context(state.side, vol_vote, asset_rules)

    state.vol_context = context

    best_price = state.peak_price if state.side == "LONG" else state.trough_price
    if isinstance(best_price, (int, float)):
        exit_reason, context = evaluate_post_entry_validation(
            side=state.side,
            entry_price=float(state.entry_price),
            best_price=float(best_price),
            context=context,
            asset_rules=asset_rules,
        )
        state.vol_context = context
        if exit_reason:
            return exit_reason, context

    candles = get_recent_candles(symbol, limit=max(asset_rules.regime_lookback + 2, 12))

    if _structure_break(state, candles, asset_rules):
        return "structure_break", context

    if _momentum_failure(state, price, candles, asset_rules):
        return "momentum_failure", context

    if _volatility_collapse(candles, state, asset_rules):
        return "volatility_collapse", context

    return None, context
