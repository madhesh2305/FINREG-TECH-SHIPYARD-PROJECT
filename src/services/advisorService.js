import { apiCall } from './api';

const MOCK_ADVISORS = [];

const MOCK_TEAM_MEMBERS = [];

/**
 * Fetches expert advisors via GET /advisors
 */
export async function getAdvisors() {
  try {
    const data = await apiCall('/advisors', 'GET');
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.warn('[advisorService] GET /advisors failed.');
    return [];
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
    console.warn(`[advisorService] GET /projects/${projectId}/members failed.`);
    return [];
  }
}

/**
 * Submits authoritative advice for a project requirement via POST /projects/{projectId}/advice
 */
export async function submitProjectAdvice(projectId, advicePayload) {
  return await apiCall(`/projects/${projectId}/advice`, 'POST', advicePayload);
}

/**
 * Fetches authoritative advice submissions for a project via GET /projects/{projectId}/advice
 */
export async function getProjectAdvice(projectId) {
  try {
    const data = await apiCall(`/projects/${projectId}/advice`, 'GET');
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.warn(`[advisorService] GET /projects/${projectId}/advice failed:`, err.message);
    return [];
  }
}

/**
 * Sends an invitation via POST /projects/{projectId}/advisor-invitations
 */
export async function sendAdvisorInvitation(projectId, payload) {
  return await apiCall(`/projects/${projectId}/advisor-invitations`, 'POST', payload);
}
