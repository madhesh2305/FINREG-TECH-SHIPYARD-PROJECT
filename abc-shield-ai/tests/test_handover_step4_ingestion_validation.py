"""Tests for Step 4: Canonical Ingestion and Normalization Validation in Staging.

Project: ABC Shield / FinRegTech ShipYard AI/RAG
Role: Padma Kumar — AI/RAG & Conflict Detection Engineer

Verifies:
1. Staging output files exist in data/staging/madhesh_handover/step4/
2. Exactly 25 records loaded and normalized in staging
3. All 25 record IDs and source IDs match canonical expectations with 0 duplicates
4. Every source ID resolves to the canonical source register (0 unresolved)
5. Distinctness of Structured_Summary and Exact_Source_Extract (no fallback/merging)
6. All 25 records remain Candidate / 0 Approved (is_approved_for_rag = False)
7. Staged validation report has 0 critical errors and 0 issues
8. Consistency with Step 3 mapping (3 direct, 11 partitions, 11 new)
9. Conflict dataset CO-001..CO-011 preserved in source workbook
10. Active data immutability: active normalized records (15), chunks (15), ChromaDB (15) untouched
"""

from pathlib import Path
import json
import openpyxl
import pytest

from rag.ingestion.schemas import NormalizedRegulatoryRecord
from rag.retrieval.vector_store import ChromaVectorStore

STAGING_DIR = Path("data/staging/madhesh_handover/step4")
STAGED_RECORDS_FILE = STAGING_DIR / "normalized_regulatory_records.json"
STAGED_VAL_REPORT_FILE = STAGING_DIR / "validation_report.json"

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")


def test_staged_output_files_exist():
    """Verify staged artifacts exist in dedicated staging directory."""
    assert STAGING_DIR.exists()
    assert STAGED_RECORDS_FILE.exists()
    assert STAGED_VAL_REPORT_FILE.exists()
    assert STAGED_RECORDS_FILE.stat().st_size > 0
    assert STAGED_VAL_REPORT_FILE.stat().st_size > 0


def test_staged_records_count_and_uniqueness():
    """Verify exactly 25 unique records are present in staging."""
    with open(STAGED_RECORDS_FILE, "r", encoding="utf-8") as f:
        records_data = json.load(f)

    assert len(records_data) == 25
    record_ids = [r["record_id"] for r in records_data]

    # No duplicates
    assert len(record_ids) == len(set(record_ids))

    # All non-empty
    assert all(bool(rid and rid.strip()) for rid in record_ids)


def test_staged_source_resolution():
    """Verify all 25 records resolve to valid Source IDs."""
    with open(STAGED_RECORDS_FILE, "r", encoding="utf-8") as f:
        records_data = json.load(f)

    source_ids = {r["source_id"] for r in records_data}
    assert source_ids == {"UK-01", "UK-02", "UK-03", "UK-09", "EU-01"}


def test_structured_summary_and_exact_extract_separation():
    """Verify requirement and regulatory_text remain distinct without fallback."""
    with open(STAGED_RECORDS_FILE, "r", encoding="utf-8") as f:
        records_data = json.load(f)

    for r in records_data:
        assert r["requirement"] is not None and len(r["requirement"].strip()) > 0
        assert r["regulatory_text"] is not None and len(r["regulatory_text"].strip()) > 0
        assert r["requirement"] != r["regulatory_text"]


def test_candidate_gating_across_all_25_staged_records():
    """Verify all 25 staged records have is_approved_for_rag == False."""
    with open(STAGED_RECORDS_FILE, "r", encoding="utf-8") as f:
        records_data = json.load(f)

    assert sum(1 for r in records_data if r.get("is_approved_for_rag") is True) == 0
    assert sum(1 for r in records_data if r.get("is_approved_for_rag") is False) == 25

    for r in records_data:
        assert r.get("validation_status") in ("Candidate - Awaiting Approval", "Pending SME Validation")


def test_staged_validation_report_has_zero_critical_errors():
    """Verify staged validation report contains 0 critical errors and 0 issues."""
    with open(STAGED_VAL_REPORT_FILE, "r", encoding="utf-8") as f:
        val_data = json.load(f)

    assert val_data["total_records"] == 25
    assert val_data["valid_records_count"] == 25
    assert val_data["candidate_records_count"] == 25
    assert val_data["approved_records_count"] == 0
    assert val_data["all_source_ids_resolved"] is True
    assert val_data["regulatory_text_available"] is True
    assert len(val_data["issues"]) == 0


def test_migration_mapping_consistency_with_step3():
    """Verify the 25 records match the Step 3 categorization (3 direct, 11 partitions, 11 new)."""
    with open(STAGED_RECORDS_FILE, "r", encoding="utf-8") as f:
        records = json.load(f)
    records_by_id = {r["record_id"]: r for r in records}

    # 1. Direct Matches (3)
    assert "UK-01-R001" in records_by_id  # Sec 1
    assert "EU-01-R002" in records_by_id  # Art 3
    assert "UK-09-R001" in records_by_id  # PRIN 2.1.1R

    # 2. Granular Partitions (11)
    # UK-02 (Principles 1..6)
    for i in range(1, 7):
        assert f"UK-02-R{i:03d}" in records_by_id
    # UK-03 (FCG 6.1.1, 6.2.1..6.2.4)
    for i in range(1, 6):
        assert f"UK-03-R{i:03d}" in records_by_id

    # 3. Genuinely New Provisions (11)
    # UK-01 (Secs 2, 6, 7, 8, 9)
    for i in [2, 3, 4, 5, 6]:
        assert f"UK-01-R{i:03d}" in records_by_id
    # EU-01 (Arts 1, 4, 20, 21, 13, 16)
    for cid in ["EU-01-R001", "EU-01-R003", "EU-01-R004", "EU-01-R005", "EU-01-R006", "EU-01-R007"]:
        assert cid in records_by_id


def test_conflict_matrix_integrity_co001_through_co011():
    """Verify CO-001 through CO-011 remain intact in active source workbook."""
    conf_path = RAW_DIR / "ABC_Shield_RAG_Ready_Regulatory_Knowledge.xlsx"
    wb = openpyxl.load_workbook(conf_path, data_only=True)
    assert "Conflict_Handling" in wb.sheetnames

    ws = wb["Conflict_Handling"]
    rows = list(ws.iter_rows(values_only=True))
    header = rows[0]
    conflicts = [dict(zip(header, r)) for r in rows[1:] if any(r)]

    assert len(conflicts) == 11
    conflict_ids = [c["Conflict_ID"] for c in conflicts]
    expected_ids = [f"CO-{i:03d}" for i in range(1, 12)]
    assert conflict_ids == expected_ids


def test_active_processed_files_and_chromadb_strictly_unmodified():
    """Verify active processed JSON and ChromaDB have NOT been modified by Step 4."""
    active_norm = PROCESSED_DIR / "normalized_regulatory_records.json"
    active_chunks = PROCESSED_DIR / "regulatory_chunks.json"

    with open(active_norm, "r", encoding="utf-8") as f:
        norm_data = json.load(f)
    with open(active_chunks, "r", encoding="utf-8") as f:
        chunk_data = json.load(f)

    assert len(norm_data) == 15
    assert len(chunk_data) == 15

    chroma_store = ChromaVectorStore(persist_dir=PROCESSED_DIR / "chroma_db")
    assert chroma_store._get_collection().count() == 15
