# VPS Deployment

This setup keeps VS Code off the VPS during normal development.

Daily workflow:

1. Edit and test on your local machine.
2. Commit and push to `main`.
3. GitHub Actions connects to the VPS by SSH.
4. The VPS runs `scripts/vps_pull_deploy.sh`.
5. The VPS pulls `origin/main` and restarts the systemd service.

## Local workflow

On your own computer, clone the repo and open that local folder in VS Code:

```bash
git clone git@github.com:BishuSharma994/Delta_Trading_Bot.git
cd Delta_Trading_Bot
code .
```

Do not use VS Code Remote SSH for normal editing. The VPS should only run the service and pull from Git.

## Deploy workflow

After the one-time setup is complete, use this as your normal process:

```bash
git pull
# edit locally
python3 -m unittest
git add <changed files>
git commit -m "Describe the change"
git push origin main
```

The push triggers `.github/workflows/deploy.yml`. GitHub Actions SSHs into the VPS, runs `scripts/vps_pull_deploy.sh`, pulls `origin/main`, and restarts `delta-trading-bot.service`.

## One-time VPS setup

Clone the repository on the VPS if it is not already present:

```bash
cd /root
git clone git@github.com:BishuSharma994/Delta_Trading_Bot.git
cd /root/Delta_Trading_Bot
```

Install the service:

```bash
sudo cp deploy/systemd/delta-trading-bot.service /etc/systemd/system/delta-trading-bot.service
sudo systemctl daemon-reload
sudo systemctl enable delta-trading-bot.service
sudo systemctl restart delta-trading-bot.service
```

Check it:

```bash
sudo systemctl status delta-trading-bot.service
```

Confirm the VPS can pull from GitHub:

```bash
cd /root/Delta_Trading_Bot
git fetch origin main
```

Because the repo remote uses `git@github.com:BishuSharma994/Delta_Trading_Bot.git`, the VPS needs a GitHub SSH key with read access to this repository.

## GitHub secrets

Add these secrets in GitHub:

- `VPS_HOST`: VPS IP address or hostname
- `VPS_USER`: SSH user, for example `root`
- `VPS_SSH_KEY`: private key that can SSH into the VPS
- `VPS_PORT`: optional, defaults to `22`
- `VPS_APP_DIR`: optional, defaults to `/root/Delta_Trading_Bot`

The SSH user must be able to run `git pull` in the repo. If the user is not `root`, it also needs passwordless sudo for restarting `delta-trading-bot.service`.

`VPS_SSH_KEY` is the key GitHub Actions uses to enter the VPS. It is separate from the VPS key used to pull from GitHub, unless you intentionally use the same key for both.

## Important rule

Do not edit tracked files directly on the VPS. The deploy script intentionally stops if tracked files have local VPS edits, because the VPS should be a deployment target only. Runtime files such as `.env`, logs, and JSON state stay ignored by Git.

## Viewing VPS trades locally

Do not commit trade logs, JSONL event files, `execution_state.json`, or `bot.log` to Git. They are runtime data.

To review trades locally, sync a read-only mirror from the VPS:

```bash
VPS_HOST=<your-vps-ip> ./scripts/fetch_vps_runtime.sh
```

Optional environment variables:

- `VPS_USER`: defaults to `root`
- `VPS_PORT`: defaults to `22`
- `VPS_APP_DIR`: defaults to `/root/Delta_Trading_Bot`
- `LOCAL_RUNTIME_DIR`: defaults to `runtime_mirror`

The script copies runtime files into `runtime_mirror/`, which is ignored by Git, and then runs:

```bash
python3 trade_stats.py --file runtime_mirror/data/events/paper_trades.jsonl
```

For a nicer long-term view, the next step would be a small read-only dashboard that reads the mirrored JSONL files locally or exposes a private VPS status endpoint. Git should stay only for code.
