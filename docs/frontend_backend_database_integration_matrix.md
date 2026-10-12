# Frontend-Backend-Database Integration Matrix
## FinRegTech ShipYard | FCC Project Cockpit — ABC Shield Prototype

**Project:** FinRegTech ShipYard — FCC Project Cockpit
**Application Prototype:** ABC Shield for The Compliance Register, UK
**Evaluation Date:** October 13, 2026
**Auditor & Lead Architect:** Vishal (Backend Lead & Database Architect)
**Database Target:** PostgreSQL 18.6 (`"FinRegTech ShipYard"`)
**Status:** **`DATABASE INTEGRATION VERIFIED`**

---

## 1. Executive Matrix Overview

This document provides complete, line-by-line architectural traceability connecting user interactions on the React frontend to the backend REST API endpoints, service operations, and underlying PostgreSQL database tables.

---

## 2. Comprehensive Integration Matrix

| Domain & User Action | Frontend Component | Frontend Service | API Route & Method | Backend Service Function | PostgreSQL Table & Model | SQL / ORM Operation | Transaction Guarantee | Restart Persistence | Status |
|---|---|---|---|---|---|---|---|:---:|:---:|
| **User Sign Up** | `LoginForm.jsx` | `authService.registerUser` | `POST /api/v1/auth/register` | `auth_service.register_user` | `identity.users` (`User`), `identity.roles` (`Role`) | `INSERT INTO identity.users` with bcrypt hash | Atomic transaction commit | **YES** | `VERIFIED` |
| **User Sign In** | `LoginForm.jsx` | `authService.loginUser` | `POST /api/v1/auth/login` | `auth_service.authenticate_user` | `identity.users` (`User`) | `SELECT ... WHERE email = :email` + hash verify | Read-only | **YES** | `VERIFIED` |
| **Fetch Current User** | `DashboardView.jsx` | `authService.getCurrentUser` | `GET /api/v1/users/me` | `get_current_user` dependency | `identity.users` (`User`) | `SELECT ... WHERE user_id = :id` | Read-only | **YES** | `VERIFIED` |
| **Update User Profile** | `SettingsView.jsx` | `userService.updateUserProfile` | `PATCH /api/v1/users/me` | `users.update_me` | `identity.users` (`User`) | `UPDATE identity.users SET full_name = ...` | Atomic commit | **YES** | `VERIFIED` |
| **Create Project** | `DashboardView.jsx` | `projectService.createProject` | `POST /api/v1/projects` | `project_service.create_project` | `project_management.projects` (`Project`), `project_profiles` (`ProjectProfile`), `project_members` (`ProjectMember`) | `INSERT` into `projects`, `profiles`, and `members` (role=OWNER) | Multi-table atomic transaction; rollback on error | **YES** | `VERIFIED` |
| **List Projects** | `DashboardView.jsx` | `projectService.getProjects` | `GET /api/v1/projects` | `project_service.list_user_projects` | `project_management.projects`, `project_members` | `SELECT` joined on `project_members WHERE user_id = :uid` | Read-only | **YES** | `VERIFIED` |
| **View Project Details** | `DashboardView.jsx` | `projectService.getProjectDetails` | `GET /api/v1/projects/{id}` | `project_service.get_project_by_identifier` | `project_management.projects`, `project_profiles` | `SELECT` with numeric ID or string code resolution | Read-only | **YES** | `VERIFIED` |
| **Update Project** | `DashboardView.jsx` | `projectService.updateProject` | `PATCH /api/v1/projects/{id}` | `project_service.update_project` | `project_management.projects`, `project_profiles` | `UPDATE project_management.projects` | Atomic commit | **YES** | `VERIFIED` |
| **List Curated Rules** | `RegulatorySupportView.jsx` | `regulatoryService.getRegulatoryRequirements` | `GET /api/v1/regulatory-requirements` | `regulatory.get_global_regulatory_requirements` | `regulatory.regulatory_sources` (`RegulatorySource`) | `SELECT * FROM regulatory.regulatory_sources` | Read-only | **YES** | `VERIFIED` |
| **Add Requirement** | `DashboardView.jsx` | `adviceService.createProjectRequirement` | `POST /api/v1/projects/{id}/requirements` | `regulatory_service.create_project_requirement` | `regulatory.regulatory_requirements` (`RegulatoryRequirement`) | `INSERT INTO regulatory.regulatory_requirements` | Provenance check + atomic commit | **YES** | `VERIFIED` |
| **List Requirements** | `DashboardView.jsx` | `adviceService.getProjectRequirements` | `GET /api/v1/projects/{id}/requirements` | `regulatory_service.list_project_requirements` | `regulatory.regulatory_requirements` | `SELECT ... WHERE project_id = :pid` | Read-only | **YES** | `VERIFIED` |
| **Update Requirement** | `DashboardView.jsx` | `adviceService.updateRequirement` | `PATCH /api/v1/projects/{id}/requirements/{reqId}` | `regulatory_service.update_project_requirement` | `regulatory.regulatory_requirements` | `UPDATE regulatory.regulatory_requirements` | Atomic commit | **YES** | `VERIFIED` |
| **List Advisors** | `AdvisorsExpertsView.jsx` | `advisorService.getAdvisors` | `GET /api/v1/advisors` | `advisor_service.list_advisors` | `advisor_management.advisor_profiles`, `identity.users` | `SELECT` joined on `identity.users` | Read-only | **YES** | `VERIFIED` |
| **Invite Advisor** | `DashboardView.jsx` | `advisorService.sendAdvisorInvitation` | `POST /api/v1/projects/{id}/advisor-invitations` | `advisor_service.create_advisor_invitation` | `advisor_management.advisor_invitations` (`AdvisorInvitation`) | `INSERT INTO advisor_invitations` + `INSERT project_members` | Atomic multi-table commit | **YES** | `VERIFIED` |
| **List Team Members** | `DashboardView.jsx` | `advisorService.getProjectMembers` | `GET /api/v1/projects/{id}/members` | `member_service.list_project_members` | `project_management.project_members`, `identity.users` | `SELECT ... WHERE project_id = :pid` | Read-only | **YES** | `VERIFIED` |
| **Remove Member** | `DashboardView.jsx` | `advisorService.removeMember` | `DELETE /api/v1/projects/{id}/members/{uid}` | `member_service.remove_project_member` | `project_management.project_members` | `DELETE FROM project_members` | Sole-owner protection check + commit | **YES** | `VERIFIED` |
| **Submit Advice** | `AdvisorDashboardView.jsx` | `adviceService.submitAdvice` | `POST /api/v1/projects/{id}/advice` | `advice_service.create_advice` | `advice.advice` (`Advice`), `advice_source_links` | `INSERT INTO advice.advice` | Emits audit log + atomic commit | **YES** | `VERIFIED` |
| **List Advice** | `DashboardView.jsx` | `adviceService.getProjectAdvice` | `GET /api/v1/projects/{id}/advice` | `advice_service.list_project_advice` | `advice.advice` | `SELECT ... WHERE project_id = :pid` | Read-only | **YES** | `VERIFIED` |
| **Record Decision** | `DashboardView.jsx` | `adviceService.recordDecision` | `POST /api/v1/projects/{id}/decisions` | `decision_service.record_decision` | `decision.decisions` (`Decision`), `audit.audit_events` | `INSERT INTO decision.decisions` | Role check (BUILDER only) + commit | **YES** | `VERIFIED` |
| **List Decisions** | `DashboardView.jsx` | `adviceService.getProjectDecisions` | `GET /api/v1/projects/{id}/decisions` | `decision_service.list_decisions` | `decision.decisions` | `SELECT ... WHERE project_id = :pid` | Read-only | **YES** | `VERIFIED` |
| **Audit Readiness Score** | `DashboardView.jsx` | `adviceService.getProjectReadiness` | `GET /api/v1/projects/{id}/readiness` | `readiness_service.calculate_readiness` | `regulatory_requirements`, `advice`, `decisions` | Aggregate counts: 40% reqs + 30% advice + 30% decisions | Dynamically calculated from live tables | **YES** | `VERIFIED` |
| **Audit Trail Stream** | `DashboardView.jsx` | `auditService.getAuditEvents` | `GET /api/v1/projects/{id}/audit-events` | `audit_service.list_project_audit_events` | `audit.audit_events` (`AuditEvent`) | `SELECT ... WHERE project_id = :pid ORDER BY created_at` | Append-only read | **YES** | `VERIFIED` |
| **RAG Statutory Search** | `DashboardView.jsx` | `apiCall('/rag/analyze')` | `POST /api/v1/rag/analyze` | `ai.analyze_rag` | `regulatory.regulatory_sources` (`RegulatorySource`) | Token-matched search against statutory sources | Read-only (transient search) | **YES** | `VERIFIED` |
| **Admin Stats** | `AdminDashboardView.jsx` | `adminService.getAdminStats` | `GET /api/v1/admin/stats` | `admin.get_admin_stats` | `identity.users`, `projects`, `sources`, `audit_events` | Multiple `SELECT COUNT(*)` across schemas | ADMIN role guard | **YES** | `VERIFIED` |
| **Admin User Directory** | `AdminDashboardView.jsx` | `adminService.getAdminUsers` | `GET /api/v1/admin/users` | `admin.list_admin_users` | `identity.users` | `SELECT * FROM identity.users` | ADMIN role guard | **YES** | `VERIFIED` |
| **Admin User Toggle** | `AdminDashboardView.jsx` | `adminService.updateUserStatus` | `PATCH /api/v1/admin/users/{uid}/status` | `admin.toggle_user_status` | `identity.users` | `UPDATE identity.users SET is_active = :val` | Atomic commit | **YES** | `VERIFIED` |
| **Trusted Ecosystem Tools** | `ToolsView.jsx` | `toolService.toggleToolUsage` | Client-side only | None | None | `localStorage.setItem('ecosystem_tools')` | Browser storage | **N/A (Local)** | `LOCAL_ONLY` |
| **Notification Settings** | `SettingsView.jsx` | `userService.updateNotificationPreferences` | Client-side only | None | None | `localStorage.setItem('userNotificationPreferences')` | Browser storage | **N/A (Local)** | `LOCAL_ONLY` |

---

## 3. Honest Disclosure of Browser-Local Storage (`LOCAL_ONLY`)

The following features deliberately store state in browser storage rather than PostgreSQL:

1. **`authToken` (`localStorage`):** The JSON Web Token issued upon successful login or registration is retained client-side to maintain session persistence across page refreshes. The token is cryptographically signed (HS256) and verified against the backend and database on every HTTP request.
2. **`currentUser` (`localStorage`):** A client-side cache of user display metadata (email, full name, platform role) used to prevent visual layout flicker during page initializations. It is validated against `GET /api/v1/users/me` upon application mount.
3. **`ecosystem_tools` (`localStorage`):** Toggle states for third-party compliance tools in the Tools view (ControlMap, RiskLens, ModelGuard). This operates as a client-side exploratory feature.
4. **`userNotificationPreferences` (`localStorage`):** Toggle preferences for email, browser, and digest notifications in the Settings view.

All other business data — accounts, projects, requirements, advisors, advice, decisions, readiness calculations, and audit trails — are stored exclusively in PostgreSQL.

---

## 4. Multi-Tenant Project Isolation (BOLA / IDOR Defense)

All project-scoped endpoints (`/projects/{projectId}/*`) strictly enforce project boundary checks via FastAPI dependencies:

1. **`require_project_member` Dependency:** Validates that the requesting authenticated user has an active membership record in `project_management.project_members` for the targeted `project_id`.
2. **Rejection Policy:** If an authenticated user belongs to Project A and attempts to access or modify resources in Project B, the API immediately halts execution and returns **HTTP 403 Forbidden**.
3. **Database Integrity:** Denied requests never trigger database mutations.
