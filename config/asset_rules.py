from dataclasses import dataclass, fields, replace


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

# Symbol overrides are intentionally explicit and opt-in.
# Extend this mapping when a symbol needs a non-default rule set.
ASSET_RULE_OVERRIDES: dict[str, dict] = {}


def get_asset_rules(symbol: str | None = None) -> AssetRules:
    if not symbol:
        return DEFAULT_ASSET_RULES

    overrides = ASSET_RULE_OVERRIDES.get(symbol.upper())
    if not overrides:
        return DEFAULT_ASSET_RULES

    valid_fields = {field.name for field in fields(AssetRules)}
    compatible_overrides = {
        key: value for key, value in overrides.items() if key in valid_fields
    }
    if not compatible_overrides:
        return DEFAULT_ASSET_RULES

    return replace(DEFAULT_ASSET_RULES, **compatible_overrides)


# ── xStock Asset Rules ────────────────────────────────────────────────────────
# Volatility tiers:
#   LOW  (ETFs):        SPY, QQQ         — tightest stops
#   MED  (Blue chips):  GOOGL, META, AAPL, AMZN, NVDA
#   HIGH (High beta):   TSLA, COIN, CRCL — widest stops

XSTOCK_ASSET_RULES = {
    "GOOGLXUSD": {
        "min_lot_usd":            5.0,
        "vol_hard_stop_pct":      0.008,
        "vol_take_profit_pct":    0.012,
        "vol_trailing_stop_pct":  0.003,
        "vol_min_activation_pct": 0.004,
        "max_bid_ask_spread_pct": 0.0015,
        "funding_stop_pct":       0.004,
        "min_funding_rate_abs":   0.0001,
        "max_pre_volatility_5m":  0.003,
    },
    "METAXUSD": {
        "min_lot_usd":            5.0,
        "vol_hard_stop_pct":      0.008,
        "vol_take_profit_pct":    0.012,
        "vol_trailing_stop_pct":  0.003,
        "vol_min_activation_pct": 0.004,
        "max_bid_ask_spread_pct": 0.0015,
        "funding_stop_pct":       0.004,
        "min_funding_rate_abs":   0.0001,
        "max_pre_volatility_5m":  0.003,
    },
    "AAPLXUSD": {
        "min_lot_usd":            5.0,
        "vol_hard_stop_pct":      0.006,
        "vol_take_profit_pct":    0.010,
        "vol_trailing_stop_pct":  0.002,
        "vol_min_activation_pct": 0.003,
        "max_bid_ask_spread_pct": 0.0015,
        "funding_stop_pct":       0.003,
        "min_funding_rate_abs":   0.0001,
        "max_pre_volatility_5m":  0.002,
    },
    "AMZNXUSD": {
        "min_lot_usd":            5.0,
        "vol_hard_stop_pct":      0.008,
        "vol_take_profit_pct":    0.012,
        "vol_trailing_stop_pct":  0.003,
        "vol_min_activation_pct": 0.004,
        "max_bid_ask_spread_pct": 0.0015,
        "funding_stop_pct":       0.004,
        "min_funding_rate_abs":   0.0001,
        "max_pre_volatility_5m":  0.003,
    },
    "TSLAXUSD": {
        "min_lot_usd":            5.0,
        "vol_hard_stop_pct":      0.012,
        "vol_take_profit_pct":    0.018,
        "vol_trailing_stop_pct":  0.004,
        "vol_min_activation_pct": 0.006,
        "max_bid_ask_spread_pct": 0.0020,
        "funding_stop_pct":       0.006,
        "min_funding_rate_abs":   0.0001,
        "max_pre_volatility_5m":  0.005,
    },
    "NVDAXUSD": {
        "min_lot_usd":            5.0,
        "vol_hard_stop_pct":      0.010,
        "vol_take_profit_pct":    0.015,
        "vol_trailing_stop_pct":  0.003,
        "vol_min_activation_pct": 0.005,
        "max_bid_ask_spread_pct": 0.0015,
        "funding_stop_pct":       0.005,
        "min_funding_rate_abs":   0.0001,
        "max_pre_volatility_5m":  0.004,
    },
    "COINXUSD": {
        "min_lot_usd":            5.0,
        "vol_hard_stop_pct":      0.015,
        "vol_take_profit_pct":    0.022,
        "vol_trailing_stop_pct":  0.005,
        "vol_min_activation_pct": 0.007,
        "max_bid_ask_spread_pct": 0.0025,
        "funding_stop_pct":       0.007,
        "min_funding_rate_abs":   0.0001,
        "max_pre_volatility_5m":  0.006,
    },
    "CRCLXUSD": {
        "min_lot_usd":            5.0,
        "vol_hard_stop_pct":      0.015,
        "vol_take_profit_pct":    0.022,
        "vol_trailing_stop_pct":  0.005,
        "vol_min_activation_pct": 0.007,
        "max_bid_ask_spread_pct": 0.0025,
        "funding_stop_pct":       0.007,
        "min_funding_rate_abs":   0.0001,
        "max_pre_volatility_5m":  0.006,
    },
    "QQQXUSD": {
        "min_lot_usd":            5.0,
        "vol_hard_stop_pct":      0.007,
        "vol_take_profit_pct":    0.010,
        "vol_trailing_stop_pct":  0.002,
        "vol_min_activation_pct": 0.003,
        "max_bid_ask_spread_pct": 0.0012,
        "funding_stop_pct":       0.003,
        "min_funding_rate_abs":   0.0001,
        "max_pre_volatility_5m":  0.002,
    },
    "SPYXUSD": {
        "min_lot_usd":            5.0,
        "vol_hard_stop_pct":      0.006,
        "vol_take_profit_pct":    0.009,
        "vol_trailing_stop_pct":  0.002,
        "vol_min_activation_pct": 0.003,
        "max_bid_ask_spread_pct": 0.0012,
        "funding_stop_pct":       0.003,
        "min_funding_rate_abs":   0.0001,
        "max_pre_volatility_5m":  0.002,
    },
}

# Merge xStock rules into main ASSET_RULES
# If ASSET_RULES exists above: ASSET_RULES.update(XSTOCK_ASSET_RULES)
# If not: create ASSET_RULES = {**existing_dict, **XSTOCK_ASSET_RULES}
ASSET_RULES = dict(globals().get("ASSET_RULES", {}))
ASSET_RULES.update(XSTOCK_ASSET_RULES)

XSTOCK_ASSET_RULES = {
    "GOOGLXUSD": {"leverage": 25, "sl_pct": 0.008, "tp_pct": 0.016, "max_pos_usd": 500},
    "METAXUSD":  {"leverage": 25, "sl_pct": 0.008, "tp_pct": 0.016, "max_pos_usd": 500},
    "AAPLXUSD":  {"leverage": 25, "sl_pct": 0.008, "tp_pct": 0.016, "max_pos_usd": 500},
    "AMZNXUSD":  {"leverage": 25, "sl_pct": 0.008, "tp_pct": 0.016, "max_pos_usd": 500},
    "TSLAXUSD":  {"leverage": 25, "sl_pct": 0.010, "tp_pct": 0.020, "max_pos_usd": 300},
    "NVDAXUSD":  {"leverage": 25, "sl_pct": 0.010, "tp_pct": 0.020, "max_pos_usd": 300},
    "COINXUSD":  {"leverage": 25, "sl_pct": 0.010, "tp_pct": 0.020, "max_pos_usd": 300},
    "CRCLXUSD":  {"leverage": 25, "sl_pct": 0.010, "tp_pct": 0.020, "max_pos_usd": 300},
    "QQQXUSD":   {"leverage": 25, "sl_pct": 0.006, "tp_pct": 0.012, "max_pos_usd": 700},
    "SPYXUSD":   {"leverage": 25, "sl_pct": 0.006, "tp_pct": 0.012, "max_pos_usd": 700},
}

ASSET_RULE_OVERRIDES.update(XSTOCK_ASSET_RULES)
