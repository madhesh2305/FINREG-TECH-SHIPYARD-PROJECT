"""Test suite for Regulatory Data Ingestion (Task W4.2).

Verifies Week 4 ingestion enhancements and backward compatibility:
- Loading of preferred Week 4 workbooks and legacy Week 3 workbooks
- Detection of new worksheets (RAG_Records, Source_Control, RAG_Rules, Conflict_Handling, Official_Verification)
- Preservation of all 15 records and 15 sources with 0 orphaned foreign keys
- Preservation of upstream Chunk_IDs, Retrieval_Text, Retrieval_Tags, Citation_Label, Retrieval_Priority, Authority_Rule, RAG_Instruction
- Strict candidate gating (is_approved_for_rag == False for all 15 records)
- Strict separation of Requirement paraphrase, verbatim Regulatory_Text, and Retrieval_Text
- Parsing of semicolon-delimited Retrieval_Tags into clean List[str]
- Verification that missing Retrieval_Text fails validation
- File immutability across all raw Excel workbooks
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
    SourceRegisterRecord,
    RAGRuleRecord,
    OfficialVerificationRecord,
)

RAW_DATA_DIR = Path("data/raw")


def compute_file_hash(filepath: Path) -> str:
    """Compute SHA-256 hash of a file to assert immutability."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


# 1. Excel files can be loaded (preferred Week 4 workbooks)
def test_1_excel_files_can_be_loaded():
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    data_dict = loader.load_data_dictionary()
    sources = loader.load_source_register()
    raw_records = loader.load_regulatory_records_raw()

    assert len(data_dict) == 17
    assert len(sources) == 15
    assert len(raw_records) == 15


# 2. Correct worksheets are detected in both preferred and legacy workbooks
def test_2_correct_worksheets_detected():
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    
    dd_sheets = loader.get_sheet_names(loader.data_dictionary_path)
    assert "Sheet1" in dd_sheets

    sr_sheets = loader.get_sheet_names(loader.source_register_path)
    assert "Source Register" in sr_sheets
    if "Review Notes" in sr_sheets:
        assert "Review Notes" in sr_sheets

    rr_sheets = loader.get_sheet_names(loader.regulatory_records_path)
    # Preferred Week 4 sheets
    assert "RAG_Records" in rr_sheets
    assert "Source_Control" in rr_sheets
    assert "RAG_Rules" in rr_sheets
    assert "Conflict_Handling" in rr_sheets
    assert "Official_Verification" in rr_sheets

    # Also verify legacy workbook sheets remain intact
    legacy_rr_path = RAW_DATA_DIR / loader.LEGACY_REGULATORY_RECORDS_FILENAME
    if legacy_rr_path.exists():
        legacy_sheets = loader.get_sheet_names(legacy_rr_path)
        assert "Regulatory Records" in legacy_sheets
        assert "Conflict Overlap" in legacy_sheets


# 3. Regulatory records are normalized successfully
def test_3_regulatory_records_normalized_successfully():
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    sources = loader.load_source_register()
    raw_records = loader.load_regulatory_records_raw()

    normalizer = RegulatoryDataNormalizer(sources)
    normalized = normalizer.normalize_all(raw_records)

    assert len(normalized) == 15
    for rec in normalized:
        assert isinstance(rec, NormalizedRegulatoryRecord)
        assert rec.record_id.startswith("RR-")
        assert rec.jurisdiction in ("UK", "EU")


# 4. Source Register metadata can be associated using Source ID
def test_4_source_register_metadata_associated_using_source_id():
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    sources = loader.load_source_register()
    raw_records = loader.load_regulatory_records_raw()

    normalizer = RegulatoryDataNormalizer(sources)
    normalized = normalizer.normalize_all(raw_records)

    # Check UK-01 record RR-UK-01
    rr_uk_01 = next(r for r in normalized if r.record_id == "RR-UK-01")
    assert rr_uk_01.source_id == "UK-01"
    assert rr_uk_01.authority_level == "A"
    assert rr_uk_01.source_type == "Primary Legislation"
    assert "Bribery" in rr_uk_01.topic


# 5. Record ID is preserved
def test_5_record_id_is_preserved():
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    sources = loader.load_source_register()
    raw_records = loader.load_regulatory_records_raw()

    raw_ids = [r["Record_ID"] for r in raw_records]
    normalizer = RegulatoryDataNormalizer(sources)
    normalized = normalizer.normalize_all(raw_records)
    norm_ids = [r.record_id for r in normalized]

    assert norm_ids == raw_ids


# 6. Source ID is preserved
def test_6_source_id_is_preserved():
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    sources = loader.load_source_register()
    raw_records = loader.load_regulatory_records_raw()

    raw_source_ids = [r["Source_ID"] for r in raw_records]
    normalizer = RegulatoryDataNormalizer(sources)
    normalized = normalizer.normalize_all(raw_records)
    norm_source_ids = [r.source_id for r in normalized]

    assert norm_source_ids == raw_source_ids


# 7. Section / Article is preserved
def test_7_section_article_is_preserved():
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    sources = loader.load_source_register()
    raw_records = loader.load_regulatory_records_raw()

    normalizer = RegulatoryDataNormalizer(sources)
    normalized = normalizer.normalize_all(raw_records)

    record_map = {r.record_id: r.section_article for r in normalized}
    assert record_map["RR-UK-01"] == "Section 1"
    assert record_map["RR-UK-02"] == "Six Principles"
    assert record_map["RR-UK-03"] == "FCG 6"
    assert record_map["RR-EU-01"] == "Article 3"
    assert record_map["RR-UK-09"] == "PRIN 2.1.1R / Principle 1"
    assert record_map["RR-EU-03"] == "Article 19"


# 8. Requirement remains separate from Regulatory_Text
def test_8_requirement_remains_separate_from_regulatory_text():
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    sources = loader.load_source_register()
    raw_records = loader.load_regulatory_records_raw()

    normalizer = RegulatoryDataNormalizer(sources)
    normalized = normalizer.normalize_all(raw_records)

    for rec in normalized:
        assert rec.requirement is not None and len(rec.requirement) > 0
        assert rec.regulatory_text is None
        assert rec.requirement != rec.regulatory_text


# 9. Missing regulatory_text is not fabricated
def test_9_missing_regulatory_text_is_not_fabricated():
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    sources = loader.load_source_register()
    raw_records = loader.load_regulatory_records_raw()

    normalizer = RegulatoryDataNormalizer(sources)
    normalized = normalizer.normalize_all(raw_records)

    # Asserts that regulatory_text remains strictly None across all 15 records
    assert all(r.regulatory_text is None for r in normalized)


# 10. Candidate/Pending/Awaiting Approval status is preserved
def test_10_candidate_pending_status_preserved():
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    sources = loader.load_source_register()
    raw_records = loader.load_regulatory_records_raw()

    normalizer = RegulatoryDataNormalizer(sources)
    normalized = normalizer.normalize_all(raw_records)

    for rec in normalized:
        assert "Candidate" in rec.validation_status and "Awaiting" in rec.validation_status


# 11. Candidate/Pending records are NOT converted to Approved
def test_11_candidate_records_not_converted_to_approved():
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    sources = loader.load_source_register()
    raw_records = loader.load_regulatory_records_raw()

    normalizer = RegulatoryDataNormalizer(sources)
    normalized = normalizer.normalize_all(raw_records)

    validator = RegulatoryDataValidator(sources)
    val_report = validator.validate_records(normalized)

    assert val_report.candidate_records_count == 15
    assert val_report.approved_records_count == 0
    assert all(not r.is_approved_for_rag for r in normalized)

    # Synthetic test fixture (clearly labeled): Test guardrail when candidate tries to be approved
    # [SYNTHETIC TEST FIXTURE - NOT REAL REGULATORY DATA]
    synthetic_rec = NormalizedRegulatoryRecord(
        record_id="RR-TEST-SYNTHETIC-01",
        source_id="UK-01",
        regulation="Synthetic Test Regulation",
        regulator="Synthetic Authority",
        jurisdiction="UK",
        section_article="Article 99",
        title="Synthetic Test Obligation",
        requirement="Synthetic test requirement content for validation.",
        validation_status="Candidate - Awaiting Approval",
        is_approved_for_rag=True  # Intentional invalid attempt
    )
    # The Pydantic validator must override is_approved_for_rag to False because status is Candidate
    assert synthetic_rec.is_approved_for_rag is False


# 12. Chunking preserves parent metadata
def test_12_chunking_preserves_parent_metadata():
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    sources = loader.load_source_register()
    raw_records = loader.load_regulatory_records_raw()

    normalizer = RegulatoryDataNormalizer(sources)
    normalized = normalizer.normalize_all(raw_records)

    chunker = RegulatoryRecordChunker()
    chunks = chunker.chunk_all(normalized)

    assert len(chunks) == len(normalized)
    for rec, chunk in zip(normalized, chunks):
        assert chunk.record_id == rec.record_id
        assert chunk.source_id == rec.source_id
        assert chunk.regulation == rec.regulation
        assert chunk.regulator == rec.regulator
        assert chunk.jurisdiction == rec.jurisdiction
        assert chunk.section_article == rec.section_article
        assert chunk.title == rec.title
        assert chunk.requirement == rec.requirement
        assert chunk.validation_status == rec.validation_status
        assert chunk.authority_level == rec.authority_level
        assert chunk.source_type == rec.source_type
        assert chunk.is_approved_for_rag is False
        expected_text = rec.retrieval_text.strip() if rec.retrieval_text else rec.requirement
        assert chunk.text == expected_text


# 13. Original Excel files are never modified
def test_13_original_excel_files_never_modified():
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    files = [
        loader.data_dictionary_path,
        loader.source_register_path,
        loader.regulatory_records_path,
        RAW_DATA_DIR / loader.LEGACY_SOURCE_REGISTER_FILENAME,
        RAW_DATA_DIR / loader.LEGACY_REGULATORY_RECORDS_FILENAME,
    ]

    hashes_before = {f: compute_file_hash(f) for f in files if f.exists()}

    # Execute full load, normalize, validate, and chunk cycle
    data_dict = loader.load_data_dictionary()
    sources = loader.load_source_register()
    raw_records = loader.load_regulatory_records_raw()
    normalizer = RegulatoryDataNormalizer(sources)
    normalized = normalizer.normalize_all(raw_records)
    validator = RegulatoryDataValidator(sources)
    val_report = validator.validate_records(normalized)
    chunker = RegulatoryRecordChunker()
    chunks = chunker.chunk_all(normalized)

    hashes_after = {f: compute_file_hash(f) for f in files if f.exists()}

    for f in hashes_before:
        assert hashes_before[f] == hashes_after[f], f"File {f.name} was modified!"


# 14. Week 4 RAG fields populated on normalized records
def test_14_new_rag_fields_populated_on_normalized_records():
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    sources = loader.load_source_register()
    raw_records = loader.load_regulatory_records_raw()

    normalizer = RegulatoryDataNormalizer(sources)
    normalized = normalizer.normalize_all(raw_records)

    for rec in normalized:
        assert rec.chunk_id is not None and rec.chunk_id.startswith("RR-")
        assert rec.retrieval_text is not None and len(rec.retrieval_text) > 30
        assert rec.citation_label is not None and "|" in rec.citation_label
        assert rec.retrieval_priority is not None and any(rec.retrieval_priority.startswith(p) for p in ("P1", "P2", "P3", "P4"))
        assert rec.authority_rule is not None and len(rec.authority_rule) > 10
        assert rec.rag_instruction is not None and len(rec.rag_instruction) > 10
        assert rec.official_source_check_note is not None and len(rec.official_source_check_note) > 10


# 15. Retrieval_Tags parsed into clean List[str]
def test_15_retrieval_tags_parsed_into_clean_list():
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    sources = loader.load_source_register()
    raw_records = loader.load_regulatory_records_raw()

    normalizer = RegulatoryDataNormalizer(sources)
    normalized = normalizer.normalize_all(raw_records)

    uk_01 = next(r for r in normalized if r.record_id == "RR-UK-01")
    assert isinstance(uk_01.retrieval_tags, list)
    assert len(uk_01.retrieval_tags) >= 3
    assert "UK" in uk_01.retrieval_tags
    assert "Bribery Act 2010" in uk_01.retrieval_tags
    assert "Section 1" in uk_01.retrieval_tags

    for rec in normalized:
        assert isinstance(rec.retrieval_tags, list)
        assert len(rec.retrieval_tags) > 0
        assert all(isinstance(t, str) and len(t) > 0 for t in rec.retrieval_tags)


# 16. Chunk IDs are unique across all records
def test_16_chunk_ids_unique_across_records():
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    sources = loader.load_source_register()
    raw_records = loader.load_regulatory_records_raw()

    normalizer = RegulatoryDataNormalizer(sources)
    normalized = normalizer.normalize_all(raw_records)

    chunk_ids = [r.chunk_id for r in normalized]
    assert len(chunk_ids) == 15
    assert len(set(chunk_ids)) == 15
    for cid in chunk_ids:
        assert cid.endswith("-C01")


# 17. Official_Source_URL maps to official_source with legacy fallback
def test_17_official_source_url_mapping_and_legacy_fallback():
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    sources = loader.load_source_register()
    raw_records = loader.load_regulatory_records_raw()

    normalizer = RegulatoryDataNormalizer(sources)
    normalized = normalizer.normalize_all(raw_records)

    for rec in normalized:
        assert rec.official_source is not None
        assert rec.official_source.startswith("http")

    # Test synthetic fallback where Official_Source_URL is missing but Source_URL is provided
    # [SYNTHETIC TEST FIXTURE]
    raw_fallback = {
        "Record_ID": "RR-SYNTH-URL-01",
        "Source_ID": "UK-01",
        "Regulation_Name": "Synthetic URL Fallback Act",
        "Issuing_Authority": "Synthetic Authority",
        "Jurisdiction": "UK",
        "Section_Article": "Section 99",
        "Title": "URL Fallback Check",
        "Requirement": "Synthetic requirement for checking URL fallback.",
        "Source_URL": "https://example.gov.uk/legacy-source-url",
        "Validation_Status": "Candidate - Awaiting Approval"
    }
    norm_fallback = normalizer.normalize_record(raw_fallback)
    assert norm_fallback.official_source == "https://example.gov.uk/legacy-source-url"


# 18. Conflict_Handling loads and legacy Conflict Overlap fallback works
def test_18_conflict_handling_sheet_and_legacy_fallback():
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    conflicts = loader.load_conflict_overlap()

    assert len(conflicts) == 11
    conflict_ids = [c.conflict_id for c in conflicts]
    assert conflict_ids == [f"CO-{i:03d}" for i in range(1, 12)]

    # Test legacy fallback loader pointing explicitly to legacy workbook
    legacy_rr = RAW_DATA_DIR / loader.LEGACY_REGULATORY_RECORDS_FILENAME
    if legacy_rr.exists():
        legacy_loader = ExcelWorkbookLoader(
            RAW_DATA_DIR,
            regulatory_records_path=legacy_rr
        )
        legacy_conflicts = legacy_loader.load_conflict_overlap()
        assert len(legacy_conflicts) == 11
        assert [c.conflict_id for c in legacy_conflicts] == conflict_ids


# 19. RAG_Rules loads successfully
def test_19_rag_rules_loading():
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    rules = loader.load_rag_rules()

    assert len(rules) == 10
    rule_ids = [r.rule_id for r in rules]
    assert rule_ids == [f"RAG-{i:02d}" for i in range(1, 11)]
    for r in rules:
        assert isinstance(r, RAGRuleRecord)
        assert len(r.rag_rule) > 10


# 20. Official_Verification loads successfully
def test_20_official_verification_loading():
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    verifications = loader.load_official_verification()

    assert len(verifications) == 5
    verified_sources = [v.source_id for v in verifications]
    assert verified_sources == ["UK-01", "UK-02", "UK-03", "EU-01", "EU-02"]
    for v in verifications:
        assert isinstance(v, OfficialVerificationRecord)
        assert v.verification == "Verified"
        assert v.official_url.startswith("http")


# 21. Reviewed Source Register contains new fields
def test_21_reviewed_source_register_new_fields():
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    sources = loader.load_source_register()

    assert len(sources) == 15
    uk_01_src = next(s for s in sources if s.source_id == "UK-01")
    assert uk_01_src.publication_date is not None and "8 April 2010" in uk_01_src.publication_date
    assert uk_01_src.effective_date is not None and "1 July 2011" in uk_01_src.effective_date
    assert uk_01_src.extraction_priority is not None and "P1" in uk_01_src.extraction_priority
    assert uk_01_src.last_checked is not None and "2026-09-24" in uk_01_src.last_checked


# 22. Legacy Week 3 workbooks full compatibility
def test_22_legacy_week_3_workbooks_full_compatibility():
    legacy_rr = RAW_DATA_DIR / ExcelWorkbookLoader.LEGACY_REGULATORY_RECORDS_FILENAME
    legacy_sr = RAW_DATA_DIR / ExcelWorkbookLoader.LEGACY_SOURCE_REGISTER_FILENAME

    if legacy_rr.exists() and legacy_sr.exists():
        legacy_loader = ExcelWorkbookLoader(
            RAW_DATA_DIR,
            regulatory_records_path=legacy_rr,
            source_register_path=legacy_sr
        )
        sources = legacy_loader.load_source_register()
        raw_records = legacy_loader.load_regulatory_records_raw()
        assert len(sources) == 15
        assert len(raw_records) == 15

        normalizer = RegulatoryDataNormalizer(sources)
        normalized = normalizer.normalize_all(raw_records)
        assert len(normalized) == 15

        # In legacy mode, require_retrieval_text=False
        validator = RegulatoryDataValidator(sources, require_retrieval_text=False)
        val_report = validator.validate_records(normalized)
        assert val_report.valid_records_count == 15
        assert not val_report.has_critical_errors


# 23. Missing Retrieval_Text fails validation appropriately
def test_23_missing_retrieval_text_fails_validation():
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    sources = loader.load_source_register()
    
    # [SYNTHETIC TEST FIXTURE] Record with missing retrieval_text
    synthetic_rec = NormalizedRegulatoryRecord(
        record_id="RR-SYNTH-NO-RETRIEVAL",
        source_id="UK-01",
        regulation="Synthetic Test Act",
        regulator="Synthetic Regulator",
        jurisdiction="UK",
        section_article="Section 1",
        title="Obligation Title",
        requirement="Paraphrased requirement text for testing.",
        validation_status="Candidate - Awaiting Approval",
        retrieval_text=None  # Missing retrieval text
    )

    validator = RegulatoryDataValidator(sources, require_retrieval_text=True)
    report = validator.validate_records([synthetic_rec])

    assert report.has_critical_errors is True
    assert report.valid_records_count == 0
    issue = next(i for i in report.issues if i.field == "retrieval_text")
    assert issue.issue_type == "ERROR"
    assert "mandatory" in issue.message


# 24. Authority level and content type preserved
def test_24_authority_level_and_content_type_preserved():
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    sources = loader.load_source_register()
    raw_records = loader.load_regulatory_records_raw()

    normalizer = RegulatoryDataNormalizer(sources)
    normalized = normalizer.normalize_all(raw_records)

    auth_levels = {r.authority_level for r in normalized}
    assert auth_levels == {"A", "B", "C", "D"}

    content_types = {r.content_type for r in normalized}
    assert "Primary Legislation" in content_types
    assert "Official Government Guidance" in content_types


# 25. Requirement is never copied into Regulatory_Text or Retrieval_Text
def test_25_requirement_never_copied_into_regulatory_text():
    loader = ExcelWorkbookLoader(RAW_DATA_DIR)
    sources = loader.load_source_register()
    raw_records = loader.load_regulatory_records_raw()

    normalizer = RegulatoryDataNormalizer(sources)
    normalized = normalizer.normalize_all(raw_records)

    for rec in normalized:
        # 1. Verbatim regulatory text must remain strictly None
        assert rec.regulatory_text is None
        # 2. Requirement paraphrase must not be identical to retrieval_text
        assert rec.requirement != rec.retrieval_text
        # 3. Retrieval_text is a composite block containing "Source:" and "Reference:"
        assert "Source:" in rec.retrieval_text
        assert "Reference:" in rec.retrieval_text
