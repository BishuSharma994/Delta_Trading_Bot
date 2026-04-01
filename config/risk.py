from dataclasses import dataclass


@dataclass(frozen=True)
class RiskConfig:
    max_daily_trades_per_symbol: int = 3
    max_daily_loss_pct: float = 0.012
    max_consecutive_losses: int = 2

    max_stale_loop_gap_sec: int = 180
    warmup_loops_after_stale_gap: int = 3
    max_funding_trade_age_sec: int = 20 * 60
    max_vol_trade_age_sec: int = 20 * 60

    max_bid_ask_spread_pct: float = 0.0020

    min_funding_rate_abs: float = 0.0008
    funding_signal_window_sec: int = 3600
    funding_entry_window_sec: int = 120
    max_funding_pre_volatility_5m: float = 0.0020
    funding_stop_pct: float = 0.0030

    min_vol_confidence: float = 0.55
    max_vol_pre_volatility_5m: float = 0.0040
    funding_blackout_for_vol_sec: int = 180

    vol_take_profit_pct: float = 0.0060
    vol_hard_stop_pct: float = 0.0040
    vol_min_activation_pct: float = 0.0030
    vol_trailing_stop_pct: float = 0.0040
    vol_timeout_sec: int = 15 * 60

    win_cooldown_sec: int = 5 * 60
    losing_exit_cooldown_sec: int = 30 * 60
    stop_loss_cooldown_sec: int = 60 * 60


RISK = RiskConfig()
