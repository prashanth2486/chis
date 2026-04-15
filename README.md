# Cattle Health Intelligence System

Production-readiness baseline for a FastAPI + Streamlit cattle health platform.

## What Was Added
- JWT auth with bcrypt hashing and RBAC enforcement
- Request validation hardening with Pydantic `Field` constraints + `EmailStr`
- Pagination support on major list APIs (`limit`, `offset`)
- Unified error schema and request-id based structured logging
- Health endpoints: `/health`, `/ready`
- Versioned migrations with Alembic
- Pytest suite with unit + integration + negative tests
- GitHub Actions CI workflow
- Environment profiles (`.env.example`, `.env.stage`, `.env.prod`)
- Backup/restore scripts for DB and uploads
- Scope freeze baseline for end-to-end sign-off

## Local Run (venv)

### Backend
```bash
cd /Users/prashanth/Desktop/chis/pattern_prediction/backend
./venv/bin/python -m pip install -r requirements-dev.txt
./venv/bin/python -m alembic -c alembic.ini upgrade head
./venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

### Frontend
```bash
cd /Users/prashanth/Desktop/chis/pattern_prediction/frontend
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

## Local Run (Docker Compose with PostgreSQL)
```bash
cd /Users/prashanth/Desktop/chis/pattern_prediction
docker compose up -d --build
docker compose exec backend alembic -c alembic.ini upgrade head
```

## Tests
```bash
cd /Users/prashanth/Desktop/chis/pattern_prediction/backend
./venv/bin/python -m pytest -q
```

## Backup / Restore

### Default (local SQLite from `.env.example`)
```bash
cd /Users/prashanth/Desktop/chis/pattern_prediction
./scripts/backup.sh
./scripts/restore.sh /path/to/pattern_prediction_YYYYMMDD_HHMMSS.db /path/to/uploads_YYYYMMDD_HHMMSS.tar.gz
```

### Stage/Prod PostgreSQL
```bash
cd /Users/prashanth/Desktop/chis/pattern_prediction
ENV_PROFILE_FILE=.env.prod ./scripts/backup.sh
ENV_PROFILE_FILE=.env.prod ./scripts/restore.sh /path/to/pattern_prediction_YYYYMMDD_HHMMSS.sql.gz /path/to/uploads_YYYYMMDD_HHMMSS.tar.gz
```

Notes:
- You can always override by exporting `DATABASE_URL` explicitly.
- PostgreSQL backup/restore requires `pg_dump` and `psql` on the host.

## Deployment Smoke Test
```bash
./scripts/smoke_test.sh
```
Optional:
```bash
API_URL=https://api.example.com FRONTEND_URL=https://app.example.com ./scripts/smoke_test.sh
SMOKE_ADMIN_PASSWORD='your-admin-password' ./scripts/smoke_test.sh
```

## Dependency Lock Strategy
- Runtime dependencies are pinned in:
  - `backend/requirements.txt`
  - `frontend/requirements.txt`
- Dev/test dependencies are pinned in:
  - `backend/requirements-dev.txt`
- CI installs pinned files directly for reproducible builds.

## Presentation Docs
- Scope freeze: `docs/SCOPE_FREEZE.md`
- Architecture: `docs/ARCHITECTURE.md`
- Deployment runbook: `docs/DEPLOYMENT_RUNBOOK.md`
- API endpoints: `docs/API_ENDPOINTS.md`
- UAT checklist: `docs/UAT_CHECKLIST.md`
- Project brief: `docs/PROJECT_BRIEF.md`
- Demo checklist: `docs/DEMO_CHECKLIST.md`
