# Delta Trading Bot — Institutional Market Intelligence System

**Last Updated:** 2026-02-06  
**Current Version:** V2.4 (Offline Research Phase)  
**Operational Mode:** Live Data Collection + Offline Analysis  
**Execution Status:** Permanently Gated (Locked)

---

## 1. Purpose (Non-Negotiable)

This project is an institutional-grade **market intelligence and research system** for crypto derivatives markets.

The system is designed to:
- Preserve capital above all else
- Prefer abstention over false certainty
- Separate intelligence from authority
- Accumulate evidence before action
- Evolve safely and auditable across versions

This project is **not**:
- A retail trading bot  
- A signal-following system  
- An autonomous execution engine  
- A self-arming AI trader  

---

## 2. Current Operational State

### Live System
- Runs continuously on a VPS (DigitalOcean, Ubuntu)
- Connects securely to Delta Exchange (India)
- Collects live market data (price, funding, volatility context)
- Writes append-only JSONL event logs
- Derives features from historical memory
- Executes analytical strategies in **read-only mode**
- Records all strategy votes (including abstentions)
- Produces high-level decisions
- Never places trades

### Execution
- Disabled by design
- Gated behind explicit permission logic
- Requires manual arming (not implemented)
- No execution code is active

The system is safe to run unattended.

---

## 3. Analyst Role Model (Locked)

The system evolves **analyst seniority**, not trading authority.

### V2.x — Junior Analyst (Completed)

Responsibilities:
- Observe live market conditions
- Build raw and derived features
- Emit conservative strategy votes
- Abstain aggressively under uncertainty
- Persist all observations and decisions
- Enable offline analysis of behavior

Limitations:
- No hypothesis testing
- No regime labeling
- No replay orchestration
- No execution awareness
- No capital logic

---

### V3.x — Associate Analyst (Planned)

Responsibilities:
- Regime classification (trend, range, squeeze)
- Cross-feature interaction analysis
- Conditional statistics
- Pattern frequency and rarity analysis
- Multi-timeframe context building

Constraints:
- No execution
- No position sizing
- No leverage or capital allocation
- No self-arming behavior

---

### V4.x — Senior Analyst (Planned)

Responsibilities:
- Hypothesis generation and validation
- Scenario scoring and stress analysis
- False-positive suppression
- Strategy disagreement arbitration
- Confidence calibration over time
- Offline backtest orchestration
- Regime-specific research playbooks

Permanent constraints:
- No order placement
- No position management
- No leverage decisions
- No direct market interaction

---

## 4. Execution Authority (Permanent Rule)

Execution is handled by a **separate, permissioned layer** and is:

- Disabled by default
- Gated by explicit criteria
- Manually armed only
- Auditable
- Reversible

The analyst system can only output:
- Recommendations
- Evidence
- Confidence
- Risk flags

It can never output:
- Buy / Sell orders
- Position sizes
- Capital exposure decisions

This separation is permanent and non-negotiable.

---

## 5. Offline Intelligence (V2.3 — Completed)

The system includes a complete **junior-analyst offline intelligence pipeline**:

- Strategy vote distribution analysis
- Cross-strategy confluence detection
- Temporal persistence analysis

Observed behavior:
- High abstention rates
- No confluence events
- No persistent non-neutral signals

This confirms conservative, correct system behavior.

---

## 6. Current Phase — V2.4 (Offline Research Only)

### Definition

V2.4 is a **research-only phase** focused on **offline replay design, gate definition, and stress-testing**.

This phase:
- Does **not** introduce execution
- Does **not** modify live trading behavior
- Does **not** expand authority
- Does **not** permit coupling to capital

All work in V2.4 is:
- Read-only
- Offline
- Descriptive
- Analytical

---

### Objectives of V2.4

- Define execution gate criteria (configuration only)
- Replay historical data offline
- Measure how often execution *would* be permitted
- Stress-test false positives
- Validate governance logic
- Prepare senior-analyst research scaffolding

---

## 7. Current System Status Summary

- Live ingestion: Stable  
- Strategy execution: Stable  
- Offline analysis: Working  
- Signal scarcity: Confirmed  
- Execution authority: Locked  

The system is behaving exactly as intended.

---

## 8. Next Planned Phase

**V2.4 continuation:** Offline replay & gate stress-testing  
**Future:** V3.x — Associate Analyst capabilities  

Execution will only be considered after:
- Sufficient real evidence
- Stable analyst behavior
- Successful offline replay validation
- Explicit manual authorization

---

## 9. Current Path (Authoritative)

**You are here:**  
**V2.4 — Offline Research & Gate Design (No Execution)**

This status should be used as the reference point for all future discussions.
