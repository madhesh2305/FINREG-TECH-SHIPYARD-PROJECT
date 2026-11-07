"""ABC Shield Fast-Track Step 6: Final Integration Smoke Test Script.

Role: Padma Kumar — AI/RAG & Conflict Detection Engineer
Goal: Verify that the completed RAG module is ready for frontend and backend consumption,
execute live HTTP integration smoke tests across all endpoints, verify responses and
non-adjudication safeguards, verify legacy store integrity, and document frontend availability.
"""

import sys
import os
import time
import json
import threading
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# Set project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import chromadb
import uvicorn
from config.settings import settings


def verify_vector_stores():
    """Verify integrity of both legacy (15-vector) and canonical (25-vector) stores."""
    print("=" * 80)
    print("STEP 1: VECTOR STORE INTEGRITY VERIFICATION")
    print("=" * 80)

    legacy_path = PROJECT_ROOT / "data/processed/chroma_db"
    legacy_client = chromadb.PersistentClient(path=str(legacy_path))
    legacy_col = legacy_client.get_collection("regulatory_records")
    legacy_count = legacy_col.count()
    print(f"Legacy Store:    path={legacy_path}")
    print(f"                 collection={legacy_col.name}, vectors={legacy_count}")
    assert legacy_count == 15, f"Expected 15 legacy vectors, found {legacy_count}"

    canonical_path = PROJECT_ROOT / "data/staging/madhesh_handover/step6/chroma_db"
    canonical_client = chromadb.PersistentClient(path=str(canonical_path))
    canonical_col = canonical_client.get_collection("canonical_regulatory_records")
    canonical_count = canonical_col.count()
    print(f"Canonical Store: path={canonical_path}")
    print(f"                 collection={canonical_col.name}, vectors={canonical_count}")
    assert canonical_count == 25, f"Expected 25 canonical vectors, found {canonical_count}"

    print(f"Active Mode:     {settings.rag_knowledge_base_mode}")
    print(f"Active Collection: {settings.chroma_collection_name}")
    print(f"Active Persist Dir: {settings.chroma_persist_dir}")
    print("[PASS] Vector stores verified.\n")

    return {
        "legacy": {"path": str(legacy_path), "collection": legacy_col.name, "count": legacy_count},
        "canonical": {"path": str(canonical_path), "collection": canonical_col.name, "count": canonical_count},
    }


def verify_frontend_availability():
    """Inspect workspace for frontend code or repositories."""
    print("=" * 80)
    print("STEP 2: FRONTEND CODE AVAILABILITY AUDIT")
    print("=" * 80)

    parent_dir = PROJECT_ROOT.parent
    found_frontend = []

    for item in parent_dir.rglob("package.json"):
        # Ignore virtualenv or cache
        if ".venv" not in str(item) and "node_modules" not in str(item):
            found_frontend.append(str(item))

    if found_frontend:
        print(f"Frontend packages located: {found_frontend}")
        status = "AVAILABLE"
    else:
        print("Audit Result: No frontend codebase (package.json / React / Next.js) present in workspace.")
        print("Documented finding: Full frontend-to-backend end-to-end testing remains pending frontend availability.")
        status = "PENDING_FRONTEND_AVAILABILITY"

    print("[PASS] Frontend audit complete.\n")
    return {"status": status, "found_files": found_frontend}


def send_http(method: str, url: str, data: dict = None) -> tuple[int, dict]:
    """Helper to send HTTP request and return status code and parsed JSON."""
    headers = {"Content-Type": "application/json"}
    body = json.dumps(data).encode("utf-8") if data else None
    req = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(req, timeout=30) as resp:
            code = resp.getcode()
            res_data = json.loads(resp.read().decode("utf-8"))
            return code, res_data
    except HTTPError as e:
        err_data = json.loads(e.read().decode("utf-8")) if e.fp else {"error": str(e)}
        return e.code, err_data
    except URLError as e:
        return 0, {"error": str(e)}


class UvicornServerThread:
    """Runs uvicorn in a background thread."""

    def __init__(self, host="127.0.0.1", port=8000):
        self.host = host
        self.port = port
        self.config = uvicorn.Config(
            "api.main:app",
            host=self.host,
            port=self.port,
            log_level="warning",
            loop="asyncio",
        )
        self.server = uvicorn.Server(self.config)
        self.thread = threading.Thread(target=self.server.run, daemon=True)

    def start(self):
        print(f"Starting uvicorn server on http://{self.host}:{self.port} ...")
        self.thread.start()
        # Wait until server is listening
        max_retries = 30
        for _ in range(max_retries):
            time.sleep(0.5)
            try:
                code, _ = send_http("GET", f"http://{self.host}:{self.port}/health")
                if code == 200:
                    print(f"Uvicorn server is UP and responding on http://{self.host}:{self.port}")
                    return True
            except Exception:
                pass
        raise RuntimeError("Uvicorn server failed to start within timeout.")

    def stop(self):
        print("Shutting down uvicorn server...")
        self.server.should_exit = True
        self.thread.join(timeout=5)
        print("Uvicorn server stopped.")


def run_smoke_tests():
    """Execute all smoke test cases against the live HTTP service."""
    print("=" * 80)
    print("STEP 3: LIVE HTTP SMOKE TESTS")
    print("=" * 80)

    base_url = "http://127.0.0.1:8000"
    results = {}

    # 1. Health check
    print("\n--- Test 1: GET /health and GET /api/v1/health ---")
    c1, h1 = send_http("GET", f"{base_url}/health")
    c2, h2 = send_http("GET", f"{base_url}/api/v1/health")
    print(f"GET /health: {c1} -> {h1}")
    print(f"GET /api/v1/health: {c2} -> {h2}")
    assert c1 == 200 and h1["status"] == "ok" and h1["chromadb_status"] == "connected"
    assert c2 == 200 and h2["status"] == "ok" and h2["chromadb_status"] == "connected"
    results["health"] = {"code": c1, "response": h1}

    # 2. Representative Grounded Query (UK Bribery Act Section 7)
    print("\n--- Test 2: POST /api/v1/query (UK Bribery Act Section 7) ---")
    query_payload = {
        "query": "Under UK Bribery Act 2010, what does Section 7 cover regarding failure of commercial organisations to prevent bribery?",
        "context": {"jurisdiction": "UK"}
    }
    cq1, rq1 = send_http("POST", f"{base_url}/api/v1/query", query_payload)
    print(f"POST /api/v1/query status: {cq1}")
    print(f"Response status: {rq1.get('status')}")
    print(f"Answer snippet: {rq1.get('answer')[:120]}...")
    print(f"Citations count: {len(rq1.get('citations', []))}")
    print(f"First Citation: {rq1.get('citations', [])[0] if rq1.get('citations') else 'None'}")
    print(f"Retrieved Evidence: {len(rq1.get('retrieved_evidence', []))} chunks")
    print(f"Provenance Count: {len(rq1.get('provenance', []))}")
    print(f"Candidate evidence flag: {rq1.get('metadata', {}).get('has_candidate_evidence')}")
    assert cq1 == 200
    assert rq1["status"] == "GROUNDED"
    assert rq1["grounded"] is True
    assert len(rq1["citations"]) > 0
    assert any("legislation.gov.uk" in (c.get("official_source") or "") for c in rq1["citations"])
    assert rq1["metadata"]["has_candidate_evidence"] is True
    results["grounded_query"] = {"code": cq1, "response": rq1}

    # 3. Approved-Only Query (fail-closed test)
    print("\n--- Test 3: POST /api/v1/query (filter_approved_only=True) ---")
    approved_only_payload = {
        "query": "Under UK Bribery Act 2010, what does Section 7 cover?",
        "context": {"filter_approved_only": True}
    }
    cq2, rq2 = send_http("POST", f"{base_url}/api/v1/query", approved_only_payload)
    print(f"POST /api/v1/query status: {cq2}")
    print(f"Response status: {rq2.get('status')}")
    print(f"Answer snippet: {rq2.get('answer')[:120]}...")
    print(f"Citations: {len(rq2.get('citations', []))}")
    print(f"Retrieved Evidence: {len(rq2.get('retrieved_evidence', []))}")
    print(f"Human review required: {rq2.get('metadata', {}).get('requires_human_review')}")
    assert cq2 == 200
    assert rq2["status"] == "UNAPPROVED_EVIDENCE"
    assert rq2["grounded"] is False
    assert len(rq2["citations"]) == 0
    assert len(rq2["retrieved_evidence"]) == 0
    assert rq2["metadata"]["requires_human_review"] is True
    results["approved_only_query"] = {"code": cq2, "response": rq2}

    # 4. Out-of-Scope Query (Sanctions Screening)
    print("\n--- Test 4: POST /api/v1/query (Sanctions Screening - Out of Scope) ---")
    sanctions_payload = {
        "query": "What are ABC Shield's sanctions screening obligations under OFAC and UK sanctions regimes?"
    }
    cq3, rq3 = send_http("POST", f"{base_url}/api/v1/query", sanctions_payload)
    print(f"POST /api/v1/query status: {cq3}")
    print(f"Response status: {rq3.get('status')}")
    print(f"Answer snippet: {rq3.get('answer')[:120]}...")
    print(f"Citations: {len(rq3.get('citations', []))}")
    print(f"Gap: {rq3.get('gap')}")
    assert cq3 == 200
    assert rq3["status"] == "OUT_OF_SCOPE"
    assert rq3["grounded"] is False
    assert len(rq3["citations"]) == 0
    assert rq3["gap"] is not None
    assert rq3["gap"]["gap_type"] == "OUT_OF_SCOPE"
    results["out_of_scope_query"] = {"code": cq3, "response": rq3}

    # 5. Insufficient Evidence / Unsupported Transposition (French Transposition)
    print("\n--- Test 5: POST /api/v1/query (French Transposition - Insufficient Evidence) ---")
    french_payload = {
        "query": "What are the specific transposition provisions under French national law for the EU Whistleblower Directive?"
    }
    cq4, rq4 = send_http("POST", f"{base_url}/api/v1/query", french_payload)
    print(f"POST /api/v1/query status: {cq4}")
    print(f"Response status: {rq4.get('status')}")
    print(f"Answer snippet: {rq4.get('answer')[:120]}...")
    print(f"Citations: {len(rq4.get('citations', []))}")
    print(f"Gap: {rq4.get('gap')}")
    assert cq4 == 200
    assert rq4["status"] == "INSUFFICIENT_EVIDENCE"
    assert rq4["grounded"] is False
    assert len(rq4["citations"]) == 0
    assert rq4["gap"] is not None
    assert rq4["gap"]["gap_type"] == "DATA_COVERAGE_LIMITATION"
    results["insufficient_evidence_query"] = {"code": cq4, "response": rq4}

    # 6. Advice Comparison Endpoint (co-retrieval UK-01 & UK-02, CO-001, decision=None)
    print("\n--- Test 6: POST /api/v1/compare (Advice Comparison with CO-001) ---")
    compare_payload = {
        "comparison_id": "CMP-CANONICAL-001",
        "requirement_ids": ["REQ-UK-01"],
        "advisor_1": {
            "advice_id": "ADV-001",
            "advisor_name": "Senior Compliance Counsel",
            "advice_text": "Bribery Act 2010 Section 1 offences of bribing another person.",
            "source_reference": "UK Bribery Act 2010 Section 1"
        },
        "advisor_2": {
            "advice_id": "ADV-002",
            "advisor_name": "External Consultant",
            "advice_text": "Bribery Act 2010 Guidance Ministry of Justice Six Principles prevention procedures.",
            "source_reference": "MoJ Guidance on Bribery Act 2010"
        },
        "context": {
            "jurisdiction": "UK",
            "regulatory_area": "Anti-Bribery and Corruption"
        }
    }
    cc1, rc1 = send_http("POST", f"{base_url}/api/v1/compare", compare_payload)
    print(f"POST /api/v1/compare status: {cc1}")
    print(f"Differences count: {len(rc1.get('differences', []))}")
    print(f"Relationships count: {len(rc1.get('relationships', []))}")
    rel_ids = [r.get("conflict_id") for r in rc1.get("relationships", [])]
    print(f"Relationship IDs: {rel_ids}")
    print(f"Human review required: {rc1.get('human_review_required')}")
    print(f"Decision: {rc1.get('decision')}")
    print(f"Disclaimer: {rc1.get('disclaimer')[:90]}...")
    assert cc1 == 200
    assert len(rc1["differences"]) >= 1
    assert "CO-001" in rel_ids
    assert rc1["human_review_required"] is True
    assert rc1["decision"] is None
    results["advice_comparison"] = {"code": cc1, "response": rc1}

    print("\n[PASS] All 6 live HTTP smoke test endpoints passed successfully!")
    return results


def main():
    print("=" * 80)
    print("ABC SHIELD FAST-TRACK STEP 6: FINAL INTEGRATION SMOKE TESTS")
    print("=" * 80)

    # 1. Vector store integrity
    store_results = verify_vector_stores()

    # 2. Frontend availability
    frontend_results = verify_frontend_availability()

    # 3. Live HTTP smoke tests
    server = UvicornServerThread(host="127.0.0.1", port=8000)
    server.start()

    try:
        smoke_results = run_smoke_tests()
    finally:
        server.stop()

    # Save results to staging
    out_dir = PROJECT_ROOT / "data/staging/fast_track"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_data = {
        "vector_stores": store_results,
        "frontend_audit": frontend_results,
        "smoke_test_results": smoke_results,
        "summary": {
            "status": "PASSED",
            "provisional_status": "Approved for RAG Integration - Pending SME Validation",
            "authoritative_production": False,
            "frontend_ready": True,
            "backend_ready": True,
            "frontend_code_present_in_workspace": len(frontend_results["found_files"]) > 0,
            "full_app_integration": "PENDING_FRONTEND_AVAILABILITY"
        }
    }
    out_file = out_dir / "smoke_test_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    print(f"\nSmoke test results saved to: {out_file}")
    print("=" * 80)
    print("ALL INTEGRATION SMOKE TESTS COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    main()
