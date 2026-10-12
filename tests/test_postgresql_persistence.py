"""
Automated PostgreSQL Persistence and Transaction Integrity Test Suite
Verifies real persistence across all 5 schemas in PostgreSQL ("FinRegTech ShipYard").
"""

import time
import pytest
from datetime import datetime, timezone
from sqlalchemy import text
from app.db.session import engine, SessionLocal
from app.models.identity import User, Role
from app.models.project import Project, ProjectMember
from app.models.regulatory import RegulatoryRequirement, RegulatorySource
from app.models.decision import Decision
from app.models.audit import AuditEvent

def test_db_dialect_is_strictly_postgresql():
    """Verify that the active engine dialect is PostgreSQL, not SQLite."""
    with engine.connect() as conn:
        dialect = engine.dialect.name
        assert dialect == "postgresql", f"Forbidden dialect: {dialect}. FinRegTech ShipYard must run on PostgreSQL."

def test_registration_persists_bcrypt_hash(client):
    """Verify that user registration writes directly to identity.users with bcrypt hashing."""
    suffix = int(time.time() * 1000)
    email = f"pytest_user_{suffix}@shipyard.io"
    password = f"TestPass_{suffix}!Secure"
    full_name = f"Pytest Persisted User {suffix}"

    res = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "full_name": full_name,
        "role": "BUILDER"
    })
    assert res.status_code == 201
    user_id = res.json()["user_id"]

    # Verify directly in PostgreSQL
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        assert user is not None
        assert user.email == email.lower()
        assert user.full_name == full_name
        assert user.is_active is True
        assert user.password_hash.startswith("$2b$") or user.password_hash.startswith("$2a$")
        assert password not in user.password_hash
    finally:
        db.close()

def test_duplicate_registration_rejected(client):
    """Verify that duplicate email registration fails with HTTP 409 and does not alter database."""
    suffix = int(time.time() * 1000)
    email = f"dup_user_{suffix}@shipyard.io"
    payload = {
        "email": email,
        "password": "Password123!",
        "full_name": "First User",
        "role": "BUILDER"
    }
    r1 = client.post("/api/v1/auth/register", json=payload)
    assert r1.status_code == 201

    r2 = client.post("/api/v1/auth/register", json=payload)
    assert r2.status_code == 409

    # Verify only 1 record exists in PostgreSQL
    db = SessionLocal()
    try:
        count = db.query(User).filter(User.email == email.lower()).count()
        assert count == 1
    finally:
        db.close()

def test_login_validates_persisted_hash(client):
    """Verify that login authenticates against the persisted bcrypt hash."""
    suffix = int(time.time() * 1000)
    email = f"login_user_{suffix}@shipyard.io"
    password = f"CorrectPass_{suffix}!"
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Login Tester",
        "role": "BUILDER"
    })

    # Good login
    good_res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert good_res.status_code == 200
    assert "access_token" in good_res.json()

    # Bad login
    bad_res = client.post("/api/v1/auth/login", json={"email": email, "password": "WrongPassword!"})
    assert bad_res.status_code == 401

def test_project_lifecycle_writes_to_postgresql(client):
    """Verify that project creation, requirements, and decisions persist in PostgreSQL."""
    suffix = int(time.time() * 1000)
    builder_email = f"lead_{suffix}@shipyard.io"
    builder_pwd = f"Pass_{suffix}!"
    reg = client.post("/api/v1/auth/register", json={
        "email": builder_email,
        "password": builder_pwd,
        "full_name": "Project Lead",
        "role": "BUILDER"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create project
    proj_code = f"PRJ-TST-{suffix % 10000}"
    p_res = client.post("/api/v1/projects", headers=headers, json={
        "name": f"Test Project {suffix}",
        "code": proj_code,
        "type": "Anti-Bribery & Corruption (ABC)",
        "description": "Integration test project"
    })
    assert p_res.status_code == 201
    project_id = p_res.json()["project_id"]

    # Verify project in PostgreSQL
    db = SessionLocal()
    try:
        proj = db.query(Project).filter(Project.project_id == project_id).first()
        assert proj is not None
        assert proj.project_code == proj_code

        # Add Requirement
        r_res = client.post(f"/api/v1/projects/{project_id}/requirements", headers=headers, json={
            "source_id": 1,
            "requirement_code": f"REQ-T-{suffix % 1000}",
            "requirement_title": "Test Requirement",
            "requirement_text": "Text for test requirement."
        })
        assert r_res.status_code == 201
        req_id = r_res.json()["requirement_id"]

        req = db.query(RegulatoryRequirement).filter(RegulatoryRequirement.requirement_id == req_id).first()
        assert req is not None
        assert req.project_id == project_id

        # Record Decision
        d_res = client.post(f"/api/v1/projects/{project_id}/decisions", headers=headers, json={
            "decision_type": "ACCEPT",
            "decision_rationale": "Test Decision Rationale."
        })
        assert d_res.status_code == 201
        dec_id = d_res.json()["decision_id"]

        dec = db.query(Decision).filter(Decision.decision_id == dec_id).first()
        assert dec is not None
        assert dec.project_id == project_id

        # Verify Audit Log entry in PostgreSQL
        audit = db.query(AuditEvent).filter(AuditEvent.project_id == project_id).all()
        assert len(audit) >= 3
    finally:
        db.close()

def test_project_isolation_bola_defense(client):
    """Verify that outsider users are blocked from accessing another project's records."""
    suffix = int(time.time() * 1000)
    # Register Owner
    owner_reg = client.post("/api/v1/auth/register", json={
        "email": f"owner_{suffix}@test.io",
        "password": "Password123!",
        "full_name": "Project Owner",
        "role": "BUILDER"
    })
    owner_token = owner_reg.json()["access_token"]
    p_res = client.post("/api/v1/projects", headers={"Authorization": f"Bearer {owner_token}"}, json={
        "name": f"Private Project {suffix}",
        "code": f"PRJ-PRIV-{suffix % 1000}",
        "type": "Anti-Bribery & Corruption (ABC)"
    })
    project_id = p_res.json()["project_id"]

    # Register Outsider
    outsider_reg = client.post("/api/v1/auth/register", json={
        "email": f"outsider_{suffix}@test.io",
        "password": "Password123!",
        "full_name": "Outsider",
        "role": "BUILDER"
    })
    outsider_token = outsider_reg.json()["access_token"]
    outsider_headers = {"Authorization": f"Bearer {outsider_token}"}

    # Outsider requests
    assert client.get(f"/api/v1/projects/{project_id}", headers=outsider_headers).status_code == 403
    assert client.get(f"/api/v1/projects/{project_id}/requirements", headers=outsider_headers).status_code == 403
    assert client.get(f"/api/v1/projects/{project_id}/decisions", headers=outsider_headers).status_code == 403
    assert client.get(f"/api/v1/projects/{project_id}/audit-events", headers=outsider_headers).status_code == 403
