# Delta Trading Bot — Analyst-First Market Intelligence System

---

## Overview

This repository contains an institutional-grade **crypto derivatives market intelligence system** designed to study markets conservatively before any execution logic is introduced.

The system behaves like a **research desk**, not a trader.

---

## Design Philosophy

- Intelligence matures before authority  
- Abstention is preferred over false certainty  
- Execution is permissioned, not inferred  
- Capital preservation is the primary objective  
- Every decision is auditable  

---

## High-Level Architecture

1. **Observer (Live System)**  
   - Collects live market data  
   - Writes append-only events  
   - Executes strategies in read-only mode  
   - Never places trades  

2. **Memory Layer**  
   - Event-sourced storage (JSONL)  
   - Immutable historical record  

3. **Feature Pipeline**  
   - Derives features from memory  
   - Deterministic  
   - No API calls  

4. **Strategies**  
   - Independent analytical viewpoints  
   - Conservative voting behavior  
   - Explicit abstention  

5. **Offline Analysis Tools**  
   - Vote behavior analysis  
   - Strategy confluence detection  
   - Temporal persistence measurement  

6. **Execution Gate (Future)**  
   - Permissioned system  
   - Manual arming only  
   - No automatic trading  

---

## Analyst Role Evolution

The system evolves through analyst roles:

- **Junior Analyst (V2.x)**  
  Observation, voting, abstention, logging  

- **Associate Analyst (V3.x)**  
  Regime awareness and interaction analysis  

- **Senior Analyst (V4.x)**  
  Hypothesis testing and research orchestration  

At no stage does the analyst directly trade.

---

## Security & Safety

- API keys stored via environment variables  
- Execution disabled by default  
- Kill switch implemented  
- No hard-coded secrets  
- Repository remains private until hardened  

---

## Current Status

- Live bot running safely  
- No execution enabled  
- Offline analysis complete  
- Ready for replay and senior-analyst research  

---

## Intended Use

This project is intended for:
- Research
- Learning institutional system design
- Building safe, auditable trading intelligence

It is not intended for:
- Retail automation
- Unsupervised capital deployment
- High-frequency trading

---

## Project Roadmap

- V2.3 — Junior analyst + offline intelligence (complete)
- V2.4 — Offline replay & gate stress-testing
- V3.x — Associate analyst capabilities
- V4.x — Senior analyst research desk

Execution will only be considered after extensive evidence.

---

## Current Path

**V2.3 — Junior Analyst + Offline Intelligence (Complete)**

Next phase:
**V2.4 — Offline Replay & Senior-Analyst Scaffolding**
