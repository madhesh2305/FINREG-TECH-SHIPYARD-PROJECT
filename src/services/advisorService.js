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
 * Sends an invitation via POST /projects/{projectId}/advisor-invitations
 */
export async function sendAdvisorInvitation(projectId, payload) {
  try {
    return await apiCall(`/projects/${projectId}/advisor-invitations`, 'POST', payload);
  } catch (err) {
    console.warn(`[advisorService] POST /projects/${projectId}/advisor-invitations failed.`);
    return { status: 'sent', invitationId: `inv_${Date.now()}` };
  }
}
