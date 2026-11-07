"""Runtime security policy evaluation for ABC Shield RAG.

Provides deterministic policy decisions (ALLOW, ALERT, REQUIRE_APPROVAL, BLOCK)
strictly outside the LLM, enforcing source approval, tenant boundaries,
jurisdiction constraints, and provider access rules.
"""

from enum import Enum
from typing import List, Optional, Dict, Any, Set
from pydantic import BaseModel, Field

from rag.retrieval.retriever import RetrievalResult
from rag.conflict.conflict_detector import ConflictFinding


class PolicyOutcome(str, Enum):
    """The four canonical runtime security policy outcomes."""
    ALLOW = "ALLOW"
    ALERT = "ALERT"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    BLOCK = "BLOCK"


class PolicyDecision(BaseModel):
    """Deterministic evaluation outcome from the RAG security policy gate."""
    outcome: PolicyOutcome = Field(..., description="Canonical policy outcome")
    reason: str = Field(..., description="Explanation of why this policy outcome was triggered")
    requires_human_review: bool = Field(False, description="Whether SME/compliance review is required")
    evidence_allowed: List[RetrievalResult] = Field(
        default_factory=list,
        description="Sanitized evidence chunks permitted to reach downstream processing/LLM"
    )
    blocked_count: int = Field(0, description="Count of evidence chunks blocked by policy")
    rule_applied: str = Field(..., description="Primary security rule identifier")


class RuntimeSecurityPolicy:
    """Deterministic policy gate for ABC Shield RAG execution."""

    AUTHORIZED_PROVIDERS: Set[str] = {"mock", "openai", "azure", "ollama"}

    @classmethod
    def evaluate(
        cls,
        retrieved_chunks: List[RetrievalResult],
        filter_approved_only: bool = False,
        authorized_project_id: Optional[str] = None,
        requested_jurisdiction: Optional[str] = None,
        conflicts: Optional[List[ConflictFinding]] = None,
        provider_name: Optional[str] = None,
    ) -> PolicyDecision:
        """Evaluate security rules over retrieved context and execution parameters.

        This gate is completely deterministic and runs outside LLM discretion.
        Adversarial prompt text or retrieved evidence cannot alter its decisions.
        """
        # 1. Provider authorization check (RAG-10)
        p_name = (provider_name or "mock").lower()
        if p_name not in cls.AUTHORIZED_PROVIDERS:
            return PolicyDecision(
                outcome=PolicyOutcome.BLOCK,
                reason=f"Provider '{provider_name}' is not authorized by server security policy.",
                requires_human_review=True,
                evidence_allowed=[],
                blocked_count=len(retrieved_chunks),
                rule_applied="RAG-10_PROVIDER_AUTHORIZATION",
            )

        # 2. Filter evidence by project and jurisdiction boundaries (RAG-02, RAG-14)
        allowed: List[RetrievalResult] = []
        blocked_count = 0

        for chunk in retrieved_chunks:
            # Check project boundary
            if authorized_project_id and chunk.project_id and chunk.project_id != authorized_project_id:
                blocked_count += 1
                continue

            # Check jurisdiction boundary
            if requested_jurisdiction and chunk.jurisdiction != requested_jurisdiction:
                blocked_count += 1
                continue

            allowed.append(chunk)

        # 3. Source Approval Evaluation (RAG-12)
        if filter_approved_only:
            approved_chunks = [c for c in allowed if c.is_approved_for_rag is True]
            if not approved_chunks:
                return PolicyDecision(
                    outcome=PolicyOutcome.REQUIRE_APPROVAL,
                    reason="Request requires approved evidence, but no approved records exist in the retrieved set.",
                    requires_human_review=True,
                    evidence_allowed=[],
                    blocked_count=blocked_count + len(allowed),
                    rule_applied="RAG-12_APPROVED_SOURCE_GATE",
                )
            allowed = approved_chunks

        # If all retrieved chunks were blocked by boundary checks
        if retrieved_chunks and not allowed:
            return PolicyDecision(
                outcome=PolicyOutcome.BLOCK,
                reason="All retrieved chunks violated project or jurisdiction boundary policies.",
                requires_human_review=True,
                evidence_allowed=[],
                blocked_count=blocked_count,
                rule_applied="RAG-11_BOUNDARY_ENFORCEMENT",
            )

        # 4. Conflict Evaluation (RAG-11)
        if conflicts and len(conflicts) > 0:
            return PolicyDecision(
                outcome=PolicyOutcome.ALERT,
                reason=f"Identified {len(conflicts)} documented regulatory overlap/conflict finding(s).",
                requires_human_review=True,
                evidence_allowed=allowed,
                blocked_count=blocked_count,
                rule_applied="RAG-11_CONFLICT_ALERT",
            )

        # 5. Candidate Evidence Alert (RAG-11)
        has_candidate = any(not c.is_approved_for_rag for c in allowed)
        if has_candidate:
            return PolicyDecision(
                outcome=PolicyOutcome.ALERT,
                reason="Retrieved evidence contains Candidate records awaiting SME approval.",
                requires_human_review=True,
                evidence_allowed=allowed,
                blocked_count=blocked_count,
                rule_applied="RAG-11_CANDIDATE_EVIDENCE_ALERT",
            )

        # 6. All clear (RAG-11)
        return PolicyDecision(
            outcome=PolicyOutcome.ALLOW,
            reason="All retrieved evidence conforms to authorized project, jurisdiction, and approval criteria.",
            requires_human_review=False,
            evidence_allowed=allowed,
            blocked_count=blocked_count,
            rule_applied="RAG-11_STANDARD_ALLOW",
        )
