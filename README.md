# Delta Trading Bot - v5.1

Algorithmic trading bot for Delta Exchange India.
Trades crypto perpetuals and xStock token perpetuals.

## Architecture

Local Machine                        VPS (DigitalOcean)
-----------------------------        ------------------
brain/runner.py (weekly)             core/main.py (24/7)
brain/data/ <- local only            config/ <- via git
config/risk.py <- after approval     live trades on Delta Exchange

## Symbols

### Crypto Perpetuals
| Symbol | ID    |
|--------|-------|
| BTCUSD | 27    |
| ETHUSD | 3136  |
| SOLUSD | 14823 |
| BNBUSD | 15042 |

### xStock Perpetuals (24/7 on Delta Exchange)
| Symbol     | Stock      | ID     |
|------------|------------|--------|
| GOOGLXUSD  | Alphabet   | 119235 |
| METAXUSD   | Meta       | 119236 |
| AAPLXUSD   | Apple      | 119238 |
| AMZNXUSD   | Amazon     | 119239 |
| TSLAXUSD   | Tesla      | 119240 |
| NVDAXUSD   | Nvidia     | 119241 |
| COINXUSD   | Coinbase   | 125551 |
| CRCLXUSD   | Circle     | 125552 |
| QQQXUSD    | Nasdaq ETF | 129940 |
| SPYXUSD    | S&P500 ETF | 129941 |

## Setup
pip install -r requirements.txt
cp .env.example .env  # fill in your keys

## Run Brain (Local - Weekly)
python -m brain.runner --refresh
python -m brain.config_writer
python -m brain.config_writer --approve
git add config/risk.py
git commit -m "brain: weekly update"
git push origin main

## View Performance (Local)
python trade_stats.py                      # full report to stdout
python trade_stats.py --equity --save      # update equity log + save report
python trade_stats.py --weekly             # this week's summary
python trade_stats.py --symbol BTCUSD      # one symbol
python trade_stats.py --since 7            # last 7 days

# Register scheduled tasks (Windows or Linux):
python scripts/schedule_setup.py

## Deploy to VPS
git add .
git commit -m "message"
git push origin main
# On VPS:
git pull origin main
systemctl restart trading-bot

## Phase Status
- [x] Phase 1 - Crypto perpetuals live
- [x] Phase 1.1 - xStock symbols added
- [ ] Phase 2 - Brain pattern-driven risk management
- [x] Phase 5 - Performance Dashboard
