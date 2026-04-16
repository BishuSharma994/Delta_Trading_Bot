#!/usr/bin/env bash
set -euo pipefail

: "${VPS_HOST:?Set VPS_HOST to your VPS IP or hostname.}"

VPS_USER="${VPS_USER:-root}"
VPS_PORT="${VPS_PORT:-22}"
VPS_APP_DIR="${VPS_APP_DIR:-/root/Delta_Trading_Bot}"
LOCAL_RUNTIME_DIR="${LOCAL_RUNTIME_DIR:-runtime_mirror}"

remote_app_dir="$(printf '%q' "$VPS_APP_DIR")"

mkdir -p "$LOCAL_RUNTIME_DIR"

echo "Fetching runtime files from $VPS_USER@$VPS_HOST:$VPS_APP_DIR"

ssh -p "$VPS_PORT" "$VPS_USER@$VPS_HOST" \
  "cd $remote_app_dir && tar -czf - --ignore-failed-read execution_state.json observer.out bot.log logs data/events data/audit 2>/dev/null" \
  | tar -xzf - -C "$LOCAL_RUNTIME_DIR"

echo "Runtime mirror updated at $LOCAL_RUNTIME_DIR"

paper_trades="$LOCAL_RUNTIME_DIR/data/events/paper_trades.jsonl"
if [ -f "$paper_trades" ]; then
  echo
  python3 trade_stats.py --file "$paper_trades"
else
  echo "No paper trade file found at $paper_trades"
fi
