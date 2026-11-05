import { apiCall, getToken } from './api';

/**
 * Fetches all authorized user projects from live PostgreSQL backend.
 */
export async function getProjects() {
  const data = await apiCall('/projects', 'GET');
  return Array.isArray(data) ? data : [];
}

// Deprecated local storage bridges redirected to live API (DEF-28)
export const getLocalProjects = getProjects;
export const saveLocalProjects = () => {};

/**
 * Fetches summary metrics for user's projects.
 */
export async function getProjectSummary() {
  return await apiCall('/projects/summary', 'GET');
}

/**
 * Fetches single project details.
 */
export async function getProjectDetails(projectId) {
  return await apiCall(`/projects/${projectId}`, 'GET');
}

/**
 * Creates a new project in PostgreSQL.
 */
export async function createProject(projectPayload) {
  return await apiCall('/projects', 'POST', projectPayload);
}

/**
 * Updates an existing project in PostgreSQL.
 */
export async function updateProject(projectId, updatePayload) {
  return await apiCall(`/projects/${projectId}`, 'PATCH', updatePayload);
}

/**
 * Updates project lifecycle status: PATCH /admin/projects/{projectId}/status (DEF-38)
 */
export async function updateProjectStatus(projectId, status) {
  return await apiCall(`/admin/projects/${projectId}/status`, 'PATCH', { 
    status: status.toUpperCase(),
    reason: 'Administrative oversight action',
  });
}

/**
 * Disables a project: POST /admin/projects/{projectId}/disable (DEF-38)
 */
export async function disableProject(projectId) {
  return await apiCall(`/admin/projects/${projectId}/disable`, 'POST');
}

/**
 * Re-activates an enabled project: POST /admin/projects/{projectId}/activate (DEF-38)
 */
export async function activateProject(projectId) {
  return await apiCall(`/admin/projects/${projectId}/activate`, 'POST');
}

/**
 * Fetches project regulatory workflow structure and step progress: GET /projects/{projectId}/workflow
 */
export async function getProjectWorkflow(projectId) {
  return await apiCall(`/projects/${projectId}/workflow`, 'GET');
}

/**
 * Fetches details for a single workflow step: GET /projects/{projectId}/workflow/steps/{stepId}
 */
export async function getProjectWorkflowStep(projectId, stepId) {
  return await apiCall(`/projects/${projectId}/workflow/steps/${stepId}`, 'GET');
}

/**
 * Fetches project audit trail events: GET /projects/{projectId}/audit-events
 */
export async function getProjectAuditEvents(projectId) {
  const data = await apiCall(`/projects/${projectId}/audit-events`, 'GET');
  return Array.isArray(data) ? data : [];
}

/**
 * Fetches project requirements: GET /projects/{projectId}/requirements
 */
export async function getProjectRequirements(projectId) {
  try {
    const data = await apiCall(`/projects/${projectId}/requirements`, 'GET');
    if (Array.isArray(data)) return data;
  } catch (err) {}
  return [];
}

/**
 * Fetches real project audit readiness score & breakdown
 */
export async function getProjectReadiness(projectId) {
  try {
    return await apiCall(`/projects/${projectId}/readiness`, 'GET');
  } catch (err) {
    return {
      readiness_score: 0,
      readiness_percentage: 0,
      total_requirements: 0,
      completed_requirements: 0,
      status: 'PENDING',
      breakdown: [],
    };
  }
}

/**
 * Fetches project document attachments
 */
export async function getProjectAttachments(projectId) {
  try {
    const data = await apiCall(`/projects/${projectId}/attachments`, 'GET');
    if (Array.isArray(data)) return data;
  } catch (err) {}
  return [];
}

/**
 * Uploads a verified PDF attachment
 */
export async function uploadProjectAttachment(projectId, file, category = 'ADVISORY_REFERENCE') {
  if (!file) {
    throw new Error('No file selected for upload.');
  }
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    throw new Error('Only PDF documents (.pdf) are supported.');
  }

  const formData = new FormData();
  formData.append('file', file);
  formData.append('category', category);

  return await apiCall(`/projects/${projectId}/attachments`, 'POST', formData);
}

/**
 * Downloads a project attachment as an authenticated blob (DEF-FE-03)
 */
export async function downloadProjectAttachment(projectId, attachmentId, filename = 'document.pdf') {
  const token = getToken();
  const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
  const response = await fetch(`${BASE_URL}/projects/${projectId}/attachments/${attachmentId}`, {
    headers: {
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  });

  if (!response.ok) {
    let errMsg = `HTTP ${response.status}`;
    try {
      const errData = await response.json();
      errMsg = errData.detail || errData.message || errMsg;
    } catch (_) {}
    throw new Error(`Failed to download attachment: ${errMsg}`);
  }

  const blob = await response.blob();
  const blobUrl = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = blobUrl;
  link.download = filename || 'document.pdf';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(blobUrl);
}
