import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

DEFAULT_FILE = Path("data/events/paper_trades.jsonl")


@dataclass(frozen=True)
class ClosedTrade:
    symbol: str
    trade_type: str
    side: str
    entry_reason: str
    exit_reason: str
    entry_price: float
    exit_price: float
    entry_ts: str
    exit_ts: str
    return_pct: float
    duration_min: float


def load_trade_events(path: Path) -> list[dict]:
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


def _trade_return(side: str, entry_price: float, exit_price: float) -> float:
    if side == "LONG":
        return (exit_price - entry_price) / entry_price
    if side == "SHORT":
        return (entry_price - exit_price) / entry_price
    raise ValueError(f"Unsupported side: {side}")


def pair_trades(events: list[dict]) -> tuple[list[ClosedTrade], dict, int, Counter]:
    open_trades = {}
    closed_trades = []
    skipped_rows = 0
    reject_counts = Counter()  # ← NEW

    for event in events:
        action = event.get("action")
        symbol = event.get("symbol")
        trade_type = event.get("trade_type")
        key = (symbol, trade_type)

        if action == "REJECT":
            reject_counts[event.get("reason", "unknown")] += 1  # ← NEW
            continue

        if action == "ENTRY":
            side = event.get("side")
            if side not in {"LONG", "SHORT"}:
                skipped_rows += 1
                continue
            open_trades[key] = event
            continue

        if action != "EXIT":
            skipped_rows += 1
            continue

        entry = open_trades.pop(key, None)
        if not entry:
            skipped_rows += 1
            continue

        side = entry.get("side")
        try:
            entry_price = float(entry["price"])
            exit_price = float(event["price"])
            entry_ts = datetime.fromisoformat(entry["timestamp_utc"])
            exit_ts = datetime.fromisoformat(event["timestamp_utc"])
            trade_return = _trade_return(side, entry_price, exit_price)
        except (KeyError, TypeError, ValueError):
            skipped_rows += 1
            continue

        closed_trades.append(
            ClosedTrade(
                symbol=symbol,
                trade_type=trade_type,
                side=side,
                entry_reason=entry.get("reason", "unknown"),
                exit_reason=event.get("reason", "unknown"),
                entry_price=entry_price,
                exit_price=exit_price,
                entry_ts=entry["timestamp_utc"],
                exit_ts=event["timestamp_utc"],
                return_pct=trade_return,
                duration_min=(exit_ts - entry_ts).total_seconds() / 60,
            )
        )

    return closed_trades, open_trades, skipped_rows, reject_counts


def _bucket_stats(trades: list[ClosedTrade]) -> dict:
    if not trades:
        return {
            "count": 0,
            "win_rate": 0.0,
            "avg_bps": 0.0,
            "total_return_pct": 0.0,
            "median_duration_min": 0.0,
        }

    total_return = 1.0
    for trade in trades:
        total_return *= 1 + trade.return_pct

    durations = sorted(trade.duration_min for trade in trades)
    median_duration = durations[len(durations) // 2]

    return {
        "count": len(trades),
        "win_rate": sum(1 for trade in trades if trade.return_pct > 0) / len(trades),
        "avg_bps": sum(trade.return_pct for trade in trades) / len(trades) * 10000,
        "total_return_pct": (total_return - 1) * 100,
        "median_duration_min": median_duration,
    }


def summarize_trades(trades: list[ClosedTrade]) -> dict:
    equity = 1.0
    peak = 1.0
    max_drawdown = 0.0

    for trade in trades:
        equity *= 1 + trade.return_pct
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, (peak - equity) / peak)

    grouped = {}
    for label, key_fn in {
        "trade_type": lambda trade: trade.trade_type,
        "symbol": lambda trade: trade.symbol,
        "side": lambda trade: trade.side,
        "entry_reason": lambda trade: trade.entry_reason,
        "exit_reason": lambda trade: trade.exit_reason,
    }.items():
        buckets = defaultdict(list)
        for trade in trades:
            buckets[key_fn(trade)].append(trade)
        grouped[label] = {
            bucket: _bucket_stats(bucket_trades)
            for bucket, bucket_trades in sorted(buckets.items(), key=lambda item: str(item[0]))
        }

    return {
        "overall": _bucket_stats(trades),
        "max_drawdown_pct": max_drawdown * 100,
        "grouped": grouped,
        "exit_reason_counts": Counter(trade.exit_reason for trade in trades),
        "worst_trades": sorted(trades, key=lambda trade: trade.return_pct)[:10],
        "best_trades": sorted(trades, key=lambda trade: trade.return_pct, reverse=True)[:10],
    }


def _render_bucket(title: str, stats: dict) -> list[str]:
    lines = [f"\n## {title}"]
    for bucket, values in stats.items():
        lines.append(
            (
                f"{bucket}: n={values['count']} "
                f"win={values['win_rate']:.3f} "
                f"avg_bps={values['avg_bps']:.1f} "
                f"total_pct={values['total_return_pct']:.2f} "
                f"median_dur_min={values['median_duration_min']:.1f}"
            )
        )
    return lines


def render_report(path: Path, trades: list[ClosedTrade], open_trades: dict, skipped_rows: int, reject_counts: Counter) -> str:
    summary = summarize_trades(trades)
    overall = summary["overall"]

    lines = [
        f"File: {path}",
        f"Closed trades: {overall['count']}",
        f"Open trades: {len(open_trades)}",
        f"Skipped rows: {skipped_rows}",
        (
            "Overall: "
            f"win={overall['win_rate']:.3f} "
            f"avg_bps={overall['avg_bps']:.1f} "
            f"total_pct={overall['total_return_pct']:.2f} "
            f"median_dur_min={overall['median_duration_min']:.1f} "
            f"max_dd_pct={summary['max_drawdown_pct']:.2f}"
        ),
    ]

    for label, grouped_stats in summary["grouped"].items():
        lines.extend(_render_bucket(label, grouped_stats))

    lines.append("\n## Exit Counts")
    for reason, count in summary["exit_reason_counts"].most_common():
        lines.append(f"{reason}: {count}")

    lines.append("\n## Reject Counts")  # ← NEW
    for reason, count in reject_counts.most_common():
        lines.append(f"{reason}: {count}")

    lines.append("\n## Worst Trades")
    for trade in summary["worst_trades"]:
        lines.append(
            (
                f"{trade.entry_ts} {trade.symbol} {trade.trade_type} {trade.side} "
                f"{trade.exit_reason} ret_pct={trade.return_pct * 100:.3f} "
                f"dur_min={trade.duration_min:.1f}"
            )
        )

    lines.append("\n## Best Trades")
    for trade in summary["best_trades"]:
        lines.append(
            (
                f"{trade.entry_ts} {trade.symbol} {trade.trade_type} {trade.side} "
                f"{trade.exit_reason} ret_pct={trade.return_pct * 100:.3f} "
                f"dur_min={trade.duration_min:.1f}"
            )
        )

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Analyze paper-trade JSONL output.")
    parser.add_argument("--file", default=str(DEFAULT_FILE), help="Path to paper_trades.jsonl")
    args = parser.parse_args()

    path = Path(args.file)
    events = load_trade_events(path)
    trades, open_trades, skipped_rows, reject_counts = pair_trades(events)
    print(render_report(path, trades, open_trades, skipped_rows, reject_counts))


if __name__ == "__main__":
    main()
