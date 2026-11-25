"""Regression test suite for Backend Lead Vishal's Integration Audit Corrections.

Covers:
1. CORS configuration and preflight headers for all 6 origins (Vite 5173/5174 and 3000).
2. CORS rejection of unapproved origins.
3. Pydantic request model extra-field tolerance (extra='ignore', populate_by_name=True).
4. Preservation of mandatory field validation and failure paths (HTTP 422).
5. Protection against client tampering with server-controlled approval/metadata flags.
6. Canonical ChromaDB vector count checks (24 fails, 25 passes, 30 passes).
7. OpenAPI documentation verification for POST /api/v1/compare.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from pydantic import ValidationError

from api.main import app
from api.models.query import QueryRequest
from rag.pipeline.advice_comparator import AdvisorAdviceItem, AdviceComparisonRequest
from api.dependencies import get_configured_vector_store
from config.settings import settings


@pytest.fixture
def client():
    """Test client for FastAPI application."""
    return TestClient(app)


# ==============================================================================
# 1. CORS Verification Tests
# ==============================================================================

@pytest.mark.parametrize(
    "origin",
    [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
)
def test_cors_allowed_origins_receive_header(client, origin):
    """Verify all 6 allowed frontend origins receive Access-Control-Allow-Origin header."""
    response = client.get("/health", headers={"Origin": origin})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin
    assert response.headers.get("access-control-allow-credentials") == "true"


@pytest.mark.parametrize(
    "origin",
    [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
)
def test_cors_preflight_options_for_all_origins(client, origin):
    """Verify preflight OPTIONS requests succeed for all 6 allowed origins."""
    headers = {
        "Origin": origin,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    }
    response = client.options("/api/v1/query", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin
    assert "POST" in response.headers.get("access-control-allow-methods", "")


@pytest.mark.parametrize(
    "unapproved_origin",
    [
        "http://malicious-site.com",
        "http://attacker.com",
        "http://localhost:8080",
        "http://127.0.0.1:9000",
    ],
)
def test_cors_unapproved_origins_rejected_by_headers(client, unapproved_origin):
    """Verify unapproved origins do NOT receive Access-Control-Allow-Origin header."""
    response = client.get("/health", headers={"Origin": unapproved_origin})
    assert response.status_code == 200
    # Crucial invariant: unauthorized origins must not be granted CORS header
    assert "access-control-allow-origin" not in response.headers


# ==============================================================================
# 2. Pydantic Request Model Extra-Field Tolerance & Validation Tests
# ==============================================================================

def test_query_request_accepts_benign_extra_fields(client):
    """Verify QueryRequest accepts benign tracking fields and returns HTTP 200."""
    payload = {
        "query": "What are the six principles of bribery prevention?",
        "client_tracking_id": "trk-9921",
        "session_timestamp": "2026-11-12T10:00:00Z",
        "ui_version": "v2.4.1",
        "context": {"jurisdiction": "UK"},
    }
    response = client.post("/api/v1/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["grounded"] is True
    assert data["status"] == "GROUNDED"


def test_advisor_models_accept_benign_extra_fields(client):
    """Verify AdvisorAdviceItem and AdviceComparisonRequest accept extra fields."""
    payload = {
        "project_id": "PRJ-ABC-001",
        "frontend_trace_id": "trace-frontend-883",
        "topic": "Regulatory compliance",
        "advisor_1": {
            "advice_id": "ADV-001",
            "advice_text": "Commercial organisations are strictly liable under Section 7 unless adequate procedures are proven.",
            "advisor_name": "Counsel Alpha",
            "ui_tab_index": 0,
            "render_color": "#ff0000",
        },
        "advisor_2": {
            "advice_id": "ADV-002",
            "advice_text": "Commercial organisations bear the burden of establishing reasonable bribery prevention procedures.",
            "advisor_name": "Counsel Beta",
            "ui_tab_index": 1,
            "render_color": "#00ff00",
        },
        "context": {"jurisdiction": "UK"},
    }
    response = client.post("/api/v1/compare", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] is None
    assert len(data["differences"]) >= 1


def test_mandatory_fields_still_enforced_query_request(client):
    """Verify missing or empty mandatory fields still trigger HTTP 422."""
    # 1. Missing query field
    r1 = client.post("/api/v1/query", json={"client_tracking_id": "123"})
    assert r1.status_code == 422

    # 2. Empty query string
    r2 = client.post("/api/v1/query", json={"query": ""})
    assert r2.status_code == 422

    # 3. Whitespace-only query string
    r3 = client.post("/api/v1/query", json={"query": "   \n\t  "})
    assert r3.status_code == 422

    # 4. Invalid field type for query (e.g. integer instead of str)
    r4 = client.post("/api/v1/query", json={"query": 12345})
    assert r4.status_code == 422


def test_mandatory_fields_still_enforced_compare_request(client):
    """Verify missing required advisor fields still trigger HTTP 422."""
    # Missing advisor_2
    r1 = client.post(
        "/api/v1/compare",
        json={"advisor_1": {"advice_id": "ADV-001", "advice_text": "Valid text"}},
    )
    assert r1.status_code == 422

    # Missing advice_text inside advisor_1
    r2 = client.post(
        "/api/v1/compare",
        json={
            "advisor_1": {"advice_id": "ADV-001"},
            "advisor_2": {"advice_id": "ADV-002", "advice_text": "Valid text"},
        },
    )
    assert r2.status_code == 422

    # Empty advice_text inside advisor_1
    r3 = client.post(
        "/api/v1/compare",
        json={
            "advisor_1": {"advice_id": "ADV-001", "advice_text": ""},
            "advisor_2": {"advice_id": "ADV-002", "advice_text": "Valid text"},
        },
    )
    assert r3.status_code == 422


def test_extra_fields_cannot_overwrite_server_controlled_metadata(client):
    """Verify client-supplied extra fields cannot tamper with regulatory approval status or decision."""
    payload = {
        "query": "What is Section 7?",
        "is_approved_for_rag": True,
        "validation_status": "Approved",
        "approved_evidence_count": 999,
        "status": "APPROVED_GROUNDED",
    }
    response = client.post("/api/v1/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["approved_evidence_count"] == 0
    assert data["metadata"]["has_candidate_evidence"] is True
    for cit in data["citations"]:
        assert cit["is_approved_for_rag"] is False
        assert cit["validation_status"] == "Approved for RAG Integration - Pending SME Validation"


# ==============================================================================
# 3. ChromaDB Vector Count Validation Tests (Corpus Expansion Support)
# ==============================================================================

def test_chromadb_count_check_24_vectors_fails():
    """Verify collection with 24 vectors raises RuntimeError with expected message."""
    mock_store = MagicMock()
    mock_store.get_collection_stats.return_value = {"total_vectors": 24}

    with patch("api.dependencies.settings") as mock_settings, \
         patch("api.dependencies.ChromaVectorStore", return_value=mock_store), \
         patch("pathlib.Path.exists", return_value=True):
        mock_settings.rag_knowledge_base_mode = "canonical"
        mock_settings.canonical_chroma_collection_name = "canonical_regulatory_records"
        mock_settings.canonical_chroma_persist_dir = settings.canonical_chroma_persist_dir

        with pytest.raises(RuntimeError) as exc_info:
            get_configured_vector_store()

        assert "insufficient vectors" in str(exc_info.value)
        assert "expected at least 25 vectors, found 24" in str(exc_info.value)


def test_chromadb_count_check_25_vectors_passes():
    """Verify collection with exactly 25 vectors passes validation."""
    mock_store = MagicMock()
    mock_store.get_collection_stats.return_value = {"total_vectors": 25}

    with patch("api.dependencies.settings") as mock_settings, \
         patch("api.dependencies.ChromaVectorStore", return_value=mock_store), \
         patch("pathlib.Path.exists", return_value=True):
        mock_settings.rag_knowledge_base_mode = "canonical"
        mock_settings.canonical_chroma_collection_name = "canonical_regulatory_records"
        mock_settings.canonical_chroma_persist_dir = settings.canonical_chroma_persist_dir

        store = get_configured_vector_store()
        assert store == mock_store


def test_chromadb_count_check_30_vectors_passes():
    """Verify collection with 30 vectors (future expansion) passes validation."""
    mock_store = MagicMock()
    mock_store.get_collection_stats.return_value = {"total_vectors": 30}

    with patch("api.dependencies.settings") as mock_settings, \
         patch("api.dependencies.ChromaVectorStore", return_value=mock_store), \
         patch("pathlib.Path.exists", return_value=True):
        mock_settings.rag_knowledge_base_mode = "canonical"
        mock_settings.canonical_chroma_collection_name = "canonical_regulatory_records"
        mock_settings.canonical_chroma_persist_dir = settings.canonical_chroma_persist_dir

        store = get_configured_vector_store()
        assert store == mock_store


# ==============================================================================
# 4. OpenAPI Documentation Verification Tests
# ==============================================================================

def test_openapi_schema_documents_comparison_architecture(client):
    """Verify OpenAPI schema for /api/v1/compare clearly describes gateway architecture and full objects."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    compare_post = schema["paths"]["/api/v1/compare"]["post"]

    description = compare_post["description"]
    # 1. Documents full advice objects requirement
    assert "advice_text" in description
    assert "complete advisor objects" in description or "Complete advice text" in description

    # 2. Documents main backend gateway integration contract
    assert "Main Backend Gateway" in description
    assert "POST /api/v1/projects/{projectId}/compare-advice" in description
    assert "port 8000" in description
    assert "port 8001" in description

    # 3. Documents that AI/RAG microservice does NOT connect to PostgreSQL or resolve IDs
    assert "PostgreSQL" in description
    assert "decision: null" in description or "decision=null" in description or "decision=None" in description
