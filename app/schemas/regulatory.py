from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class RegulatorySourceBase(BaseModel):
    source_title: str = Field(..., max_length=250)
    issuing_authority: str = Field(..., max_length=200)
    jurisdiction: str = Field(..., max_length=100)
    source_url: str = Field(..., description="Official URL or verified registry reference")
    version_label: str = Field(..., max_length=50)
    publication_date: date
    validation_status: str = Field("VALIDATED", pattern="^(PENDING|VALIDATED|REJECTED)$")
    topic: str = Field(..., max_length=150)
    relevance: str
    applicability_rationale: str

class RegulatorySourceCreate(RegulatorySourceBase):
    pass

class RegulatorySourceResponse(RegulatorySourceBase):
    model_config = ConfigDict(from_attributes=True)

    source_id: int
    retrieved_at: datetime
    created_at: datetime
    updated_at: datetime

class RegulatoryRequirementCreate(BaseModel):
    source_id: int = Field(..., description="Approved Regulatory Source ID for provenance linkage")
    requirement_code: str = Field(..., max_length=50, description="Unique requirement code, e.g. REQ-ABC-001")
    requirement_title: str = Field(..., max_length=250)
    requirement_text: str = Field(..., description="Full normative text of the requirement")
    applicability_status: str = Field("APPLICABLE", pattern="^(APPLICABLE|NOT_APPLICABLE|UNDER_REVIEW)$")
    requirement_status: str = Field("OPEN", pattern="^(OPEN|IN_REVIEW|COMPLETED|BLOCKED)$")

class RegulatoryRequirementUpdate(BaseModel):
    requirement_title: Optional[str] = Field(None, max_length=250)
    requirement_text: Optional[str] = None
    applicability_status: Optional[str] = Field(None, pattern="^(APPLICABLE|NOT_APPLICABLE|UNDER_REVIEW)$")
    requirement_status: Optional[str] = Field(None, pattern="^(OPEN|IN_REVIEW|COMPLETED|BLOCKED)$")

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
    source: Optional[RegulatorySourceResponse] = None
