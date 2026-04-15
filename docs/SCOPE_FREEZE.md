# Scope Freeze (Phase 1)

## Locked User Flow
Visitor -> Login (Farmer / Doctor / Admin) -> Role-specific core actions -> Logout

## In-Scope Role Journeys

### Visitor
- View product overview and role guidance.
- Navigate to Farmer/Doctor/Admin login and registration entry points.

### Farmer
- Predict disease from symptoms.
- Save prediction history.
- Submit doctor queries.
- View previous queries and replies.

### Doctor
- Register cattle profiles.
- Create case sheets with predicted vs confirmed disease.
- Generate prescription guidance.
- Review cattle timeline and lab reports.
- Triage farmer queries.
- Update clinical outcomes and review quality analytics.

### Admin
- Manage users (view farmers/doctors, register doctor).
- Monitor platform analytics dashboard.
- Run Eclat mining for pattern discovery.
- Generate demo seed data for interview walkthroughs.

## Out of Scope (Post-Freeze)
- New roles/permissions beyond Farmer/Doctor/Admin.
- Multi-tenant organization model.
- Mobile-native app.
- Real-time notification service.
- ML retraining pipeline automation.

## Acceptance Baseline
- Every locked journey is manually testable end-to-end.
- All protected actions require JWT and RBAC.
- Stage/prod deployment profile uses PostgreSQL.
