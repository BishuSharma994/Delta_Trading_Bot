# PROJECT_STATE.md
Delta Trading Bot — Institutional Phased System

Last Updated: 2026-02-05  
Version: V1.12 (Intelligence Scaffolding Phase)

---

## 1. PURPOSE (NON-NEGOTIABLE)

This project is an **institutional-grade autonomous trading system** designed to:

- Preserve capital first
- Trade only when statistical, structural, and temporal edges exist
- Learn from historical and live data
- Evolve strategies across versions without breaking prior logic
- Operate safely on low capital and scale responsibly

This is **not**:
- A retail bot
- A signal follower
- A high-frequency system
- A “funding-only” arbitrage script

---

## 2. CURRENT OPERATIONAL STATUS

### Trading State
- Environment: **Delta Exchange India (Live + Testnet validated)**
- Current mode: **READ / ANALYZE / LOG**
- Execution: **Enabled but gated**
- Kill Switch: **Implemented and verified**
- VPS: **DigitalOcean Ubuntu**
- Runtime: **screen-managed background process**

### What the bot DOES right now
- Connects to Delta API securely
- Fetches:
  - Wallet balances
  - Mark price
  - Funding rate (when available)
- Logs all observations
- Enforces kill switch
- Prevents overtrading
- Sleeps deterministically

### What the bot DOES NOT do yet
- No autonomous multi-symbol trading
- No indicator-based execution
- No machine learning
- No self-modifying logic
- No capital scaling

This is **intentional**.

---

## 3. ARCHITECTURE OVERVIEW

### High-level flow
