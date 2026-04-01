import argparse
import json
import math
import sys
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from statistics import stdev

ROOT = Path(__file__).resolve().parents[2]
PARENT = ROOT.parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

from app.strategy import msb_ob_engine
from core.state_engine import StateEngine
from strategies.funding_bias import FundingBiasStrategy
from strategies.volatility_regime import evaluate_volatility
from trade_stats import pair_trades, render_report

PRICE_PATH = ROOT / "data" / "events" / "price_snapshot.jsonl"
FUNDING_PATH = ROOT / "data" / "events" / "funding_snapshot.jsonl"


def _parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _load_jsonl(path: Path) -> list[dict]:
    events = []

    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    return events


def _filter_range(events: list[dict], start: datetime | None, end: datetime | None) -> list[dict]:
    filtered = []

    for event in events:
        ts_raw = event.get("timestamp_utc")
        if not ts_raw:
            continue

        ts = _parse_ts(ts_raw)
        if start and ts < start:
            continue
        if end and ts > end:
            continue
        filtered.append(event)

    return filtered


def _log_returns(prices: list[float]) -> list[float] | None:
    returns = []

    for prev_price, price in zip(prices, prices[1:]):
        if prev_price <= 0 or price <= 0:
            return None
        returns.append(math.log(price / prev_price))

    return returns


def _build_features(latest_funding: dict | None, recent_snapshots: deque, current_snapshot: dict) -> dict:
    features = {}

    if latest_funding:
        funding_rate = latest_funding.get("funding_rate")
        if isinstance(funding_rate, (int, float)):
            features["funding_rate"] = float(funding_rate)
            features["funding_rate_abs"] = abs(float(funding_rate))

        ttf = latest_funding.get("time_to_funding_sec")
        if isinstance(ttf, (int, float)) and ttf >= 0:
            features["time_to_funding_sec"] = float(ttf)

    prices = [
        float(snapshot["mark_price"])
        for snapshot in list(recent_snapshots)[-5:]
        if isinstance(snapshot.get("mark_price"), (int, float))
    ]

    if len(prices) >= 2:
        returns = _log_returns(prices)
        if returns and len(returns) >= 2:
            features["pre_volatility_5m"] = float(stdev(returns))

    best_bid = current_snapshot.get("best_bid")
    best_ask = current_snapshot.get("best_ask")
    if (
        isinstance(best_bid, (int, float))
        and isinstance(best_ask, (int, float))
        and best_ask > best_bid > 0
    ):
        mid = (best_bid + best_ask) / 2
        features["bid_ask_spread_pct"] = float((best_ask - best_bid) / mid)

    return features


def _build_candles(recent_snapshots: deque) -> list[dict]:
    candles = []
    prev_close = None

    for snapshot in recent_snapshots:
        close_price = snapshot.get("mark_price")
        if not isinstance(close_price, (int, float)):
            continue

        close_price = float(close_price)
        open_price = float(prev_close if prev_close is not None else close_price)
        bounds = [open_price, close_price]

        for value in (
            snapshot.get("best_bid"),
            snapshot.get("best_ask"),
            snapshot.get("index_price"),
        ):
            if isinstance(value, (int, float)):
                bounds.append(float(value))

        candles.append(
            {
                "timestamp_utc": snapshot.get("timestamp_utc"),
                "open": open_price,
                "high": max(bounds),
                "low": min(bounds),
                "close": close_price,
            }
        )
        prev_close = close_price

    return candles


def _build_vol_vote(symbol: str, recent_snapshots: deque) -> dict:
    candles = _build_candles(recent_snapshots)

    if len(candles) < 20:
        return {
            "state": "NO_DATA",
            "bias": 0,
            "confidence": 0.0,
            "reason": "Insufficient candles",
            "signal": None,
        }

    regime_data, structure = evaluate_volatility(symbol, candles)

    if regime_data["regime"] != "TRENDING":
        return {
            "state": "NO_TRADE",
            "bias": 0,
            "confidence": 0.0,
            "reason": "Regime blocked",
            "signal": None,
            "regime": regime_data.get("regime"),
        }

    signal = structure.get("signal")
    confidence = min(
        1.0,
        max(
            float(regime_data.get("dir_strength", 0.0)),
            float(regime_data.get("trend_strength", 0.0)) * 100,
        ),
    )

    if signal in {"LONG", "SHORT"}:
        return {
            "state": "STRUCTURE_CONFIRMED",
            "bias": 1 if signal == "LONG" else -1,
            "confidence": confidence,
            "reason": structure.get("reason"),
            "signal": signal,
            "sl": structure.get("sl"),
            "regime": regime_data.get("regime"),
            "market": structure.get("market"),
            "ob": structure.get("ob"),
        }

    return {
        "state": "TRENDING_NO_SIGNAL",
        "bias": 0,
        "confidence": 0.0,
        "reason": "Waiting for OB breakout",
        "signal": None,
        "regime": regime_data.get("regime"),
        "market": structure.get("market"),
        "ob": structure.get("ob"),
    }


class ReplayStateEngine(StateEngine):
    def __init__(self):
        self.symbols = {}
        self.logged_events = []
        self._active_now = None

    def _load(self):
        return

    def _save(self):
        return

    def _log(self, symbol, action, trade_type, side, price, reason):
        timestamp_utc = (
            self._active_now.isoformat()
            if isinstance(self._active_now, datetime)
            else datetime.now(timezone.utc).isoformat()
        )
        self.logged_events.append(
            {
                "symbol": symbol,
                "action": action,
                "trade_type": trade_type,
                "side": side,
                "price": float(price),
                "reason": reason,
                "timestamp_utc": timestamp_utc,
            }
        )

    def process(self, symbol, decision, features, price, funding_vote, vol_vote, now=None):
        self._active_now = now
        return super().process(symbol, decision, features, price, funding_vote, vol_vote, now=now)


def run_replay(start: datetime | None = None, end: datetime | None = None) -> dict:
    funding_events = _filter_range(_load_jsonl(FUNDING_PATH), start, end)
    price_events = _filter_range(_load_jsonl(PRICE_PATH), start, end)

    merged_events = []
    for event in funding_events:
        merged_events.append((_parse_ts(event["timestamp_utc"]), 0, "funding", event))
    for event in price_events:
        merged_events.append((_parse_ts(event["timestamp_utc"]), 1, "price", event))
    merged_events.sort(key=lambda item: (item[0], item[1], item[3].get("symbol", "")))

    msb_ob_engine._SYMBOL_STATE.clear()

    funding_strategy = FundingBiasStrategy()
    engine = ReplayStateEngine()
    recent_snapshots: dict[str, deque] = defaultdict(lambda: deque(maxlen=40))
    latest_funding: dict[str, dict] = {}

    for ts, _, event_type, event in merged_events:
        symbol = event.get("symbol")
        if not symbol:
            continue

        if event_type == "funding":
            latest_funding[symbol] = event
            continue

        recent_snapshots[symbol].append(event)
        features = _build_features(latest_funding.get(symbol), recent_snapshots[symbol], event)
        funding_vote = funding_strategy.vote(features)
        vol_vote = _build_vol_vote(symbol, recent_snapshots[symbol])

        mark_price = event.get("mark_price")
        if not isinstance(mark_price, (int, float)):
            continue

        engine.process(
            symbol=symbol,
            decision={},
            features=features,
            price=float(mark_price),
            funding_vote=funding_vote,
            vol_vote=vol_vote,
            now=ts,
        )

    closed_trades, open_trades, skipped_rows = pair_trades(engine.logged_events)
    report = render_report(Path("<replay>"), closed_trades, open_trades, skipped_rows)

    return {
        "events_processed": len(merged_events),
        "trade_events": engine.logged_events,
        "report": report,
        "closed_trades": closed_trades,
        "open_trades": open_trades,
        "skipped_rows": skipped_rows,
    }


def main():
    parser = argparse.ArgumentParser(description="Offline replay for the current paper-trading runtime.")
    parser.add_argument("--start", help="Inclusive ISO timestamp, e.g. 2026-03-22T00:00:00+00:00")
    parser.add_argument("--end", help="Inclusive ISO timestamp, e.g. 2026-04-01T00:01:30+00:00")
    parser.add_argument("--report-out", help="Optional path to write the text report")
    parser.add_argument("--trade-log-out", help="Optional path to write replay trade JSONL")
    args = parser.parse_args()

    start = _parse_ts(args.start) if args.start else None
    end = _parse_ts(args.end) if args.end else None

    results = run_replay(start=start, end=end)
    print(results["report"])

    if args.report_out:
        report_path = Path(args.report_out)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(results["report"] + "\n", encoding="utf-8")

    if args.trade_log_out:
        trade_path = Path(args.trade_log_out)
        trade_path.parent.mkdir(parents=True, exist_ok=True)
        with trade_path.open("w", encoding="utf-8") as handle:
            for event in results["trade_events"]:
                handle.write(json.dumps(event, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
