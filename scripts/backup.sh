#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_DIR="$ROOT_DIR/backups"
STAMP="$(date +"%Y%m%d_%H%M%S")"
UPLOADS_SRC="$ROOT_DIR/backend/uploads"
mkdir -p "$BACKUP_DIR"

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
  # SQLAlchemy URL -> libpq URL
  echo "${url//+psycopg2/}"
}

backup_sqlite() {
  local db_url="$1"
  local sqlite_path="${db_url#sqlite:///}"

  if [[ "$sqlite_path" != /* ]]; then
    sqlite_path="$ROOT_DIR/backend/$sqlite_path"
  fi

  if [[ ! -f "$sqlite_path" ]]; then
    echo "SQLite DB not found at: $sqlite_path"
    exit 1
  fi

  cp "$sqlite_path" "$BACKUP_DIR/pattern_prediction_${STAMP}.db"
  echo "SQLite backup saved: $BACKUP_DIR/pattern_prediction_${STAMP}.db"
}

backup_postgres() {
  local db_url="$1"
  local pg_url
  pg_url="$(normalize_pg_url "$db_url")"

  if ! command -v pg_dump >/dev/null 2>&1; then
    echo "pg_dump is required for PostgreSQL backups. Install PostgreSQL client tools first."
    exit 1
  fi

  local db_file="$BACKUP_DIR/pattern_prediction_${STAMP}.sql.gz"
  pg_dump "$pg_url" | gzip > "$db_file"
  echo "PostgreSQL backup saved: $db_file"
}

DB_URL="$(resolve_database_url)"
if [[ -z "$DB_URL" ]]; then
  echo "DATABASE_URL not found. Set DATABASE_URL or add it in env files."
  exit 1
fi

if [[ "$DB_URL" == postgresql://* || "$DB_URL" == postgresql+psycopg2://* || "$DB_URL" == postgres://* ]]; then
  backup_postgres "$DB_URL"
elif [[ "$DB_URL" == sqlite:///* ]]; then
  backup_sqlite "$DB_URL"
else
  echo "Unsupported DATABASE_URL format: $DB_URL"
  exit 1
fi

if [[ -d "$UPLOADS_SRC" ]]; then
  tar -czf "$BACKUP_DIR/uploads_${STAMP}.tar.gz" -C "$ROOT_DIR/backend" uploads
  echo "Uploads backup saved: $BACKUP_DIR/uploads_${STAMP}.tar.gz"
else
  echo "Uploads directory not found, skipping uploads backup."
fi

echo "Backup completed at $BACKUP_DIR"
