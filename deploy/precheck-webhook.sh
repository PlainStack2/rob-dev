#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/opt/rob-webhook/app}"
SERVICE_NAME="${SERVICE_NAME:-rob-webhook-dev.service}"
PYTHON_BIN="${PYTHON_BIN:-${APP_DIR}/.venv/bin/python}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8080/health}"

echo "[1/8] Checking required commands"
command -v git >/dev/null || { echo "ERROR: git not found"; exit 1; }
command -v python3 >/dev/null || { echo "ERROR: python3 not found"; exit 1; }
command -v sudo >/dev/null || { echo "ERROR: sudo not found"; exit 1; }
command -v curl >/dev/null || { echo "ERROR: curl not found"; exit 1; }

echo "[2/8] Checking app directory"
cd "$APP_DIR"

if [[ ! -d ".git" ]]; then
  echo "ERROR: ${APP_DIR} is not a git repository."
  exit 1
fi

if [[ ! -f ".env" ]]; then
  echo "ERROR: ${APP_DIR}/.env does not exist."
  exit 1
fi

echo "[3/8] Checking virtual environment"
if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "ERROR: Python venv not found at ${PYTHON_BIN}"
  echo "Run the deploy script once or recreate the venv."
  exit 1
fi

echo "[4/8] Checking service exists"
if ! systemctl list-unit-files "$SERVICE_NAME" >/dev/null 2>&1; then
  echo "ERROR: systemd service not found: ${SERVICE_NAME}"
  exit 1
fi

echo "[5/8] Loading environment"
set -a
source .env
set +a

for required in DATABASE_URL THRONE_WEBHOOK_HOST THRONE_WEBHOOK_PORT; do
  if [[ -z "${!required:-}" ]]; then
    echo "ERROR: Required env var missing: ${required}"
    exit 1
  fi
done

echo "[6/8] Running database check"
PYTHONPATH=. "$PYTHON_BIN" scripts/check_db.py

echo "[7/8] Checking current service state"
systemctl is-active "$SERVICE_NAME" || true

echo "[8/8] Checking current health endpoint if service is running"
if systemctl is-active --quiet "$SERVICE_NAME"; then
  curl -fsS "$HEALTH_URL" >/dev/null
  echo "Webhook health endpoint is responding."
else
  echo "Webhook service is not currently active; skipping live health check."
fi

echo
echo "Webhook server precheck passed."
