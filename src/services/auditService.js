import { apiCall } from './api';

const MOCK_AUDIT_EVENTS = [
  {
    id: 'evt_1',
    badge: 'YO',
    user: 'You',
    action: 'updated',
    target: 'AML Compliance Framework',
    time: '2h ago',
  },
  {
    id: 'evt_2',
    badge: 'SO',
    user: 'S. Okonkwo',
    action: 'submitted',
    target: 'KYC Onboarding Workflow',
    time: '5h ago',
  },
  {
    id: 'evt_3',
    badge: 'MC',
    user: 'M. Chen',
    action: 'completed',
    target: 'GDPR Data Audit Trail',
    time: 'Yesterday',
  },
  {
    id: 'evt_4',
    badge: 'AP',
    user: 'A. Petrov',
    action: 'created draft',
    target: 'Regulatory Reporting Q3',
    time: '3 days ago',
  },
];

/**
 * Fetches audit events for a project via GET /projects/{projectId}/audit-events
 */
export async function getAuditEvents(projectId = 'PRJ-001') {
  try {
    const data = await apiCall(`/projects/${projectId}/audit-events`, 'GET');
    return Array.isArray(data) && data.length > 0 ? data : MOCK_AUDIT_EVENTS;
  } catch (err) {
    console.warn(`[auditService] GET /projects/${projectId}/audit-events failed. Returning mock audit feed.`);
    return MOCK_AUDIT_EVENTS;
  }
}
