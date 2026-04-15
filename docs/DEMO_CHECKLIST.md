# Demo Checklist (Interview Ready)

## 1. Start Demo
1. Run `./scripts/run_demo.sh` from project root.
2. Open:
- `http://127.0.0.1:8501` (UI)
- `http://127.0.0.1:8000/docs` (API)

## 2. Suggested 8-10 Minute Flow
1. Landing + role story
- Explain Farmer, Doctor, Admin journeys.

2. Farmer flow
- Farmer login/register.
- Submit symptoms and show prediction + saved history.
- Submit a doctor query.

3. Doctor flow
- Create/choose cattle profile.
- Create case sheet with symptoms.
- Show predicted vs confirmed disease, severity/escalation, prescription guidance.
- Update case outcome and show timeline view.
- Show data quality and outcomes analytics.

4. Admin flow
- Show user management and analytics.
- Run Eclat with sample dataset.

5. Engineering proof
- Show `/docs`, `/health`, `/ready`.
- Mention JWT + bcrypt + RBAC + Alembic + CI + pytest.

## 3. Backup Talking Points
- Why this design is production-ready:
- Validation + response contracts
- Observability (request-id + structured logs)
- Environment profiles (`dev/stage/prod`)
- Backup/restore scripts
- Reproducible pinned dependencies

## 4. If Something Fails During Demo
1. Health check: `curl http://127.0.0.1:8000/health`
2. See logs:
- `.demo_logs/backend.log`
- `.demo_logs/frontend.log`
3. Restart quickly:
- `./scripts/stop_demo.sh`
- `./scripts/run_demo.sh`

## 5. End Demo
- Run `./scripts/stop_demo.sh`
