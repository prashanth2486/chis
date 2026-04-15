# Manual UAT Checklist

## 1. Visitor
- Open app root.
- Validate Home/Farmer/Doctor/Admin/About tabs render.
- Confirm Farmer and Doctor registration forms submit successfully.

## 2. Authentication + RBAC
- Login as Farmer, Doctor, Admin.
- Verify token-based access works for each role dashboard.
- Verify unauthorized endpoint access returns 401/403.

## 3. Farmer Flow
- Select symptoms and run prediction.
- Verify treatment text is shown.
- Verify prediction is saved in history.
- Submit doctor query and verify it appears in previous queries.

## 4. Doctor Flow
- Create cattle profile.
- Create case sheet with symptoms, diagnosis, treatment.
- Confirm predicted vs confirmed disease fields appear.
- Upload lab report.
- Open timeline and verify visit + report appear.
- Triage farmer query and send reply.
- Update outcome status.

## 5. Admin Flow
- View users list and register a doctor.
- Open analytics and verify metrics load.
- Run Eclat with valid dataset and confirm outputs.
- Run demo seed endpoint from admin dashboard and verify idempotent behavior.

## 6. Data + Reliability
- Restart backend and verify data persistence.
- Run `/health` and `/ready` probes.
- Validate pagination on large lists (`limit`, `offset`).

## 7. Security Regression
- Attempt protected API call without token -> expect 401.
- Attempt role-restricted API with wrong role -> expect 403.
- Attempt invalid payloads -> expect validation errors.

## Sign-Off
- [ ] Visitor flow pass
- [ ] Farmer flow pass
- [ ] Doctor flow pass
- [ ] Admin flow pass
- [ ] Security checks pass
- [ ] Deployment smoke test pass
