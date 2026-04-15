# Deployment Runbook

## 1) Prerequisites
- Linux/macOS host with Docker Engine + Docker Compose plugin
- Ports `8000` and `8501` open (or reverse-proxied)
- Repo available on host

## 2) Configure Environment
Use one profile file:
- Stage: `.env.stage`
- Prod: `.env.prod`

Minimum values to update before deploy:
- `JWT_SECRET_KEY`
- `DEFAULT_ADMIN_PASSWORD`
- `DATABASE_URL`
- `POSTGRES_PASSWORD`
- `CORS_ALLOWED_ORIGINS`
- `PATTERN_PREDICTION_API_URL`

## 3) Start Services
From project root:

```bash
cd /Users/prashanth/Desktop/chis/pattern_prediction
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

For stage, replace `docker-compose.prod.yml` with `docker-compose.stage.yml`.

## 4) Run Migrations
```bash
docker compose exec backend alembic -c alembic.ini upgrade head
```

## 5) Smoke Check
```bash
./scripts/smoke_test.sh
```

Optional with custom endpoints:
```bash
API_URL=https://api.example.com FRONTEND_URL=https://app.example.com ./scripts/smoke_test.sh
```

Optional auth check:
```bash
SMOKE_ADMIN_PASSWORD='your-admin-password' ./scripts/smoke_test.sh
```

## 6) Seed Demo Data (Optional)
Use admin dashboard button (`Generate Demo Data`) or API:

```bash
curl -X POST "$API_URL/admin/demo-seed" -H "Authorization: Bearer <JWT>"
```

## 7) Rollback Basics
- Re-deploy previous image tag (if tagged)
- Restore DB and uploads from backups:

```bash
ENV_PROFILE_FILE=.env.prod ./scripts/restore.sh /path/to/db.sql.gz /path/to/uploads.tar.gz
```

## 8) Operational Checks
- Health: `GET /health`
- Readiness: `GET /ready`
- Logs:

```bash
docker compose logs backend --tail=200
docker compose logs frontend --tail=200
```
