import { apiCall } from './api';

const MOCK_AUDIT_EVENTS = [];

/**
 * Fetches audit events for a project via GET /projects/{projectId}/audit-events
 */
export async function getAuditEvents(projectId = 'PRJ-001') {
  try {
    const data = await apiCall(`/projects/${projectId}/audit-events`, 'GET');
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.warn(`[auditService] GET /projects/${projectId}/audit-events failed.`);
    return [];
  }
}
