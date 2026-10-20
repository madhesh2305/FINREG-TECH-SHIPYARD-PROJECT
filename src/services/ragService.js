import { apiCall } from './api';

/**
 * Sends RAG conflict and analysis query to backend via POST /rag/analyze
 * @param {object} payload - { project_id, query, requirement_ids, advisor_advice_ids }
 */
export async function analyzeRAGConflict(payload) {
  try {
    const data = await apiCall('/rag/analyze', 'POST', payload);
    return data || null;
  } catch (err) {
    console.warn('[ragService] POST /rag/analyze failed.');
    return null;
  }
}
