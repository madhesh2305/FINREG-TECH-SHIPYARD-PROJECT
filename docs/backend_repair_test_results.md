# BACKEND REPAIR TEST RESULTS — FINREGTECH SHIPYARD
**Project:** FinRegTech ShipYard | FCC Project Cockpit  
**Application Scope:** ABC Shield (UK Bribery Act 2010 & EU Anti-Corruption Directives)  
**Database Authority:** PostgreSQL 18.6 (`"FinRegTech ShipYard"`)  
**Execution Timestamp:** 11 October 2026  
**Auditor / Lead Engineer:** Vishal S.R.  

---

## 1. Issue Status Verdicts

| Issue Under Investigation | Status Verdict | Verification Summary |
|---------------------------|:--------------:|----------------------|
| **1. `sqlite3.OperationalError: no such table: identity_users`** | **FIXED AND VERIFIED** | PostgreSQL 18.6 confirmed as active dialect. Silent SQLite fallback eliminated. Schema `identity.users` queries execute natively without error. |
| **2. Repeated `401 Unauthorized` responses from `GET /api/v1/projects`** | **FIXED AND VERIFIED** | Validated full authentication lifecycle. 6 distinct authentication scenarios verified. Bearer token injection verified. Demo user password hashes synchronized in DB with zero hardcoded code exceptions. |
| **3. FastAPI `404 Not Found` response: `{"detail":"Not Found"}`** | **FIXED AND VERIFIED** | Resolved string project code path matching (`PRJ-ABC-001`), implemented missing `PATCH /api/v1/users/me` endpoint, and eliminated blind frontend invocations to nonexistent `/tools` path. |

---

## 2. Test Execution Commands & Raw Evidence

### Test Suite 1: Full Backend Pytest Suite (60/60 Passed)
- **Command:** `& "C:\Users\Vishal\AppData\Local\Programs\Python\Python312\python.exe" -m pytest tests/`
- **Working Directory:** `c:\Users\Vishal\OneDrive\Documents\FinRegTechnology ShipYard\backend`
- **Exit Code:** `0`
- **Duration:** `28.38s`
- **Passed:** 60
- **Failed:** 0
- **Skipped:** 0
- **Warnings:** 3 (FastAPI/Starlette deprecation notices)

```text
============================= test session starts =============================
platform win32 -- Python 3.12.0, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\Vishal\OneDrive\Documents\FinRegTechnology ShipYard\backend
plugins: anyio-4.13.0
collected 60 items

tests\test_admin.py .....                                                [  8%]
tests\test_advice.py .....                                               [ 16%]
tests\test_advisors.py ...                                               [ 21%]
tests\test_ai_and_audit.py ......                                        [ 31%]
tests\test_auth.py ........                                              [ 45%]
tests\test_decisions.py ......                                           [ 55%]
tests\test_members.py ....                                               [ 61%]
tests\test_projects.py ......                                            [ 71%]
tests\test_register.py ......                                            [ 81%]
tests\test_regulatory.py ......                                          [ 91%]
tests\test_security_negative.py ....                                     [ 98%]
tests\test_verify_live.py .                                              [100%]

======================= 60 passed, 3 warnings in 28.38s =======================
```

---

### Test Suite 2: 12-Stage Live Multi-Intern Lifecycle Verification
- **Command:** `& "C:\Users\Vishal\AppData\Local\Programs\Python\Python312\python.exe" -m pytest tests/test_verify_live.py -v -s`
- **Working Directory:** `c:\Users\Vishal\OneDrive\Documents\FinRegTechnology ShipYard\backend`
- **Exit Code:** `0`
- **Duration:** `2.37s`
- **Passed:** 1 (encompassing 12 sub-stages)
- **Failed:** 0
- **Key Evidence:**
  - Stage 1: Advisor registration & PostgreSQL persistence (`identity.users`, `advisory.advisor_profiles`).
  - Stage 2: Advisor login & session validation (`ADVISOR` role).
  - Stage 3: Builder registration & project creation (`PRJ-795C46` sole owner).
  - Stage 4: Project resolution by string code `PRJ-795C46` & regulatory library loading (27 sources).
  - Stage 5: Advisor invitation & service role assignment (`REGULATORY`).
  - Stage 6: Advisor advice submission & traceability.
  - Stage 7: Grounded AI retrieval & conflict gap detection (W4.11 specification).
  - Stage 8: Builder decision governance & audit recording.
  - Stage 9: Dynamic audit readiness score calculation (`50%`, `IN_PROGRESS`).
  - Stage 10: Immutable audit event trail (5 events recorded).
  - Stage 11: Security guards (Admin self-registration 403, BOLA/IDOR 403, Unauthenticated 401).
  - Stage 12: Admin cockpit stats & user status toggle in PostgreSQL.

---

### Test Suite 3: 10-Workflow Acceptance Audit against Active Uvicorn Daemon
- **Command:** `& "C:\Users\Vishal\AppData\Local\Programs\Python\Python312\python.exe" scripts/audit_e2e_verification.py`
- **Working Directory:** `c:\Users\Vishal\OneDrive\Documents\FinRegTechnology ShipYard\backend`
- **Exit Code:** `0`
- **Duration:** `2.12s`
- **Workflows Verified:**
  1. Registration & Authentication: **PASSED**
  2. Builder Project Creation & Persistence: **PASSED**
  3. Project Profile & Regulatory Requirements: **PASSED**
  4. Advisor Invitation & Access: **PASSED**
  5. Advice Submission & Review: **PASSED**
  6. RAG Retrieval & No-Source Handling: **PASSED**
  7. Conflict Review & Decision Recording: **PASSED**
  8. Dynamic Audit Readiness Evaluation: **PASSED**
  9. Audit Event Defensibility Stream: **PASSED**
  10. Security: RBAC, BOLA/IDOR & Isolation: **PASSED**

---

### Test Suite 4: Frontend Production Build
- **Command:** `npm run build`
- **Working Directory:** `c:\Users\Vishal\OneDrive\Documents\FinRegTechnology ShipYard\frontend`
- **Exit Code:** `0`
- **Duration:** `1.25s`
- **Transformed Modules:** `1902`
- **Errors:** `0`
- **Syntax / Import Warnings:** `0`

---

## 3. Preservation of Invariants

- **Database Engine:** PostgreSQL 18.6 (`"FinRegTech ShipYard"`).
- **Destructive Operations:** Zero database drops, truncations, or table resets were performed.
- **Sole Owner Invariant:** `Project 1` sole owner `jun@finregtech.io` (`Jun Chen`, `BUILDER`, `ACTIVE`) is intact.
- **Security Posture:** No authentication bypass, fake responses, or silent database fallbacks were introduced.
