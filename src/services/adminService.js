import { apiCall } from './api';

/**
 * Fetches platform administrative summary statistics via GET /admin/stats
 */
export async function getAdminStats() {
  try {
    return await apiCall('/admin/stats', 'GET');
  } catch (err) {
    console.warn('[adminService] GET /admin/stats failed:', err);
    return {
      total_users: 0,
      active_users: 0,
      total_projects: 0,
      regulatory_sources_count: 0,
      total_audit_events: 0,
    };
  }
}

/**
 * Fetches platform user directory via GET /admin/users
 */
export async function getAdminUsers() {
  try {
    const data = await apiCall('/admin/users', 'GET');
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.warn('[adminService] GET /admin/users failed:', err);
    return [];
  }
}

/**
 * Updates a user account active status via PATCH /admin/users/{userId}/status
 */
export async function updateUserStatus(userId, isActive) {
  try {
    return await apiCall(`/admin/users/${userId}/status`, 'PATCH', { is_active: isActive });
  } catch (err) {
    console.error(`[adminService] PATCH /admin/users/${userId}/status failed:`, err);
    throw err;
  }
}

/**
 * Fetches platform-wide immutable audit events via GET /admin/audit-events (DEF-03)
 */
export async function getAdminAuditEvents(limit = 100) {
  try {
    const data = await apiCall(`/admin/audit-events?limit=${limit}`, 'GET');
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.warn('[adminService] GET /admin/audit-events failed:', err);
    return [];
  }
}
