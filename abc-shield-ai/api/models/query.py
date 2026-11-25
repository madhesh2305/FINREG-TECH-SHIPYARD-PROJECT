"""Query request model and response schema re-export for Task 11 API."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

from rag.output.structured_response import StructuredAIResponse
from config.settings import settings


class QueryRequest(BaseModel):
    """Natural-language regulatory query request contract.

    Enforces non-empty, non-whitespace queries within configured length constraints.
    Supports integration context from backend workflows (id, project_id, requirement_ids,
    advisor_advice_ids, context).
    Supports alternative query field names (prompt, text, question, message) for Builder compatibility.
    Rejects client attempts to inject server-controlled regulatory metadata or unauthorized fields.
    """

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "n1ggk9",
                "project_id": None,
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

    @model_validator(mode="before")
    @classmethod
    def resolve_query_field(cls, data: Any) -> Any:
        """Resolve alternative query field aliases (prompt, text, question, message) for Builder compatibility."""
        if isinstance(data, dict):
            if "query" not in data or not data["query"]:
                for alt_key in ("prompt", "text", "question", "message", "query_text"):
                    if alt_key in data and data[alt_key]:
                        data["query"] = data[alt_key]
                        break
        return data

    @field_validator("query")
    @classmethod
    def validate_non_whitespace(cls, value: str) -> str:
        """Ensure the query is not empty or contain only whitespace."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Query string cannot be empty or contain only whitespace.")
        return cleaned


__all__ = ["QueryRequest", "StructuredAIResponse"]
