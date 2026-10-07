from typing import List
from sqlalchemy.orm import Session
from app.models.regulatory import RegulatorySource
from app.schemas.ai import CitationItem, RetrievalRequest, RetrievalResponse

def retrieve_grounded_sources(db: Session, project_id: int, request: RetrievalRequest) -> RetrievalResponse:
    """
    Grounded regulatory retrieval baseline.
    Rules:
    - Queries approved sources and project requirements
    - Returns source citations only when relevant evidence exists
    - Never fabricates citations
    - Returns 'NO_SOURCE_FOUND' when no suitable source matches
    """
    tokens = [t.lower() for t in request.query.split() if len(t) > 2]
    sources = db.query(RegulatorySource).filter(RegulatorySource.validation_status == "VALIDATED").all()

    matched: List[CitationItem] = []
    for s in sources:
        searchable_text = f"{s.source_title} {s.topic} {s.relevance} {s.applicability_rationale}".lower()
        score = sum(1 for t in tokens if t in searchable_text)
        if score > 0:
            matched.append((score, CitationItem(
                source_id=s.source_id,
                source_title=s.source_title,
                issuing_authority=s.issuing_authority,
                jurisdiction=s.jurisdiction,
                source_url=s.source_url,
                topic=s.topic,
                applicability_rationale=s.applicability_rationale,
                relevance_summary=s.relevance[:200] + "..." if len(s.relevance) > 200 else s.relevance
            )))

    matched.sort(key=lambda x: x[0], reverse=True)
    citations = [item[1] for item in matched[:request.top_k]]

    if citations:
        status = "GROUNDED_EVIDENCE_FOUND"
    else:
        status = "NO_SOURCE_FOUND"

    return RetrievalResponse(
        query=request.query,
        status=status,
        citations=citations
    )
