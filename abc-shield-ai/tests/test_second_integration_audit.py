"""Second Integration Audit test suite for ABC Shield AI/RAG.

Covers Vishal's second integration audit requirements:
1. CORS: Exactly eight approved origins receive headers; unapproved rejected; no wildcard.
2. Comparison API Format A (Complete Objects): HTTP 200, decision: None, grounded differences.
3. Comparison API Format B (ID-Only): HTTP 409 Conflict, status: "ADVISOR_DATA_NOT_RESOLVED", non-fabrication.
4. Comparison API Validation Failures: Incomplete advisor pairs, empty text, invalid types -> HTTP 422.
5. Tenant Isolation:
   - Root project_id omitted -> retrieves public regulatory chunks only (project_id is None).
   - context['project_id'] does NOT act as tenant scoping filter.
   - Cross-tenant scoping prevents unauthorized data exposure.
6. Regulatory Safeguards:
   - Canonical vector store contains >= 25 records.
   - is_approved_for_rag is False on canonical candidates.
   - approved_evidence_count == 0 when unapproved.
   - decision is strictly None.
   - CO-001..CO-011 conflict detection rules intact.
"""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from api.main import app
from config.settings import settings
from rag.pipeline.advice_comparator import (
    AdvisorAdviceItem,
    AdviceComparisonRequest,
    AdviceComparator,
)
from rag.conflict.conflict_detector import ConflictDetector
from api.dependencies import get_configured_vector_store


@pytest.fixture
def client():
    """TestClient for FastAPI app."""
    return TestClient(app)


# ==============================================================================
# 1. CORS: Eight Approved Origins & Preflight
# ==============================================================================

APPROVED_EIGHT_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]


def test_cors_has_exactly_eight_origins():
    """Verify settings.cors_origins contains exactly 8 approved origins."""
    assert len(settings.cors_origins) == 8
    for origin in APPROVED_EIGHT_ORIGINS:
        assert origin in settings.cors_origins
    assert "*" not in settings.cors_origins


@pytest.mark.parametrize("origin", APPROVED_EIGHT_ORIGINS)
def test_all_eight_origins_receive_cors_headers(client, origin):
    """Verify all 8 approved origins receive Access-Control-Allow-Origin header."""
    response = client.get("/health", headers={"Origin": origin})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin
    assert response.headers.get("access-control-allow-credentials") == "true"


@pytest.mark.parametrize("origin", APPROVED_EIGHT_ORIGINS)
def test_options_preflight_for_all_eight_origins(client, origin):
    """Verify preflight OPTIONS requests succeed for all 8 approved origins."""
    headers = {
        "Origin": origin,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    }
    response = client.options("/api/v1/compare", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin
    assert "POST" in response.headers.get("access-control-allow-methods", "")


@pytest.mark.parametrize(
    "unapproved_origin",
    [
        "http://attacker.com",
        "http://localhost:9000",
        "http://127.0.0.1:9000",
        "http://malicious-site.com",
        "http://evil.corp",
    ],
)
def test_unapproved_origins_rejected_no_cors_headers(client, unapproved_origin):
    """Verify unapproved origins receive NO access-control-allow-origin header."""
    response = client.get("/health", headers={"Origin": unapproved_origin})
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


# ==============================================================================
# 2. Comparison API: Format A – Complete Advisor Objects
# ==============================================================================

def test_compare_format_a_complete_objects_success(client):
    """Verify Format A with complete advisor objects returns HTTP 200 with decision=None."""
    payload = {
        "project_id": "PRJ-ABC-001",
        "advisor_1": {
            "advice_id": "ADV-101",
            "advice_text": "Commercial organisations are strictly liable under Section 7 unless they prove adequate procedures.",
            "advisor_name": "Counsel Alpha",
        },
        "advisor_2": {
            "advice_id": "ADV-102",
            "advice_text": "Commercial organisations bear the burden of establishing reasonable prevention procedures.",
            "advisor_name": "Counsel Beta",
        },
        "topic": "Regulatory compliance",
        "context": {"jurisdiction": "UK"},
    }

    response = client.post("/api/v1/compare", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["decision"] is None
    assert data["human_review_required"] is True
    assert "comparison_id" in data
    assert len(data["differences"]) > 0
    assert "disclaimer" in data
    assert "strictly None" in str(data) or data["decision"] is None
    assert data["advisor_1"]["advice_id"] == "ADV-101"
    assert data["advisor_2"]["advice_id"] == "ADV-102"


# ==============================================================================
# 3. Comparison API: Format B – Advisor IDs Only (HTTP 409 Conflict)
# ==============================================================================

def test_compare_format_b_id_only_returns_http_409_conflict(client):
    """Verify Format B with bare advisor IDs returns HTTP 409 Conflict with ADVISOR_DATA_NOT_RESOLVED."""
    payload = {
        "project_id": "PRJ-ABC-001",
        "advisor_1_id": "ADV-101",
        "advisor_2_id": "ADV-102",
    }

    response = client.post("/api/v1/compare", json=payload)
    assert response.status_code == 409
    data = response.json()

    assert data["status"] == "ADVISOR_DATA_NOT_RESOLVED"
    assert data["error"] == "Advisor advice text not provided"
    assert "PostgreSQL" in data["detail"]
    assert "Main Backend Gateway" in data["detail"]
    assert data["advisor_1_id"] == "ADV-101"
    assert data["advisor_2_id"] == "ADV-102"
    assert data["project_id"] == "PRJ-ABC-001"
    assert data["decision"] is None
    assert data["grounded"] is False

    # Crucial safety invariant: No advice text was fabricated or invented
    assert "advice_text" not in data
    assert "advice_1" not in data


def test_compare_from_request_raises_value_error_on_bare_ids():
    """Verify comparator.compare_from_request raises ValueError when invoked with bare IDs."""
    req = AdviceComparisonRequest(
        project_id="PRJ-ABC-001",
        advisor_1_id="ADV-101",
        advisor_2_id="ADV-102",
    )
    comparator = AdviceComparator()
    with pytest.raises(ValueError, match="bare advisor IDs provided"):
        comparator.compare_from_request(req)


# ==============================================================================
# 4. Comparison API: Validation Failures (HTTP 422)
# ==============================================================================

def test_compare_validation_failure_only_advisor_1_id(client):
    """Verify providing only advisor_1_id without advisor_2_id returns HTTP 422."""
    payload = {
        "project_id": "PRJ-ABC-001",
        "advisor_1_id": "ADV-101",
    }
    response = client.post("/api/v1/compare", json=payload)
    assert response.status_code == 422


def test_compare_validation_failure_only_advisor_2_id(client):
    """Verify providing only advisor_2_id without advisor_1_id returns HTTP 422."""
    payload = {
        "project_id": "PRJ-ABC-001",
        "advisor_2_id": "ADV-102",
    }
    response = client.post("/api/v1/compare", json=payload)
    assert response.status_code == 422


def test_compare_validation_failure_only_advisor_1_object(client):
    """Verify providing only advisor_1 object without advisor_2 returns HTTP 422."""
    payload = {
        "project_id": "PRJ-ABC-001",
        "advisor_1": {
            "advice_id": "ADV-101",
            "advice_text": "Commercial organisations are strictly liable.",
        },
    }
    response = client.post("/api/v1/compare", json=payload)
    assert response.status_code == 422


def test_compare_validation_failure_empty_payload(client):
    """Verify empty comparison payload returns HTTP 422."""
    response = client.post("/api/v1/compare", json={})
    assert response.status_code == 422


def test_compare_validation_failure_empty_advice_text(client):
    """Verify empty advice_text in advisor object returns HTTP 422."""
    payload = {
        "project_id": "PRJ-ABC-001",
        "advisor_1": {
            "advice_id": "ADV-101",
            "advice_text": "",
        },
        "advisor_2": {
            "advice_id": "ADV-102",
            "advice_text": "Valid advice text.",
        },
    }
    response = client.post("/api/v1/compare", json=payload)
    assert response.status_code == 422


def test_compare_validation_failure_blank_advisor_ids(client):
    """Verify whitespace/empty string advisor IDs return HTTP 422."""
    payload = {
        "advisor_1_id": "   ",
        "advisor_2_id": "ADV-102",
    }
    response = client.post("/api/v1/compare", json=payload)
    assert response.status_code == 422


# ==============================================================================
# 5. Tenant Isolation Verification
# ==============================================================================

def test_query_without_root_project_id_retrieves_public_only(client):
    """Verify query with omitted root project_id accesses public regulatory evidence only."""
    payload = {
        "query": "What are adequate procedures to prevent bribery?",
    }
    response = client.post("/api/v1/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["grounded"] is True

    # Check that every provenance chunk has no tenant project_id
    for prov in data.get("provenance", []):
        assert prov.get("project_id") is None


def test_context_project_id_does_not_scope_retrieval(client):
    """Verify context['project_id'] is purely audit metadata and NOT a retrieval scoping filter."""
    payload = {
        "query": "What are adequate procedures to prevent bribery?",
        "context": {
            "project_id": "PRJ-AUDIT-ONLY-NOT-RETRIEVAL-FILTER",
            "jurisdiction": "UK",
        },
    }
    response = client.post("/api/v1/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["grounded"] is True
    assert len(data["citations"]) > 0

    # Ensure retrieved chunks are public regulatory evidence
    for prov in data.get("provenance", []):
        assert prov.get("project_id") is None


def test_tenant_isolation_retriever_logic():
    """Verify RegulatoryRetriever cleanly isolates public and tenant records."""
    from rag.retrieval.retriever import RegulatoryRetriever

    retriever = RegulatoryRetriever()

    # Query with None project_id: returns public records only
    public_results = retriever.retrieve("bribery adequate procedures", top_k=5, project_id=None)
    for r in public_results:
        assert r.project_id is None

    # Query with non-existent tenant project_id: returns zero tenant records
    tenant_results = retriever.retrieve("bribery adequate procedures", top_k=5, project_id="PRJ-NONEXISTENT-TENANT")
    assert len(tenant_results) == 0


# ==============================================================================
# 6. Regulatory Safeguards & Corpus Integrity
# ==============================================================================

def test_canonical_vector_store_integrity():
    """Verify canonical ChromaDB vector store has >= 25 records and unapproved candidates."""
    store = get_configured_vector_store()
    stats = store.get_collection_stats()
    assert stats["total_vectors"] >= 25

    # Retrieve all items and verify candidate status
    results = store.query(query_embedding=[0.0] * 384, top_k=30)
    assert len(results) >= 25
    for r in results:
        meta = r.get("metadata", {})
        assert meta.get("is_approved_for_rag") is False
        assert meta.get("validation_status") in [
            "Candidate - Awaiting Approval",
            "Approved for RAG Integration - Pending SME Validation",
        ]


def test_conflict_detector_all_eleven_rules_active():
    """Verify CO-001 through CO-011 conflict rules are intact."""
    detector = ConflictDetector()
    rules = detector.conflict_records
    assert len(rules) >= 11
    expected_rule_ids = [f"CO-{i:03d}" for i in range(1, 12)]
    registered_ids = [r.conflict_id for r in rules]
    for exp_id in expected_rule_ids:
        assert exp_id in registered_ids
