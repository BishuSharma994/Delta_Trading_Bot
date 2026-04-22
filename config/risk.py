from dataclasses import dataclass


@dataclass(frozen=True)
class RiskConfig:
    max_daily_trades_per_symbol: int = 2
    max_daily_loss_pct: float = 0.010
    max_consecutive_losses: int = 2
    portfolio_max_daily_drawdown_pct: float = 0.030
    max_concurrent_positions_per_symbol: int = 1

    max_stale_loop_gap_sec: int = 180
    warmup_loops_after_stale_gap: int = 3
    max_funding_trade_age_sec: int = 20 * 60
    max_vol_trade_age_sec: int = 45 * 60

    max_bid_ask_spread_pct: float = 0.0008

    min_funding_rate_abs: float = 0.0008
    max_funding_rate_abs: float = 0.0030
    funding_signal_window_sec: int = 3600
    funding_entry_window_sec: int = 900
    max_funding_pre_volatility_5m: float = 0.0020
    funding_stop_pct: float = 0.0030

    min_vol_confidence: float = 0.65
    max_vol_pre_volatility_5m: float = 0.0040
    funding_blackout_for_vol_sec: int = 1800
    base_position_notional_usd: float = 100.0
    min_position_notional_usd: float = 35.0
    max_position_notional_usd: float = 250.0
    min_position_confidence: float = 0.50
    max_position_confidence: float = 1.00
    position_confidence_floor_scale: float = 0.60
    position_volatility_target_pct: float = 0.0020
    position_volatility_floor_scale: float = 0.50
    position_volatility_ceiling_scale: float = 1.50

    vol_take_profit_pct: float = 0.0060
    vol_hard_stop_pct: float = 0.0040
    vol_min_activation_pct: float = 0.0030
    vol_trailing_stop_pct: float = 0.0025
    vol_trailing_activation_profit_pct: float = 0.0010
    vol_timeout_trailing_buffer_pct: float = 0.0005
    vol_timeout_sec: int = 45 * 60

    win_cooldown_sec: int = 5 * 60
    losing_exit_cooldown_sec: int = 30 * 60
    stop_loss_cooldown_sec: int = 60 * 60


RISK = RiskConfig()
