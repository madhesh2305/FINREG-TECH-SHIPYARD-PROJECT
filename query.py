"""Query request model and response schema re-export for Task 11 API."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

from rag.output.structured_response import StructuredAIResponse
from config.settings import settings


class QueryRequest(BaseModel):
    """Natural-language regulatory query request contract.

    Enforces non-empty, non-whitespace queries within configured length constraints.
    Supports integration context from backend workflows (id, project_id, requirement_ids,
    advisor_advice_ids, context).
    Rejects client attempts to inject server-controlled regulatory metadata or unauthorized fields.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "id": "n1ggk9",
                "project_id": "PRJ-ABC-001",
                "query": "What procedures should commercial organisations implement to prevent bribery?",
                "requirement_ids": ["REQ-001", "REQ-002"],
                "advisor_advice_ids": ["ADV-UK-001"],
                "context": {
                    "jurisdiction": "UK",
                    "regulatory_area": "Anti-Bribery and Corruption",
                },
            }
        },
    )

    query: str = Field(
        ...,
        min_length=1,
        max_length=settings.query_max_length,
        description="Natural language compliance or regulatory question to evaluate against the knowledge base.",
    )
    id: Optional[str] = Field(
        None,
        description="Optional client or backend correlation request identifier.",
    )
    project_id: Optional[str] = Field(
        None,
        description="Optional client or project identifier provided by backend workflow context.",
    )
    requirement_ids: Optional[List[str]] = Field(
        None,
        description="Optional upstream requirement identifiers related to the query.",
    )
    advisor_advice_ids: Optional[List[str]] = Field(
        None,
        description="Optional legal/compliance advisor advisory note identifiers related to the query.",
    )
    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional contextual dictionary such as jurisdiction or regulatory area filter hints.",
    )

    @field_validator("query")
    @classmethod
    def validate_non_whitespace(cls, value: str) -> str:
        """Ensure the query is not empty or contain only whitespace."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Query string cannot be empty or contain only whitespace.")
        return cleaned


__all__ = ["QueryRequest", "StructuredAIResponse"]
