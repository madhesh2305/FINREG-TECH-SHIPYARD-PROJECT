import { apiCall } from './api';

/**
 * Records an authoritative compliance decision for a project
 * POST /projects/{projectId}/decisions
 */
export async function recordDecision(projectId, payload) {
  return await apiCall(`/projects/${projectId}/decisions`, 'POST', payload);
}

/**
 * Retrieves all compliance decisions for a project
 * GET /projects/{projectId}/decisions
 */
export async function getProjectDecisions(projectId) {
  try {
    const data = await apiCall(`/projects/${projectId}/decisions`, 'GET');
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.warn(`[decisionService] GET /projects/${projectId}/decisions failed:`, err.message);
    return [];
  }
}

/**
 * Retrieves a specific compliance decision by ID
 * GET /projects/{projectId}/decisions/{decisionId}
 */
export async function getDecisionDetails(projectId, decisionId) {
  return await apiCall(`/projects/${projectId}/decisions/${decisionId}`, 'GET');
}
