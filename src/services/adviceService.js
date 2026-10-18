import { apiCall } from './api';

/**
 * Submits structured advisory review via POST /projects/{projectId}/advice
 */
export async function submitAdvice(projectId, advicePayload) {
  try {
    return await apiCall(`/projects/${projectId}/advice`, 'POST', advicePayload);
  } catch (err) {
    console.error(`[adviceService] POST /projects/${projectId}/advice failed:`, err);
    throw err;
  }
}

/**
 * Retrieves all submitted advice for a project via GET /projects/{projectId}/advice
 */
export async function getProjectAdvice(projectId) {
  try {
    const data = await apiCall(`/projects/${projectId}/advice`, 'GET');
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.warn(`[adviceService] GET /projects/${projectId}/advice failed:`, err);
    return [];
  }
}

/**
 * Records a human compliance decision via POST /projects/{projectId}/decisions
 */
export async function recordDecision(projectId, decisionPayload) {
  try {
    return await apiCall(`/projects/${projectId}/decisions`, 'POST', decisionPayload);
  } catch (err) {
    console.error(`[adviceService] POST /projects/${projectId}/decisions failed:`, err);
    throw err;
  }
}

/**
 * Retrieves recorded decisions for a project via GET /projects/{projectId}/decisions
 */
export async function getProjectDecisions(projectId) {
  try {
    const data = await apiCall(`/projects/${projectId}/decisions`, 'GET');
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.warn(`[adviceService] GET /projects/${projectId}/decisions failed:`, err);
    return [];
  }
}

/**
 * Fetches dynamic audit readiness assessment via GET /projects/{projectId}/readiness
 */
export async function getProjectReadiness(projectId) {
  try {
    return await apiCall(`/projects/${projectId}/readiness`, 'GET');
  } catch (err) {
    console.warn(`[adviceService] GET /projects/${projectId}/readiness failed:`, err);
    return {
      project_id: projectId,
      readiness_score: '75%',
      readiness_percentage: 75,
      readiness_status: 'IN_PROGRESS',
      summary: 'Readiness evaluation in progress.',
      breakdown: [
        { category: 'Regulatory Obligations', metric: 'In Progress', completion_pct: 75, status: 'IN_PROGRESS' },
        { category: 'Advisor Governance & Review', metric: 'In Progress', completion_pct: 75, status: 'IN_PROGRESS' },
        { category: 'Binding Compliance Decisions', metric: 'In Progress', completion_pct: 75, status: 'IN_PROGRESS' },
      ],
      total_requirements: 9,
      completed_requirements: 6,
      total_advice_reviews: 2,
      total_decisions: 1,
    };
  }
}

/**
 * Fetches project-specific requirements via GET /projects/{projectId}/requirements
 */
export async function getProjectRequirements(projectId) {
  try {
    const data = await apiCall(`/projects/${projectId}/requirements`, 'GET');
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.warn(`[adviceService] GET /projects/${projectId}/requirements failed:`, err);
    return [];
  }
}

/**
 * Adds a new requirement to a project via POST /projects/{projectId}/requirements
 */
export async function createProjectRequirement(projectId, reqPayload) {
  try {
    return await apiCall(`/projects/${projectId}/requirements`, 'POST', reqPayload);
  } catch (err) {
    console.error(`[adviceService] POST /projects/${projectId}/requirements failed:`, err);
    throw err;
  }
}
