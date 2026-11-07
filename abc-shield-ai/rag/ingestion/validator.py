"""Validator for normalized regulatory records.

Ensures mandatory field completeness, provenance consistency, validation-status integrity,
non-fabrication of regulatory text, and verification of Week 4 RAG-specific metadata.
"""

from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel, Field

from rag.ingestion.schemas import (
    NormalizedRegulatoryRecord,
    SourceRegisterRecord,
    is_sme_approved,
    CANONICAL_SME_APPROVED_STATUSES,
)


class ValidationIssue(BaseModel):
    """Specific validation notice or defect."""
    record_id: str
    field: str
    issue_type: str  # "ERROR", "WARNING", "INFO"
    message: str


class IngestionValidationReport(BaseModel):
    """Comprehensive validation summary for ingested regulatory records."""
    total_records: int = 0
    valid_records_count: int = 0
    candidate_records_count: int = 0
    approved_records_count: int = 0
    regulatory_text_available: bool = False
    all_source_ids_resolved: bool = True
    issues: List[ValidationIssue] = Field(default_factory=list)

    @property
    def has_critical_errors(self) -> bool:
        return any(issue.issue_type == "ERROR" for issue in self.issues)


class RegulatoryDataValidator:
    """Validates normalized regulatory records and checks compliance guardrails."""

    REQUIRED_FIELDS = [
        "record_id",
        "source_id",
        "regulation",
        "regulator",
        "jurisdiction",
        "section_article",
        "title",
        "requirement",
        "validation_status",
    ]

    # Valid priority prefixes derived from actual workbook values (P1 to P4)
    VALID_PRIORITY_PREFIXES = ("P1", "P2", "P3", "P4")

    def __init__(
        self,
        source_register: List[SourceRegisterRecord],
        require_retrieval_text: bool = True,
    ):
        self.valid_source_ids = {s.source_id.strip() for s in source_register if s.source_id}
        self.require_retrieval_text = require_retrieval_text

    def validate_records(self, records: List[NormalizedRegulatoryRecord]) -> IngestionValidationReport:
        """Run full validation checks across a list of normalized regulatory records."""
        report = IngestionValidationReport(total_records=len(records))
        verbatim_count = 0

        seen_record_ids: Set[str] = set()
        seen_chunk_ids: Set[str] = set()

        for rec in records:
            rec_valid = True

            # 1. Uniqueness check for Record_ID
            if rec.record_id in seen_record_ids:
                report.issues.append(
                    ValidationIssue(
                        record_id=rec.record_id,
                        field="record_id",
                        issue_type="ERROR",
                        message=f"Duplicate Record_ID detected: '{rec.record_id}'."
                    )
                )
                rec_valid = False
            seen_record_ids.add(rec.record_id)

            # 2. Uniqueness check for Chunk_ID (if present)
            if rec.chunk_id:
                if rec.chunk_id in seen_chunk_ids:
                    report.issues.append(
                        ValidationIssue(
                            record_id=rec.record_id,
                            field="chunk_id",
                            issue_type="ERROR",
                            message=f"Duplicate Chunk_ID detected: '{rec.chunk_id}'."
                        )
                    )
                    rec_valid = False
                seen_chunk_ids.add(rec.chunk_id)

            # 3. Required field completeness
            for field_name in self.REQUIRED_FIELDS:
                val = getattr(rec, field_name, None)
                if not val or not str(val).strip():
                    report.issues.append(
                        ValidationIssue(
                            record_id=rec.record_id,
                            field=field_name,
                            issue_type="ERROR",
                            message=f"Mandatory field '{field_name}' is missing or empty."
                        )
                    )
                    rec_valid = False

            # 4. Source provenance check (foreign key to source register)
            if rec.source_id not in self.valid_source_ids:
                report.issues.append(
                    ValidationIssue(
                        record_id=rec.record_id,
                        field="source_id",
                        issue_type="ERROR",
                        message=f"Source ID '{rec.source_id}' does not match any entry in the Source Register."
                    )
                )
                report.all_source_ids_resolved = False
                rec_valid = False

            # 5. Validation status integrity and approval gate
            status_raw = rec.validation_status or ""
            norm_status = " ".join(status_raw.strip().lower().split())

            if is_sme_approved(status_raw):
                report.approved_records_count += 1
                if not rec.is_approved_for_rag:
                    report.issues.append(
                        ValidationIssue(
                            record_id=rec.record_id,
                            field="is_approved_for_rag",
                            issue_type="WARNING",
                            message=f"Record '{rec.record_id}' has SME-approved status but is_approved_for_rag is False."
                        )
                    )
            else:
                # Fails closed: non-approved status must never have is_approved_for_rag = True
                if rec.is_approved_for_rag:
                    report.issues.append(
                        ValidationIssue(
                            record_id=rec.record_id,
                            field="is_approved_for_rag",
                            issue_type="ERROR",
                            message=(
                                f"Record '{rec.record_id}' was flagged as approved for RAG (is_approved_for_rag=True), "
                                f"but its validation status '{rec.validation_status}' is not canonical SME-approved."
                            )
                        )
                    )
                    rec_valid = False

                if "candidate" in norm_status or "awaiting" in norm_status or "pending" in norm_status:
                    report.candidate_records_count += 1
                elif norm_status == "validated":
                    # Data quality validation is distinct from SME approval
                    report.issues.append(
                        ValidationIssue(
                            record_id=rec.record_id,
                            field="validation_status",
                            issue_type="INFO",
                            message=f"Record '{rec.record_id}' has data quality status 'validated' which does not confer SME approval or RAG eligibility."
                        )
                    )
                elif norm_status in ("rejected", "draft", "unverified"):
                    pass
                else:
                    report.issues.append(
                        ValidationIssue(
                            record_id=rec.record_id,
                            field="validation_status",
                            issue_type="WARNING",
                            message=f"Unrecognized validation status: '{rec.validation_status}'."
                        )
                    )

            # 6. Official source URL presence
            if not rec.official_source or not str(rec.official_source).startswith("http"):
                report.issues.append(
                    ValidationIssue(
                        record_id=rec.record_id,
                        field="official_source",
                        issue_type="WARNING",
                        message=f"Official source URL is missing or not a valid HTTP URL: '{rec.official_source}'."
                    )
                )

            # 7. Regulatory text vs Requirement distinction check
            if rec.regulatory_text is not None and str(rec.regulatory_text).strip():
                verbatim_count += 1
                if str(rec.regulatory_text).strip() == str(rec.requirement).strip():
                    report.issues.append(
                        ValidationIssue(
                            record_id=rec.record_id,
                            field="regulatory_text",
                            issue_type="WARNING",
                            message="regulatory_text is identical to requirement paraphrase; possible conflation."
                        )
                    )
            else:
                # Expected in current workbook; log as informational
                report.issues.append(
                    ValidationIssue(
                        record_id=rec.record_id,
                        field="regulatory_text",
                        issue_type="INFO",
                        message="Verbatim regulatory_text is null (only requirement paraphrase provided in source files)."
                    )
                )

            # 8. Week 4 Retrieval_Text validation
            if self.require_retrieval_text:
                if not rec.retrieval_text or not isinstance(rec.retrieval_text, str) or not rec.retrieval_text.strip():
                    report.issues.append(
                        ValidationIssue(
                            record_id=rec.record_id,
                            field="retrieval_text",
                            issue_type="ERROR",
                            message="retrieval_text is mandatory for Week 4 RAG knowledge but missing or empty."
                        )
                    )
                    rec_valid = False
                elif len(rec.retrieval_text.strip()) < 20:
                    report.issues.append(
                        ValidationIssue(
                            record_id=rec.record_id,
                            field="retrieval_text",
                            issue_type="ERROR",
                            message="retrieval_text is too short to contain usable evidence."
                        )
                    )
                    rec_valid = False

            # 9. Week 4 Citation_Label validation (if supplied)
            if rec.citation_label is not None:
                if not rec.citation_label.strip():
                    report.issues.append(
                        ValidationIssue(
                            record_id=rec.record_id,
                            field="citation_label",
                            issue_type="WARNING",
                            message="citation_label is empty."
                        )
                    )

            # 10. Week 4 Retrieval_Priority validation (if supplied)
            if rec.retrieval_priority:
                pri = rec.retrieval_priority.strip()
                if not any(pri.startswith(pfx) for pfx in self.VALID_PRIORITY_PREFIXES):
                    report.issues.append(
                        ValidationIssue(
                            record_id=rec.record_id,
                            field="retrieval_priority",
                            issue_type="WARNING",
                            message=f"retrieval_priority '{rec.retrieval_priority}' does not match expected prefixes {self.VALID_PRIORITY_PREFIXES}."
                        )
                    )

            # 11. Week 4 Retrieval_Tags validation
            if rec.retrieval_tags is not None and not isinstance(rec.retrieval_tags, list):
                report.issues.append(
                    ValidationIssue(
                        record_id=rec.record_id,
                        field="retrieval_tags",
                        issue_type="ERROR",
                        message="retrieval_tags must be a list of strings."
                    )
                )
                rec_valid = False

            # 12. Authority_Rule validation (if supplied)
            if rec.authority_rule is not None and not rec.authority_rule.strip():
                report.issues.append(
                    ValidationIssue(
                        record_id=rec.record_id,
                        field="authority_rule",
                        issue_type="WARNING",
                        message="authority_rule is empty string."
                    )
                )

            # 13. RAG_Instruction validation (if supplied)
            if rec.rag_instruction is not None and not rec.rag_instruction.strip():
                report.issues.append(
                    ValidationIssue(
                        record_id=rec.record_id,
                        field="rag_instruction",
                        issue_type="WARNING",
                        message="rag_instruction is empty string."
                    )
                )

            if rec_valid:
                report.valid_records_count += 1

        report.regulatory_text_available = (verbatim_count > 0)
        return report
