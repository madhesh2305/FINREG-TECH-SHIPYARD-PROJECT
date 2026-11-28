from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class RegulatorySourceBase(BaseModel):
    source_title: str = Field(..., max_length=250)
    issuing_authority: str = Field(..., max_length=200)
    jurisdiction: str = Field(..., max_length=100)
    source_url: Optional[str] = Field(None, description="Official URL or verified registry reference")
    version_label: str = Field("1.0", max_length=50)
    publication_date: date
    validation_status: str = Field("PENDING", pattern="^(PENDING|VALIDATED|REJECTED)$")
    topic: str = Field("Financial Crime Compliance", max_length=150)
    relevance: str = Field("Regulatory compliance baseline obligation")
    applicability_rationale: str = Field("Pending per-project applicability verification")

class RegulatorySourceCreate(RegulatorySourceBase):
    document_name: Optional[str] = Field(None, max_length=255, description="Official document filename or reference if URL omitted")
    provenance: Optional[str] = Field(None, max_length=500, description="Source origin, registry extract, or internal verification reference")
    section_reference: Optional[str] = Field(None, max_length=150, description="Primary statutory section or article reference")
    applicability_notes: Optional[str] = Field(None, max_length=1000, description="Initial scope and applicability guidance")

class RegulatorySourceValidationRequest(BaseModel):
    decision: str = Field(..., pattern="^(APPROVED|VALIDATED|REJECTED|CHANGES_REQUESTED)$")
    reason: Optional[str] = Field(None, max_length=1000, description="Validation rationale (required for REJECTED or CHANGES_REQUESTED)")

class RegulatorySourceResponse(RegulatorySourceBase):
    model_config = ConfigDict(from_attributes=True)

    source_id: int
    retrieved_at: datetime
    created_at: datetime
    updated_at: datetime
    source_code: Optional[str] = None
    document_name: Optional[str] = None
    provenance: Optional[str] = None
    section_reference: Optional[str] = None
    applicability_notes: Optional[str] = None
    validation_state: str = "PENDING_VALIDATION"
    submitted_by_user_id: Optional[int] = None
    submitted_by_name: Optional[str] = None
    reviewer_user_id: Optional[int] = None
    reviewer_name: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    decision: Optional[str] = None
    review_reason: Optional[str] = None

class RegulatoryRequirementCreate(BaseModel):
    source_id: int = Field(..., description="Approved Regulatory Source ID for provenance linkage")
    requirement_code: str = Field(..., max_length=50, description="Unique requirement code, e.g. REQ-ABC-001")
    requirement_title: str = Field(..., max_length=250)
    requirement_text: str = Field(..., description="Full normative text of the requirement")
    applicability_status: str = Field("UNDER_REVIEW", pattern="^(APPLICABLE|NOT_APPLICABLE|UNDER_REVIEW)$")
    requirement_status: str = Field("OPEN", pattern="^(OPEN|IN_REVIEW|COMPLETED|BLOCKED)$")
    section_reference: Optional[str] = Field(None, max_length=150)
    source_version: Optional[str] = Field(None, max_length=50)
    jurisdiction: Optional[str] = Field(None, max_length=100)
    applicability_notes: Optional[str] = Field(None, max_length=1000)

class RegulatoryRequirementUpdate(BaseModel):
    requirement_title: Optional[str] = Field(None, max_length=250)
    requirement_text: Optional[str] = None
    applicability_status: Optional[str] = Field(None, pattern="^(APPLICABLE|NOT_APPLICABLE|UNDER_REVIEW)$")
    requirement_status: Optional[str] = Field(None, pattern="^(OPEN|IN_REVIEW|COMPLETED|BLOCKED)$")
    section_reference: Optional[str] = Field(None, max_length=150)
    applicability_notes: Optional[str] = Field(None, max_length=1000)

class RegulatoryRequirementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    requirement_id: int
    project_id: int
    source_id: int
    requirement_code: str
    requirement_title: str
    requirement_text: str
    applicability_status: str
    requirement_status: str
    created_at: datetime
    updated_at: datetime
    source_code: Optional[str] = None
    source_title: Optional[str] = None
    section_reference: Optional[str] = None
    source_version: Optional[str] = None
    jurisdiction: Optional[str] = None
    applicability_notes: Optional[str] = None
    validation_state: Optional[str] = None
    source_validation_status: Optional[str] = None
    project_code: Optional[str] = None
    project_name: Optional[str] = None
    source: Optional[RegulatorySourceResponse] = None
