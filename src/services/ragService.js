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
 */
export async function submitRegulatoryQuery({ project_id, query }) {
  const cleanQuery = (query || '').trim();
  if (!cleanQuery) {
    throw new Error('Please enter a regulatory question.');
  }

  // Live Gateway Request to ShipYard Backend
  const payload = {
    query: cleanQuery,
    projectId: project_id && project_id !== 'null' ? project_id : 1,
    context: {
      jurisdiction: 'UK',
    },
  };

  return await apiCall('/rag/analyze', 'POST', payload);
}

/**
 * Compare Advisor Positions: POST /rag/compare
 * Live Gateway Request to ShipYard Backend (Port 8000)
 */
export async function compareAdvisorPositions({
  project_id = 1,
  advisor_1_name = 'Eleanor Vance (Vance Legal LLP)',
  advice_1_text = 'UK Bribery Act 2010 Section 1 offences and Section 7 failure of commercial organisations to prevent bribery.',
  advisor_2_name = 'Marcus Reid (FCC Consulting Europe)',
  advice_2_text = 'Ministry of Justice Guidance Six Principles prevention procedures and proportionate risk thresholds.',
} = {}) {
  const payload = {
    comparison_id: `CMP-${Date.now().toString().slice(-6)}`,
    projectId: project_id && project_id !== 'null' ? project_id : 1,
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
 * DEF-27: Human Review Endpoints
 */
export async function getHumanReviews(projectId = null) {
  const url = projectId ? `/rag/human-reviews?project_id=${projectId}` : `/rag/human-reviews`;
  try {
    return await apiCall(url, 'GET');
  } catch (err) {
    console.warn('[ragService] getHumanReviews error:', err.message);
    return [];
  }
}

export async function resolveHumanReview(reviewId, decision, notes) {
  return await apiCall(`/rag/human-reviews/${reviewId}/resolve`, 'POST', {
    decision,
    resolution_notes: notes,
  });
}

export const submitRagQuery = submitRegulatoryQuery;
