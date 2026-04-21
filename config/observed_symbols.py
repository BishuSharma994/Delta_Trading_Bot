"""
Observed Symbols Configuration
READ-ONLY | DATA COLLECTION ONLY
"""

OBSERVED_SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "SOLUSDT",
]

CRYPTO_SYMBOLS = [
    "BTCUSD",
    "ETHUSD",
    "SOLUSD",
    "BNBUSD",
]

# ── xStock Perpetuals ─────────────────────────────────────────────────────────
# Added: 2026-04-22
# Min trade size: ~5–10 USD | Leverage: 25x | Funding: 0.0100%
# These are synthetic stock tokens — trade 24/7 like crypto perpetuals
# Market hours note: price follows US equity hours for volatility
# Outside US hours (9:30 AM – 4:00 PM EST): lower volume, wider spreads
# Bot will apply spread filter — most trades will fire during US hours only

XSTOCK_SYMBOLS = [
    "GOOGLXUSD",  # Alphabet
    "METAXUSD",   # Meta
    "AAPLXUSD",   # Apple
    "AMZNXUSD",   # Amazon
    "TSLAXUSD",   # Tesla  — high beta, volatile like crypto
    "NVDAXUSD",   # Nvidia
    "COINXUSD",   # Coinbase — very high beta
    "CRCLXUSD",   # Circle  — very high beta
    "QQQXUSD",    # Nasdaq ETF — low volatility
    "SPYXUSD",    # S&P500 ETF — lowest volatility
]

ALL_SYMBOLS = CRYPTO_SYMBOLS + XSTOCK_SYMBOLS
