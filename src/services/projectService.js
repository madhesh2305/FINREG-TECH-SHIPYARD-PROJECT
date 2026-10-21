import { apiCall } from './api';

// Projects List initialized to empty array (ready for live backend API data)
const MOCK_PROJECTS = [];

export const PROJECTS_STORAGE_KEY = 'finreg_projects';

/**
 * Retrieves persisted custom projects from local storage
 */
export function getLocalProjects() {
  try {
    const raw = localStorage.getItem(PROJECTS_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    const clean = parsed.filter(
      (p) =>
        p &&
        p.id !== 'PRJ-001' &&
        p.name !== 'ABC Shield' &&
        p.name !== 'KYC Onboarding Controls' &&
        !p.id?.includes('MOCK')
    );
    try {
      localStorage.setItem(PROJECTS_STORAGE_KEY, JSON.stringify(clean));
    } catch (e) {}
    return clean;
  } catch (e) {
    return [];
  }
}

/**
 * Fetches all user projects via GET /projects
 */
export async function getProjects() {
  try {
    const data = await apiCall('/projects', 'GET');
    if (Array.isArray(data)) return data;
  } catch (err) {
    console.warn('[projectService] GET /projects failed:', err.message);
  }
  return [];
}

/**
 * Fetches summary metrics via GET /projects/summary
 */
export async function getProjectSummary() {
  try {
    return await apiCall('/projects/summary', 'GET');
  } catch (err) {
    console.warn('[projectService] GET /projects/summary failed:', err.message);
    const projects = await getProjects();
    return {
      total: projects.length,
      inProgress: projects.filter((p) => p.status === 'In Progress').length,
      underReview: projects.filter((p) => p.status === 'Under Review').length,
      completed: projects.filter((p) => p.status === 'Completed').length,
    };
  }
}

/**
 * Fetches single project details via GET /projects/{projectId}
 * Strictly avoids falling back to other users' projects (prevents BOLA / IDOR leak)
 */
export async function getProjectDetails(projectId) {
  return await apiCall(`/projects/${projectId}`, 'GET');
}

/**
 * Creates a new project via POST /projects
 */
export async function createProject(projectPayload) {
  return await apiCall('/projects', 'POST', projectPayload);
}

/**
 * Updates an existing project via PATCH /projects/{projectId}
 */
export async function updateProject(projectId, updatePayload) {
  try {
    return await apiCall(`/projects/${projectId}`, 'PATCH', updatePayload);
  } catch (err) {
    console.warn(`[projectService] PATCH /projects/${projectId} failed.`);
    return updatePayload;
  }
}

/**
 * Fetches project requirements via GET /projects/{projectId}/requirements
 */
export async function getProjectRequirements(projectId) {
  try {
    const data = await apiCall(`/projects/${projectId}/requirements`, 'GET');
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.warn(`[projectService] GET /projects/${projectId}/requirements failed.`);
    return [];
  }
}
