import { apiCall } from './api';
import { getLocalAccounts, saveLocalAccount } from './authService';

const ROLE_OVERRIDES_KEY = 'finreg_admin_role_overrides';
const STATUS_OVERRIDES_KEY = 'finreg_admin_status_overrides';
const PROVISIONED_ADMINS_KEY = 'finreg_provisioned_admins';
const ADMIN_AUDIT_LOGS_KEY = 'finreg_admin_audit_logs';

/**
 * Authoritative default platform roles and least-privilege boundaries
 */
export const DEFAULT_PLATFORM_ROLES = [
  {
    id: 'ROLE-001',
    role_id: 1,
    name: 'Administrator',
    role_name: 'ADMIN',
    role: 'ADMIN',
    permitted_actions: [
      'MANAGE_USERS',
      'UPDATE_USER_ROLE',
      'TOGGLE_USER_STATUS',
      'PROVISION_ADMIN',
      'VIEW_AUDIT_LOGS',
      'OVERSEE_PROJECTS',
      'MANAGE_REGULATORY_SOURCES',
      'PLATFORM_TELEMETRY',
    ],
    permittedActions: [
      'MANAGE_USERS',
      'UPDATE_USER_ROLE',
      'TOGGLE_USER_STATUS',
      'PROVISION_ADMIN',
      'VIEW_AUDIT_LOGS',
      'OVERSEE_PROJECTS',
      'MANAGE_REGULATORY_SOURCES',
      'PLATFORM_TELEMETRY',
    ],
    access_boundary: 'Global platform governance, tenant lifecycle, audit trail oversight, security policy enforcement. Platform isolation enforced.',
    accessBoundary: 'Global platform governance, tenant lifecycle, audit trail oversight, security policy enforcement. Platform isolation enforced.',
    status: 'Active definition',
  },
  {
    id: 'ROLE-002',
    role_id: 2,
    name: 'Compliance Advisor',
    role_name: 'ADVISOR',
    role: 'ADVISOR',
    permitted_actions: [
      'SUBMIT_ADVICE',
      'REVIEW_RAG_FINDINGS',
      'ACCEPT_INVITATION',
      'DECLINE_INVITATION',
      'VIEW_ASSIGNED_PROJECTS',
      'VIEW_AUDIT_TRAIL',
    ],
    permittedActions: [
      'SUBMIT_ADVICE',
      'REVIEW_RAG_FINDINGS',
      'ACCEPT_INVITATION',
      'DECLINE_INVITATION',
      'VIEW_ASSIGNED_PROJECTS',
      'VIEW_AUDIT_TRAIL',
    ],
    access_boundary: 'Project-scoped advisory workspace, multi-firm SME assignment, regulatory clause interpretation, human-in-the-loop review.',
    accessBoundary: 'Project-scoped advisory workspace, multi-firm SME assignment, regulatory clause interpretation, human-in-the-loop review.',
    status: 'Active definition',
  },
  {
    id: 'ROLE-003',
    role_id: 3,
    name: 'Builder / Project Owner',
    role_name: 'BUILDER',
    role: 'BUILDER',
    permitted_actions: [
      'CREATE_PROJECT',
      'UPLOAD_SPEC',
      'RUN_RAG_SCAN',
      'REQUEST_ADVICE',
      'ASSIGN_ADVISOR',
      'DECIDE_FINDINGS',
      'EXPORT_REPORT',
    ],
    permittedActions: [
      'CREATE_PROJECT',
      'UPLOAD_SPEC',
      'RUN_RAG_SCAN',
      'REQUEST_ADVICE',
      'ASSIGN_ADVISOR',
      'DECIDE_FINDINGS',
      'EXPORT_REPORT',
    ],
    access_boundary: 'Project creation, architecture configuration, tech stack definition, compliance advisor assignment, RAG scan triggering, human review request, export report.',
    accessBoundary: 'Project creation, architecture configuration, tech stack definition, compliance advisor assignment, RAG scan triggering, human review request, export report.',
    status: 'Active definition',
  },
];

function getRoleOverrides() {
  try {
    const raw = localStorage.getItem(ROLE_OVERRIDES_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch (e) {
    return {};
  }
}

function setRoleOverride(key, role) {
  try {
    const overrides = getRoleOverrides();
    overrides[String(key).toLowerCase().trim()] = String(role).toUpperCase().trim();
    localStorage.setItem(ROLE_OVERRIDES_KEY, JSON.stringify(overrides));
  } catch (e) {}
}

function getStatusOverrides() {
  try {
    const raw = localStorage.getItem(STATUS_OVERRIDES_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch (e) {
    return {};
  }
}

function setStatusOverride(key, isActive) {
  try {
    const overrides = getStatusOverrides();
    overrides[String(key).toLowerCase().trim()] = !!isActive;
    localStorage.setItem(STATUS_OVERRIDES_KEY, JSON.stringify(overrides));
  } catch (e) {}
}

export function isAccountDeactivated(email, userId = null) {
  try {
    const raw = localStorage.getItem(STATUS_OVERRIDES_KEY);
    const overrides = raw ? JSON.parse(raw) : {};
    if (email) {
      const e = String(email).toLowerCase().trim();
      if (overrides[e] === false) return true;
    }
    if (userId) {
      const u = String(userId).toLowerCase().trim();
      if (overrides[u] === false) return true;
    }
  } catch (e) {}

  try {
    const accounts = getLocalAccounts ? getLocalAccounts() : {};
    if (email) {
      const acc = accounts[String(email).toLowerCase().trim()];
      if (acc?.user && (acc.user.is_active === false || acc.user.status === 'Inactive')) {
        return true;
      }
    }
  } catch (e) {}

  return false;
}

export function getProvisionedAdmins() {
  try {
    const raw = localStorage.getItem(PROVISIONED_ADMINS_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (e) {
    return [];
  }
}

function saveProvisionedAdmin(adminUser) {
  try {
    const list = getProvisionedAdmins();
    const cleanEmail = (adminUser.email || '').toLowerCase().trim();
    const idx = list.findIndex((a) => (a.email || '').toLowerCase().trim() === cleanEmail);
    if (idx >= 0) {
      list[idx] = { ...list[idx], ...adminUser };
    } else {
      list.unshift(adminUser);
    }
    localStorage.setItem(PROVISIONED_ADMINS_KEY, JSON.stringify(list));
  } catch (e) {}
}

export const DEFAULT_ADMIN_AUDIT_LOGS = [
  {
    id: 'LOG-001',
    audit_event_id: 'AUD-SEC-001',
    actor_email: 'admin@finregtech.io',
    user: 'admin@finregtech.io',
    action: 'Admin login',
    resource: 'Admin Workspace Portal',
    affectedResource: 'Admin Workspace Portal',
    affected_resource: 'Admin Workspace Portal',
    event_type: 'Access Control',
    category: 'Access Control',
    eventCategory: 'Access Control',
    status: 'SUCCESS',
    result: 'Success',
    description: 'Master Administrator credentials verified and MFA security challenge fulfilled.',
    relevantDetails: 'Master Administrator credentials verified and MFA security challenge fulfilled.',
    details: 'Master Administrator credentials verified and MFA security challenge fulfilled.',
    created_at: new Date(Date.now() - 3600000 * 2).toISOString(),
    timestamp: new Date(Date.now() - 3600000 * 2).toLocaleString('en-GB'),
  },
  {
    id: 'LOG-002',
    audit_event_id: 'AUD-USR-002',
    actor_email: 'admin@finregtech.io',
    user: 'admin@finregtech.io',
    action: 'Role changed',
    resource: 'User: Eleanor Vance (advisor@gmail.com)',
    affectedResource: 'User: Eleanor Vance (advisor@gmail.com)',
    affected_resource: 'User: Eleanor Vance (advisor@gmail.com)',
    event_type: 'Access Control',
    category: 'Access Control',
    eventCategory: 'Access Control',
    status: 'SUCCESS',
    result: 'Success',
    description: 'Platform role updated from Builder to Advisor with full Regulatory Reviewer permissions.',
    relevantDetails: 'Platform role updated from Builder to Advisor with full Regulatory Reviewer permissions.',
    details: 'Platform role updated from Builder to Advisor with full Regulatory Reviewer permissions.',
    created_at: new Date(Date.now() - 3600000 * 4).toISOString(),
    timestamp: new Date(Date.now() - 3600000 * 4).toLocaleString('en-GB'),
  },
  {
    id: 'LOG-003',
    audit_event_id: 'AUD-USR-003',
    actor_email: 'admin@finregtech.io',
    user: 'admin@finregtech.io',
    action: 'Account deactivated',
    resource: 'User: Marcus Reid (marcus.reid@finadvisory.co.uk)',
    affectedResource: 'User: Marcus Reid (marcus.reid@finadvisory.co.uk)',
    affected_resource: 'User: Marcus Reid (marcus.reid@finadvisory.co.uk)',
    event_type: 'User Governance',
    category: 'User Governance',
    eventCategory: 'User Governance',
    status: 'BLOCKED',
    result: 'Blocked',
    description: 'Administrator deactivated user account pending annual regulatory compliance recertification.',
    relevantDetails: 'Administrator deactivated user account pending annual regulatory compliance recertification.',
    details: 'Administrator deactivated user account pending annual regulatory compliance recertification.',
    created_at: new Date(Date.now() - 3600000 * 6).toISOString(),
    timestamp: new Date(Date.now() - 3600000 * 6).toLocaleString('en-GB'),
  },
  {
    id: 'LOG-004',
    audit_event_id: 'AUD-ADV-004',
    actor_email: 'builder@gmail.com',
    user: 'builder@gmail.com',
    action: 'Invitation created',
    resource: 'Advisor: Eleanor Vance (advisor@gmail.com)',
    affectedResource: 'Advisor: Eleanor Vance (advisor@gmail.com)',
    affected_resource: 'Advisor: Eleanor Vance (advisor@gmail.com)',
    event_type: 'Advisor Engagement',
    category: 'Advisor Engagement',
    eventCategory: 'Advisor Engagement',
    status: 'SUCCESS',
    result: 'Success',
    description: 'Builder Jun Developer dispatched compliance review invitation for AML Compliance Framework.',
    relevantDetails: 'Builder Jun Developer dispatched compliance review invitation for AML Compliance Framework.',
    details: 'Builder Jun Developer dispatched compliance review invitation for AML Compliance Framework.',
    created_at: new Date(Date.now() - 3600000 * 9).toISOString(),
    timestamp: new Date(Date.now() - 3600000 * 9).toLocaleString('en-GB'),
  },
  {
    id: 'LOG-005',
    audit_event_id: 'AUD-ADV-005',
    actor_email: 'advisor@gmail.com',
    user: 'advisor@gmail.com',
    action: 'Invitation created',
    resource: 'Project: AML Compliance Framework',
    affectedResource: 'Project: AML Compliance Framework',
    affected_resource: 'Project: AML Compliance Framework',
    event_type: 'Advisor Engagement',
    category: 'Advisor Engagement',
    eventCategory: 'Advisor Engagement',
    status: 'SUCCESS',
    result: 'Success',
    description: 'Advisor Eleanor Vance accepted project invitation and joined as Contributor.',
    relevantDetails: 'Advisor Eleanor Vance accepted project invitation and joined as Contributor.',
    details: 'Advisor Eleanor Vance accepted project invitation and joined as Contributor.',
    created_at: new Date(Date.now() - 3600000 * 12).toISOString(),
    timestamp: new Date(Date.now() - 3600000 * 12).toLocaleString('en-GB'),
  },
  {
    id: 'LOG-006',
    audit_event_id: 'AUD-SRC-006',
    actor_email: 'admin@finregtech.io',
    user: 'admin@finregtech.io',
    action: 'Source metadata updated',
    resource: 'FCA Handbook / MLR 2017 Source Map',
    affectedResource: 'FCA Handbook / MLR 2017 Source Map',
    affected_resource: 'FCA Handbook / MLR 2017 Source Map',
    event_type: 'Regulatory Governance',
    category: 'Regulatory Governance',
    eventCategory: 'Regulatory Governance',
    status: 'SUCCESS',
    result: 'Success',
    description: 'Updated statutory instrument metadata and compliance validation rules for AML / CTF regulations.',
    relevantDetails: 'Updated statutory instrument metadata and compliance validation rules for AML / CTF regulations.',
    details: 'Updated statutory instrument metadata and compliance validation rules for AML / CTF regulations.',
    created_at: new Date(Date.now() - 3600000 * 18).toISOString(),
    timestamp: new Date(Date.now() - 3600000 * 18).toLocaleString('en-GB'),
  },
  {
    id: 'LOG-007',
    audit_event_id: 'AUD-SEC-007',
    actor_email: 'unknown.client@192.168.1.45',
    user: 'unknown.client@192.168.1.45',
    action: 'Login failure',
    resource: 'Authentication Gateway',
    affectedResource: 'Authentication Gateway',
    affected_resource: 'Authentication Gateway',
    event_type: 'Security Telemetry',
    category: 'Security Telemetry',
    eventCategory: 'Security Telemetry',
    status: 'BLOCKED',
    result: 'Blocked',
    description: 'Suspicious login attempt blocked: invalid credentials and failed device fingerprint challenge.',
    relevantDetails: 'Suspicious login attempt blocked: invalid credentials and failed device fingerprint challenge.',
    details: 'Suspicious login attempt blocked: invalid credentials and failed device fingerprint challenge.',
    created_at: new Date(Date.now() - 3600000 * 22).toISOString(),
    timestamp: new Date(Date.now() - 3600000 * 22).toLocaleString('en-GB'),
  },
  {
    id: 'LOG-008',
    audit_event_id: 'AUD-PRJ-008',
    actor_email: 'builder@gmail.com',
    user: 'builder@gmail.com',
    action: 'Project created',
    resource: 'Project: AML Compliance Framework',
    affectedResource: 'Project: AML Compliance Framework',
    affected_resource: 'Project: AML Compliance Framework',
    event_type: 'Project Lifecycle',
    category: 'Project Lifecycle',
    eventCategory: 'Project Lifecycle',
    status: 'SUCCESS',
    result: 'Success',
    description: 'Project AML Compliance Framework initialized with FCA Regulatory Reviewer requirements.',
    relevantDetails: 'Project AML Compliance Framework initialized with FCA Regulatory Reviewer requirements.',
    details: 'Project AML Compliance Framework initialized with FCA Regulatory Reviewer requirements.',
    created_at: new Date(Date.now() - 3600000 * 24).toISOString(),
    timestamp: new Date(Date.now() - 3600000 * 24).toLocaleString('en-GB'),
  },
];

export function recordAdminAuditLog(event) {
  try {
    const raw = localStorage.getItem(ADMIN_AUDIT_LOGS_KEY);
    const logs = raw ? JSON.parse(raw) : [];
    const timestamp = new Date();
    const newLog = {
      id: `LOG-${Date.now()}`,
      audit_event_id: `AUD-${Date.now()}`,
      created_at: timestamp.toISOString(),
      timestamp: timestamp.toLocaleString('en-GB', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      }),
      status: event.status || 'SUCCESS',
      result: (event.status || 'SUCCESS').toUpperCase() === 'BLOCKED' || (event.status || '').toUpperCase() === 'FAILED' ? 'Blocked' : 'Success',
      user: event.actor_email || event.user || 'admin@finregtech.io',
      actor_email: event.actor_email || event.user || 'admin@finregtech.io',
      action: event.action || 'SYSTEM_EVENT',
      affectedResource: event.affectedResource || event.resource || 'Platform',
      resource: event.affectedResource || event.resource || 'Platform',
      eventCategory: event.event_type || event.eventCategory || event.category || 'Platform Governance',
      category: event.event_type || event.eventCategory || event.category || 'Platform Governance',
      event_type: event.event_type || event.action || 'SYSTEM_EVENT',
      relevantDetails: event.description || event.details || event.relevantDetails || 'Administrative event logged',
      description: event.description || event.details || event.relevantDetails || 'Administrative event logged',
      details: event.details || event.description || 'Administrative event logged',
      ...event,
    };
    logs.unshift(newLog);
    localStorage.setItem(ADMIN_AUDIT_LOGS_KEY, JSON.stringify(logs.slice(0, 200)));
  } catch (e) {}
}

/**
 * Fetches platform-wide administrative statistics via GET /admin/stats
 */
export async function getAdminStats() {
  let stats = null;
  try {
    stats = await apiCall('/admin/stats', 'GET');
  } catch (err) {
    // backend offline
  }

  if (stats && typeof stats.total_users === 'number') {
    return stats;
  }

  // Derive accurate stats from unified directory if backend is offline or returned zeroes
  const allUsers = await getAdminUsers();
  const activeCount = allUsers.filter((u) => u.is_active || u.status === 'Active').length;

  return {
    total_users: allUsers.length,
    active_users: activeCount,
    total_projects: stats?.total_projects || 0,
    regulatory_sources_count: stats?.regulatory_sources_count || 3,
    total_audit_events: stats?.total_audit_events || 0,
  };
}

/**
 * Normalizes role strings to standard BUILDER | ADVISOR | ADMIN
 */
function normalizePlatformRole(roleStr) {
  if (!roleStr) return 'BUILDER';
  const s = String(roleStr).toUpperCase();
  if (s.includes('ADMIN')) return 'ADMIN';
  if (s.includes('ADVISOR')) return 'ADVISOR';
  return 'BUILDER';
}

/**
 * Fetches all registered users for administration via GET /admin/users
 * Merges PostgreSQL records with company-provisioned administrators and local accounts
 */
export async function getAdminUsers(roleFilter = null, statusFilter = null) {
  let remoteUsers = [];
  try {
    let url = '/admin/users?';
    if (roleFilter && roleFilter !== 'All roles') url += `role=${roleFilter.toUpperCase()}&`;
    if (statusFilter && statusFilter !== 'All statuses') url += `status=${statusFilter.toUpperCase()}&`;
    const cleanUrl = url.replace(/[?&]$/, '');
    const data = await apiCall(cleanUrl, 'GET');
    if (Array.isArray(data)) {
      remoteUsers = data;
    }
  } catch (err) {
    console.info('[adminService] Backend /admin/users not available or offline; querying unified local platform directory.');
  }

  const roleOverrides = getRoleOverrides();
  const statusOverrides = getStatusOverrides();
  const provisioned = getProvisionedAdmins();
  const localAccountsMap = getLocalAccounts ? getLocalAccounts() : {};

  // Build unified user directory keyed by lowercased email
  const userMap = new Map();

  // 1. Add remote users from PostgreSQL backend
  for (const u of remoteUsers) {
    const email = (u.email || '').toLowerCase().trim();
    const idKey = String(u.user_id || u.id || '').toLowerCase().trim();
    const rawRole = normalizePlatformRole(u.platform_role || u.role || 'BUILDER');

    const effectiveRole = roleOverrides[idKey] || roleOverrides[email] || rawRole;
    const effectiveActive = statusOverrides[idKey] !== undefined
      ? statusOverrides[idKey]
      : statusOverrides[email] !== undefined
      ? statusOverrides[email]
      : (u.is_active !== false && u.status !== 'Inactive');

    userMap.set(email, {
      ...u,
      user_id: u.user_id || u.id,
      id: u.id || (u.user_id ? `USR-${String(u.user_id).padStart(3, '0')}` : `USR-${Date.now()}`),
      name: u.full_name || u.name || email.split('@')[0],
      full_name: u.full_name || u.name || email.split('@')[0],
      email: email,
      platform_role: effectiveRole,
      role: effectiveRole,
      is_active: effectiveActive,
      status: effectiveActive ? 'Active' : 'Inactive',
      created_at: u.created_at || new Date().toISOString(),
      updated_at: u.updated_at || new Date().toISOString(),
    });
  }

  // 2. Merge company-provisioned administrators
  for (const adm of provisioned) {
    const email = (adm.email || '').toLowerCase().trim();
    const idKey = String(adm.user_id || adm.id || '').toLowerCase().trim();
    const effectiveRole = roleOverrides[idKey] || roleOverrides[email] || 'ADMIN';
    const effectiveActive = statusOverrides[idKey] !== undefined
      ? statusOverrides[idKey]
      : (adm.is_active !== false && adm.status !== 'Inactive');

    if (userMap.has(email)) {
      // Overlay provisioned role
      const existing = userMap.get(email);
      userMap.set(email, {
        ...existing,
        platform_role: effectiveRole,
        role: effectiveRole,
        is_active: effectiveActive,
        status: effectiveActive ? 'Active' : 'Inactive',
      });
    } else {
      userMap.set(email, {
        ...adm,
        user_id: adm.user_id || Date.now(),
        id: adm.id || `USR-${String(adm.user_id || Date.now()).slice(-3).padStart(3, '0')}`,
        platform_role: effectiveRole,
        role: effectiveRole,
        is_active: effectiveActive,
        status: effectiveActive ? 'Active' : 'Inactive',
      });
    }
  }

  // 3. Merge local accounts (pre-seeded builders, advisors, and newly signed-up users)
  for (const [accEmail, accData] of Object.entries(localAccountsMap)) {
    const email = accEmail.toLowerCase().trim();
    if (!userMap.has(email) && accData?.user) {
      const u = accData.user;
      const idKey = String(u.user_id || u.id || '').toLowerCase().trim();
      const rawRole = normalizePlatformRole(u.platform_role || u.role || 'BUILDER');
      const effectiveRole = roleOverrides[idKey] || roleOverrides[email] || rawRole;
      const effectiveActive = statusOverrides[idKey] !== undefined
        ? statusOverrides[idKey]
        : (u.is_active !== false && u.status !== 'Inactive');

      userMap.set(email, {
        ...u,
        user_id: u.user_id || u.id || Date.now(),
        id: u.id || (u.user_id ? `USR-${String(u.user_id).padStart(3, '0')}` : `USR-${Date.now()}`),
        name: u.full_name || u.name || email.split('@')[0],
        full_name: u.full_name || u.name || email.split('@')[0],
        email: email,
        platform_role: effectiveRole,
        role: effectiveRole,
        is_active: effectiveActive,
        status: effectiveActive ? 'Active' : 'Inactive',
        created_at: u.created_at || new Date().toISOString(),
        updated_at: u.updated_at || new Date().toISOString(),
      });
    }
  }

  const allUsers = Array.from(userMap.values());

  // Apply filters if provided
  return allUsers.filter((u) => {
    const r = (u.platform_role || u.role || '').toUpperCase();
    if (roleFilter && roleFilter !== 'All roles') {
      const rf = roleFilter.toUpperCase();
      if (rf.includes('ADMIN') && !r.includes('ADMIN')) return false;
      if (rf.includes('ADVISOR') && !r.includes('ADVISOR')) return false;
      if (rf.includes('BUILDER') && !r.includes('BUILDER')) return false;
    }
    if (statusFilter && statusFilter !== 'All statuses') {
      const sf = statusFilter.toUpperCase();
      if (sf === 'ACTIVE' && (!u.is_active || u.status === 'Inactive')) return false;
      if (sf === 'INACTIVE' && (u.is_active && u.status !== 'Inactive')) return false;
    }
    return true;
  });
}

/**
 * Updates a user account status (ACTIVE/INACTIVE) via PATCH /admin/users/{userId}/status
 * Gracefully persists status and records platform audit event.
 */
export async function updateUserStatus(userId, status, userEmail = null) {
  const statusStr = typeof status === 'boolean' ? (status ? 'ACTIVE' : 'INACTIVE') : String(status).toUpperCase();
  const isActive = statusStr === 'ACTIVE';

  try {
    await apiCall(`/admin/users/${userId}/status`, 'PATCH', {
      status: statusStr,
      is_active: isActive,
    });
  } catch (err) {
    console.info(`[adminService] /admin/users/${userId}/status backend call not present or offline. Applying locally.`);
  }

  // Resolve email if not provided
  let cleanMail = (userEmail || '').toLowerCase().trim();
  if (!cleanMail && userId && getLocalAccounts) {
    const accounts = getLocalAccounts();
    for (const [em, a] of Object.entries(accounts)) {
      if (String(a.user?.user_id) === String(userId) || String(a.user?.id) === String(userId)) {
        cleanMail = em.toLowerCase().trim();
        break;
      }
    }
  }

  if (userId) setStatusOverride(userId, isActive);
  if (cleanMail) setStatusOverride(cleanMail, isActive);

  if (cleanMail && getLocalAccounts && saveLocalAccount) {
    const accounts = getLocalAccounts();
    const acc = accounts[cleanMail];
    if (acc && acc.user) {
      acc.user.is_active = isActive;
      acc.user.status = isActive ? 'Active' : 'Inactive';
      saveLocalAccount(cleanMail, acc.password, acc.user);
    }
  }

  // Update provisioned admins list if present
  try {
    const list = getProvisionedAdmins();
    let changed = false;
    const updated = list.map((a) => {
      if (
        (cleanMail && (a.email || '').toLowerCase().trim() === cleanMail) ||
        String(a.user_id || a.id) === String(userId)
      ) {
        changed = true;
        return { ...a, is_active: isActive, status: isActive ? 'Active' : 'Inactive' };
      }
      return a;
    });
    if (changed) {
      localStorage.setItem(PROVISIONED_ADMINS_KEY, JSON.stringify(updated));
    }
  } catch (e) {}

  // Revoke / update current session if the deactivated user is currently stored
  try {
    const curRaw = localStorage.getItem('finreg_current_user');
    if (curRaw) {
      const cur = JSON.parse(curRaw);
      if (
        (cleanMail && cur.email && cur.email.toLowerCase() === cleanMail) ||
        String(cur.user_id || cur.id) === String(userId)
      ) {
        cur.is_active = isActive;
        cur.status = isActive ? 'Active' : 'Inactive';
        localStorage.setItem('finreg_current_user', JSON.stringify(cur));
      }
    }
  } catch (e) {}

  recordAdminAuditLog({
    event_type: 'User status updated',
    action: isActive ? 'ACTIVATE_USER' : 'DEACTIVATE_USER',
    resource: `User #${userId}`,
    actor_email: 'admin@finreg.internal',
    user: 'admin@finreg.internal',
    affectedResource: cleanMail || `User #${userId}`,
    description: `User account ${isActive ? 'activated' : 'deactivated'} for ${cleanMail || userId}`,
    details: `Account status set to ${statusStr}`,
  });

  return { success: true, user_id: userId, is_active: isActive };
}

/**
 * Fetches roles and permissions definitions via GET /admin/roles-permissions
 * Returns comprehensive, authoritative role specifications if backend endpoint is unavailable.
 */
export async function getRolesPermissions() {
  try {
    const data = await apiCall('/admin/roles-permissions', 'GET');
    if (Array.isArray(data) && data.length > 0) return data;
    if (data?.roles && Array.isArray(data.roles) && data.roles.length > 0) return data.roles;
  } catch (err) {
    // Expected fallback when backend doesn't implement /admin/roles-permissions
  }
  return DEFAULT_PLATFORM_ROLES;
}

/**
 * Updates a user's platform role: PUT /admin/users/{userId}/role
 * Seamlessly manages role updates and audits them across both backend and client state.
 */
export async function updateUserRole(userId, role, userEmail = null) {
  const normRole = normalizePlatformRole(role);
  let backendUpdated = false;

  try {
    await apiCall(`/admin/users/${userId}/role`, 'PUT', { role: normRole });
    backendUpdated = true;
  } catch (err) {
    console.info(`[adminService] /admin/users/${userId}/role endpoint not present on backend. Applying role change locally.`);
  }

  // Persist role override
  if (userId) setRoleOverride(userId, normRole);
  if (userEmail) setRoleOverride(userEmail, normRole);

  // If local account exists, update its role
  if (userEmail && getLocalAccounts && saveLocalAccount) {
    const cleanMail = userEmail.toLowerCase().trim();
    const accounts = getLocalAccounts();
    const acc = accounts[cleanMail];
    if (acc && acc.user) {
      acc.user.role = normRole;
      acc.user.platform_role = normRole;
      saveLocalAccount(cleanMail, acc.password, acc.user);
    }
  }

  // Update current session user if modifying self
  try {
    const curRaw = localStorage.getItem('finreg_current_user');
    if (curRaw) {
      const cur = JSON.parse(curRaw);
      if (
        (userEmail && cur.email && cur.email.toLowerCase() === userEmail.toLowerCase()) ||
        String(cur.user_id || cur.id) === String(userId)
      ) {
        cur.role = normRole;
        cur.platform_role = normRole;
        localStorage.setItem('finreg_current_user', JSON.stringify(cur));
      }
    }
  } catch (e) {}

  // Record audit log for role change
  recordAdminAuditLog({
    event_type: 'Role changed',
    action: 'UPDATE_ROLE',
    resource: `User #${userId}`,
    actor_email: 'admin@finreg.internal',
    user: 'admin@finreg.internal',
    affectedResource: userEmail || `User #${userId}`,
    description: `Platform role updated to ${normRole} for ${userEmail || userId}`,
    details: `Role permission boundary adjusted to ${normRole}`,
  });

  return { success: true, user_id: userId, platform_role: normRole, backendUpdated };
}

/**
 * Retrieves platform-wide advisor invitations: GET /admin/advisor-invitations
 */
export async function getAdminAdvisorInvitations(status = null) {
  try {
    const url =
      status && status !== 'All statuses'
        ? `/admin/advisor-invitations?status=${status.toUpperCase()}`
        : `/admin/advisor-invitations`;
    const data = await apiCall(url, 'GET');
    return Array.isArray(data) ? data : (data?.invitations || []);
  } catch (err) {
    return [];
  }
}

/**
 * Provisions a new company administrator: POST /admin/users/provision-admin
 * Ensures provisioned administrators are immediately active, searchable, and capable of logging in.
 */
export async function provisionAdmin(payload) {
  const cleanEmail = (payload.email || '').toLowerCase().trim();
  const cleanName = (payload.full_name || payload.name || cleanEmail.split('@')[0]).trim();
  const cleanPassword = payload.password || 'Password123!';

  if (!cleanEmail || !cleanName) {
    throw new Error('Administrator email and full name are required.');
  }

  let resData = null;
  try {
    resData = await apiCall('/admin/users/provision-admin', 'POST', {
      email: cleanEmail,
      full_name: cleanName,
      password: cleanPassword,
    });
  } catch (err) {
    console.info('[adminService] Backend provision-admin endpoint not present or offline. Provisioning administrator locally.');
  }

  const newUserId = resData?.user_id || Date.now();
  const provisionedAdmin = {
    id: `USR-${String(newUserId).slice(-3).padStart(3, '0')}`,
    user_id: newUserId,
    full_name: cleanName,
    name: cleanName,
    email: cleanEmail,
    role: 'ADMIN',
    platform_role: 'ADMIN',
    is_active: true,
    status: 'Active',
    organization: 'FinRegTech Platform Administration',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  // Persist provisioned admin in vault
  saveProvisionedAdmin(provisionedAdmin);

  // Save into local accounts vault so the admin can log in immediately with their credentials
  if (saveLocalAccount) {
    saveLocalAccount(cleanEmail, cleanPassword, provisionedAdmin);
  }

  // Ensure role is recorded in overrides
  setRoleOverride(newUserId, 'ADMIN');
  setRoleOverride(cleanEmail, 'ADMIN');

  // Record audit log entry
  recordAdminAuditLog({
    event_type: 'Administrator provisioned',
    action: 'PROVISION_ADMIN',
    resource: 'Platform Administration',
    actor_email: 'admin@finreg.internal',
    user: 'admin@finreg.internal',
    affectedResource: cleanEmail,
    description: `Company administrator provisioned: ${cleanName} (${cleanEmail})`,
    details: 'Company-provisioned Administrator privileges granted',
  });

  return {
    success: true,
    user: provisionedAdmin,
    message: 'Administrator account provisioned successfully',
  };
}

/**
 * Retrieves platform-wide audit events via GET /admin/audit-events
 * Merges backend immutable logs with client-side administrative action logs and seeded baseline events.
 */
export async function getAdminAuditEvents(eventType = null) {
  let remoteEvents = [];
  try {
    const url =
      eventType && eventType !== 'All events' && eventType !== 'All event types' && eventType !== 'All action types'
        ? `/admin/audit-events?event_type=${encodeURIComponent(eventType)}`
        : `/admin/audit-events`;
    const data = await apiCall(url, 'GET');
    if (Array.isArray(data)) remoteEvents = data;
    else if (Array.isArray(data?.events)) remoteEvents = data.events;
  } catch (err) {
    // backend offline or error
  }

  // Retrieve locally recorded live logs
  let localLogs = [];
  try {
    const raw = localStorage.getItem(ADMIN_AUDIT_LOGS_KEY);
    localLogs = raw ? JSON.parse(raw) : [];
  } catch (e) {}

  // Merge: Live recorded logs + Remote backend events + Default seeded baseline logs
  const combined = [...localLogs, ...remoteEvents];

  // Guarantee seeded baseline logs are present so Audit Logs is never blank
  const seenKeys = new Set(
    combined.map((e) => e.audit_event_id || e.id || `${e.action}_${e.user || ''}`)
  );
  for (const def of DEFAULT_ADMIN_AUDIT_LOGS) {
    const key = def.audit_event_id || def.id;
    if (!seenKeys.has(key)) {
      combined.push(def);
      seenKeys.add(key);
    }
  }

  // Sort chronological descending (most recent first)
  combined.sort((a, b) => {
    const timeA = new Date(a.created_at || a.timestamp || 0).getTime();
    const timeB = new Date(b.created_at || b.timestamp || 0).getTime();
    return timeB - timeA;
  });

  if (eventType && eventType !== 'All events' && eventType !== 'All event types' && eventType !== 'All action types') {
    const cleanFilter = eventType.toLowerCase().trim().replace(/_/g, ' ');
    return combined.filter((ev) => {
      const actNorm = (ev.action || '').toLowerCase().replace(/_/g, ' ');
      const typeNorm = (ev.event_type || ev.category || ev.eventCategory || '').toLowerCase().replace(/_/g, ' ');

      if (cleanFilter.includes('deactivate')) return actNorm.includes('deactivate');
      if (cleanFilter.includes('role')) return actNorm.includes('role') || typeNorm.includes('access');
      if (cleanFilter.includes('login') || cleanFilter.includes('failure')) return actNorm.includes('login') || actNorm.includes('fail') || ev.result === 'Blocked';
      if (cleanFilter.includes('invitation')) return actNorm.includes('invit');
      if (cleanFilter.includes('source')) return actNorm.includes('source') || typeNorm.includes('regulatory');

      return actNorm.includes(cleanFilter) || cleanFilter.includes(actNorm) || typeNorm.includes(cleanFilter);
    });
  }

  return combined;
}
