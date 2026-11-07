"""Test suite for Source-Control and Approval Validation (Task W4.3).

Project: ABC Shield / FinRegTech ShipYard
Role: Padma Kumar — AI/RAG & Conflict Detection Engineer

Validates:
1. Strict fail-closed regulatory source-control and approval rules:
   - No regulatory record is treated as approved/authoritative RAG evidence (is_approved_for_rag = True)
     unless its validation status explicitly matches the canonical SME approval status.
2. Canonical SME approval statuses:
   - {"approved", "sme approved"}
3. Non-approving statuses:
   - "Candidate - Awaiting Approval", "Candidate", "Awaiting Approval", "Pending",
     "Pending SME Validation", "Rejected", "Draft", "Unverified", "", None, unknown.
4. Prevention of loose substring false approvals:
   - "Not Approved", "Approval Pending", "Approved - Pending Review", "Pre-Approved", "Unapproved"
5. Clear separation between:
   - Data quality validation (e.g. "Validated")
   - Official source verification (e.g. legislation.gov.uk, EUR-Lex check in Official_Verification)
   - Authority Level (e.g. Level A binding primary legislation)
   - Retrieval priority (e.g. P1 - Core)
   - Official source URL presence
   - SME approval
   - RAG eligibility (is_approved_for_rag)
6. All 15 production records, 15 production sources, and 15 source control entries are Candidate.
7. 0 records are approved in production.
8. Rule RAG-04 and Review Notes integrity.
9. Immutability of raw Excel workbooks.
"""

from pathlib import Path
import hashlib
import pytest

from rag.ingestion.excel_loader import ExcelWorkbookLoader
from rag.ingestion.normalizer import RegulatoryDataNormalizer
from rag.ingestion.validator import RegulatoryDataValidator
from rag.ingestion.chunker import RegulatoryRecordChunker
from rag.ingestion.schemas import (
    NormalizedRegulatoryRecord,
    RegulatoryChunk,
    SourceRegisterRecord,
    SourceControlRecord,
    CANONICAL_SME_APPROVED_STATUSES,
    is_sme_approved,
)

RAW_DATA_DIR = Path("data/raw")


def compute_file_hash(filepath: Path) -> str:
    """Compute SHA-256 hash of a file to assert immutability."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


# ---------------------------------------------------------------------------
# 1. Canonical SME Approval Function Tests (Unit & Edge Cases)
# ---------------------------------------------------------------------------

def test_1_canonical_sme_approved_statuses_exact_match():
    """Verify that only documented canonical SME approved statuses evaluate to True."""
    assert is_sme_approved("Approved") is True
    assert is_sme_approved("approved") is True
    assert is_sme_approved("APPROVED") is True
    assert is_sme_approved("SME Approved") is True
    assert is_sme_approved("sme approved") is True
    assert is_sme_approved("  SME   Approved  ") is True


def test_2_candidate_and_pending_statuses_fail_closed():
    """Verify that all candidate, pending, awaiting, draft, and rejected statuses evaluate to False."""
    assert is_sme_approved("Candidate - Awaiting Approval") is False
    assert is_sme_approved("Candidate") is False
    assert is_sme_approved("Awaiting Approval") is False
    assert is_sme_approved("Pending") is False
    assert is_sme_approved("Pending SME Validation") is False
    assert is_sme_approved("Draft") is False
    assert is_sme_approved("Rejected") is False
    assert is_sme_approved("Unverified") is False
    assert is_sme_approved("") is False
    assert is_sme_approved(None) is False
    assert is_sme_approved("   ") is False
    assert is_sme_approved("In Review") is False
    assert is_sme_approved("Unknown Status") is False


def test_3_substring_patterns_do_not_falsely_approve():
    """Critical safety test: Ensure substring matching does not falsely approve negative statuses."""
    # Under naive substring matching ('approved' in status), all these would falsely pass:
    assert is_sme_approved("Not Approved") is False
    assert is_sme_approved("Approval Pending") is False
    assert is_sme_approved("Approved - Pending Review") is False
    assert is_sme_approved("Pre-Approved") is False
    assert is_sme_approved("Unapproved") is False
    assert is_sme_approved("Self-Approved") is False
    assert is_sme_approved("Partially Approved") is False
    assert is_sme_approved("Disapproved") is False


def test_4_data_quality_validation_is_distinct_from_sme_approval():
    """Verify that data quality status 'Validated' does NOT evaluate to SME approval."""
    assert is_sme_approved("Validated") is False
    assert is_sme_approved("validated") is False
    assert is_sme_approved("Data Validated") is False
    assert is_sme_approved("Schema Validated") is False


# ---------------------------------------------------------------------------
# 2. Production Regulatory Corpus Verification (15 Records, 15 Sources)
# ---------------------------------------------------------------------------

def test_5_all_15_production_records_are_candidate_status():
    """Verify all 15 production regulatory records have Candidate status and is_approved_for_rag == False."""
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    sources = loader.load_source_register()
    raw_records = loader.load_regulatory_records_raw()

    normalizer = RegulatoryDataNormalizer(sources)
    normalized = normalizer.normalize_all(raw_records)

    assert len(normalized) == 15
    for rec in normalized:
        assert rec.validation_status == "Candidate - Awaiting Approval"
        assert rec.is_approved_for_rag is False


def test_6_all_15_production_sources_are_candidate_status():
    """Verify all 15 production source register records have Candidate status."""
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    sources = loader.load_source_register()

    assert len(sources) == 15
    for s in sources:
        assert "Candidate" in s.status
        assert "Awaiting Approval" in s.status


def test_7_all_15_source_control_entries_are_candidate_gated():
    """Verify all 15 entries in Source_Control sheet have Candidate status and Approval_Gate."""
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    source_controls = loader.load_source_control()

    assert len(source_controls) == 15
    for sc in source_controls:
        assert isinstance(sc, SourceControlRecord)
        assert sc.source_id.startswith(("UK-", "EU-"))
        assert "Candidate" in sc.status
        assert "Candidate" in sc.approval_gate


def test_8_approved_only_filter_returns_zero_production_records():
    """Verify that filtering for approved records on production corpus returns strictly 0 records."""
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    sources = loader.load_source_register()
    raw_records = loader.load_regulatory_records_raw()

    normalizer = RegulatoryDataNormalizer(sources)
    normalized = normalizer.normalize_all(raw_records)

    approved = [r for r in normalized if r.is_approved_for_rag]
    assert len(approved) == 0


def test_9_validation_report_candidate_and_approved_counts():
    """Verify that RegulatoryDataValidator reports 15 candidate records and 0 approved records."""
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    sources = loader.load_source_register()
    raw_records = loader.load_regulatory_records_raw()

    normalizer = RegulatoryDataNormalizer(sources)
    normalized = normalizer.normalize_all(raw_records)

    validator = RegulatoryDataValidator(sources)
    report = validator.validate_records(normalized)

    assert report.total_records == 15
    assert report.valid_records_count == 15  # All 15 pass data quality schema validation
    assert report.candidate_records_count == 15
    assert report.approved_records_count == 0
    assert report.has_critical_errors is False


# ---------------------------------------------------------------------------
# 3. Metadata Bypass Prevention Tests (Authority, Priority, URL, Verification)
# ---------------------------------------------------------------------------

def test_10_authority_level_a_does_not_confer_sme_approval():
    """Verify that Authority Level A (binding primary legislation) does NOT confer SME approval."""
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    sources = loader.load_source_register()
    raw_records = loader.load_regulatory_records_raw()

    normalizer = RegulatoryDataNormalizer(sources)
    normalized = normalizer.normalize_all(raw_records)

    # UK-01 (Bribery Act 2010) is Authority Level A Primary Legislation
    uk01 = next(r for r in normalized if r.record_id == "RR-UK-01")
    assert uk01.authority_level == "A"
    assert uk01.is_approved_for_rag is False


def test_11_retrieval_priority_p1_does_not_confer_sme_approval():
    """Verify that Retrieval Priority P1 does NOT confer SME approval."""
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    sources = loader.load_source_register()
    raw_records = loader.load_regulatory_records_raw()

    normalizer = RegulatoryDataNormalizer(sources)
    normalized = normalizer.normalize_all(raw_records)

    uk01 = next(r for r in normalized if r.record_id == "RR-UK-01")
    assert "P1" in (uk01.retrieval_priority or "")
    assert uk01.is_approved_for_rag is False


def test_12_official_source_url_does_not_confer_sme_approval():
    """Verify that having a valid official legislation URL does NOT confer SME approval."""
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    sources = loader.load_source_register()
    raw_records = loader.load_regulatory_records_raw()

    normalizer = RegulatoryDataNormalizer(sources)
    normalized = normalizer.normalize_all(raw_records)

    uk01 = next(r for r in normalized if r.record_id == "RR-UK-01")
    assert uk01.official_source == "https://www.legislation.gov.uk/ukpga/2010/23/contents"
    assert uk01.is_approved_for_rag is False


def test_13_official_verification_does_not_confer_sme_approval():
    """Verify that Official_Verification status 'Verified' does NOT confer SME approval."""
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    verifications = loader.load_official_verification()
    sources = loader.load_source_register()
    raw_records = loader.load_regulatory_records_raw()

    # UK-01 is verified on legislation.gov.uk
    uk01_ver = next(v for v in verifications if v.source_id == "UK-01")
    assert uk01_ver.verification == "Verified"
    assert "legislation.gov.uk" in uk01_ver.official_origin

    # But its normalized regulatory record remains unapproved
    normalizer = RegulatoryDataNormalizer(sources)
    normalized = normalizer.normalize_all(raw_records)
    uk01 = next(r for r in normalized if r.record_id == "RR-UK-01")
    assert uk01.is_approved_for_rag is False


def test_14_source_qa_note_and_legal_effect_do_not_confer_sme_approval():
    """Verify that source register screening notes do NOT confer SME approval."""
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    sources = loader.load_source_register()

    uk01_source = next(s for s in sources if s.source_id == "UK-01")
    assert uk01_source.legal_regulatory_effect is not None
    assert uk01_source.source_qa_note is not None
    assert is_sme_approved(uk01_source.status) is False


def test_15_rag_rules_sheet_confirms_rag_04_candidate_caveat():
    """Verify that Rule RAG-04 explicitly forbids representing Candidate records as SME-approved."""
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    rules = loader.load_rag_rules()

    rag04 = next(r for r in rules if r.rule_id == "RAG-04")
    assert "Candidate - Awaiting Approval" in rag04.rag_rule
    assert "SME-approved requirements" in rag04.rag_rule


def test_16_review_notes_confirm_no_source_promoted_to_approved():
    """Verify that Review Notes explicitly state no source is promoted to approved corpus."""
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    notes = loader.load_validation_notes()

    control_note = None
    for n in notes:
        vals = [str(v) for v in n.values()]
        if any("Important control" in v for v in vals):
            control_note = n
            break

    assert control_note is not None
    assert any("No source is promoted to approved corpus" in str(v) for v in control_note.values())


# ---------------------------------------------------------------------------
# 4. Tamper Prevention & Schema Field Validator Tests
# ---------------------------------------------------------------------------

def test_17_tamper_attempt_candidate_with_approved_flag_is_neutralized():
    """Verify that attempting to initialize a Candidate record with is_approved_for_rag=True is overridden."""
    rec = NormalizedRegulatoryRecord(
        record_id="RR-TEST-SYNTHETIC-01",
        source_id="UK-01",
        regulation="Synthetic Test Regulation",
        regulator="Synthetic Authority",
        jurisdiction="UK",
        section_article="Article 1",
        title="Synthetic Obligation",
        requirement="Synthetic requirement text.",
        retrieval_text="Synthetic retrieval text block for testing.",
        validation_status="Candidate - Awaiting Approval",
        is_approved_for_rag=True,  # Tamper attempt
    )
    assert rec.is_approved_for_rag is False


def test_18_tamper_attempt_not_approved_with_approved_flag_is_neutralized():
    """Verify that attempting to initialize a 'Not Approved' record with is_approved_for_rag=True is overridden."""
    rec = NormalizedRegulatoryRecord(
        record_id="RR-TEST-SYNTHETIC-02",
        source_id="UK-01",
        regulation="Synthetic Test Regulation",
        regulator="Synthetic Authority",
        jurisdiction="UK",
        section_article="Article 2",
        title="Synthetic Obligation",
        requirement="Synthetic requirement text.",
        retrieval_text="Synthetic retrieval text block for testing.",
        validation_status="Not Approved",
        is_approved_for_rag=True,  # Tamper attempt
    )
    assert rec.is_approved_for_rag is False


def test_19_tamper_attempt_validated_with_approved_flag_is_neutralized():
    """Verify that 'Validated' data quality status does NOT allow is_approved_for_rag=True."""
    rec = NormalizedRegulatoryRecord(
        record_id="RR-TEST-SYNTHETIC-03",
        source_id="UK-01",
        regulation="Synthetic Test Regulation",
        regulator="Synthetic Authority",
        jurisdiction="UK",
        section_article="Article 3",
        title="Synthetic Obligation",
        requirement="Synthetic requirement text.",
        retrieval_text="Synthetic retrieval text block for testing.",
        validation_status="Validated",
        is_approved_for_rag=True,  # Tamper attempt
    )
    assert rec.is_approved_for_rag is False


def test_20_validator_detects_and_errors_on_tampered_record():
    """Verify that RegulatoryDataValidator raises an ERROR if is_approved_for_rag is manually forced on candidate."""
    rec = NormalizedRegulatoryRecord(
        record_id="RR-TEST-SYNTHETIC-04",
        source_id="UK-01",
        regulation="Synthetic Test Regulation",
        regulator="Synthetic Authority",
        jurisdiction="UK",
        section_article="Article 4",
        title="Synthetic Obligation",
        requirement="Synthetic requirement text.",
        retrieval_text="Synthetic retrieval text block for testing.",
        validation_status="Candidate - Awaiting Approval",
    )
    # Simulate accidental or malicious dictionary bypass
    rec.__dict__["is_approved_for_rag"] = True

    sources = [
        SourceRegisterRecord(
            source_id="UK-01",
            source_name="Bribery Act 2010",
            issuing_authority="UK Parliament",
            jurisdiction="UK",
            source_type="Primary Legislation",
            authority_level="A",
            status="Candidate - Awaiting Approval",
        )
    ]
    validator = RegulatoryDataValidator(sources)
    report = validator.validate_records([rec])

    assert report.has_critical_errors is True
    error_issue = next(i for i in report.issues if i.field == "is_approved_for_rag")
    assert error_issue.issue_type == "ERROR"
    assert "not canonical SME-approved" in error_issue.message


# ---------------------------------------------------------------------------
# 5. Synthetic Approved Fixture Tests (Isolated & Clearly Labeled)
# ---------------------------------------------------------------------------

def test_21_synthetic_approved_record_sets_flag_and_validator_counts():
    """Verify that an explicitly 'Approved' record sets is_approved_for_rag=True and is counted by validator.

    [SYNTHETIC TEST FIXTURE - NOT PRODUCTION DATA]
    """
    rec = NormalizedRegulatoryRecord(
        record_id="RR-TEST-APPROVED-01",
        source_id="UK-01",
        regulation="Synthetic Test Regulation",
        regulator="Synthetic Authority",
        jurisdiction="UK",
        section_article="Article 10",
        title="Synthetic Obligation",
        requirement="Synthetic requirement text.",
        retrieval_text="Synthetic retrieval text block for testing.",
        official_source="https://www.legislation.gov.uk/ukpga/2010/23/contents",
        validation_status="Approved",
    )
    assert rec.is_approved_for_rag is True

    sources = [
        SourceRegisterRecord(
            source_id="UK-01",
            source_name="Bribery Act 2010",
            issuing_authority="UK Parliament",
            jurisdiction="UK",
            source_type="Primary Legislation",
            authority_level="A",
            status="Candidate - Awaiting Approval",
        )
    ]
    validator = RegulatoryDataValidator(sources)
    report = validator.validate_records([rec])

    assert report.approved_records_count == 1
    assert report.candidate_records_count == 0
    assert report.valid_records_count == 1
    assert report.has_critical_errors is False


def test_22_synthetic_sme_approved_record_sets_flag():
    """Verify that an explicitly 'SME Approved' record sets is_approved_for_rag=True.

    [SYNTHETIC TEST FIXTURE - NOT PRODUCTION DATA]
    """
    rec = NormalizedRegulatoryRecord(
        record_id="RR-TEST-APPROVED-02",
        source_id="UK-01",
        regulation="Synthetic Test Regulation",
        regulator="Synthetic Authority",
        jurisdiction="UK",
        section_article="Article 11",
        title="Synthetic Obligation",
        requirement="Synthetic requirement text.",
        retrieval_text="Synthetic retrieval text block for testing.",
        official_source="https://www.legislation.gov.uk/ukpga/2010/23/contents",
        validation_status="SME Approved",
    )
    assert rec.is_approved_for_rag is True


# ---------------------------------------------------------------------------
# 6. Chunker Propagation & RegulatoryChunk Approval Gate
# ---------------------------------------------------------------------------

def test_23_chunker_propagates_approval_flag_faithfully():
    """Verify that chunker faithfully propagates is_approved_for_rag from parent record to chunks."""
    rec_candidate = NormalizedRegulatoryRecord(
        record_id="RR-TEST-CAND-01",
        source_id="UK-01",
        regulation="Synthetic Test Regulation",
        regulator="Synthetic Authority",
        jurisdiction="UK",
        section_article="Article 1",
        title="Candidate Obligation",
        requirement="Candidate requirement text.",
        retrieval_text="Candidate retrieval text block.",
        validation_status="Candidate - Awaiting Approval",
    )
    rec_approved = NormalizedRegulatoryRecord(
        record_id="RR-TEST-APPR-01",
        source_id="UK-01",
        regulation="Synthetic Test Regulation",
        regulator="Synthetic Authority",
        jurisdiction="UK",
        section_article="Article 2",
        title="Approved Obligation",
        requirement="Approved requirement text.",
        retrieval_text="Approved retrieval text block.",
        validation_status="Approved",
    )

    chunker = RegulatoryRecordChunker()
    cand_chunks = chunker.chunk_record(rec_candidate)
    appr_chunks = chunker.chunk_record(rec_approved)

    assert all(c.is_approved_for_rag is False for c in cand_chunks)
    assert all(c.is_approved_for_rag is True for c in appr_chunks)


def test_24_regulatory_chunk_model_validator_blocks_unapproved_tampering():
    """Verify that RegulatoryChunk model validator overrides is_approved_for_rag to False if status is unapproved."""
    chunk = RegulatoryChunk(
        chunk_id="RR-TEST-C01",
        record_id="RR-TEST-01",
        source_id="UK-01",
        regulation="Synthetic Regulation",
        regulator="Synthetic Regulator",
        jurisdiction="UK",
        section_article="Article 1",
        title="Synthetic Title",
        text="Sample chunk text content.",
        requirement="Sample requirement content.",
        validation_status="Candidate - Awaiting Approval",
        is_approved_for_rag=True,  # Tamper attempt
    )
    assert chunk.is_approved_for_rag is False


# ---------------------------------------------------------------------------
# 7. Raw Excel Workbook File Immutability (Zero Modification)
# ---------------------------------------------------------------------------

def test_25_raw_excel_workbooks_remain_completely_unmodified():
    """Verify that SHA-256 hashes of all raw Excel workbooks match their verified state."""
    expected_hashes = {
        "ABC shield_Data Dictionary.xlsx": "57e9484826dd3bb3db71845d54e74db8e3a90fc4d504731d5bbec78e57ead2e6",
        "ABC_Shield_RAG_Ready_Regulatory_Knowledge.xlsx": "2bab8181ef04d9643358d6e751117e414848cd01db82cfd33281f3b983fa6b5b",
        "ABC_Shield_Regulatory_Records_15_with_Conflict_Overlap.xlsx": "5a17ab6a3a883c1307c1e0a24cc1e94db705fee0b3aa6ff322d9cb6bee7f8e00",
        "ABC_Shield_Source_Register (1).xlsx": "0b6920636525ec871463ed458c285d61e4f50949a590a9e52b7dce41f0a7fa2b",
        "ABC_Shield_Source_Register_Reviewed (1).xlsx": "fde4d138f9cdd114304268ea6157d3cdaee60643789ff9f6fbdb54abfcf262c4",
    }
    for filename, expected_hash in expected_hashes.items():
        filepath = RAW_DATA_DIR / filename
        assert filepath.exists(), f"File missing: {filename}"
        current_hash = compute_file_hash(filepath)
        assert current_hash == expected_hash, f"File {filename} was modified! Expected {expected_hash}, got {current_hash}"
