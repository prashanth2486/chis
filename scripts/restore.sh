#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <db-backup-file> <uploads-backup-file>"
  echo "Examples:"
  echo "  $0 backups/pattern_prediction_YYYYMMDD_HHMMSS.db backups/uploads_YYYYMMDD_HHMMSS.tar.gz"
  echo "  $0 backups/pattern_prediction_YYYYMMDD_HHMMSS.sql.gz backups/uploads_YYYYMMDD_HHMMSS.tar.gz"
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DB_BACKUP="$1"
UPLOADS_BACKUP="$2"

resolve_database_url() {
  if [[ -n "${DATABASE_URL:-}" ]]; then
    echo "$DATABASE_URL"
    return
  fi

  local candidates=()
  if [[ -n "${ENV_PROFILE_FILE:-}" ]]; then
    candidates+=("$ROOT_DIR/$ENV_PROFILE_FILE")
  fi
  candidates+=("$ROOT_DIR/.env.example" "$ROOT_DIR/.env.stage" "$ROOT_DIR/.env.prod")

  for env_file in "${candidates[@]}"; do
    if [[ -f "$env_file" ]]; then
      local line
      line="$(grep -E '^DATABASE_URL=' "$env_file" | tail -n 1 || true)"
      if [[ -n "$line" ]]; then
        echo "${line#DATABASE_URL=}"
        return
      fi
    fi
  done

  echo ""
}

normalize_pg_url() {
  local url="$1"
  echo "${url//+psycopg2/}"
}

restore_sqlite() {
  local db_url="$1"
  local sqlite_path="${db_url#sqlite:///}"

  if [[ "$sqlite_path" != /* ]]; then
    sqlite_path="$ROOT_DIR/backend/$sqlite_path"
  fi

  mkdir -p "$(dirname "$sqlite_path")"
  cp "$DB_BACKUP" "$sqlite_path"
  echo "SQLite restore completed: $sqlite_path"
}

restore_postgres() {
  local db_url="$1"
  local pg_url
  pg_url="$(normalize_pg_url "$db_url")"

  if ! command -v psql >/dev/null 2>&1; then
    echo "psql is required for PostgreSQL restore. Install PostgreSQL client tools first."
    exit 1
  fi

  # Reset schema before restore
  psql "$pg_url" -v ON_ERROR_STOP=1 -c "DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;"

  if [[ "$DB_BACKUP" == *.sql.gz ]]; then
    gunzip -c "$DB_BACKUP" | psql "$pg_url" -v ON_ERROR_STOP=1
  elif [[ "$DB_BACKUP" == *.sql ]]; then
    psql "$pg_url" -v ON_ERROR_STOP=1 -f "$DB_BACKUP"
  else
    echo "For PostgreSQL restore, DB backup must be .sql or .sql.gz"
    exit 1
  fi

  echo "PostgreSQL restore completed."
}

if [[ ! -f "$DB_BACKUP" ]]; then
  echo "DB backup file not found: $DB_BACKUP"
  exit 1
fi

if [[ ! -f "$UPLOADS_BACKUP" ]]; then
  echo "Uploads backup file not found: $UPLOADS_BACKUP"
  exit 1
fi

DB_URL="$(resolve_database_url)"
if [[ -z "$DB_URL" ]]; then
  echo "DATABASE_URL not found. Set DATABASE_URL or add it in env files."
  exit 1
fi

if [[ "$DB_URL" == postgresql://* || "$DB_URL" == postgresql+psycopg2://* || "$DB_URL" == postgres://* ]]; then
  restore_postgres "$DB_URL"
elif [[ "$DB_URL" == sqlite:///* ]]; then
  restore_sqlite "$DB_URL"
else
  echo "Unsupported DATABASE_URL format: $DB_URL"
  exit 1
fi

rm -rf "$ROOT_DIR/backend/uploads"
mkdir -p "$ROOT_DIR/backend/uploads"
tar -xzf "$UPLOADS_BACKUP" -C "$ROOT_DIR/backend"

echo "Uploads restore completed."
echo "Restore completed."
