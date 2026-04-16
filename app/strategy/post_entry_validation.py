from config.asset_rules import AssetRules


def _favorable_move(side: str, entry_price: float, reference_price: float) -> float:
    if entry_price <= 0:
        return 0.0

    if side == "LONG":
        return (reference_price - entry_price) / entry_price
    if side == "SHORT":
        return (entry_price - reference_price) / entry_price
    return 0.0


def initialize_post_entry_validation(
    entry_atr_pct: float,
    asset_rules: AssetRules,
) -> dict:
    return {
        "validation_remaining": asset_rules.post_entry_validation_candles,
        "validation_passed": asset_rules.post_entry_validation_candles <= 0,
        "entry_atr_pct": max(0.0, float(entry_atr_pct)),
    }


def evaluate_post_entry_validation(
    side: str,
    entry_price: float,
    best_price: float,
    context: dict,
    asset_rules: AssetRules,
) -> tuple[str | None, dict]:
    if not isinstance(context, dict):
        context = {}

    if context.get("validation_passed"):
        return None, context

    remaining = int(context.get("validation_remaining", 0))
    if remaining <= 0:
        return "no_expansion", context

    threshold = float(context.get("entry_atr_pct", 0.0)) * asset_rules.post_entry_min_progress_atr

    if threshold <= 0:
        context["validation_passed"] = True
        context["validation_remaining"] = 0
        return None, context

    progress = _favorable_move(side, entry_price, best_price)
    if progress >= threshold:
        context["validation_passed"] = True
        context["validation_remaining"] = 0
        return None, context

    context["validation_remaining"] = remaining - 1
    if context["validation_remaining"] <= 0:
        return "no_expansion", context

    return None, context
