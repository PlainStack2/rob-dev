#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="/opt/rob-webhook/app"
SERVICE_NAME="rob-webhook-dev.service"
DEPLOY_BRANCH="${DEPLOY_BRANCH:-main}"
DEPLOY_REF="${DEPLOY_REF:-${DEPLOY_BRANCH}}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8080/health}"

echo "[1/12] Entering ${APP_DIR}"
cd "$APP_DIR"

echo "[2/12] Checking repository state"
if [[ ! -d ".git" ]]; then
    echo "ERROR: ${APP_DIR} is not a git repository."
    exit 1
fi

echo "[3/12] Preserving local .env"
if [[ ! -f ".env" ]]; then
    echo "ERROR: ${APP_DIR}/.env does not exist."
    exit 1
fi

echo "[4/12] Fetching ${DEPLOY_BRANCH} + deploy ref ${DEPLOY_REF}"
git fetch origin --prune "$DEPLOY_BRANCH"
git fetch origin "${DEPLOY_REF}" || true

echo "[5/12] Resetting tracked files to deploy ref"
# This intentionally discards local tracked-code changes on the server.
# Your .env is untracked/ignored and should not be touched.
if [[ "${DEPLOY_REF}" == "${DEPLOY_BRANCH}" ]]; then
    git checkout "$DEPLOY_BRANCH" || git checkout -B "$DEPLOY_BRANCH" "origin/$DEPLOY_BRANCH"
    git reset --hard "origin/$DEPLOY_BRANCH"
else
    if git rev-parse --verify --quiet "${DEPLOY_REF}" >/dev/null; then
        git checkout --detach "${DEPLOY_REF}"
    else
        git checkout --detach FETCH_HEAD
    fi
fi
git clean -fd --exclude=.env --exclude=.venv

echo "[6/12] Preparing virtual environment"
if [[ ! -d ".venv" ]]; then
    python3 -m venv .venv
fi

echo "[7/12] Installing dependencies"
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

echo "[8/12] Running compile checks"
PYTHONPATH=. .venv/bin/python -m compileall apps rob scripts

echo "[9/12] Installing global rob command"
./scripts/install-rob-global.sh

echo "[10/12] Running migrations and database checks"
set -a
source .env
set +a
PYTHONPATH=. .venv/bin/python scripts/run_migrations.py
PYTHONPATH=. .venv/bin/python scripts/check_db.py

echo "[11/12] Restarting ${SERVICE_NAME}"
sudo systemctl restart "$SERVICE_NAME"

echo "[12/12] Running health check: ${HEALTH_URL}"
for attempt in {1..20}; do
    if curl -fsS "$HEALTH_URL"; then
        echo
        echo "Webhook deploy completed successfully."
        exit 0
    fi

    echo "Waiting for webhook service... attempt ${attempt}/20"
    sleep 2
done

echo "ERROR: Webhook health check failed."
echo
echo "Service status:"
sudo systemctl status "$SERVICE_NAME" --no-pager || true

echo
echo "Recent logs:"
sudo journalctl -u "$SERVICE_NAME" -n 120 --no-pager || true

exit 1
