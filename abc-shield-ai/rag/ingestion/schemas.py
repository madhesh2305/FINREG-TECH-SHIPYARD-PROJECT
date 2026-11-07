"""Pydantic schemas for regulatory records, source registers, chunks, and RAG controls.

These schemas enforce strict typing, metadata preservation, and validation-status
integrity according to the ABC Shield regulatory framework.
"""

from typing import Optional, List, Dict, Any, Set
from pydantic import BaseModel, Field, field_validator, model_validator

# Canonical status strings that explicitly represent SME approval
CANONICAL_SME_APPROVED_STATUSES: Set[str] = {"approved", "sme approved"}


def is_sme_approved(status: Optional[str]) -> bool:
    """Determine whether a validation status explicitly represents canonical SME approval.

    Distinguishes SME approval from data quality validation, official source verification,
    and candidate/pending states. Fails closed on any unknown, ambiguous, or substring patterns.
    """
    if not status:
        return False
    norm = " ".join(str(status).strip().lower().split())
    return norm in CANONICAL_SME_APPROVED_STATUSES


class DataDictionaryEntry(BaseModel):
    """Entry from ABC Shield Data Dictionary."""
    field_name: str = Field(..., description="Field Name in data dictionary")
    description: str = Field(..., description="Description of the field")
    example: Optional[str] = Field(None, description="Example value")
    required: bool = Field(False, description="Whether the field is marked required in the dictionary")


class SourceRegisterRecord(BaseModel):
    """Source-level record from ABC_Shield_Source_Register (supports Week 3 & Week 4 reviewed formats)."""
    source_id: str = Field(..., description="Unique Source ID (e.g. UK-01, EU-01)")
    source_name: str = Field(..., description="Official title/name of the source")
    issuing_authority: str = Field(..., description="Authority issuing the source")
    jurisdiction: str = Field(..., description="Jurisdiction (e.g. UK, EU)")
    source_type: str = Field(..., description="Type of source (Primary Legislation, Guidance, etc.)")
    authority_level: str = Field(..., description="Authority classification level (A, B, C, D)")
    publication_effective_date: Optional[str] = Field(None, description="Publication or effective date (legacy combined field)")
    version_last_updated: Optional[str] = Field(None, description="Version or last updated timestamp")
    official_link_reference: Optional[str] = Field(None, description="Official canonical URL or link")
    topic: Optional[str] = Field(None, description="Regulatory topic(s)")
    status: str = Field(..., description="Status in source register (e.g. Candidate - Awaiting Approval)")
    approval_validator: Optional[str] = Field(None, description="Approval/Validator name if validated")
    notes_limitations: Optional[str] = Field(None, description="Source-level limitations and notes")

    # New Week 4 Source Register fields
    adoption_date: Optional[str] = Field(None, description="Date of adoption where applicable")
    publication_date: Optional[str] = Field(None, description="Official journal or formal publication date")
    effective_date: Optional[str] = Field(None, description="Structured entry-into-force or application date")
    abc_shield_relevance: Optional[str] = Field(None, description="ABC Shield project relevance and in-scope rationale")
    extraction_priority: Optional[str] = Field(None, description="Source extraction priority (P1, P2, P3, P4)")
    legal_regulatory_effect: Optional[str] = Field(None, description="Preliminary legal/regulatory effect screening note")
    sme_decision_date_comments: Optional[str] = Field(None, description="SME approval decision date and comments")
    last_checked: Optional[str] = Field(None, description="Date the official source was last audited/checked")
    source_qa_note: Optional[str] = Field(None, description="Source verification or QA audit note")

    # Canonical handover fields
    regulatory_layer: Optional[str] = Field(None, description="Regulatory Layer (e.g. Primary Law, Statutory Guidance)")
    corpus_status_current: Optional[str] = Field(None, description="Current corpus extraction status")
    corpus_record_count: Optional[int] = Field(None, description="Extracted record count in corpus")
    reconciliation_note: Optional[str] = Field(None, description="Source reconciliation note")


class SourceControlRecord(BaseModel):
    """Source control and approval gating entry from Source_Control sheet."""
    source_id: str = Field(..., description="Unique Source ID (e.g. UK-01, EU-01)")
    source_name: str = Field(..., description="Source Name")
    jurisdiction: str = Field(..., description="Jurisdiction (UK, EU)")
    source_type: str = Field(..., description="Source Type")
    authority_level: str = Field(..., description="Authority Level (A, B, C, D)")
    topic: Optional[str] = Field(None, description="Topic")
    status: str = Field(..., description="Source status")
    extraction_priority: Optional[str] = Field(None, description="Extraction Priority")
    official_link_reference: Optional[str] = Field(None, description="Official Link/Reference")
    abc_shield_relevance: Optional[str] = Field(None, description="ABC Shield project relevance")
    legal_regulatory_effect: Optional[str] = Field(None, description="Preliminary legal/regulatory effect screening note")
    notes_limitations: Optional[str] = Field(None, description="Notes/limitations")
    rag_use: Optional[str] = Field(None, description="RAG use guideline")
    approval_gate: str = Field(..., description="Approval Gate status (e.g. Candidate - Awaiting Approval)")


class ConflictOverlapRecord(BaseModel):
    """Pre-identified conflict or overlap relationship from Conflict Overlap / Conflict_Handling sheet."""
    conflict_id: str = Field(..., description="Identifier for overlap/conflict entry (e.g. CO-001)")
    topic: str = Field(..., description="Topic area of the overlap")
    source_id_1: str = Field(..., description="First source identifier")
    source_1: str = Field(..., description="First source name")
    source_id_2: str = Field(..., description="Second source identifier")
    source_2: str = Field(..., description="Second source name")
    relationship: str = Field(..., description="Relationship type (e.g. Overlap - complementary)")
    requirement_comparison: Optional[str] = Field(None, description="Comparison of requirements")
    scope_difference: Optional[str] = Field(None, description="Difference in legal or operational scope")
    authority_difference: Optional[str] = Field(None, description="Difference in authority levels")
    version_effective_date_difference: Optional[str] = Field(None, description="Difference in dates/versions")
    conflict_status: str = Field(..., description="Status (e.g. No direct conflict identified)")
    rag_use: Optional[str] = Field(None, description="Guidance for RAG retrieval priority")


class RAGRuleRecord(BaseModel):
    """Rule from RAG_Rules sheet governing retrieval, guidance separation, citations, and gates."""
    rule_id: str = Field(..., description="Unique rule ID (e.g. RAG-01)")
    rule_type: str = Field(..., description="Rule category / type")
    rag_rule: str = Field(..., description="Text of the RAG rule")
    implementation_note: Optional[str] = Field(None, description="Technical implementation notes")


class OfficialVerificationRecord(BaseModel):
    """Record from Official_Verification sheet tracking primary source verification."""
    source_id: str = Field(..., description="Source ID verified (e.g. UK-01)")
    source_name: str = Field(..., description="Official name of the source")
    official_origin: Optional[str] = Field(None, description="Official issuing origin / platform")
    verification: str = Field(..., description="Verification status (e.g. Verified)")
    official_url: Optional[str] = Field(None, description="Canonical official URL")
    verification_note: Optional[str] = Field(None, description="Verification details and audit note")


class NormalizedRegulatoryRecord(BaseModel):
    """Normalized internal regulatory record with joined source metadata.

    Preserves strict separation between verbatim regulatory text (which may be null
    if unavailable in the source data), paraphrased requirement summaries, and
    retrieval text blocks.
    """
    record_id: str = Field(..., description="Unique record identifier (e.g. RR-UK-01)")
    source_id: str = Field(..., description="Linked source identifier (e.g. UK-01)")
    regulation: str = Field(..., description="Name of the regulation or regulatory instrument")
    regulator: str = Field(..., description="Issuing authority / regulator")
    jurisdiction: str = Field(..., description="Geographic or legal jurisdiction (e.g. UK, EU)")
    section_article: str = Field(..., description="Specific section, article, or principle reference")
    title: str = Field(..., description="Title or descriptive header of the section")
    
    # Strict separation between verbatim regulatory text, requirement paraphrase, and retrieval text
    regulatory_text: Optional[str] = Field(
        None,
        description="Verbatim approved text from official legislation. Null if unavailable in source files."
    )
    requirement: str = Field(
        ...,
        description="Paraphrased regulatory requirement summary from source records."
    )
    summary: Optional[str] = Field(
        None,
        description="Structured summary if separately provided. Defaults to None."
    )
    
    topic: Optional[str] = Field(None, description="Regulatory topic taxonomy")
    official_source: Optional[str] = Field(None, description="Canonical official URL or link")
    version_date: Optional[str] = Field(None, description="Version or last updated timestamp")
    effective_date: Optional[str] = Field(None, description="Effective date")
    validation_status: str = Field(..., description="Validation status (e.g. Candidate - Awaiting Approval)")
    validation_date: Optional[str] = Field(None, description="Date of extraction validation / handover review")

    # Extended provenance fields preserved from input files
    applicability: Optional[str] = Field(None, description="Scope of applicability")
    relevance_to_project: Optional[str] = Field(None, description="Project context")
    notes_limitations: Optional[str] = Field(None, description="Record-level limitations and notes")
    source_type: Optional[str] = Field(None, description="Inherited from source register (e.g. Primary Legislation)")
    authority_level: Optional[str] = Field(None, description="Authority classification (A, B, C, D)")
    source_notes: Optional[str] = Field(None, description="Source register notes/limitations")

    # Authoritative gating flag (computed/validated)
    is_approved_for_rag: bool = Field(
        False,
        description="Whether this record is approved for authoritative RAG generation."
    )

    # Week 4 RAG-Specific Fields
    chunk_id: Optional[str] = Field(None, description="Upstream pre-assigned chunk ID (e.g. RR-UK-01-C01)")
    content_type: Optional[str] = Field(None, description="Specific content classification (e.g. Primary Legislation, Statutory Guidance)")
    retrieval_text: Optional[str] = Field(None, description="Context-rich evidence text combining Source, Reference, Topic, Requirement, and Applicability")
    retrieval_tags: List[str] = Field(default_factory=list, description="Parsed keyword tags for search and filtering")
    citation_label: Optional[str] = Field(None, description="Preformatted citation label (e.g. UK-01 | Bribery Act 2010 | Section 1)")
    retrieval_priority: Optional[str] = Field(None, description="Extraction and retrieval priority (P1, P2, P3, P4)")
    authority_rule: Optional[str] = Field(None, description="Legal hierarchy and bindingness guidance")
    rag_instruction: Optional[str] = Field(None, description="Generation and retrieval instructions")
    official_source_check_note: Optional[str] = Field(None, description="Source verification check note")

    @model_validator(mode="after")
    def check_approval_flag(self) -> "NormalizedRegulatoryRecord":
        """Fail closed: Only explicitly documented canonical SME approval statuses can produce True.

        Candidate, pending, unverified, data quality validated, or ambiguous statuses strictly evaluate to False.
        """
        self.is_approved_for_rag = is_sme_approved(self.validation_status)
        return self


class RegulatoryChunk(BaseModel):
    """Chunk prepared for downstream RAG processing.

    Preserves 100% of parent record metadata and explicit provenance pointers.
    """
    chunk_id: str = Field(..., description="Unique chunk identifier (e.g. RR-UK-01-C01)")
    record_id: str = Field(..., description="Parent record ID")
    source_id: str = Field(..., description="Parent source ID")
    regulation: str = Field(..., description="Regulation name")
    regulator: str = Field(..., description="Issuing authority / regulator")
    jurisdiction: str = Field(..., description="Jurisdiction (UK, EU)")
    section_article: str = Field(..., description="Section / Article reference")
    title: str = Field(..., description="Section / requirement title")
    text: str = Field(..., description="Chunk text content derived strictly from source requirement or retrieval text")
    
    # Provenance and text-type distinction
    text_type: str = Field("requirement_paraphrase", description="'regulatory_text', 'requirement_paraphrase', or 'retrieval_text'")
    requirement: str = Field(..., description="Original requirement string")
    regulatory_text: Optional[str] = Field(None, description="Verbatim regulatory text if available")
    summary: Optional[str] = Field(None, description="Summary if available")
    
    topic: Optional[str] = Field(None, description="Topic classification")
    official_source: Optional[str] = Field(None, description="Official URL")
    version_date: Optional[str] = Field(None, description="Version/date")
    effective_date: Optional[str] = Field(None, description="Effective date")
    validation_status: str = Field(..., description="Preserved validation status")
    validation_date: Optional[str] = Field(None, description="Date of extraction validation / handover review")
    
    # Metadata for retrieval ranking & filtering
    authority_level: Optional[str] = Field(None, description="Authority Level A/B/C/D")
    source_type: Optional[str] = Field(None, description="Source Type")
    is_approved_for_rag: bool = Field(False, description="Authoritative approval flag")
    chunk_index: int = Field(0, description="0-indexed position within parent record")
    total_chunks: int = Field(1, description="Total chunks derived from parent record")

    # Optional Week 4 fields for W4.5 compatibility
    content_type: Optional[str] = Field(None, description="Specific content classification")
    retrieval_text: Optional[str] = Field(None, description="Retrieval text block")
    retrieval_tags: List[str] = Field(default_factory=list, description="Parsed keyword tags")
    citation_label: Optional[str] = Field(None, description="Citation label")
    retrieval_priority: Optional[str] = Field(None, description="Retrieval priority")
    authority_rule: Optional[str] = Field(None, description="Authority rule")
    rag_instruction: Optional[str] = Field(None, description="RAG instruction")
    official_source_check_note: Optional[str] = Field(None, description="Official source check note")

    @model_validator(mode="after")
    def check_approval_flag(self) -> "RegulatoryChunk":
        """Fail closed: Only explicitly documented canonical SME approval statuses can produce True."""
        self.is_approved_for_rag = is_sme_approved(self.validation_status)
        return self

