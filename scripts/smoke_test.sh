#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://127.0.0.1:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://127.0.0.1:8501}"
SMOKE_ADMIN_ID="${SMOKE_ADMIN_ID:-admin}"
SMOKE_ADMIN_PASSWORD="${SMOKE_ADMIN_PASSWORD:-}"

echo "Running smoke tests"
echo "API_URL=$API_URL"
echo "FRONTEND_URL=$FRONTEND_URL"

echo "- Checking backend health"
health_body="$(curl -fsS "$API_URL/health")"
echo "  /health => $health_body"

echo "- Checking backend readiness"
ready_body="$(curl -fsS "$API_URL/ready")"
echo "  /ready => $ready_body"

echo "- Checking frontend"
frontend_root_status="$(curl -s -L -o /dev/null -w "%{http_code}" "$FRONTEND_URL" || echo 000)"
if [[ "$frontend_root_status" == "200" ]]; then
  echo "  Frontend root status => $frontend_root_status"
else
  frontend_health_url="${FRONTEND_URL%/}/_stcore/health"
  frontend_health_status="$(curl -s -L -o /dev/null -w "%{http_code}" "$frontend_health_url" || echo 000)"
  if [[ "$frontend_health_status" != "200" ]]; then
    echo "Frontend check failed: root=$frontend_root_status, _stcore/health=$frontend_health_status"
    exit 1
  fi
  echo "  Frontend root status => $frontend_root_status (acceptable fallback)"
  echo "  Frontend _stcore/health => $frontend_health_status"
fi

if [[ -n "$SMOKE_ADMIN_PASSWORD" ]]; then
  echo "- Checking auth login (admin)"
  login_code="$(curl -s -o /tmp/chis_login_response.json -w "%{http_code}" \
    -X POST "$API_URL/login" \
    -H "Content-Type: application/json" \
    -d "{\"user_id\":\"$SMOKE_ADMIN_ID\",\"password\":\"$SMOKE_ADMIN_PASSWORD\",\"role\":\"admin\"}")"

  if [[ "$login_code" != "200" ]]; then
    echo "  Login check failed: status=$login_code"
    cat /tmp/chis_login_response.json
    exit 1
  fi
  echo "  Admin login => OK"
else
  echo "- Skipping auth login check (set SMOKE_ADMIN_PASSWORD to enable)"
fi

echo "Smoke tests passed."
