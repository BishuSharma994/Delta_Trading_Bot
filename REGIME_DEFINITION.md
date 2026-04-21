Version: V5.1 | Status: IMPLEMENTED REGIME TAXONOMY | Last Updated: 2026-04-22

# Regime Definition

Market regimes provide descriptive context for the observer and analyst layers. They are not direct trade triggers. A regime can allow trading context, block trading context, or simply describe the environment around a separate signal.

## Regime Table

| Regime | Characteristics | Bot Behavior |
| --- | --- | --- |
| `VOLATILITY_COMPRESSION` | Tight range, low realized volatility, signal scarcity | Allowed context |
| `VOLATILITY_EXPANSION` | Large candles, range expansion, unstable follow-through | Always abstain |
| `TREND_UP` | Higher highs, higher lows, directional consistency | Allowed context |
| `TREND_DOWN` | Lower highs, lower lows, directional consistency | Allowed context |
| `RANGE` | Mean reversion, low directional persistence, rotational price action | Allowed context |
| `TRANSITION` | Ambiguous structure, regime disagreement, feature instability | Always abstain |

## Regime Notes

### VOLATILITY_COMPRESSION

- Often precedes breakout attempts.
- Compatible with V5.1 directional setups.
- Does not create an entry by itself.

### VOLATILITY_EXPANSION

- Represents unstable expansion conditions.
- V5.1 governance treats this regime as non-tradable.
- Any setup in this regime must resolve to `ABSTAIN`.

### TREND_UP

- Directional bias is persistent.
- Long continuation contexts can remain valid if other gates pass.
- Still requires vote agreement and confidence.

### TREND_DOWN

- Directional bias is persistent to the downside.
- Short continuation contexts can remain valid if other gates pass.
- Still requires vote agreement and confidence.

### RANGE

- Price is mean-reverting and direction is less persistent.
- Signals can still be observed but need clean alignment and risk filters.
- Range alone does not imply no-trade.

### TRANSITION

- Mixed evidence and unstable context.
- Treated as non-tradable in V5.1.
- Any setup in this regime must resolve to `ABSTAIN`.

## Governance Constraint

Regimes are descriptive context only. They do not directly trigger entries, size positions, or override risk rules.
