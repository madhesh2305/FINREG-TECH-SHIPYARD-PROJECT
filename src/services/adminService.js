import { apiCall } from './api';

/**
 * Fetches platform-wide administrative statistics via GET /admin/stats
 */
export async function getAdminStats() {
  try {
    return await apiCall('/admin/stats', 'GET');
  } catch (err) {
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
 * Fetches all registered users for administration via GET /admin/users
 */
export async function getAdminUsers(roleFilter = null, statusFilter = null) {
  let url = '/admin/users?';
  if (roleFilter && roleFilter !== 'All roles') url += `role=${roleFilter.toUpperCase()}&`;
  if (statusFilter && statusFilter !== 'All statuses') url += `status=${statusFilter.toUpperCase()}&`;
  const cleanUrl = url.replace(/[?&]$/, '');
  const data = await apiCall(cleanUrl, 'GET');
  return Array.isArray(data) ? data : [];
}

/**
 * Updates a user account status (ACTIVE/INACTIVE) via PATCH /admin/users/{userId}/status
 */
export async function updateUserStatus(userId, status) {
  const statusStr = typeof status === 'boolean' ? (status ? 'ACTIVE' : 'INACTIVE') : String(status).toUpperCase();
  return await apiCall(`/admin/users/${userId}/status`, 'PATCH', {
    status: statusStr,
    is_active: statusStr === 'ACTIVE',
  });
}

/**
 * Fetches roles and permissions definitions: GET /admin/roles-permissions
 */
export async function getRolesPermissions() {
  const data = await apiCall('/admin/roles-permissions', 'GET');
  return Array.isArray(data) ? data : [];
}

/**
 * Updates a user's platform role: PUT /admin/users/{userId}/role
 */
export async function updateUserRole(userId, role) {
  return await apiCall(`/admin/users/${userId}/role`, 'PUT', { role: role.toUpperCase() });
}

/**
 * Retrieves platform-wide advisor invitations: GET /admin/advisor-invitations
 */
export async function getAdminAdvisorInvitations(status = null) {
  const url =
    status && status !== 'All statuses'
      ? `/admin/advisor-invitations?status=${status.toUpperCase()}`
      : `/admin/advisor-invitations`;
  const data = await apiCall(url, 'GET');
  return Array.isArray(data) ? data : [];
}

/**
 * Provisions a new company administrator: POST /admin/users/provision-admin
 */
export async function provisionAdmin(payload) {
  return await apiCall('/admin/users/provision-admin', 'POST', payload);
}

/**
 * Retrieves platform-wide audit events via GET /admin/audit-events
 */
export async function getAdminAuditEvents(eventType = null) {
  const url =
    eventType && eventType !== 'All events' && eventType !== 'All event types'
      ? `/admin/audit-events?event_type=${eventType.toUpperCase()}`
      : `/admin/audit-events`;
  const data = await apiCall(url, 'GET');
  return Array.isArray(data) ? data : [];
}
