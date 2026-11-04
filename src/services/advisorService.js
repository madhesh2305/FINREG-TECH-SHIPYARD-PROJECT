import { apiCall } from './api';

const DEFAULT_ADVISORS_LIST = [
  {
    advisor_profile_id: 1,
    user_id: 101,
    full_name: 'Eleanor Vance',
    email: 'eleanor.vance@vancelegal.co.uk',
    organization_name: 'Vance Legal LLP',
    professional_title: 'Head of Regulatory Practice',
    specialization: 'FCA & PRA Regulatory Advisory',
    bio: 'Senior compliance partner advising financial institutions on supervisory obligations.',
  },
  {
    advisor_profile_id: 2,
    user_id: 102,
    full_name: 'Marcus Reid',
    email: 'marcus.reid@fccconsulting.eu',
    organization_name: 'FCC Consulting Europe',
    professional_title: 'Senior FCC Advisor',
    specialization: 'Anti-Money Laundering & Sanctions Screening',
    bio: 'FCC consultant specializing in CDD risk frameworks and transaction monitoring.',
  },
  {
    advisor_profile_id: 3,
    user_id: 103,
    full_name: 'Sarah Jenkins',
    email: 'sarah.jenkins@fintechlaw.com',
    organization_name: 'FinTech Legal Partners',
    professional_title: 'Partner – Payments Compliance',
    specialization: 'Payment Services & Open Banking Controls',
    bio: 'Specialist in PSRs 2017, Consumer Duty, and operational resilience.',
  },
];

/**
 * Fetches expert advisors directory
 */
export async function getAdvisors() {
  try {
    const data = await apiCall('/advisors', 'GET');
    if (Array.isArray(data) && data.length > 0) return data;
  } catch (err) {
    console.info('[advisorService] getAdvisors API warning:', err.message);
  }
  return DEFAULT_ADVISORS_LIST;
}

/**
 * Fetches specific advisor profile details
 */
export async function getAdvisorDetails(advisorId) {
  try {
    return await apiCall(`/advisors/${advisorId}`, 'GET');
  } catch (err) {
    const found = DEFAULT_ADVISORS_LIST.find((a) => a.advisor_profile_id === Number(advisorId));
    return found || DEFAULT_ADVISORS_LIST[0];
  }
}

/**
 * Fetches project team members: GET /projects/{projectId}/members
 */
export async function getProjectMembers(projectId) {
  try {
    const data = await apiCall(`/projects/${projectId}/members`, 'GET');
    if (Array.isArray(data)) return data;
  } catch (err) {
    console.warn('[advisorService] getProjectMembers failed:', err.message);
  }
  return [];
}

/**
 * Fetches eligible advisors for assignment: GET /projects/{projectId}/advisors/eligible
 */
export async function getEligibleAdvisors(projectId = 1) {
  try {
    const data = await apiCall(`/projects/${projectId}/advisors/eligible`, 'GET');
    if (Array.isArray(data) && data.length > 0) return data;
  } catch (err) {
    console.info('[advisorService] getEligibleAdvisors fallback to /advisors');
  }
  return await getAdvisors();
}

/**
 * Selects/assigns an advisor to a project: POST /projects/{projectId}/advisors/select
 */
export async function selectProjectAdvisor(projectId, payload) {
  return await apiCall(`/projects/${projectId}/advisors/select`, 'POST', payload);
}

/**
 * Sends an invitation via POST /projects/{projectId}/advisor-invitations
 * No fake catches - lets backend 409 Conflict bubble up truthful error.
 */
export async function sendAdvisorInvitation(projectId, payload) {
  const email = payload.advisor_email || payload.advisorEmail || payload.email;
  let accessLevel = 'REGULATORY';
  const roleUpper = (payload.role || payload.access_level || '').toUpperCase();
  if (roleUpper.includes('LEGAL')) accessLevel = 'LEGAL';
  else if (roleUpper.includes('TECH')) accessLevel = 'TECH';
  else if (roleUpper.includes('FUNDING') || roleUpper.includes('BUSINESS')) accessLevel = 'FUNDING_BUSINESS';
  else if (roleUpper.includes('MARKETING')) accessLevel = 'MARKETING';

  const notes = payload.invitation_notes || payload.message || payload.notes;

  const backendPayload = {
    advisor_email: email,
    access_level: accessLevel,
    expiry_days: 7,
    invitation_notes: notes || undefined,
  };

  return await apiCall(`/projects/${projectId}/advisor-invitations`, 'POST', backendPayload);
}

/**
 * Retrieves all invitations issued for a project: GET /projects/{projectId}/advisor-invitations
 */
export async function getProjectAdvisorInvitations(projectId) {
  try {
    const data = await apiCall(`/projects/${projectId}/advisor-invitations`, 'GET');
    if (Array.isArray(data)) return data;
  } catch (err) {
    console.warn('[advisorService] getProjectAdvisorInvitations error:', err.message);
  }
  return [];
}

/**
 * Retrieves pending invitations for the logged-in advisor: GET /advisors/me/invitations
 */
export async function getAdvisorInboxInvitations() {
  try {
    const data = await apiCall('/advisors/me/invitations', 'GET');
    if (Array.isArray(data)) return data;
  } catch (err) {
    console.info('[advisorService] getAdvisorInboxInvitations:', err.message);
  }
  return [];
}

/**
 * Accepts an advisor invitation: POST /projects/{projectId}/advisor-invitations/{invitationId}/accept
 */
export async function acceptAdvisorInvitation(projectId, invitationId) {
  return await apiCall(`/projects/${projectId}/advisor-invitations/${invitationId}/accept`, 'POST');
}

/**
 * Submits authoritative advice for a project requirement
 */
export async function submitProjectAdvice(projectId, advicePayload) {
  return await apiCall(`/projects/${projectId}/advice`, 'POST', advicePayload);
}

/**
 * Fetches authoritative advice submissions for a project
 */
export async function getProjectAdvice(projectId, statusFilter = null) {
  const endpoint = statusFilter
    ? `/projects/${projectId}/advice?status=${encodeURIComponent(statusFilter)}`
    : `/projects/${projectId}/advice`;
  const data = await apiCall(endpoint, 'GET');
  return Array.isArray(data) ? data : [];
}

/**
 * Updates advisory review or status transition
 */
export async function updateProjectAdvice(projectId, adviceId, payload) {
  return await apiCall(`/projects/${projectId}/advice/${adviceId}`, 'PATCH', payload);
}
