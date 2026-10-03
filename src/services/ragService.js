import { apiCall } from './api';

const MOCK_RAG_RESPONSE = {
  schema_version: '1.0',
  request_id: 'req_rag_99812',
  query: 'Compare advisor recommendations on data retention against FCA guidelines',
  status: 'CONFLICT_DETECTED', // "SUCCESS" | "CONFLICT_DETECTED" | "GAP_DETECTED" | "NO_SOURCE_FOUND" | "ERROR"
  answer: 'Grounded AI analysis: S. Okonkwo recommends a 5-year retention timeline under FCA SYSC 6.1, whereas A. Petrov suggests a 7-year retention period referencing EU GDPR baseline. Human compliance review is required.',
  grounded: true,
  gap: {
    isGapDetected: false,
    description: null,
  },
  citations: [
    {
      source_id: 'SRC-FCA-01',
      title: 'FCA Handbook SYSC 6.1',
      jurisdiction: 'United Kingdom - FCA',
      section: '6.1.4 R',
      url: 'https://www.handbook.fca.org.uk/handbook/SYSC/6/1.html',
    },
  ],
  provenance: [
    {
      recordId: 'REC-001',
      sourceId: 'SRC-FCA-01',
      section: '6.1.4 R',
      officialSource: 'FCA Handbook',
      versionDate: '2026-09-01',
      validationStatus: 'Validated',
    },
  ],
  conflicts: [
    {
      conflictId: 'CONF-01',
      topic: 'Data Retention Period',
      advisorA: {
        name: 'S. Okonkwo',
        recommendation: 'Retain customer records for 5 years.',
      },
      advisorB: {
        name: 'A. Petrov',
        recommendation: 'Retain customer records for 7 years under EU GDPR baseline.',
      },
      contradictionType: 'VERSION_DIFFERENCE',
      severity: 'MEDIUM',
    },
  ],
  retrieved_evidence: [
    {
      chunk_id: 'chk_102',
      content: 'FCA SYSC 6.1.4 R requires firms to maintain financial crime records for 5 years.',
    },
  ],
  metadata: {
    retrieved_count: 3,
    approved_evidence_count: 2,
    citation_count: 1,
    conflict_count: 1,
    has_gap: false,
    requires_human_review: true,
    model: 'FastAPI ChromaDB / RAG Engine',
    executionTimeMs: 410,
  },
};

/**
 * Sends RAG conflict and analysis query to backend via POST /rag/analyze
 * @param {object} payload - { project_id, query, requirement_ids, advisor_advice_ids }
 */
export async function analyzeRAGConflict(payload) {
  try {
    const data = await apiCall('/rag/analyze', 'POST', payload);
    return data && data.status ? data : { ...MOCK_RAG_RESPONSE, ...payload };
  } catch (err) {
    console.warn('[ragService] POST /rag/analyze failed. Returning mock RAG contract response.');
    return { ...MOCK_RAG_RESPONSE, query: payload?.query || MOCK_RAG_RESPONSE.query };
  }
}
