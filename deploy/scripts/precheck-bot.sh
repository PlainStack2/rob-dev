#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/opt/rob-bot/app}"
SERVICE_NAME="${SERVICE_NAME:-rob-bot-dev.service}"
PYTHON_BIN="${PYTHON_BIN:-${APP_DIR}/.venv/bin/python}"

echo "[1/7] Checking required commands"
command -v git >/dev/null || { echo "ERROR: git not found"; exit 1; }
command -v python3 >/dev/null || { echo "ERROR: python3 not found"; exit 1; }
command -v sudo >/dev/null || { echo "ERROR: sudo not found"; exit 1; }

echo "[2/7] Checking app directory"
cd "$APP_DIR"

if [[ ! -d ".git" ]]; then
  echo "ERROR: ${APP_DIR} is not a git repository."
  exit 1
fi

if [[ ! -f ".env" ]]; then
  echo "ERROR: ${APP_DIR}/.env does not exist."
  exit 1
fi

echo "[3/7] Checking virtual environment"
if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "ERROR: Python venv not found at ${PYTHON_BIN}"
  echo "Run the deploy script once or recreate the venv."
  exit 1
fi

echo "[4/7] Checking service exists"
if ! systemctl list-unit-files "$SERVICE_NAME" >/dev/null 2>&1; then
  echo "ERROR: systemd service not found: ${SERVICE_NAME}"
  exit 1
fi

echo "[5/7] Loading environment"
set -a
source .env
set +a

for required in DATABASE_URL DISCORD_TOKEN BOT_NAME; do
  if [[ -z "${!required:-}" ]]; then
    echo "ERROR: Required env var missing: ${required}"
    exit 1
  fi
done

echo "[6/7] Running database check"
PYTHONPATH=. "$PYTHON_BIN" scripts/check_db.py

echo "[7/7] Checking current service state"
systemctl is-active "$SERVICE_NAME" || true

echo
echo "Bot server precheck passed."
