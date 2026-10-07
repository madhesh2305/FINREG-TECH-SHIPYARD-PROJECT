from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

STATUS_NORMALIZATION = {
    "DRAFT": "DRAFT",
    "NEEDS CLARIFICATION": "DRAFT",
    "SUBMITTED": "SUBMITTED",
    "PENDING REVIEW": "SUBMITTED",
    "REVIEWED": "REVIEWED",
    "ACCEPTED": "REVIEWED",
    "ARCHIVED": "ARCHIVED",
}

STATUS_DISPLAY_MAP = {
    "DRAFT": "Needs Clarification",
    "SUBMITTED": "Pending Review",
    "REVIEWED": "Accepted",
    "ARCHIVED": "Archived",
}

class AdviceSourceLinkCreate(BaseModel):
    source_id: int = Field(..., description="Regulatory source ID referenced by this advice")
    reference_note: str = Field(..., description="Note or specific citation clause from this source")

class AdviceSourceLinkResponse(BaseModel):
    advice_source_link_id: int
    source_id: int
    reference_note: str
    source_title: Optional[str] = None
    citation_reference: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}

class AdviceCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=250, description="Title of the advisory opinion")
    advice_text: str = Field(..., min_length=5, description="Full advisory observations and analysis")
    recommendation: str = Field(..., min_length=5, description="Actionable recommendation for project owners")
    assumptions: Optional[str] = Field("", description="Assumptions or operational context")
    advice_status: Optional[str] = Field("SUBMITTED", description="Status: DRAFT, SUBMITTED, REVIEWED, or ARCHIVED")
    source_links: Optional[List[AdviceSourceLinkCreate]] = Field(default=[], description="Regulatory sources backing this advice")

class AdviceUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=250)
    advice_text: Optional[str] = Field(None, min_length=5)
    recommendation: Optional[str] = Field(None, min_length=5)
    assumptions: Optional[str] = None
    advice_status: Optional[str] = Field(None, description="Updated status: DRAFT, SUBMITTED, REVIEWED, or ARCHIVED")

class AdviceResponse(BaseModel):
    advice_id: int
    project_id: int
    advisor_profile_id: int
    advisor_name: Optional[str] = None
    advisor_organization: Optional[str] = None
    title: str
    advice_text: str
    recommendation: str
    assumptions: str
    advice_status: str
    display_status: str
    submitted_at: datetime
    updated_at: datetime
    source_links: List[AdviceSourceLinkResponse] = []

    model_config = {"from_attributes": True}
