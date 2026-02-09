# GOVERNANCE — DELTA TRADING BOT (AUTHORITATIVE)

This document is the single source of truth for this repository.

---

## CORE PRINCIPLES

1. Capital preservation overrides all objectives
2. Abstention is a valid and preferred outcome
3. Evidence must precede any action
4. Research and execution are permanently separated
5. Everything must be auditable and reproducible

---

## HARD INVARIANTS

- No live execution code exists
- No live execution code may be added
- No capital deployment is possible
- No optimization for profit is allowed
- No online or adaptive learning is permitted

Violation of any invariant invalidates the system.

---

## AUTHORITY MODEL

This system is a **research and governance apparatus**, not a trader.

It may:
- Observe markets
- Generate features
- Test hypotheses offline
- Stress and falsify ideas
- Evaluate *whether execution would be permitted* under strict rules (dry-run only)

It may never:
- Place trades
- Suggest trades
- Size positions
- Manage capital
- Arm itself autonomously
- Interact with execution endpoints

---

## VERSION & SCOPE LOCK

### V4 — RESEARCH LAYER
- Status: **COMPLETE and CLOSED**
- Mutability: **NONE**
- Outputs: Locked, offline, non-executable artifacts

### V5 — GOVERNED EXECUTION DECISION FRAMEWORK
- Scope: **DRY-RUN ONLY**
- Purpose:
  - Consume locked V4 artifacts
  - Enforce evidence contracts
  - Enforce governance, authorization, and kill-switches
  - Emit audit-only order intents
- Capabilities:
  - **Decision evaluation only**
  - **No execution**
  - **No capital exposure**

V5 does **not** violate V4 invariants because:
- It cannot trade
- It cannot deploy capital
- It cannot self-arm
- It produces no live market actions

---

## EXECUTION SEPARATION (NON-NEGOTIABLE)

This repository **does not and will not** contain live execution logic.

Any live execution system must:
- Live in a separate repository
- Use separate API credentials
- Have independent governance
- Require explicit human authorization
- Be fully kill-switch protected

---

## DEFAULT STATE

**DISARMED  
ABSTAINING  
SAFE**

---

END OF GOVERNANCE
