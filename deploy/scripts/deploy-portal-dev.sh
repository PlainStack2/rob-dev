#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/opt/rob-portal/app}"
SERVICE_NAME="${SERVICE_NAME:-rob-portal-dev.service}"
DEPLOY_BRANCH="${DEPLOY_BRANCH:-main}"
DEPLOY_REF="${DEPLOY_REF:-${DEPLOY_BRANCH}}"
PYTHON_BIN="${PYTHON_BIN:-${APP_DIR}/.venv/bin/python}"
PIP_BIN="${PIP_BIN:-${APP_DIR}/.venv/bin/pip}"

echo "[1/12] Entering ${APP_DIR}"
cd "${APP_DIR}"

echo "[2/12] Verifying repository and environment"
if [[ ! -d ".git" ]]; then
  echo "ERROR: ${APP_DIR} is not a git repository."
  exit 1
fi
if [[ ! -f ".env" ]]; then
  echo "ERROR: ${APP_DIR}/.env does not exist."
  exit 1
fi

echo "[3/12] Fetching ${DEPLOY_BRANCH} + deploy ref ${DEPLOY_REF}"
git fetch origin --prune "${DEPLOY_BRANCH}"
git fetch origin "${DEPLOY_REF}" || true

echo "[4/12] Checking out deploy ref"
if [[ "${DEPLOY_REF}" == "${DEPLOY_BRANCH}" ]]; then
  git checkout "${DEPLOY_BRANCH}" || git checkout -B "${DEPLOY_BRANCH}" "origin/${DEPLOY_BRANCH}"
  git reset --hard "origin/${DEPLOY_BRANCH}"
else
  if git rev-parse --verify --quiet "${DEPLOY_REF}" >/dev/null; then
    git checkout --detach "${DEPLOY_REF}"
  else
    git checkout --detach FETCH_HEAD
  fi
fi

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "[5/12] Creating virtual environment"
  python3 -m venv "${APP_DIR}/.venv"
else
  echo "[5/12] Virtual environment already present"
fi

echo "[6/12] Installing dependencies"
"${PYTHON_BIN}" -m pip install --upgrade pip
"${PIP_BIN}" install -r requirements.txt -r portal/requirements.txt

echo "[7/12] Running compile checks"
PYTHONPATH=. "${PYTHON_BIN}" -m compileall apps rob scripts portal

echo "[8/12] Running Rob SQL migrations and DB checks"
set -a
source .env
set +a
PYTHONPATH=. "${PYTHON_BIN}" -m scripts.run_migrations
PYTHONPATH=. "${PYTHON_BIN}" -m scripts.check_db

echo "[9/12] Running Django portal migrations"
cd "${APP_DIR}/portal"
"${PYTHON_BIN}" manage.py migrate --noinput
cd "${APP_DIR}"

echo "[10/12] Collecting portal static assets"
cd "${APP_DIR}/portal"
"${PYTHON_BIN}" manage.py collectstatic --noinput
cd "${APP_DIR}"

echo "[11/12] Running Django portal checks"
cd "${APP_DIR}/portal"
# Use the standard check in dev; check --deploy is generally tuned for production-only policies.
"${PYTHON_BIN}" manage.py check
cd "${APP_DIR}"

echo "[12/12] Restarting ${SERVICE_NAME}"
sudo systemctl restart "${SERVICE_NAME}"
sudo systemctl --no-pager --full status "${SERVICE_NAME}" | sed -n '1,12p'
sudo systemctl is-active "${SERVICE_NAME}"
printf '\nPortal deploy complete.\n'
