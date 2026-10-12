"""
Comprehensive Database Integrity and Baseline Audit Script
FinRegTech ShipYard | FCC Project Cockpit
Inspects physical records, distinguishes baseline team/demo data from test data,
checks referential integrity, and verifies Project 1 (ABC Shield) invariant.
"""

from app.db.session import engine
from sqlalchemy import text

def run_integrity_audit():
    print("=" * 70)
    print("POSTGRESQL DATABASE INTEGRITY & RECORD TAXONOMY AUDIT")
    print("=" * 70)

    with engine.connect() as conn:
        # 1. Project 1 Invariant (ABC Shield Core Demo Project)
        p1 = conn.execute(text(
            "SELECT project_id, project_name, project_code, status, created_by "
            "FROM project_management.projects WHERE project_id = 1"
        )).fetchone()
        print("\n[PROJECT 1 INVARIANT]")
        print(f"  Project ID: {p1[0]}")
        print(f"  Project Name: {p1[1]}")
        print(f"  Project Code: {p1[2]}")
        print(f"  Status: {p1[3]}")
        print(f"  Creator User ID: {p1[4]}")
        assert p1 is not None, "Project 1 is missing!"

        # Project 1 Profile
        prof = conn.execute(text(
            "SELECT project_profile_id, jurisdiction, regulatory_scope "
            "FROM project_management.project_profiles WHERE project_id = 1"
        )).fetchone()
        print(f"  Profile ID: {prof[0]}, Jurisdiction: {prof[1]}, Scope: {prof[2]}")

        # Project 1 Associations
        m_cnt = conn.execute(text("SELECT count(*) FROM project_management.project_members WHERE project_id = 1")).scalar()
        r_cnt = conn.execute(text("SELECT count(*) FROM regulatory.regulatory_requirements WHERE project_id = 1")).scalar()
        a_cnt = conn.execute(text("SELECT count(*) FROM advice.advice WHERE project_id = 1")).scalar()
        d_cnt = conn.execute(text("SELECT count(*) FROM decision.decisions WHERE project_id = 1")).scalar()
        print(f"  Project 1 Members: {m_cnt}")
        print(f"  Project 1 Regulatory Requirements: {r_cnt}")
        print(f"  Project 1 Advisory Reviews: {a_cnt}")
        print(f"  Project 1 Ratified Decisions: {d_cnt}")

        # 2. User Taxonomy: Demo Users vs Test Users
        print("\n[USER TAXONOMY]")
        total_users = conn.execute(text("SELECT count(*) FROM identity.users")).scalar()
        demo_users = conn.execute(text(
            "SELECT user_id, email, full_name, role_id, is_active "
            "FROM identity.users "
            "WHERE email IN ('builder@shipyard.io', 'advisor@advisory.io', 'admin@shipyard.io', 'jun@finregtech.io', 'eleanor.vance@vancelegal.co.uk') "
            "ORDER BY user_id ASC"
        )).fetchall()
        print(f"  Total Users in Database: {total_users}")
        print(f"  Core Baseline Demo Users ({len(demo_users)}):")
        for u in demo_users:
            role = conn.execute(text("SELECT role_name FROM identity.roles WHERE role_id = :rid"), {"rid": u[3]}).scalar()
            print(f"    - ID {u[0]}: {u[1]} ({u[2]}) | Role: {role} | Active: {u[4]}")

        # Categorize remaining users
        test_audit_users = conn.execute(text("SELECT count(*) FROM identity.users WHERE email LIKE 'audit_%'")).scalar()
        test_browser_users = conn.execute(text("SELECT count(*) FROM identity.users WHERE email LIKE 'browser_%'")).scalar()
        test_pytest_users = conn.execute(text("SELECT count(*) FROM identity.users WHERE email LIKE 'pytest_%' OR email LIKE 'lead_%' OR email LIKE 'dup_%' OR email LIKE 'login_%' OR email LIKE 'owner_%' OR email LIKE 'outsider_%'")).scalar()
        other_team_users = total_users - len(demo_users) - test_audit_users - test_browser_users - test_pytest_users
        print(f"  User Distribution Breakdown:")
        print(f"    - Baseline Demo Users: {len(demo_users)}")
        print(f"    - Audit Runner Users (audit_*): {test_audit_users}")
        print(f"    - Browser Acceptance Users (browser_*): {test_browser_users}")
        print(f"    - Pytest Generated Users (pytest_*, etc.): {test_pytest_users}")
        print(f"    - Other Pre-existing Team/Dev Accounts: {other_team_users}")

        # 3. Project Taxonomy
        print("\n[PROJECT TAXONOMY]")
        total_projects = conn.execute(text("SELECT count(*) FROM project_management.projects")).scalar()
        test_projects = conn.execute(text("SELECT count(*) FROM project_management.projects WHERE project_code LIKE 'PRJ-AUDIT-%' OR project_code LIKE 'PRJ-TST-%' OR project_code LIKE 'PRJ-PRIV-%' OR project_code LIKE 'PRJ-E2E%'")).scalar()
        team_projects = total_projects - test_projects
        print(f"  Total Projects in Database: {total_projects}")
        print(f"  Pre-existing Team / Seed Projects: {team_projects}")
        print(f"  Test-Generated Projects: {test_projects}")

        # 4. Foreign Key and Referential Integrity Checks
        print("\n[REFERENTIAL INTEGRITY CHECKS]")
        # Orphaned project members?
        orphaned_members = conn.execute(text(
            "SELECT count(*) FROM project_management.project_members pm "
            "LEFT JOIN project_management.projects p ON pm.project_id = p.project_id "
            "WHERE p.project_id IS NULL"
        )).scalar()
        print(f"  Orphaned Project Members (no project): {orphaned_members} (Expected: 0)")
        assert orphaned_members == 0, "Orphaned project members detected!"

        # Orphaned requirements?
        orphaned_reqs = conn.execute(text(
            "SELECT count(*) FROM regulatory.regulatory_requirements r "
            "LEFT JOIN project_management.projects p ON r.project_id = p.project_id "
            "WHERE p.project_id IS NULL"
        )).scalar()
        print(f"  Orphaned Requirements (no project): {orphaned_reqs} (Expected: 0)")
        assert orphaned_reqs == 0, "Orphaned requirements detected!"

        # Orphaned advice?
        orphaned_advice = conn.execute(text(
            "SELECT count(*) FROM advice.advice a "
            "LEFT JOIN project_management.projects p ON a.project_id = p.project_id "
            "WHERE p.project_id IS NULL"
        )).scalar()
        print(f"  Orphaned Advice (no project): {orphaned_advice} (Expected: 0)")
        assert orphaned_advice == 0, "Orphaned advice detected!"

        # Orphaned decisions?
        orphaned_decisions = conn.execute(text(
            "SELECT count(*) FROM decision.decisions d "
            "LEFT JOIN project_management.projects p ON d.project_id = p.project_id "
            "WHERE p.project_id IS NULL"
        )).scalar()
        print(f"  Orphaned Decisions (no project): {orphaned_decisions} (Expected: 0)")
        assert orphaned_decisions == 0, "Orphaned decisions detected!"

        # True orphaned audit events (where project_id is NOT NULL but project does not exist)
        orphaned_audits = conn.execute(text(
            "SELECT count(*) FROM audit.audit_events ae "
            "LEFT JOIN project_management.projects p ON ae.project_id = p.project_id "
            "WHERE ae.project_id IS NOT NULL AND p.project_id IS NULL"
        )).scalar()
        platform_events = conn.execute(text(
            "SELECT count(*) FROM audit.audit_events WHERE project_id IS NULL"
        )).scalar()
        print(f"  Platform-level Audit Events (project_id IS NULL, e.g. USER_REGISTERED): {platform_events}")
        print(f"  True Orphaned Audit Events (invalid project_id): {orphaned_audits} (Expected: 0)")
        assert orphaned_audits == 0, "Orphaned audit events detected!"

        # 5. Curated Regulatory Corpus Integrity
        print("\n[CURATED REGULATORY SOURCES INTEGRITY]")
        sources_cnt = conn.execute(text("SELECT count(*) FROM regulatory.regulatory_sources")).scalar()
        validated_cnt = conn.execute(text("SELECT count(*) FROM regulatory.regulatory_sources WHERE validation_status = 'VALIDATED'")).scalar()
        print(f"  Total Curated Rulebooks: {sources_cnt}")
        print(f"  Validated Sources: {validated_cnt}")
        assert sources_cnt == 27, f"Expected 27 curated sources, found {sources_cnt}"

        print("\n" + "=" * 70)
        print("DATABASE INTEGRITY AUDIT: 100% HEALTHY, ZERO CORRUPTION, ZERO ORPHANS")
        print("=" * 70)

if __name__ == "__main__":
    run_integrity_audit()
