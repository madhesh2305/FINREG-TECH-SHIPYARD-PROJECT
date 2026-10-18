import { apiCall } from './api';

/**
 * Fetches audit events for a project via GET /projects/{projectId}/audit-events
 */
export async function getAuditEvents(projectId = '1') {
  try {
    const data = await apiCall(`/projects/${projectId}/audit-events`, 'GET');
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.error(`[auditService] GET /projects/${projectId}/audit-events failed:`, err);
    return [];
  }
}
