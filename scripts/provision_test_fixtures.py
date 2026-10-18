"""
FINREGTECH SHIPYARD — SAFE TEST FIXTURE PROVISIONING SCRIPT
Provisions synthetic test personas, projects, requirements, advice, and decisions
strictly in 'finregtech_test'. Refuses to execute against any other database.
"""
import os
import sys
from datetime import date, datetime, timezone
from urllib.parse import unquote
from sqlalchemy.engine import make_url

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, backend_dir)

from pydantic_settings import BaseSettings, SettingsConfigDict

class BootstrapConfig(BaseSettings):
    TEST_DATABASE_URL: str | None = None
    model_config = SettingsConfigDict(
        env_file=[os.path.join(backend_dir, ".env"), ".env"],
        env_file_encoding="utf-8",
        extra="ignore"
    )

def provision_fixtures():
    # 1. Resolve and validate test database URL
    cfg = BootstrapConfig()
    test_url = os.getenv("TEST_DATABASE_URL") or cfg.TEST_DATABASE_URL
    if not test_url:
        print("FATAL: TEST_DATABASE_URL is not configured!", file=sys.stderr)
        sys.exit(1)

    parsed = make_url(test_url)
    db_name = unquote(parsed.database or "").strip()

    # Strict Fail-Closed Guard
    if db_name.lower() == "finregtech shipyard" or "shipyard" in db_name.lower():
        print("CRITICAL SECURITY ALERT: Provisioning script detected primary database! Refusing to run.", file=sys.stderr)
        sys.exit(1)

    if db_name != "finregtech_test":
        print(f"FATAL: Database name '{db_name}' is not 'finregtech_test'. Aborting.", file=sys.stderr)
        sys.exit(1)

    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    if parsed.database and "%20" in parsed.database:
        parsed = parsed.set(database=unquote(parsed.database))
    test_engine = create_engine(parsed, pool_pre_ping=True)

    # Live handshake verification
    with test_engine.connect() as conn:
        active_db = conn.execute(text("SELECT current_database()")).scalar()
        if active_db != "finregtech_test":
            print(f"FATAL: Live connection resolved to '{active_db}', expected 'finregtech_test'!", file=sys.stderr)
            sys.exit(1)

    # Override process environment so imports use test database
    os.environ["DATABASE_URL"] = test_url
    os.environ["ENVIRONMENT"] = "manual_test"

    from app.db.base import Base
    import app.models  # Register domain models
    from app.models.identity import Role, User
    from app.models.advisor import AdvisorProfile
    from app.models.project import Project, ProjectProfile, ProjectMember
    from app.models.regulatory import RegulatorySource, RegulatoryRequirement
    from app.models.advice import Advice
    from app.models.decision import Decision
    from app.core.security import get_password_hash
    from scripts.seed_data import seed_database

    TestSession = sessionmaker(bind=test_engine)
    session = TestSession()

    try:
        # Run base seed to ensure roles, curated sources, and initial seed users exist
        Base.metadata.create_all(bind=test_engine)
        seed_database(session_override=session, engine_override=test_engine)

        # 2. Ensure Marcus Reid is also an active member of Project 1 (for multi-advisor testing)
        proj1 = session.query(Project).filter(Project.project_code == "PRJ-ABC-001").first()
        marcus = session.query(User).filter(User.email == "marcus.reid@fccconsulting.eu").first()
        eleanor = session.query(User).filter(User.email == "eleanor.vance@vancelegal.co.uk").first()

        if proj1 and marcus:
            marcus_mem = session.query(ProjectMember).filter(
                ProjectMember.project_id == proj1.project_id,
                ProjectMember.user_id == marcus.user_id
            ).first()
            if not marcus_mem:
                session.add(ProjectMember(
                    project_id=proj1.project_id,
                    user_id=marcus.user_id,
                    service_role="REGULATORY",
                    service_scope="ADVISORY_REVIEW",
                    member_status="ACTIVE",
                    joined_at=datetime.now(timezone.utc)
                ))
                session.flush()
                print(f"Added Marcus Reid ({marcus.email}) as active REGULATORY member of Project 1.")

        # 3. Ensure Marcus Reid has advice submitted on Project 1 (for multi-advisor comparison W6-ADV-03)
        if proj1 and marcus:
            marcus_profile = session.query(AdvisorProfile).filter(AdvisorProfile.user_id == marcus.user_id).first()
            if marcus_profile:
                existing_adv = session.query(Advice).filter(
                    Advice.project_id == proj1.project_id,
                    Advice.advisor_profile_id == marcus_profile.advisor_profile_id
                ).first()
                if not existing_adv:
                    session.add(Advice(
                        project_id=proj1.project_id,
                        advisor_profile_id=marcus_profile.advisor_profile_id,
                        title="Automated Transaction Velocity Monitoring & SAR Assurance",
                        advice_text="Implement real-time threshold scoring and dual-analyst review before SAR filings under POCA section 330.",
                        recommendation="Set automated payment hold threshold at £5,000 for unverified accounts.",
                        assumptions="Aligned with SYSC 6.3.7R risk appetite guidelines.",
                        advice_status="SUBMITTED",
                        submitted_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    ))
                    session.flush()
                    print(f"Added Marcus Reid advice on Project 1 for multi-advisor comparison.")

        # 4. Ensure Project 2 (PRJ-001) has a requirement for BOLA / IDOR tests (W6-ISO-03)
        proj2 = session.query(Project).filter(Project.project_code == "PRJ-001").first()
        if proj2:
            req_b = session.query(RegulatoryRequirement).filter(
                RegulatoryRequirement.project_id == proj2.project_id,
                RegulatoryRequirement.requirement_code == "REQ-BETA-001"
            ).first()
            if not req_b:
                first_src = session.query(RegulatorySource).first()
                if first_src:
                    session.add(RegulatoryRequirement(
                        project_id=proj2.project_id,
                        source_id=first_src.source_id,
                        requirement_code="REQ-BETA-001",
                        requirement_title="Beta Secret Requirement (Project 2)",
                        requirement_text="Confidential security specification belonging strictly to Project 2.",
                        applicability_status="APPLICABLE",
                        requirement_status="OPEN",
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    ))
                    session.flush()
                    print(f"Added REQ-BETA-001 in Project 2 for BOLA/IDOR isolation testing.")

        session.commit()
        print("=" * 80)
        print("  TEST FIXTURES PROVISIONED SUCCESSFULLY IN 'finregtech_test'")
        print("=" * 80)
        print("  Synthetic Personas Active:")
        print("    P-BLD-01 (Builder) : jun@finregtech.io (Owner of Project 1 'PRJ-ABC-001')")
        print("    P-BLD-02 (Builder) : builder@gmail.com (Owner of Project 2 'PRJ-001', Outsider to Project 1)")
        print("    P-ADV-01 (Advisor) : eleanor.vance@vancelegal.co.uk (Active Advisor on Project 1)")
        print("    P-ADV-02 (Advisor) : marcus.reid@fccconsulting.eu (Active Advisor on Project 1)")
        print("    P-ADV-EXT (Advisor): advisor@gmail.com (Outsider Advisor to Project 1)")
        print("    P-ADM-01 (Admin)   : admin@finregtech.io (Platform Administrator)")
        print("    P-OUT-01 (Outsider): outsider@finregtech.io (Outsider Builder)")
        print("=" * 80)

    except Exception as e:
        session.rollback()
        print(f"Error provisioning fixtures: {e}", file=sys.stderr)
        raise
    finally:
        session.close()
        test_engine.dispose()

if __name__ == "__main__":
    provision_fixtures()
