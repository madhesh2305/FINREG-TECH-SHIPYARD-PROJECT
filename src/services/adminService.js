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
