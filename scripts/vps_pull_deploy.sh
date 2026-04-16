#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-$(pwd)}"
DEPLOY_REMOTE="${DEPLOY_REMOTE:-origin}"
DEPLOY_BRANCH="${DEPLOY_BRANCH:-main}"
DEPLOY_SERVICE_NAME="${DEPLOY_SERVICE_NAME:-delta-trading-bot.service}"

cd "$APP_DIR"

echo "Deploying $DEPLOY_REMOTE/$DEPLOY_BRANCH into $APP_DIR"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: $APP_DIR is not a Git working tree." >&2
  exit 1
fi

if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "ERROR: tracked files on the VPS have local edits." >&2
  echo "Commit or remove those VPS-side edits before deploying, so Git does not overwrite work." >&2
  git status --short --untracked-files=no >&2
  exit 1
fi

git fetch "$DEPLOY_REMOTE" "$DEPLOY_BRANCH"
git checkout "$DEPLOY_BRANCH"
git reset --hard "$DEPLOY_REMOTE/$DEPLOY_BRANCH"

if [ -f requirements.txt ]; then
  if [ -x .venv/bin/python ]; then
    .venv/bin/python -m pip install -r requirements.txt
  else
    python3 -m pip install --user -r requirements.txt
  fi
fi

if [ -n "$DEPLOY_SERVICE_NAME" ]; then
  if command -v systemctl >/dev/null 2>&1 && systemctl cat "$DEPLOY_SERVICE_NAME" >/dev/null 2>&1; then
    if [ "$(id -u)" -eq 0 ]; then
      systemctl restart "$DEPLOY_SERVICE_NAME"
      systemctl --no-pager --full status "$DEPLOY_SERVICE_NAME"
    else
      sudo -n systemctl restart "$DEPLOY_SERVICE_NAME"
      sudo -n systemctl --no-pager --full status "$DEPLOY_SERVICE_NAME"
    fi
  else
    echo "Service $DEPLOY_SERVICE_NAME was not found; code updated but no service was restarted."
  fi
else
  echo "DEPLOY_SERVICE_NAME is empty; code updated but no service was restarted."
fi

echo "Deploy complete."
