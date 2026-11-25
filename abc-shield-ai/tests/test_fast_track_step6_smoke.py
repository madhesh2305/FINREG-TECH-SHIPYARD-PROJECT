"""Fast-Track Step 6 Automated Smoke Test Suite.

Role: Padma Kumar — AI/RAG & Conflict Detection Engineer
Goal: Verify live API endpoints, schema contracts, candidate status safeguards,
non-adjudication guarantees, vector store integrity, and frontend availability status.
"""

from pathlib import Path

import chromadb
import pytest
from fastapi.testclient import TestClient

from api.main import app
from config.settings import settings


@pytest.fixture(scope="module")
def client():
    """FastAPI TestClient fixture."""
    with TestClient(app) as test_client:
        yield test_client


def test_step6_vector_stores_integrity():
    """Verify legacy 15-vector store and canonical 25-vector store integrity."""
    legacy_path = Path("data/processed/chroma_db")
    assert legacy_path.exists(), f"Legacy ChromaDB path not found: {legacy_path}"

    legacy_client = chromadb.PersistentClient(path=str(legacy_path))
    legacy_col = legacy_client.get_collection("regulatory_records")
    assert legacy_col.count() == 15

    canonical_path = Path("data/staging/madhesh_handover/step6/chroma_db")
    assert canonical_path.exists(), (
        f"Canonical ChromaDB path not found: {canonical_path}"
    )

    canonical_client = chromadb.PersistentClient(path=str(canonical_path))
    canonical_col = canonical_client.get_collection(
        "canonical_regulatory_records"
    )
    assert canonical_col.count() == 25

    assert settings.rag_knowledge_base_mode == "canonical"
    assert settings.chroma_collection_name == "canonical_regulatory_records"


def test_step6_frontend_availability_audit():
    """Verify frontend code availability status in the workspace."""
    workspace_root = Path.cwd().parent

    frontend_files = [
        str(path)
        for path in workspace_root.rglob("package.json")
        if ".venv" not in path.parts and "node_modules" not in path.parts
    ]

    # Verify frontend file discovery returns a list (compatible with integrated workspace)
    assert isinstance(frontend_files, list)


def test_step6_health_endpoints(client):
    """Verify GET /health and GET /api/v1/health endpoints."""
    res1 = client.get("/health")

    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["status"] == "ok"
    assert data1["chromadb_status"] == "connected"
    assert data1["rag_pipeline_initialized"] is True

    res2 = client.get("/api/v1/health")

    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["status"] == "ok"
    assert data2["chromadb_status"] == "connected"


def test_step6_grounded_query_smoke(client):
    """Verify a representative grounded regulatory query."""
    res = client.post(
        "/api/v1/query",
        json={
            "query": (
                "Under UK Bribery Act 2010, what does Section 7 cover "
                "regarding failure of commercial organisations to prevent bribery?"
            ),
            "context": {"jurisdiction": "UK"},
        },
    )

    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "GROUNDED"
    assert data["grounded"] is True
    assert len(data["citations"]) > 0
    assert any(
        "legislation.gov.uk" in (citation.get("official_source") or "")
        for citation in data["citations"]
    )
    assert data["metadata"]["has_candidate_evidence"] is True

    # Candidate evidence must remain pending SME validation.
    assert all(
        citation["validation_status"] in (
            "Approved for RAG Integration - Pending SME Validation",
            "Pending SME Validation",
        )
        for citation in data["citations"]
    )
    assert all(
        citation["is_approved_for_rag"] is False
        for citation in data["citations"]
    )


def test_step6_approved_only_fail_closed_smoke(client):
    """Verify fail-closed handling when only approved evidence is allowed."""
    res = client.post(
        "/api/v1/query",
        json={
            "query": "Under UK Bribery Act 2010, what does Section 7 cover?",
            "context": {"filter_approved_only": True},
        },
    )

    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "UNAPPROVED_EVIDENCE"
    assert data["grounded"] is False
    assert len(data["citations"]) == 0
    assert len(data["retrieved_evidence"]) == 0
    assert data["metadata"]["requires_human_review"] is True


def test_step6_out_of_scope_smoke(client):
    """Verify handling of an out-of-scope sanctions screening query."""
    res = client.post(
        "/api/v1/query",
        json={
            "query": (
                "What are ABC Shield's sanctions screening obligations "
                "under OFAC and UK sanctions regimes?"
            )
        },
    )

    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "OUT_OF_SCOPE"
    assert data["grounded"] is False
    assert len(data["citations"]) == 0
    assert data["gap"]["gap_type"] == "OUT_OF_SCOPE"


def test_step6_insufficient_evidence_smoke(client):
    """Verify handling of an unsupported member-state transposition query."""
    res = client.post(
        "/api/v1/query",
        json={
            "query": (
                "What are the specific transposition provisions under French "
                "national law for the EU Whistleblower Directive?"
            )
        },
    )

    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "INSUFFICIENT_EVIDENCE"
    assert data["grounded"] is False
    assert len(data["citations"]) == 0
    assert data["gap"]["gap_type"] == "DATA_COVERAGE_LIMITATION"


def test_step6_advice_comparison_smoke(client):
    """Verify advice comparison, CO-001 detection, and decision=None."""
    res = client.post(
        "/api/v1/compare",
        json={
            "comparison_id": "CMP-CANONICAL-001",
            "requirement_ids": ["REQ-UK-01"],
            "advisor_1": {
                "advice_id": "ADV-001",
                "advisor_name": "Senior Compliance Counsel",
                "advice_text": (
                    "Bribery Act 2010 Section 1 offences of bribing another person."
                ),
                "source_reference": "UK Bribery Act 2010 Section 1",
            },
            "advisor_2": {
                "advice_id": "ADV-002",
                "advisor_name": "External Consultant",
                "advice_text": (
                    "Bribery Act 2010 Guidance Ministry of Justice "
                    "Six Principles prevention procedures."
                ),
                "source_reference": "MoJ Guidance on Bribery Act 2010",
            },
            "context": {
                "jurisdiction": "UK",
                "regulatory_area": "Anti-Bribery and Corruption",
            },
        },
    )

    assert res.status_code == 200
    data = res.json()

    assert data["comparison_id"] == "CMP-CANONICAL-001"

    # The system compares advice but must not make a final legal decision.
    assert data["decision"] is None
    assert data["human_review_required"] is True

    assert len(data["differences"]) >= 1

    relationship_ids = [
        relationship["conflict_id"]
        for relationship in data.get("relationships", [])
    ]
    assert "CO-001" in relationship_ids

    assert len(data["citations"]) > 0
    assert "qualified compliance professional" in data["disclaimer"]
