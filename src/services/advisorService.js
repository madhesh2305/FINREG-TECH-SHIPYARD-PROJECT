import { apiCall } from './api';

/**
 * Fetches expert advisors via live backend API: GET /advisors
 */
export async function getAdvisors() {
  const data = await apiCall('/advisors', 'GET');
  return Array.isArray(data) ? data : [];
}

/**
 * Fetches specific advisor profile details: GET /advisors/{advisorId}
 */
export async function getAdvisorDetails(advisorId) {
  return await apiCall(`/advisors/${advisorId}`, 'GET');
}

/**
 * Fetches project team members via live backend API: GET /projects/{projectId}/members
 */
export async function getProjectMembers(projectId) {
  const data = await apiCall(`/projects/${projectId}/members`, 'GET');
  return Array.isArray(data) ? data : [];
}

/**
 * Submits authoritative advice for a project requirement via POST /projects/{projectId}/advice
 * Payload matches AdviceCreate schema: { title, advice_text, recommendation, assumptions, advice_status, source_links }
 */
export async function submitProjectAdvice(projectId, advicePayload) {
  return await apiCall(`/projects/${projectId}/advice`, 'POST', advicePayload);
}

/**
 * Fetches authoritative advice submissions for a project via GET /projects/{projectId}/advice
 */
export async function getProjectAdvice(projectId, statusFilter = null) {
  const endpoint = statusFilter
    ? `/projects/${projectId}/advice?status=${encodeURIComponent(statusFilter)}`
    : `/projects/${projectId}/advice`;
  const data = await apiCall(endpoint, 'GET');
  return Array.isArray(data) ? data : [];
}

/**
 * Updates advisory review or status transition via PATCH /projects/{projectId}/advice/{adviceId}
 */
export async function updateProjectAdvice(projectId, adviceId, payload) {
  return await apiCall(`/projects/${projectId}/advice/${adviceId}`, 'PATCH', payload);
}

/**
 * Sends an invitation via POST /projects/{projectId}/advisor-invitations
 * Payload conforms to AdvisorInvitationCreate schema: { advisor_email, access_level, invitation_notes }
 */
export async function sendAdvisorInvitation(projectId, payload) {
  const email = payload.advisor_email || payload.advisorEmail || payload.email;
  let accessLevel = payload.access_level || 'CONTRIBUTOR';
  const roleUpper = (payload.role || '').toUpperCase();
  if (roleUpper.includes('READ')) accessLevel = 'READ_ONLY';
  else if (roleUpper.includes('FULL') || roleUpper.includes('LEGAL')) accessLevel = 'FULL_ADVISORY';

  const notes = payload.invitation_notes || payload.message || payload.notes;

  const backendPayload = {
    advisor_email: email,
    access_level: accessLevel,
    invitation_notes: notes || undefined,
  };

  return await apiCall(`/projects/${projectId}/advisor-invitations`, 'POST', backendPayload);
}

/**
 * Retrieves all invitations issued for a project via GET /projects/{projectId}/advisor-invitations
 */
export async function getProjectAdvisorInvitations(projectId) {
  const data = await apiCall(`/projects/${projectId}/advisor-invitations`, 'GET');
  return Array.isArray(data) ? data : [];
}
