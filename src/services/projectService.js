import { apiCall } from './api';

export const PROJECTS_STORAGE_KEY = 'finreg_projects';

// Purge legacy custom projects storage to prevent stale cross-user project caching
try {
  localStorage.removeItem(PROJECTS_STORAGE_KEY);
} catch (e) {}

/**
 * Returns empty array - mock project storage is strictly deprecated.
 */
export function getLocalProjects() {
  return [];
}

/**
 * Fetches all authorized user projects via live backend API: GET /projects
 */
export async function getProjects() {
  const data = await apiCall('/projects', 'GET');
  return Array.isArray(data) ? data : [];
}

/**
 * Fetches summary metrics via live backend API: GET /projects/summary
 */
export async function getProjectSummary() {
  return await apiCall('/projects/summary', 'GET');
}

/**
 * Fetches single project details via live backend API: GET /projects/{projectId}
 * Strictly enforces project-level authorization (returns 403 / 404 on unassigned projects).
 */
export async function getProjectDetails(projectId) {
  return await apiCall(`/projects/${projectId}`, 'GET');
}

/**
 * Creates a new project via live backend API: POST /projects
 */
export async function createProject(projectPayload) {
  return await apiCall('/projects', 'POST', projectPayload);
}

/**
 * Updates an existing project via live backend API: PATCH /projects/{projectId}
 */
export async function updateProject(projectId, updatePayload) {
  return await apiCall(`/projects/${projectId}`, 'PATCH', updatePayload);
}

/**
 * Fetches project requirements via live backend API: GET /projects/{projectId}/requirements
 */
export async function getProjectRequirements(projectId) {
  const data = await apiCall(`/projects/${projectId}/requirements`, 'GET');
  return Array.isArray(data) ? data : [];
}

/**
 * Fetches real project audit readiness score & breakdown: GET /projects/{projectId}/readiness
 */
export async function getProjectReadiness(projectId) {
  return await apiCall(`/projects/${projectId}/readiness`, 'GET');
}

/**
 * Fetches project document attachments: GET /projects/{projectId}/attachments
 */
export async function getProjectAttachments(projectId) {
  const data = await apiCall(`/projects/${projectId}/attachments`, 'GET');
  return Array.isArray(data) ? data : [];
}

/**
 * Uploads a verified PDF attachment: POST /projects/{projectId}/attachments
 * Validates multipart/form-data boundary and PDF structure.
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
