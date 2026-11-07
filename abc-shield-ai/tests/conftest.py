"""Pytest configuration and test isolation fixtures for ABC Shield.

Preserves both the canonical 25-record corpus (Fast-Track & Step handover tests)
and the legacy 15-record corpus (Week 4 & Week 5 regression tests) without mixing.
"""

import pytest
from config.settings import settings
from api.dependencies import reset_grounded_generator
from rag.generation.gap_handler import GapHandler

# Test modules that validate the legacy 15-record processed corpus
LEGACY_TEST_MODULES = {
    "test_conflict_relationship_integration_w56",
    "test_evidence_gap_w49",
    "test_integrated_rag_security_w510",
    "test_rag_advice_workflow_w54",
    "test_rag_backend_contract_w52",
    "test_rag_frontend_contract_w53",
    "test_rag_end_to_end_w511",
    "test_regulatory_advice_traceability_w58",
    "test_rag_evaluation_regression_w59",
    "test_security_phase1_source_provenance",
    "test_security_phase2_retrieval_context",
    "test_security_phase3_runtime_provider",
    "test_security_phase4_adversarial_clearance",
    "test_security_s1_approved_source_control",
    "test_retrieval",
    "test_retrieval_baseline",
}

# Test modules that validate canonical 25-record corpus via Excel loader
CANONICAL_CORPUS_MODULES = {
    "test_handover_step1_adaptation",
    "test_handover_step2_alignment",
}


@pytest.fixture(autouse=True, scope="module")
def configure_test_corpus_mode_module(request):
    """Module-level isolation ensuring generator and settings align before module fixtures run."""
    mod_name = request.module.__name__.split(".")[-1]

    orig_kb_mode = getattr(settings, "rag_knowledge_base_mode", "canonical")
    orig_corpus_mode = getattr(settings, "rag_corpus_mode", None)

    if mod_name in LEGACY_TEST_MODULES:
        settings.rag_knowledge_base_mode = "legacy"
        settings.rag_corpus_mode = "preferred"
        reset_grounded_generator()
        GapHandler.reset_cache()
    elif mod_name in CANONICAL_CORPUS_MODULES:
        settings.rag_knowledge_base_mode = "canonical"
        settings.rag_corpus_mode = "canonical"
        reset_grounded_generator()
        GapHandler.reset_cache()
    else:
        # Default for fast-track, api, and production is canonical
        settings.rag_knowledge_base_mode = "canonical"
        settings.rag_corpus_mode = None
        reset_grounded_generator()
        GapHandler.reset_cache()

    yield

    settings.rag_knowledge_base_mode = orig_kb_mode
    settings.rag_corpus_mode = orig_corpus_mode
    reset_grounded_generator()
    GapHandler.reset_cache()


@pytest.fixture(autouse=True)
def configure_test_corpus_mode_function(request):
    """Function-level reset ensuring each test begins with clean generator and gap state."""
    mod_name = request.module.__name__.split(".")[-1]
    if mod_name in LEGACY_TEST_MODULES:
        settings.rag_knowledge_base_mode = "legacy"
        settings.rag_corpus_mode = "preferred"
    elif mod_name in CANONICAL_CORPUS_MODULES:
        settings.rag_knowledge_base_mode = "canonical"
        settings.rag_corpus_mode = "canonical"
    else:
        settings.rag_knowledge_base_mode = "canonical"
        settings.rag_corpus_mode = None

    yield
