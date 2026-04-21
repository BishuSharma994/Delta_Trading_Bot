Version: V5.1 | Status: IMPLEMENTED | Last Updated: 2026-04-22

# V3 Associate Analyst Spec

## 1. Purpose

The Associate Analyst layer provides market context on top of the observer and strategy stack. In V5.1 this layer is implemented and active, not design-only.

It answers:

- What market regime is active right now?
- Is the current signal context stable or unstable?
- Should descriptive context block execution even if a directional idea exists?

## 2. Active Implementation

| Component | Status |
| --- | --- |
| `app/strategy/regime_engine.py` | Active |
| `app/strategy/regime_filter.py` | Active |

## 3. What V3 Adds

| Capability | Role |
| --- | --- |
| Market regime classification | Labels the current environment |
| Context filters | Supports blocking unstable conditions |
| Descriptive annotations | Adds context to signal evaluation |
| Conditional statistics | Summarizes behavior by context without triggering trades |

## 4. Regime Set

| Regime | Meaning |
| --- | --- |
| `VOLATILITY_COMPRESSION` | Tight range and low realized volatility |
| `VOLATILITY_EXPANSION` | Large expansion candles and unstable movement |
| `TREND_UP` | Higher highs and higher lows |
| `TREND_DOWN` | Lower highs and lower lows |
| `RANGE` | Mean-reverting price action |
| `TRANSITION` | Ambiguous or unstable context |

## 5. V5.1 Enforcement Update

V5.1 uses regime context as an execution blocker in two specific cases:

| Regime | V5.1 effect |
| --- | --- |
| `VOLATILITY_EXPANSION` | Blocks execution |
| `TRANSITION` | Blocks execution |

All other regimes remain descriptive context and still require the full entry gate to pass.

## 6. Non-Authority Rule

The Associate Analyst layer does not:

- Place trades
- Set size
- Override kill-switch logic
- Override the Senior Analyst confidence gate

It provides context and blocking logic only.

## 7. Version Reference

This specification is active under V5.1.
