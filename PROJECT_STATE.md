---

## CURRENT STATE SNAPSHOT — V2.2 (As of 2026-02-06)

### System Status
- **Bot Status**: RUNNING (observer.py active on VPS)
- **Execution**: HARD-GATED (no orders possible)
- **Mode**: Live data collection + intelligence voting
- **Stability**: Stable, no import errors, no crashes

Confirmed by:
- `ps aux | grep observer.py` → python3 observer.py running
- Continuous event generation in `data/events/`

---

## ARCHITECTURE CONFIRMED (LOCKED)

### Layers
1. **Observer (observer.py)**
   - Fetches live market data (price, funding)
   - Writes event-sourced logs (JSONL)
   - Invokes feature pipeline
   - Collects strategy votes
   - Calls evaluator
   - NEVER executes trades

2. **Memory Layer (data/memory.py)**
   - Read-only access to historical events
   - Stable helper contracts:
     - read_events
     - get_latest_funding
     - get_recent_prices
     - get_latest_book
     - get_latest_strategy_vote
     - get_recent_feature_values

3. **Feature Pipeline (core/feature_pipeline.py)**
   - Builds features from memory only
   - No API calls
   - No side effects
   - Current key features:
     - funding_rate_abs
     - time_to_funding_sec
     - pre_volatility_5m
     - bid_ask_spread_pct

4. **Strategies (Vote-Only Analysts)**
   - funding_bias (V2.1)
     - Emits votes based on funding context
     - Currently abstaining due to incomplete funding timing data
   - volatility_regime (V2.2)
     - Always emits explicit votes
     - States: NO_DATA, INSUFFICIENT_HISTORY, COMPRESSED, NEUTRAL, EXPANSION_DETECTED
     - No execution authority

5. **Evaluator (core/evaluator.py)**
   - Aggregates feature readiness + strategy votes
   - Emits states:
     - INSUFFICIENT_DATA (current dominant state)
     - EDGE_DETECTED (possible future)
   - Execution remains disabled regardless of state

---

## CURRENT LIVE OBSERVATIONS (EXPECTED)

### Decision Events
- Dominant state: `INSUFFICIENT_DATA`
- Missing features frequently:
  - pre_volatility_5m
  - time_to_funding_sec
- Feature states often logged as:
  - funding_rate_abs: hot
  - time_to_funding_sec: cold
  - pre_volatility_5m: cold

This is **correct behavior**.
No trade is justified without confluence.

---

## WHAT IS WORKING (VERIFIED)

- Event sourcing is functioning
- Strategies are voting and logging explicitly
- Evaluator is running deterministically
- No silent failures
- No accidental execution paths
- System behaves like an institutional research stack

---

## WHAT IS INTENTIONALLY NOT DONE YET

- No execution logic
- No backtest-driven parameter tuning
- No ML / model fitting
- No indicator stacking
- No capital scaling
- No multi-symbol expansion

All of the above are deferred by design.

---

## NEXT PHASE — V2.3 (OFFLINE INTELLIGENCE)

### Objective
Analyze collected data offline to answer:
- How often do strategies emit actionable states?
- Do funding bias and volatility expansion ever align?
- What is the frequency and duration of EDGE_DETECTED?
- Are false positives common?

### Planned Action (DO NOT STOP BOT)
- Create offline analysis tool:
  - Location: tools/analyze_votes.py
  - Reads historical JSONL events
  - Computes distributions and overlaps
- Use results to decide:
  - Whether execution should ever be unlocked
  - What additional features are required (price structure, volume, etc.)

---

## STRICT RULES FOR FUTURE DEVELOPMENT

- Live bot = data collection only
- All intelligence validation happens offline first
- No execution without statistical evidence
- No architectural resets between versions
- Memory layer is the single source of truth

---

## SAFE RE-ENTRY INSTRUCTIONS (NEW CHAT)

If resuming in a new chat:
- State that system is at **V2.2**
- Observer is running live
- Execution is gated
- Goal is **offline analysis tooling (V2.3)**
- No need to re-debug or re-architect

---
