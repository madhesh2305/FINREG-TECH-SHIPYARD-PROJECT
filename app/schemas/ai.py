from typing import List, Optional
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
