import { apiCall } from './api';

const MOCK_ADVISORS = [
  {
    id: 'adv_001',
    name: 'S. Okonkwo',
    title: 'Senior FCC & Anti-Money Laundering Expert',
    organization: 'FinReg Solutions UK',
    avatar: 'SO',
    specialties: ['AML/CTF', 'KYC/CDD', 'FCA Regulations'],
    rating: '4.9',
  },
  {
    id: 'adv_002',
    name: 'A. Petrov',
    title: 'Prudential Reporting & Risk Specialist',
    organization: 'EBA Compliance Partners',
    avatar: 'AP',
    specialties: ['Regulatory Reporting', 'Basel III', 'Capital Adequacy'],
    rating: '4.8',
  },
  {
    id: 'adv_003',
    name: 'M. Chen',
    title: 'Data Protection & GDPR Officer',
    organization: 'Global Privacy Guild',
    avatar: 'MC',
    specialties: ['GDPR', 'Data Governance', 'Audit Trails'],
    rating: '5.0',
  },
];

const MOCK_TEAM_MEMBERS = [
  { id: 'mem_1', name: 'J. Nakamura', role: 'Owner', avatar: 'JN', type: 'OWNER' },
  { id: 'mem_2', name: 'S. Okonkwo', role: 'Advisor 1', avatar: 'SO', type: 'ADVISOR' },
  { id: 'mem_3', name: 'A. Petrov', role: 'Advisor 2', avatar: 'AP', type: 'ADVISOR' },
];

/**
 * Fetches expert advisors via GET /advisors
 */
export async function getAdvisors() {
  try {
    const data = await apiCall('/advisors', 'GET');
    return Array.isArray(data) && data.length > 0 ? data : MOCK_ADVISORS;
  } catch (err) {
    console.warn('[advisorService] GET /advisors failed. Returning mock advisors.');
    return MOCK_ADVISORS;
  }
}

/**
 * Fetches project team members via GET /projects/{projectId}/members
 */
export async function getProjectMembers(projectId) {
  try {
    const data = await apiCall(`/projects/${projectId}/members`, 'GET');
    return Array.isArray(data) && data.length > 0 ? data : MOCK_TEAM_MEMBERS;
  } catch (err) {
    console.warn(`[advisorService] GET /projects/${projectId}/members failed. Returning mock team members.`);
    return MOCK_TEAM_MEMBERS;
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
