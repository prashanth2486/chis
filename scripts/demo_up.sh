#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SMOKE_ADMIN_PASSWORD="${SMOKE_ADMIN_PASSWORD:-admin123}"

cd "$ROOT_DIR"

echo "Starting CHIS demo stack..."
docker compose down --remove-orphans
docker compose up -d postgres
docker compose run --rm backend alembic -c alembic.ini upgrade head
docker compose up -d backend frontend
SMOKE_ADMIN_PASSWORD="$SMOKE_ADMIN_PASSWORD" ./scripts/smoke_test.sh

echo ""
echo "Demo is ready:"
echo "Frontend: http://127.0.0.1:8501"
echo "Backend : http://127.0.0.1:8000"
echo "Docs    : http://127.0.0.1:8000/docs"
echo "Admin   : admin / $SMOKE_ADMIN_PASSWORD"
