#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
LOG_FILE="${TMPDIR:-/tmp}/filehub-hosted-e2e-backend.log"

cleanup() {
  if [[ -n "${BACKEND_PID:-}" ]]; then
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
    wait "$BACKEND_PID" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT

cd "$BACKEND_DIR"
source .venv/bin/activate
APP_SERVE_FRONTEND=true \
FRONTEND_DIST_DIR=../frontend/dist \
DATABASE_URL=sqlite:///./e2e_hosted.db \
ADMIN_BOOTSTRAP_ENABLED=true \
ADMIN_USERNAME=admin \
ADMIN_PASSWORD=ChangeMe123! \
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 >"$LOG_FILE" 2>&1 &
BACKEND_PID=$!

for _ in $(seq 1 60); do
  if curl -fsS http://127.0.0.1:8000/ >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

curl -fsS http://127.0.0.1:8000/ >/dev/null

cd "$FRONTEND_DIR"
npx playwright test -c playwright.hosted.config.js
