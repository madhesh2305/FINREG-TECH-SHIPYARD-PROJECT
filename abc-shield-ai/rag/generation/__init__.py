"""Generation package for ABC Shield / FinRegTech ShipYard.

Exposes provider-independent LLM interfaces, prompt templates, and grounded generator.
"""

from rag.generation.prompts import (
    SYSTEM_GROUNDING_PROMPT,
    build_evidence_context,
    build_user_prompt,
)
from rag.generation.llm_interface import (
    BaseLLMProvider,
    MockLLMProvider,
    OpenAILLMProvider,
    OllamaLLMProvider,
    get_llm_provider,
)
from rag.generation.grounded_generator import (
    GroundedResponse,
    GroundedGenerator,
    StagedGroundedGenerator,
    CANDIDATE_APPROVAL_WARNING,
)
from rag.generation.citations import (
    Citation,
    ProvenanceRecord,
    CitationBuilder,
)
from rag.generation.gap_handler import (
    GapType,
    GapResult,
    GapHandler,
)

__all__ = [
    "SYSTEM_GROUNDING_PROMPT",
    "build_evidence_context",
    "build_user_prompt",
    "BaseLLMProvider",
    "MockLLMProvider",
    "OpenAILLMProvider",
    "OllamaLLMProvider",
    "get_llm_provider",
    "GroundedResponse",
    "GroundedGenerator",
    "StagedGroundedGenerator",
    "CANDIDATE_APPROVAL_WARNING",
    "Citation",
    "ProvenanceRecord",
    "CitationBuilder",
    "GapType",
    "GapResult",
    "GapHandler",
]
