from dataclasses import dataclass, replace


@dataclass(frozen=True)
class AssetRules:
    displacement_lookback: int = 6
    displacement_range_multiplier: float = 1.0
    min_body_ratio: float = 0.60
    structure_close_buffer_pct: float = 0.0
    liquidity_sweep_lookback: int = 4

    regime_lookback: int = 12
    min_atr_pct: float = 0.0010
    min_avg_range_pct: float = 0.0010
    min_directional_efficiency: float = 0.32
    min_trend_strength: float = 0.0010

    htf_group_size: int = 5
    htf_fast_blocks: int = 3
    htf_slow_blocks: int = 6
    min_htf_trend_pct: float = 0.0015

    post_entry_validation_candles: int = 3
    post_entry_min_progress_atr: float = 0.35
    momentum_failure_lookback: int = 2
    structure_buffer_pct: float = 0.0005
    volatility_collapse_ratio: float = 0.65

    max_prefunding_atr_pct: float = 0.0025
    max_prefunding_avg_range_pct: float = 0.0020


DEFAULT_ASSET_RULES = AssetRules()

# xStock trends are usually smoother and lower-vol than crypto, so they need
# slightly lower confirmation thresholds to avoid over-filtering valid setups.
XSTOCK_ASSET_RULES = replace(
    DEFAULT_ASSET_RULES,
    min_directional_efficiency=0.18,
    min_trend_strength=0.0005,
)

XSTOCK_SYMBOLS = {
    "SPYXUSD",
    "QQQXUSD",
    "NVDAXUSD",
    "TSLAXUSD",
    "AMZNXUSD",
    "AAPLXUSD",
    "METAXUSD",
    "GOOGLXUSD",
    "COINXUSD",
    "CRCLXUSD",
}


def get_asset_rules(symbol: str | None = None) -> AssetRules:
    if symbol and symbol.upper() in XSTOCK_SYMBOLS:
        return XSTOCK_ASSET_RULES
    return DEFAULT_ASSET_RULES
