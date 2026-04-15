# API Endpoints (v1)

## Public Endpoints
- `GET /` - service welcome
- `GET /health` - liveliness probe
- `GET /ready` - readiness probe (DB + uploads)
- `POST /login` - role login and JWT issuance
- `POST /register/farmer` - farmer registration
- `POST /register/vdoctor` - doctor registration

## Authenticated Core (`farmer|doctor|admin` unless specified)
- `POST /predict` - symptom-based disease prediction (`symptoms` query param)
- `GET /symptoms` - normalized symptom vocabulary
- `POST /history` - save prediction history (owner/admin/doctor)
- `GET /history/{farmer_id}` - history list with pagination (owner/admin/doctor)
- `POST /queries` - farmer query creation
- `GET /queries` - query listing (farmer scoped automatically)

## Doctor/Admin Clinical APIs
- `POST /eclat/run` - Eclat mining with support/confidence validation
- `GET /users` - farmers/doctors directory (`admin|doctor`)
- `POST /cattle` - create cattle profile (`doctor|admin`)
- `GET /cattle` - list cattle (farmer-scoped for farmer role)
- `POST /case-sheets` - create case sheet + prescription metadata
- `GET /case-sheets` - list/filter case sheets with pagination
- `PATCH /case-sheets/{case_id}/outcome` - update case outcome
- `GET /cattle/{cattle_id}/timeline` - longitudinal timeline for one animal
- `GET /follow-ups` - follow-up queue
- `GET /doctor/queries` - doctor triage inbox
- `POST /doctor/queries/{query_id}/triage` - triage update
- `POST /queries/{query_id}/reply` - doctor/admin reply
- `POST /preventive-care` - create preventive care record
- `GET /preventive-care` - list preventive care records
- `POST /lab-reports` - upload lab report
- `GET /lab-reports` - list lab reports
- `GET /doctor/trends` - disease/village/month trends
- `GET /doctor/emergency-alerts` - emergency alerts feed
- `GET /doctor/similar-cases` - symptom-overlap case search
- `GET /doctor/outcomes` - treatment outcome analytics
- `GET /doctor/data-quality` - data quality checks

## Admin-Only APIs
- `GET /analytics` - platform KPI dashboard
- `POST /admin/demo-seed` - idempotent demo data seeding

## Security Notes
- Protected APIs require `Authorization: Bearer <JWT>`.
- RBAC is enforced by middleware + endpoint dependencies.
- Request validation is enforced through Pydantic models and query constraints.
