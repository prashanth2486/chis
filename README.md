# Cattle Health Intelligence System (CHIS)

Role-based platform that helps farmers, veterinary doctors, and admins report cattle symptoms, get disease/treatment guidance, keep clinical records, and mine frequent symptom patterns.

## What this project does

CHIS is an end-to-end cattle healthcare workflow:

- **Farmers** enter symptoms, get a predicted disease and treatment hint, save history, and ask a doctor.
- **Doctors** manage cattle profiles, case sheets, queries, lab uploads, follow-ups, and pattern mining.
- **Admins** monitor users/analytics, seed demo data, and run dataset mining.

The UI is a Streamlit portal. The API is FastAPI with JWT login and role-based access.

## Problem being solved

Cattle care is often fragmented: symptoms are recorded inconsistently, cases live in paper notes, follow-ups are easy to miss, and historical patterns are rarely analyzed. CHIS puts reporting, prediction support, case handling, and analytics in one system so farmers and vets can coordinate faster.

This is **clinical decision support**, not a replacement for a veterinary doctor.

## Technologies used

| Layer | Stack |
|---|---|
| Frontend | Streamlit, Requests, Pandas |
| Backend | FastAPI, Pydantic, Uvicorn |
| Auth | JWT (`python-jose`), bcrypt (`passlib`) |
| Database | SQLAlchemy, Alembic; SQLite (local), PostgreSQL (Docker/stage/prod) |
| Pattern mining | mlxtend (frequent itemsets + association rules) |
| Ops | Docker Compose, GitHub Actions, backup/restore scripts |

## Dataset / source

Prediction is **rule-based**, not a trained ML model. Symptom-to-disease and disease-to-treatment maps live in `backend/services/prediction_service.py` (veterinary knowledge rules).

Pattern mining uses transaction CSVs with a `Data` column of comma-separated symptoms:

- `sample_dataset.csv` — tiny example
- `realistic_cattle_dataset.csv` — synthetic cattle-symptom dataset (~200 rows) created for this project

Upload either file (or Excel) to `/eclat/run` to get frequent itemsets and association rules.

## How the project works

```
Farmer / Doctor / Admin
        |
        v
 Streamlit UI  -- JWT Bearer -->  FastAPI
                                        |
                    +-------------------+-------------------+
                    v                   v                   v
             Prediction rules      Eclat mining         SQLAlchemy
             (symptoms → disease)  (CSV/Excel)          SQLite / Postgres
```

1. User logs in or registers. Backend issues a JWT; the UI sends it on later calls.
2. RBAC blocks endpoints the role is not allowed to use (for example, only doctor/admin create cattle profiles).
3. `/predict` tokenizes symptoms, matches them to disease rules, and returns a treatment mapping.
4. Doctors store cattle, case sheets (predicted vs confirmed diagnosis), outcomes, and lab files.
5. Admins/doctors can upload a dataset and run frequent-pattern mining (support/confidence thresholds).

## How to run it

**Requirements:** Python 3.13+, optionally Docker.

Clone and configure (placeholders only — do not commit `.env`):

```bash
git clone https://github.com/prashanth2486/chis.git
cd chis
cp .env.example .env
```

### Option A — local (venv)

Backend:

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
alembic -c alembic.ini upgrade head
uvicorn main:app --host 127.0.0.1 --port 8000
```

Frontend (second terminal):

```bash
cd frontend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

### Option B — Docker Compose

```bash
docker compose up -d --build
docker compose exec backend alembic -c alembic.ini upgrade head
```

### Tests

```bash
cd backend
pytest -q
```

### URLs

- UI: http://127.0.0.1:8501
- API: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs
- Health: `GET /health` · Ready: `GET /ready`

After first start, register a farmer/doctor, or log in as admin using the local password from your `.env` (`DEFAULT_ADMIN_PASSWORD` in `.env.example`). Change it before any real deployment. Admins can also call `POST /admin/demo-seed` to create walkthrough data.

## Results / output

| Output | Where |
|---|---|
| Predicted disease + treatment | Farmer/doctor dashboards; `POST /predict` |
| Saved prediction history | Farmer history; `GET /history/{farmer_id}` |
| Case sheets, timelines, outcomes | Doctor dashboard |
| Frequent itemsets + association rules | Admin/doctor Eclat screen; `POST /eclat/run` |
| Platform KPIs | Admin analytics; `GET /analytics` |
| API contract | http://127.0.0.1:8000/docs |

Example: symptoms `fever,coughing,nasal-discharge` can map to a respiratory disease such as pneumonia, with the matching treatment guidance. Eclat on `realistic_cattle_dataset.csv` returns co-occurring symptom sets (for example fever with reduced appetite) and rules with confidence scores.

## Your contribution

Solo project covering the full stack:

- Role-based Streamlit portals (farmer, doctor, admin)
- FastAPI backend with JWT, RBAC, Pydantic validation, and pagination
- Clinical workflow: cattle registry, case sheets, queries, lab uploads, follow-ups
- Rule-based cattle disease prediction and treatment mapping
- Eclat-style frequent pattern mining on symptom datasets
- SQLAlchemy models + Alembic migrations (SQLite / PostgreSQL)
- Docker Compose, CI tests, health checks, and backup/restore scripts

## Repository hygiene

- Secrets belong in a local `.env` (gitignored). Only `.env.example` is committed, with placeholders.
- Do not commit `*.db`, `.env`, API keys, or real user data.
