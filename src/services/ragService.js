import { apiCall } from './api';

/**
 * Check RAG backend availability via Gateway: GET /rag/health
 */
export async function checkRAGHealth() {
  try {
    const data = await apiCall('/rag/health', 'GET');
    return {
      isOnline: data.status === 'healthy' || data.status === 'ok',
      status: data.status || 'OK',
      details: data.rag_microservice || data,
    };
  } catch (err) {
    return { isOnline: false, status: 'OFFLINE', error: err.message };
  }
}

/**
 * Submit Regulatory Query: POST /rag/analyze
 * Live Gateway Request to ShipYard Backend (Port 8000)
 * DEF-FE-02: Does not hardcode projectId to 1, allowing null for global searches
 */
export async function submitRegulatoryQuery({ project_id, query }) {
  const cleanQuery = (query || '').trim();
  if (!cleanQuery) {
    throw new Error('Please enter a regulatory question.');
  }

  const pid = project_id && project_id !== 'null' && project_id !== 'undefined' ? project_id : null;

  // Live Gateway Request to ShipYard Backend
  const payload = {
    query: cleanQuery,
    projectId: pid,
    context: {
      jurisdiction: 'UK',
    },
  };

  return await apiCall('/rag/analyze', 'POST', payload);
}

/**
 * Compare Advisor Positions: POST /rag/compare
 * Live Gateway Request to ShipYard Backend (Port 8000)
 * DEF-FE-02: Does not hardcode projectId to 1
 */
export async function compareAdvisorPositions({
  project_id = null,
  advisor_1_name = 'Eleanor Vance (Vance Legal LLP)',
  advice_1_text = 'UK Bribery Act 2010 Section 1 offences and Section 7 failure of commercial organisations to prevent bribery.',
  advisor_2_name = 'Marcus Reid (FCC Consulting Europe)',
  advice_2_text = 'Ministry of Justice Guidance Six Principles prevention procedures and proportionate risk thresholds.',
} = {}) {
  const pid = project_id && project_id !== 'null' && project_id !== 'undefined' ? project_id : null;

  const payload = {
    comparison_id: `CMP-${Date.now().toString().slice(-6)}`,
    projectId: pid,
    advisor_1: {
      advice_id: 'ADV-001',
      advisor_name: advisor_1_name,
      advice_text: advice_1_text,
      source_reference: 'UK Bribery Act 2010',
    },
    advisor_2: {
      advice_id: 'ADV-002',
      advisor_name: advisor_2_name,
      advice_text: advice_2_text,
      source_reference: 'MoJ Bribery Guidance',
    },
    context: {
      jurisdiction: 'UK',
    },
  };

  return await apiCall('/rag/compare', 'POST', payload);
}

/**
 * DEF-FE-01: Human Review Endpoints matching Backend routes:
 * GET /api/v1/projects/{projectId}/human-reviews
 * PATCH /api/v1/projects/{projectId}/human-reviews/{reviewId}
 */
export async function getHumanReviews(projectId = null) {
  const pid = typeof projectId === 'object' ? (projectId?.id || projectId?.project_id) : projectId;
  if (!pid || pid === 'null' || pid === 'undefined') return [];
  try {
    return await apiCall(`/projects/${pid}/human-reviews`, 'GET');
  } catch (err) {
    console.warn('[ragService] getHumanReviews error:', err.message);
    try {
      return await apiCall(`/rag/human-reviews?project_id=${pid}`, 'GET');
    } catch (_) {
      return [];
    }
  }
}

export async function resolveHumanReview(arg1, arg2, arg3, arg4) {
  let projectId, reviewId, decision, notes;
  if (arg4 !== undefined) {
    // Called with (projectId, reviewId, decision, notes)
    projectId = arg1;
    reviewId = arg2;
    decision = arg3;
    notes = arg4;
  } else {
    // Called with (reviewId, decision, notes)
    reviewId = arg1;
    decision = arg2;
    notes = arg3;
    projectId = typeof reviewId === 'object' ? reviewId.project_id : null;
  }

  const pid = typeof projectId === 'object' ? (projectId?.id || projectId?.project_id) : projectId;
  const rid = typeof reviewId === 'object' ? (reviewId?.id || reviewId?.review_id) : reviewId;
  const statusVal = (decision || 'APPROVED').toUpperCase();

  // Payload matching backend ai.py expectation: review_status & resolution_notes
  const payload = {
    review_status: statusVal,
    resolution_notes: notes || '',
    decision: statusVal,
  };

  if (pid) {
    try {
      return await apiCall(`/projects/${pid}/human-reviews/${rid}`, 'PATCH', payload);
    } catch (err) {
      console.warn(`[ragService] PATCH /projects/${pid}/human-reviews/${rid} failed:`, err.message);
    }
  }

  // Gateway fallback
  return await apiCall(`/rag/human-reviews/${rid}/resolve`, 'POST', payload);
}

export const submitRagQuery = submitRegulatoryQuery;
