"""Fast-Track Step 4 Acceptance Test Suite: Canonical RAG 15 Acceptance Test Cases.

Validates the canonical RAG integration against all 15 official acceptance cases
from data/incoming_handover_20261021/ABC_Shield_Canonical_RAG_Test_Pack.xlsx
executed against the live /api/v1/query FastAPI endpoint.
"""

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.dependencies import get_grounded_generator

client = TestClient(app)


@pytest.fixture(scope="module")
def api_active_store():
    """Verify live API active store loads canonical 25-vector collection."""
    gen = get_grounded_generator()
    store = gen.retriever.vector_store
    stats = store.get_collection_stats()
    assert stats["total_vectors"] == 25, f"Expected 25 vectors, found {stats['total_vectors']}"
    assert store.collection_name == "canonical_regulatory_records"
    return store


def test_rag_001_bribery_act_section_7(api_active_store):
    """RAG-001: Under UK Bribery Act, what does Section 7 cover?"""
    res = client.post("/api/v1/query", json={"query": "Under UK Bribery Act, what does Section 7 cover?", "id": "TEST-RAG-001"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "GROUNDED"
    assert data["grounded"] is True

    ret_recs = [c["record_id"] for c in data["retrieved_evidence"]]
    assert "UK-01-R004" in ret_recs
    assert "UK-01-R005" in ret_recs

    cited_recs = [c["record_id"] for c in data["citations"]]
    assert "UK-01-R004" in cited_recs

    cited_urls = [c["official_source"] for c in data["citations"]]
    assert any("legislation.gov.uk" in (u or "") for u in cited_urls)
    assert all(c["validation_status"] == "Approved for RAG Integration - Pending SME Validation" for c in data["citations"])
    assert all(c["is_approved_for_rag"] is False for c in data["citations"])
    assert "Section 8 defines an 'associated person'" in data["answer"]


def test_rag_002_bribery_act_section_2(api_active_store):
    """RAG-002: What does Section 2 of the Bribery Act address?"""
    res = client.post("/api/v1/query", json={"query": "What does Section 2 of the Bribery Act address?", "id": "TEST-RAG-002"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "GROUNDED"
    assert data["grounded"] is True

    ret_recs = [c["record_id"] for c in data["retrieved_evidence"]]
    assert ret_recs[0] == "UK-01-R002"

    cited_recs = [c["record_id"] for c in data["citations"]]
    assert "UK-01-R002" in cited_recs
    assert any("section/2" in (c["official_source"] or "") for c in data["citations"])


def test_rag_003_fcg_622_risk_assessment(api_active_store):
    """RAG-003: What should a firm consider when assessing bribery and corruption risks under FCA FCG 6?"""
    res = client.post("/api/v1/query", json={"query": "What should a firm consider when assessing bribery and corruption risks under FCA FCG 6?", "id": "TEST-RAG-003"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "GROUNDED"
    assert data["grounded"] is True

    ret_recs = [c["record_id"] for c in data["retrieved_evidence"]]
    assert "UK-03-R003" in ret_recs

    cited_urls = [c["official_source"] for c in data["citations"]]
    assert any("handbook.fca.org.uk" in (u or "") for u in cited_urls)


def test_rag_004_fcg_624_third_parties(api_active_store):
    """RAG-004: What controls are expected for third parties acting on behalf of a firm?"""
    res = client.post("/api/v1/query", json={"query": "What controls are expected for third parties acting on behalf of a firm?", "id": "TEST-RAG-004"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "GROUNDED"
    assert data["grounded"] is True

    ret_recs = [c["record_id"] for c in data["retrieved_evidence"]]
    assert ret_recs[0] == "UK-03-R005"
    cited_recs = [c["record_id"] for c in data["citations"]]
    assert "UK-03-R005" in cited_recs


def test_rag_005_fcg_623_policies_and_procedures(api_active_store):
    """RAG-005: What does FCA FCG 6.2.3 say about policies and procedures?"""
    res = client.post("/api/v1/query", json={"query": "What does FCA FCG 6.2.3 say about policies and procedures?", "id": "TEST-RAG-005"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "GROUNDED"
    assert data["grounded"] is True

    ret_recs = [c["record_id"] for c in data["retrieved_evidence"]]
    assert "UK-03-R004" in ret_recs
    # Must NOT include FCG 6.2.4 (UK-03-R005)
    assert "UK-03-R005" not in ret_recs

    cited_recs = [c["record_id"] for c in data["citations"]]
    assert "UK-03-R004" in cited_recs
    assert "UK-03-R005" not in cited_recs


def test_rag_006_eu_article_20_awareness(api_active_store):
    """RAG-006: Does EU Directive Article 20 directly require ABC Shield to run awareness campaigns?"""
    res = client.post("/api/v1/query", json={"query": "Does EU Directive Article 20 directly require ABC Shield to run awareness campaigns?", "id": "TEST-RAG-006"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "GROUNDED"
    assert data["grounded"] is True

    ret_recs = [c["record_id"] for c in data["retrieved_evidence"]]
    assert ret_recs[0] == "EU-01-R004"
    cited_recs = [c["record_id"] for c in data["citations"]]
    assert "EU-01-R004" in cited_recs


def test_rag_007_eu_article_21_national_strategy(api_active_store):
    """RAG-007: Does Article 21 require ABC Shield to publish a national anti-corruption strategy?"""
    res = client.post("/api/v1/query", json={"query": "Does Article 21 require ABC Shield to publish a national anti-corruption strategy?", "id": "TEST-RAG-007"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "GROUNDED"
    assert data["grounded"] is True

    ret_recs = [c["record_id"] for c in data["retrieved_evidence"]]
    assert ret_recs[0] == "EU-01-R005"
    cited_recs = [c["record_id"] for c in data["citations"]]
    assert "EU-01-R005" in cited_recs


def test_rag_008_eu_article_13_legal_persons(api_active_store):
    """RAG-008: What does Article 13 say about liability of legal persons?"""
    res = client.post("/api/v1/query", json={"query": "What does Article 13 say about liability of legal persons?", "id": "TEST-RAG-008"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "GROUNDED"
    assert data["grounded"] is True

    ret_recs = [c["record_id"] for c in data["retrieved_evidence"]]
    assert ret_recs[0] == "EU-01-R006"
    cited_recs = [c["record_id"] for c in data["citations"]]
    assert "EU-01-R006" in cited_recs


def test_rag_009_eu_article_16_mitigating_factors(api_active_store):
    """RAG-009: Which compliance-related factors are mentioned in Article 16 as potentially mitigating?"""
    res = client.post("/api/v1/query", json={"query": "Which compliance-related factors are mentioned in Article 16 as potentially mitigating?", "id": "TEST-RAG-009"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "GROUNDED"
    assert data["grounded"] is True

    ret_recs = [c["record_id"] for c in data["retrieved_evidence"]]
    assert ret_recs[0] == "EU-01-R007"
    cited_recs = [c["record_id"] for c in data["citations"]]
    assert "EU-01-R007" in cited_recs


def test_rag_010_exact_source_wording_fcg_611(api_active_store):
    """RAG-010: Give me the exact source wording for FCA FCG 6.1.1."""
    res = client.post("/api/v1/query", json={"query": "Give me the exact source wording for FCA FCG 6.1.1.", "id": "TEST-RAG-010"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "GROUNDED"
    assert data["grounded"] is True

    ret_recs = [c["record_id"] for c in data["retrieved_evidence"]]
    assert ret_recs[0] == "UK-03-R001"
    cited_recs = [c["record_id"] for c in data["citations"]]
    assert "UK-03-R001" in cited_recs
    assert "Exact Source Extract (FCA Handbook FCG 6.1.1):" in data["answer"]
    assert "Structured Summary (Separate):" in data["answer"]


def test_rag_011_sanctions_out_of_scope(api_active_store):
    """RAG-011: What are ABC Shield's sanctions-screening obligations?"""
    res = client.post("/api/v1/query", json={"query": "What are ABC Shield's sanctions-screening obligations?", "id": "TEST-RAG-011"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "OUT_OF_SCOPE"
    assert data["grounded"] is False
    assert len(data["citations"]) == 0
    assert len(data["provenance"]) == 0
    assert data["gap"] is not None
    assert data["gap"]["gap_type"] == "OUT_OF_SCOPE"
    assert "sanctions" in data["answer"].lower()


def test_rag_012_french_transposition_unsupported(api_active_store):
    """RAG-012: What exact EU member-state law implements Article 4 for ABC Shield in France?"""
    res = client.post("/api/v1/query", json={"query": "What exact EU member-state law implements Article 4 for ABC Shield in France?", "id": "TEST-RAG-012"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "INSUFFICIENT_EVIDENCE"
    assert data["grounded"] is False
    assert len(data["citations"]) == 0
    assert len(data["provenance"]) == 0
    assert data["gap"] is not None
    assert data["gap"]["gap_type"] == "DATA_COVERAGE_LIMITATION"
    assert "france" in data["answer"].lower()


def test_rag_013_compare_section_7_and_article_13(api_active_store):
    """RAG-013: Compare Section 7 of the UK Bribery Act with EU Directive Article 13."""
    res = client.post("/api/v1/query", json={"query": "Compare Section 7 of the UK Bribery Act with EU Directive Article 13.", "id": "TEST-RAG-013"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "GROUNDED"
    assert data["grounded"] is True

    ret_recs = [c["record_id"] for c in data["retrieved_evidence"]]
    assert "UK-01-R004" in ret_recs
    assert "EU-01-R006" in ret_recs

    cited_recs = [c["record_id"] for c in data["citations"]]
    assert "UK-01-R004" in cited_recs
    assert "EU-01-R006" in cited_recs

    assert "UK Bribery Act 2010 (Section 7)" in data["answer"]
    assert "Article 13 of Directive (EU) 2026/1021" in data["answer"]


def test_rag_014_sme_approval_status(api_active_store):
    """RAG-014: Is this regulatory corpus SME-approved?"""
    res = client.post("/api/v1/query", json={"query": "Is this regulatory corpus SME-approved?", "id": "TEST-RAG-014"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "GROUNDED"
    assert data["metadata"]["has_candidate_evidence"] is True
    assert data["metadata"]["approved_evidence_count"] == 0

    # Strict preservation of required disclosure
    for c in data["citations"]:
        assert c["validation_status"] == "Approved for RAG Integration - Pending SME Validation"
        assert c["is_approved_for_rag"] is False

    assert "No. The records in the regulatory corpus are not yet SME-approved" in data["answer"]
    assert "Approved for RAG Integration - Pending SME Validation" in data["answer"]


def test_rag_015_associated_person_meaning_section_8(api_active_store):
    """RAG-015: What is the meaning of an associated person for Section 7?"""
    res = client.post("/api/v1/query", json={"query": "What is the meaning of an associated person for Section 7?", "id": "TEST-RAG-015"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "GROUNDED"
    assert data["grounded"] is True

    ret_recs = [c["record_id"] for c in data["retrieved_evidence"]]
    assert ret_recs[0] == "UK-01-R005"

    cited_recs = [c["record_id"] for c in data["citations"]]
    assert "UK-01-R005" in cited_recs
    assert any("section/8" in (c["official_source"] or "") for c in data["citations"])
    assert "Section 8" in data["answer"]
