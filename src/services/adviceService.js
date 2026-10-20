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
      readiness_score: '0%',
      readiness_percentage: 0,
      readiness_status: 'ACTION_REQUIRED',
      summary: 'Readiness evaluation pending initial requirements and advice records.',
      breakdown: [
        { category: 'Regulatory Obligations', metric: '0 Requirements Defined', completion_pct: 0, status: 'ACTION_REQUIRED' },
        { category: 'Advisor Governance & Review', metric: '0 Reviews Submitted', completion_pct: 0, status: 'ACTION_REQUIRED' },
        { category: 'Binding Compliance Decisions', metric: '0 Decisions Recorded', completion_pct: 0, status: 'ACTION_REQUIRED' },
      ],
      total_requirements: 0,
      completed_requirements: 0,
      total_advice_reviews: 0,
      total_decisions: 0,
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


/**
 * Uploads a validated PDF attachment via POST /projects/{projectId}/attachments (DEF-16)
 */
export async function uploadAttachment(projectId, file, category = 'ADVISORY_REFERENCE') {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('category', category);
  return await apiCall('/projects/' + projectId + '/attachments', 'POST', formData);
}

/**
 * Lists project attachments via GET /projects/{projectId}/attachments (DEF-16)
 */
export async function getProjectAttachments(projectId) {
  try {
    const data = await apiCall('/projects/' + projectId + '/attachments', 'GET');
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.warn('[adviceService] GET /projects/' + projectId + '/attachments failed:', err);
    return [];
  }
}

/**
 * Downloads a project attachment blob via GET /projects/{projectId}/attachments/{attachmentId}
 */
export async function downloadAttachment(projectId, attachmentId) {
  return await apiCall('/projects/' + projectId + '/attachments/' + attachmentId, 'GET');
}
