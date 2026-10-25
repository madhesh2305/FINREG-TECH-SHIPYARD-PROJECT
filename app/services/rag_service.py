"""Client adapter and response mapper for the ABC Shield AI/RAG microservice."""

import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

import httpx

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError, ValidationError

logger = logging.getLogger(__name__)


class RAGServiceClient:
    """HTTP client communicating with the isolated ABC Shield AI/RAG FastAPI microservice."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.base_url = (base_url or settings.RAG_SERVICE_URL).rstrip("/")
        self.timeout = timeout or settings.RAG_SERVICE_TIMEOUT_SECONDS

    def check_health(self) -> Dict[str, Any]:
        """Query the remote RAG microservice health endpoint."""
        url = f"{self.base_url}/api/v1/health"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "status": "connected",
                        "service_status": data.get("status", "ok"),
                        "chromadb_status": data.get("chromadb_status", "connected"),
                        "rag_pipeline_initialized": data.get("rag_pipeline_initialized", True),
                        "details": data,
                    }
                return {
                    "status": "degraded",
                    "status_code": resp.status_code,
                    "error": f"RAG service returned HTTP {resp.status_code}",
                }
        except httpx.ConnectError:
            logger.warning("Failed to connect to RAG service at %s", url)
            return {
                "status": "unreachable",
                "error": f"Connection refused on {self.base_url}",
            }
        except httpx.TimeoutException:
            logger.warning("Timeout connecting to RAG service at %s", url)
            return {
                "status": "timeout",
                "error": f"Health probe timed out after {self.timeout}s",
            }
        except Exception as e:
            logger.error("Unexpected error checking RAG service health: %s", e)
            return {
                "status": "error",
                "error": str(e),
            }

    def query_rag(
        self,
        query: str,
        project_id: Optional[Union[int, str]] = None,
        requirement_ids: Optional[List[str]] = None,
        advisor_advice_ids: Optional[List[Union[int, str]]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Forward a regulatory query to the ABC Shield RAG microservice."""
        clean_query = query.strip()
        if not clean_query:
            raise ValidationError("Query cannot be empty or whitespace-only.")

        payload: Dict[str, Any] = {"query": clean_query}
        ctx = dict(context) if context else {}
        if project_id is not None:
            ctx["project_id"] = str(project_id)
        if ctx:
            payload["context"] = ctx
        if requirement_ids:
            payload["requirement_ids"] = requirement_ids
        if advisor_advice_ids:
            payload["advisor_advice_ids"] = [str(x) for x in advisor_advice_ids]

        url = f"{self.base_url}/api/v1/query"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, json=payload)
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 422:
                    raise ValidationError(f"RAG service validation failed: {resp.text}")
                else:
                    raise ServiceUnavailableError(
                        f"RAG service returned unexpected status HTTP {resp.status_code}: {resp.text}"
                    )
        except httpx.ConnectError as e:
            logger.error("RAG microservice unreachable on %s: %s", url, e)
            raise ServiceUnavailableError(
                "The regulatory AI intelligence service is currently unreachable on port 8001. "
                "Please verify that the ABC Shield service is started."
            ) from e
        except httpx.TimeoutException as e:
            logger.error("RAG microservice timed out on %s: %s", url, e)
            raise ServiceUnavailableError(
                f"The regulatory AI intelligence service timed out after {self.timeout}s."
            ) from e

    def compare_advice(
        self,
        advisor_1: Dict[str, Any],
        advisor_2: Dict[str, Any],
        comparison_id: Optional[str] = None,
        project_id: Optional[Union[int, str]] = None,
        requirement_ids: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Forward an advisor advice comparison request to the ABC Shield RAG microservice."""
        payload: Dict[str, Any] = {
            "advisor_1": advisor_1,
            "advisor_2": advisor_2,
        }
        if comparison_id:
            payload["comparison_id"] = comparison_id
        if project_id is not None:
            payload["project_id"] = str(project_id)
        if requirement_ids:
            payload["requirement_ids"] = requirement_ids
        if context:
            payload["context"] = context

        url = f"{self.base_url}/api/v1/compare"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, json=payload)
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 422:
                    raise ValidationError(f"RAG advice comparison validation failed: {resp.text}")
                else:
                    raise ServiceUnavailableError(
                        f"RAG service returned unexpected status HTTP {resp.status_code}: {resp.text}"
                    )
        except httpx.ConnectError as e:
            logger.error("RAG microservice unreachable for comparison on %s: %s", url, e)
            raise ServiceUnavailableError(
                "The regulatory AI intelligence service is currently unreachable on port 8001."
            ) from e
        except httpx.TimeoutException as e:
            logger.error("RAG microservice timed out during comparison on %s: %s", url, e)
            raise ServiceUnavailableError(
                f"The regulatory AI comparison service timed out after {self.timeout}s."
            ) from e


def format_rag_response_for_frontend(
    rag_result: Dict[str, Any],
    query_text: str,
    project_id: Optional[Union[int, str]] = None,
) -> Dict[str, Any]:
    """Map ABC Shield microservice responses into the exact contract expected by Harshini's DashboardView.jsx."""
    citations_raw = rag_result.get("citations", [])
    provenance_raw = rag_result.get("provenance", [])
    conflicts_raw = rag_result.get("conflicts", [])
    differences_raw = rag_result.get("differences", [])
    relationships_raw = rag_result.get("relationships", [])
    retrieved_raw = rag_result.get("retrieved_evidence", [])
    meta_raw = rag_result.get("metadata", {}) or {}

    # Format citations preserving both statutory naming styles
    formatted_citations = []
    for c in citations_raw:
        sec = c.get("section_article") or c.get("section") or ""
        url = c.get("official_source") or c.get("url") or ""
        formatted_citations.append({
            "source_id": c.get("source_id", ""),
            "citation_id": c.get("citation_id", ""),
            "chunk_id": c.get("chunk_id", ""),
            "title": c.get("title") or c.get("regulation", ""),
            "regulation": c.get("regulation", ""),
            "jurisdiction": c.get("jurisdiction", "UK"),
            "section": sec,
            "section_article": sec,
            "url": url,
            "official_source": url,
            "version_date": c.get("version_date", ""),
            "validation_status": c.get("validation_status", "Approved for RAG Integration - Pending SME Validation"),
            "is_approved_for_rag": c.get("is_approved_for_rag", False),
            "formatted_citation": c.get("formatted_citation", ""),
        })

    # Format provenance preserving both camelCase and snake_case
    formatted_provenance = []
    for p in provenance_raw:
        sec = p.get("section_article") or p.get("section") or ""
        src = p.get("official_source") or p.get("officialSource") or ""
        vdate = str(p.get("version_date") or p.get("versionDate") or "")
        vstatus = p.get("validation_status") or p.get("validationStatus") or "Approved for RAG Integration - Pending SME Validation"
        formatted_provenance.append({
            "recordId": p.get("record_id") or p.get("recordId") or "",
            "record_id": p.get("record_id") or p.get("recordId") or "",
            "sourceId": p.get("source_id") or p.get("sourceId") or "",
            "source_id": p.get("source_id") or p.get("sourceId") or "",
            "section": sec,
            "section_article": sec,
            "officialSource": src,
            "official_source": src,
            "versionDate": vdate,
            "version_date": vdate,
            "validationStatus": vstatus,
            "validation_status": vstatus,
            "is_approved_for_rag": p.get("is_approved_for_rag", False),
        })

    # Format conflicts from either comparison differences or conflict findings
    formatted_conflicts = []
    # A. If comparing advice, differences are primary
    if differences_raw:
        for idx, diff in enumerate(differences_raw):
            formatted_conflicts.append({
                "conflictId": f"DIFF-{idx+1:03d}",
                "topic": diff.get("difference_type", "ADVICE_DIFFERENCE"),
                "advisorA": {
                    "name": rag_result.get("advisor_1", {}).get("advisor_name") or "Advisor 1",
                    "recommendation": diff.get("advisor_1_position", ""),
                },
                "advisorB": {
                    "name": rag_result.get("advisor_2", {}).get("advisor_name") or "Advisor 2",
                    "recommendation": diff.get("advisor_2_position", ""),
                },
                "contradictionType": diff.get("difference_type", "POLICY_DISCREPANCY"),
                "severity": "HIGH" if diff.get("is_contradiction") else "MEDIUM",
                "summary": diff.get("summary", ""),
            })
    # B. Also include any registered regulatory overlaps (CO-001, etc.)
    all_rel = relationships_raw or conflicts_raw
    for c in all_rel:
        cid = c.get("conflict_id") or c.get("conflictId") or f"CONF-{uuid.uuid4().hex[:4].upper()}"
        formatted_conflicts.append({
            "conflictId": cid,
            "conflict_id": cid,
            "topic": c.get("topic", "Regulatory Overlap"),
            "advisorA": {
                "name": c.get("source_1") or "Regulatory Source 1",
                "recommendation": c.get("requirement_comparison") or c.get("source_1", ""),
            },
            "advisorB": {
                "name": c.get("source_2") or "Regulatory Source 2",
                "recommendation": c.get("scope_difference") or c.get("source_2", ""),
            },
            "contradictionType": c.get("conflict_type") or "REGULATORY_OVERLAP",
            "severity": "MEDIUM",
            "relationship": c.get("relationship", ""),
            "message": c.get("message", ""),
        })

    # Status mapping matching frontend expectations in DashboardView.jsx
    raw_status = rag_result.get("status", "GROUNDED")
    if formatted_conflicts and raw_status in ("GROUNDED", "SUCCESS"):
        display_status = "CONFLICT_DETECTED"
    elif raw_status == "GROUNDED":
        display_status = "SUCCESS"
    else:
        display_status = raw_status

    answer_text = rag_result.get("answer") or ""
    if not answer_text and differences_raw:
        answer_text = (
            f"Advice comparison complete: Identified {len(differences_raw)} difference(s) "
            f"and {len(relationships_raw)} regulatory relationship(s). "
            f"{rag_result.get('disclaimer', '')}"
        )

    # Operational metadata
    disclaimer_text = (
        rag_result.get("disclaimer")
        or meta_raw.get("disclaimer")
        or "Grounded AI synthesis derived from statutory corpus. Requires human compliance officer ratification."
    )

    metadata = {
        "retrieved_count": meta_raw.get("retrieved_count", len(retrieved_raw)),
        "approved_evidence_count": meta_raw.get("approved_evidence_count", 0),
        "citation_count": len(formatted_citations),
        "conflict_count": len(formatted_conflicts),
        "has_gap": meta_raw.get("has_gap", False),
        "gap_type": meta_raw.get("gap_type"),
        "requires_human_review": meta_raw.get("requires_human_review", False),
        "has_candidate_evidence": meta_raw.get("has_candidate_evidence", True),
        "disclaimer": disclaimer_text,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Format gap ensuring both snake_case and camelCase
    gap_raw = rag_result.get("gap")
    if gap_raw and isinstance(gap_raw, dict):
        is_gap = bool(gap_raw.get("is_gap") or gap_raw.get("isGapDetected") or meta_raw.get("has_gap", False))
        gap_type = gap_raw.get("gap_type") or gap_raw.get("description") or meta_raw.get("gap_type")
        formatted_gap = {
            "is_gap": is_gap,
            "isGapDetected": is_gap,
            "gap_type": str(gap_type) if gap_type else None,
            "description": str(gap_type) if gap_type else None,
            "message": gap_raw.get("message") or gap_raw.get("user_safe_message") or "",
            "user_safe_message": gap_raw.get("user_safe_message") or gap_raw.get("message") or "",
        }
    else:
        is_gap = bool(meta_raw.get("has_gap", False))
        gap_type = meta_raw.get("gap_type")
        formatted_gap = {
            "is_gap": is_gap,
            "isGapDetected": is_gap,
            "gap_type": str(gap_type) if gap_type else None,
            "description": str(gap_type) if gap_type else None,
            "message": "",
            "user_safe_message": "",
        }

    # Format retrieved evidence chunks
    formatted_evidence = []
    for ev in retrieved_raw:
        formatted_evidence.append({
            "chunk_id": ev.get("chunk_id", ""),
            "content": ev.get("text", ""),
            "similarity_score": ev.get("similarity_score"),
        })

    # Format UI-ready findings directly matching Harshini's AiRagFindingsView.jsx
    formatted_findings = []
    finding_idx = 1

    for conf in formatted_conflicts:
        conf_msg = conf.get("message") or "Direct conflict detected between regulatory positions."
        formatted_findings.append({
            "id": f"FND-CONF-{finding_idx}",
            "finding": f"Regulatory Conflict: {conf.get('topic') or 'Statutory Divergence'}",
            "type": "Conflict",
            "requirement": "Cross-Border / Multi-Regime",
            "supportingSource": f"{conf.get('advisorA', {}).get('name', 'Regime A')} vs {conf.get('advisorB', {}).get('name', 'Regime B')}",
            "humanReview": "Needs human review",
            "analysis": conf_msg,
            "recommendedAction": "SME compliance officer must review and ratify position before sign-off.",
            "reviewDetails": f"{conf_msg} Scope difference: {conf.get('advisorA', {}).get('recommendation', '')} vs {conf.get('advisorB', {}).get('recommendation', '')}.",
            "typeBadge": "border-amber-800/80 bg-amber-950/40 text-amber-300",
            "typeDetailBadge": "border-amber-800/80 bg-amber-950/40 text-amber-300",
            "typeDot": "bg-amber-400",
            "statusBadge": "border-red-800/80 bg-red-950/40 text-red-300",
            "detailStatusBadge": "border-red-800/80 bg-red-950/40 text-red-300",
            "statusDot": "bg-red-400",
            "detailStatusDot": "bg-red-400",
        })
        finding_idx += 1

    if formatted_gap.get("is_gap"):
        gap_msg = formatted_gap.get("user_safe_message") or "Insufficient statutory evidence in approved corpus."
        formatted_findings.append({
            "id": f"FND-GAP-{finding_idx}",
            "finding": f"Evidence Gap: {formatted_gap.get('gap_type') or 'Missing Statutory Corpus'}",
            "type": "Evidence Gap",
            "requirement": "Corpus Coverage",
            "supportingSource": "No reliable source found in approved knowledge base",
            "humanReview": "Needs human review",
            "analysis": gap_msg,
            "recommendedAction": "Upload and approve authoritative statutory texts.",
            "reviewDetails": f"{gap_msg} Statutory coverage gap requires compliance specialist verification before advice can be certified.",
            "typeBadge": "border-rose-800/80 bg-rose-950/40 text-rose-300",
            "typeDetailBadge": "border-rose-800/80 bg-rose-950/40 text-rose-300",
            "typeDot": "bg-rose-400",
            "statusBadge": "border-yellow-800/80 bg-yellow-950/40 text-yellow-300",
            "detailStatusBadge": "border-yellow-800/80 bg-yellow-950/40 text-yellow-300",
            "statusDot": "bg-yellow-400",
            "detailStatusDot": "bg-yellow-400",
        })
        finding_idx += 1

    for cit in formatted_citations:
        cit_analysis = cit.get("relevanceSummary") or cit.get("applicabilityRationale") or "Verified citation from canonical corpus."
        formatted_findings.append({
            "id": f"FND-CIT-{finding_idx}",
            "finding": f"Statutory Evidence: {cit.get('topic') or cit.get('sourceTitle')}",
            "type": "Source Grounded",
            "requirement": cit.get("topic") or "Statutory Compliance",
            "supportingSource": f"{cit.get('sourceTitle')} ({cit.get('issuingAuthority', 'Statutory')})",
            "humanReview": "Verified",
            "analysis": cit_analysis,
            "recommendedAction": "Incorporate into regulatory compliance filing with citation link.",
            "reviewDetails": f"Grounding rationale: {cit.get('applicabilityRationale') or cit_analysis}. Authority: {cit.get('issuingAuthority')}. URL: {cit.get('sourceUrl')}.",
            "typeBadge": "border-emerald-800/80 bg-emerald-950/40 text-emerald-300",
            "typeDetailBadge": "border-emerald-800/80 bg-emerald-950/40 text-emerald-300",
            "typeDot": "bg-emerald-400",
            "statusBadge": "border-emerald-800/80 bg-emerald-950/40 text-emerald-300",
            "detailStatusBadge": "border-emerald-800/80 bg-emerald-950/40 text-emerald-300",
            "statusDot": "bg-emerald-400",
            "detailStatusDot": "bg-emerald-400",
        })
        finding_idx += 1

    return {
        "schema_version": "1.0",
        "request_id": rag_result.get("request_id") or f"req_rag_{uuid.uuid4().hex[:8]}",
        "query": query_text,
        "status": display_status,
        "answer": answer_text,
        "grounded": bool(rag_result.get("grounded", len(formatted_citations) > 0)),
        "gap": formatted_gap,
        "citations": formatted_citations,
        "provenance": formatted_provenance,
        "conflicts": formatted_conflicts,
        "findings": formatted_findings,
        "retrieved_evidence": formatted_evidence,
        "metadata": metadata,
    }


_client_instance: Optional[RAGServiceClient] = None


def get_rag_service_client() -> RAGServiceClient:
    """Retrieve or initialize the shared singleton RAGServiceClient."""
    global _client_instance
    if _client_instance is None:
        _client_instance = RAGServiceClient()
    return _client_instance
