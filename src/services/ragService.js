import { apiCall } from './api';

/**
 * Sends RAG conflict and analysis query to backend via POST /rag/analyze
 * @param {object} payload - { project_id, query, requirement_ids, advisor_advice_ids }
 */
export async function analyzeRAGConflict(payload) {
  try {
    return await apiCall('/rag/analyze', 'POST', payload);
  } catch (err) {
    console.error('[ragService] POST /rag/analyze failed:', err);
    throw err;
  }
}
