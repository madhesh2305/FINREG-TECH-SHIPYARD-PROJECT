from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

class RetrievalRequest(BaseModel):
    query: str = Field(..., min_length=3, description="Regulatory requirement or compliance query")
    top_k: int = Field(5, ge=1, le=20, description="Maximum number of grounded sources to retrieve")

class CitationItem(BaseModel):
    source_id: int
    source_title: str
    issuing_authority: str
    jurisdiction: str
    source_url: str
    topic: str
    applicability_rationale: str
    relevance_summary: str

class RetrievalResponse(BaseModel):
    query: str
    status: str = Field(..., description="Status: 'GROUNDED_EVIDENCE_FOUND' or 'NO_SOURCE_FOUND'")
    citations: List[CitationItem] = []
    disclaimer: str = "AI retrieval provides source citations for human review. It does not provide legal advice or regulatory certification."

class RAGAnalyzeRequest(BaseModel):
    query: str = Field(..., description="Natural language regulatory or compliance question")
    projectId: Optional[Union[int, str]] = Field(None, description="Project ID or project code for authorization context")
    project_id: Optional[Union[int, str]] = Field(None, description="Snake_case alias for projectId")
    role: Optional[str] = Field(None, description="Optional user role hint")
    requirement_ids: Optional[List[str]] = Field(None, description="Optional project requirement IDs to scope analysis")
    advisor_advice_ids: Optional[List[Union[int, str]]] = Field(None, description="Optional advice record IDs to compare")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional context hints (e.g. jurisdiction, filter_approved_only)")

    @property
    def resolved_project_id(self) -> Optional[Union[int, str]]:
        return self.projectId if self.projectId is not None else self.project_id

class AdviceItemPayload(BaseModel):
    advice_id: str = Field(..., description="Advice identifier (e.g. ADV-001)")
    advice_text: str = Field(..., min_length=1, max_length=4000, description="Natural language advice content")
    advisor_name: Optional[str] = Field(None, description="Advisor name or title")
    source_reference: Optional[str] = Field(None, description="Claimed source reference")

class RAGCompareRequest(BaseModel):
    comparison_id: Optional[str] = Field(None, description="Correlation comparison identifier")
    projectId: Optional[Union[int, str]] = Field(None, description="Project ID for authorization")
    project_id: Optional[Union[int, str]] = Field(None, description="Snake_case alias for projectId")
    advisor_1: AdviceItemPayload = Field(..., description="First advisor position")
    advisor_2: AdviceItemPayload = Field(..., description="Second advisor position")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional context parameters (e.g. jurisdiction)")

    @property
    def resolved_project_id(self) -> Optional[Union[int, str]]:
        return self.projectId if self.projectId is not None else self.project_id
