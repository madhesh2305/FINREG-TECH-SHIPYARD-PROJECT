import { apiCall } from './api';

/**
 * Fetches platform-wide administrative statistics via GET /admin/stats
 */
export async function getAdminStats() {
  try {
    return await apiCall('/admin/stats', 'GET');
  } catch (err) {
    console.warn('[adminService] GET /admin/stats failed:', err.message);
    return null;
  }
}

/**
 * Fetches all registered users for administration via GET /admin/users
 */
export async function getAdminUsers() {
  try {
    const data = await apiCall('/admin/users', 'GET');
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.warn('[adminService] GET /admin/users failed:', err.message);
    return [];
  }
}

/**
 * Updates a user account status (active/inactive) via PATCH /admin/users/{userId}/status
 */
export async function updateUserStatus(userId, isActive) {
  return await apiCall(`/admin/users/${userId}/status`, 'PATCH', { is_active: isActive });
}

/**
 * Retrieves platform-wide audit events via GET /admin/audit-events
 */
export async function getAdminAuditEvents(limit = 100) {
  try {
    const data = await apiCall(`/admin/audit-events?limit=${limit}`, 'GET');
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.warn('[adminService] GET /admin/audit-events failed:', err.message);
    return [];
  }
}
