import { apiCall } from './api';

/**
 * Fetches expert advisors via GET /advisors
 */
export async function getAdvisors() {
  try {
    const data = await apiCall('/advisors', 'GET');
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.error('[advisorService] GET /advisors failed:', err);
    throw err;
  }
}

/**
 * Fetches project team members via GET /projects/{projectId}/members
 */
export async function getProjectMembers(projectId) {
  try {
    const data = await apiCall(`/projects/${projectId}/members`, 'GET');
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.error(`[advisorService] GET /projects/${projectId}/members failed:`, err);
    throw err;
  }
}

/**
 * Sends an invitation via POST /projects/{projectId}/advisor-invitations
 */
export async function sendAdvisorInvitation(projectId, payload) {
  try {
    return await apiCall(`/projects/${projectId}/advisor-invitations`, 'POST', payload);
  } catch (err) {
    console.error(`[advisorService] POST /projects/${projectId}/advisor-invitations failed:`, err);
    throw err;
  }
}

/**
 * Adds an existing user/advisor as a project member via POST /projects/{projectId}/members
 */
export async function addProjectMember(projectId, memberPayload) {
  try {
    return await apiCall(`/projects/${projectId}/members`, 'POST', memberPayload);
  } catch (err) {
    console.error(`[advisorService] POST /projects/${projectId}/members failed:`, err);
    throw err;
  }
}

/**
 * Fetches advisor invitations for project via GET /projects/{projectId}/advisor-invitations
 */
export async function getProjectInvitations(projectId) {
  try {
    const data = await apiCall(`/projects/${projectId}/advisor-invitations`, 'GET');
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.warn(`[advisorService] GET /projects/${projectId}/advisor-invitations failed:`, err);
    return [];
  }
}
