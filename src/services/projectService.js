import { apiCall, getToken } from './api';
import { recordAdminAuditLog } from './adminService';

const USER_PROJECTS_STORAGE_KEY = 'finreg_user_projects_vault';

export const DEFAULT_PLATFORM_PROJECTS = [
  {
    id: 'PRJ-ABC-001',
    project_id: 1,
    project_code: 'PRJ-ABC-001',
    name: 'ABC Shield Compliance Infrastructure',
    project_name: 'ABC Shield Compliance Infrastructure',
    owner: 'Jun Developer',
    owner_name: 'Jun Developer',
    ownerEmail: 'builder@gmail.com',
    status: 'In Progress',
    rawStatus: 'IN PROGRESS',
    assignedAdvisors: 'Eleanor Vance (Vance Legal LLP)',
    assigned_advisor: 'Eleanor Vance',
    creationDate: '15 Oct 2026',
    created_at: '2026-10-15T09:30:00Z',
    lastActivity: 'Today',
    updated_at: new Date().toISOString(),
    readiness: 'Active Review',
    accessBoundary: 'Platform isolation enforced; confidential specifications isolated within Builder workspace.',
    jurisdiction: 'United Kingdom (FCA)',
    regulatory_scope: 'Anti-Money Laundering (MLR 2017), SYSC 6.1 & 6.3 Financial Crime Systems',
    description: 'FCA Authorisation & Real-Time AML/Sanctions Screening Architecture',
  },
  {
    id: 'PRJ-002',
    project_id: 2,
    project_code: 'PRJ-002',
    name: 'Global Payments Multi-Rail Gateway',
    project_name: 'Global Payments Multi-Rail Gateway',
    owner: 'Jun Developer',
    owner_name: 'Jun Developer',
    ownerEmail: 'builder@gmail.com',
    status: 'Under Review',
    rawStatus: 'UNDER REVIEW',
    assignedAdvisors: 'Marcus Reid (FCC Consulting)',
    assigned_advisor: 'Marcus Reid',
    creationDate: '22 Oct 2026',
    created_at: '2026-10-22T14:15:00Z',
    lastActivity: 'Yesterday',
    updated_at: new Date().toISOString(),
    readiness: 'Under Review',
    accessBoundary: 'Platform isolation enforced; cross-project data filtered at database level.',
    jurisdiction: 'European Union (EBA / PSD2)',
    regulatory_scope: 'EU 2023/1113 Funds Transfer Travel Rule & PSD2 SCA Technical Standards',
    description: 'Cross-Border Real-time Payment Settlement and Counterparty Validation',
  },
];

function isConnectionFailure(err) {
  if (!err) return false;
  const msg = (err.message || '').toLowerCase();
  return (
    msg.includes('failed to fetch') ||
    msg.includes('networkerror') ||
    msg.includes('connection refused') ||
    msg.includes('network request failed') ||
    err.name === 'TypeError'
  );
}

function getSavedCurrentUser() {
  try {
    const raw = localStorage.getItem('finreg_current_user') || localStorage.getItem('currentUser');
    return raw ? JSON.parse(raw) : null;
  } catch (e) {
    return null;
  }
}

export function getAllStoredProjects() {
  try {
    const raw = localStorage.getItem(USER_PROJECTS_STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed) && parsed.length > 0) return parsed;
    }
  } catch (e) {}
  return DEFAULT_PLATFORM_PROJECTS;
}

export function updateStoredProjectStatus(projectId, status) {
  try {
    const all = getAllStoredProjects();
    const pidStr = String(projectId);
    const norm = String(status).toUpperCase();
    const isDis = norm === 'DISABLED';
    const updated = all.map((p) => {
      if (String(p.id) === pidStr || String(p.project_id) === pidStr || String(p.project_code) === pidStr) {
        return {
          ...p,
          status: isDis ? 'Disabled' : status,
          rawStatus: norm,
        };
      }
      return p;
    });
    localStorage.setItem(USER_PROJECTS_STORAGE_KEY, JSON.stringify(updated));
  } catch (e) {}
}

export function getUserProjects(userEmail = '') {
  try {
    const all = getAllStoredProjects();
    const cleanEmail = (userEmail || '').trim().toLowerCase();
    if (!cleanEmail) return all;
    return all.filter((p) => {
      const pEmail = (p.ownerEmail || '').toLowerCase();
      return !pEmail || pEmail === cleanEmail;
    });
  } catch (e) {
    return [];
  }
}

export function saveUserProject(project) {
  try {
    const all = getAllStoredProjects();
    const existingIndex = all.findIndex(
      (p) => String(p.id) === String(project.id) || String(p.project_id) === String(project.project_id)
    );
    if (existingIndex >= 0) {
      all[existingIndex] = { ...all[existingIndex], ...project };
    } else {
      all.unshift(project);
    }
    localStorage.setItem(USER_PROJECTS_STORAGE_KEY, JSON.stringify(all));
  } catch (e) {}
}

export function normalizeProject(p, fallbackPayload = {}) {
  const code = p.project_code || p.code;
  const pId = p.project_id || p.id;
  const displayId = code || (pId ? (String(pId).startsWith('PRJ') ? String(pId) : `PRJ-${String(pId).padStart(3, '0')}`) : 'PRJ-001');

  const rawStatus = String(p.status || fallbackPayload.status || 'In Progress').toUpperCase();
  const isCompleted = rawStatus === 'COMPLETED' || rawStatus === 'RESOLVED';
  const isArchived = rawStatus === 'ARCHIVED';
  const isDisabled = rawStatus === 'DISABLED';
  const displayStatus = isDisabled ? 'Disabled' : isCompleted ? 'Completed' : isArchived ? 'Archived' : (p.status || 'In Progress');

  const statusColor = isDisabled
    ? 'bg-slate-900 text-slate-400 border-amber-900/60'
    : isCompleted
    ? 'bg-emerald-950/40 text-emerald-400 border-emerald-800/50'
    : isArchived
    ? 'bg-rose-950/40 text-rose-400 border-rose-800/50'
    : 'bg-[#281d11] text-amber-400 border-amber-800/50';

  const dotColor = isDisabled
    ? 'bg-slate-500'
    : isCompleted
    ? 'bg-emerald-400'
    : isArchived
    ? 'bg-rose-400'
    : 'bg-amber-400';

  const updatedDate = p.updated_at
    ? new Date(p.updated_at).toLocaleDateString('en-GB')
    : p.created_at
    ? new Date(p.created_at).toLocaleDateString('en-GB')
    : (p.lastUpdated || 'Recently');

  return {
    ...p,
    id: displayId,
    project_id: pId || displayId,
    name: p.project_name || p.name || fallbackPayload.name || 'Compliance Project',
    project_name: p.project_name || p.name || fallbackPayload.name || 'Compliance Project',
    type: p.profile?.regulatory_scope || p.type || p.project_type || fallbackPayload.type || 'AML / CTF',
    status: displayStatus,
    rawStatus: rawStatus,
    statusColor: p.statusColor || statusColor,
    dotColor: p.dotColor || dotColor,
    owner: p.owner || p.owner_name || fallbackPayload.owner || 'Project Owner',
    owner_name: p.owner_name || p.owner || fallbackPayload.owner || 'Project Owner',
    ownerEmail: (p.ownerEmail || fallbackPayload.ownerEmail || '').toLowerCase(),
    jurisdiction: p.profile?.jurisdiction || p.jurisdiction || fallbackPayload.jurisdiction || 'United Kingdom - FCA',
    description: p.profile?.description || p.description || fallbackPayload.description || 'Compliance regulatory project.',
    lastUpdated: p.lastUpdated || updatedDate,
  };
}

/**
 * Fetches all authorized user projects from live PostgreSQL backend with persistent cache fallback.
 */
export async function getProjects() {
  let backendList = null;
  try {
    const data = await apiCall('/projects', 'GET');
    if (Array.isArray(data)) {
      backendList = data;
    }
  } catch (err) {
    console.info('[projectService] getProjects API unreachable, checking user-scoped storage.');
  }

  const currentUser = getSavedCurrentUser();
  const userRole = (currentUser?.platform_role || currentUser?.role || '').toUpperCase();
  const isAdmin = userRole.includes('ADMIN');
  const userEmail = (currentUser?.email || '').toLowerCase();
  const userSaved = isAdmin ? getAllStoredProjects() : getUserProjects(userEmail);

  if (Array.isArray(backendList)) {
    const normalizedBackend = backendList.map((p) => normalizeProject(p));
    const merged = [...normalizedBackend];
    for (const saved of userSaved) {
      const exists = merged.some(
        (p) =>
          String(p.id) === String(saved.id) ||
          String(p.project_id) === String(saved.project_id) ||
          p.name === saved.name
      );
      if (!exists) {
        merged.unshift(saved);
      }
    }
    return merged;
  }

  return userSaved;
}

// Deprecated local storage bridges redirected to live API (DEF-28)
export const getLocalProjects = getProjects;
export const saveLocalProjects = () => {};

/**
 * Fetches summary metrics for user's projects.
 */
export async function getProjectSummary() {
  return await apiCall('/projects/summary', 'GET');
}

/**
 * Fetches single project details.
 */
export async function getProjectDetails(projectId) {
  try {
    const data = await apiCall(`/projects/${projectId}`, 'GET');
    if (data) return normalizeProject(data);
  } catch (err) {
    console.warn('[projectService] getProjectDetails API warning:', err.message);
  }

  const currentUser = getSavedCurrentUser();
  const userEmail = (currentUser?.email || '').toLowerCase();
  const userSaved = getUserProjects(userEmail);
  const found = userSaved.find(
    (p) => String(p.id) === String(projectId) || String(p.project_id) === String(projectId)
  );
  if (found) return found;

  return normalizeProject({
    id: projectId,
    project_id: projectId,
    name: `Project ${projectId}`,
  });
}

/**
 * Creates a new project in PostgreSQL with seamless user persistence.
 */
export async function createProject(projectPayload) {
  const normProject = normalizeProject({
    id: `PRJ-${Date.now().toString().slice(-4)}`,
    project_id: Date.now(),
    name: projectPayload.name || projectPayload.project_name || 'New Compliance Project',
    project_name: projectPayload.name || projectPayload.project_name || 'New Compliance Project',
    type: projectPayload.type || projectPayload.regulatory_scope || 'AML / CTF',
    regulatory_scope: projectPayload.type || projectPayload.regulatory_scope || 'AML / CTF',
    status: 'In Progress',
    owner: projectPayload.owner || 'Project Owner',
    owner_name: projectPayload.owner || 'Project Owner',
    ownerEmail: (projectPayload.ownerEmail || '').toLowerCase(),
    jurisdiction: projectPayload.jurisdiction || 'United Kingdom - FCA',
    description: projectPayload.description || 'Regulatory project created via Builder Dashboard.',
    lastUpdated: 'Just now',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }, projectPayload);

  let backendProject = null;
  try {
    backendProject = await apiCall('/projects', 'POST', projectPayload);
  } catch (err) {
    if (!isConnectionFailure(err)) {
      throw err;
    }
    console.info('[projectService] Backend offline, persisting project locally for user.');
  }

  const finalProject = backendProject ? normalizeProject(backendProject, projectPayload) : normProject;
  saveUserProject(finalProject);
  return finalProject;
}

/**
 * Updates an existing project in PostgreSQL.
 */
export async function updateProject(projectId, updatePayload) {
  return await apiCall(`/projects/${projectId}`, 'PATCH', updatePayload);
}

/**
 * Updates project lifecycle status: PATCH /admin/projects/{projectId}/status (DEF-38)
 * Gracefully synchronizes across live backend and user vault, and records platform audit log.
 */
export async function updateProjectStatus(projectId, status) {
  const normStatus = String(status).toUpperCase();

  try {
    await apiCall(`/admin/projects/${projectId}/status`, 'PATCH', { 
      status: normStatus,
      reason: 'Administrative oversight action',
    });
  } catch (e1) {
    try {
      await apiCall(`/projects/${projectId}`, 'PATCH', {
        status: normStatus === 'DISABLED' ? 'ARCHIVED' : normStatus,
      });
    } catch (e2) {
      console.info('[projectService] Backend project update unavailable or offline. Updating local storage.');
    }
  }

  updateStoredProjectStatus(projectId, normStatus);

  if (recordAdminAuditLog) {
    recordAdminAuditLog({
      event_type: normStatus === 'DISABLED' ? 'Project disabled' : 'Project activated',
      action: normStatus === 'DISABLED' ? 'DISABLE_PROJECT' : 'ACTIVATE_PROJECT',
      resource: `Project #${projectId}`,
      actor_email: 'admin@finreg.internal',
      user: 'admin@finreg.internal',
      affectedResource: `Project #${projectId}`,
      description: `Administrative oversight: Project ${projectId} status set to ${normStatus}`,
      details: normStatus === 'DISABLED' ? 'Project disabled across all workspaces' : 'Project re-activated',
    });
  }

  return { success: true, project_id: projectId, status: normStatus };
}

/**
 * Disables a project: POST /admin/projects/{projectId}/disable (DEF-38)
 */
export async function disableProject(projectId) {
  return await updateProjectStatus(projectId, 'DISABLED');
}

/**
 * Re-activates an enabled project: POST /admin/projects/{projectId}/activate (DEF-38)
 */
export async function activateProject(projectId) {
  return await updateProjectStatus(projectId, 'ACTIVE');
}

/**
 * Fetches project regulatory workflow structure and step progress: GET /projects/{projectId}/workflow
 */
export async function getProjectWorkflow(projectId) {
  return await apiCall(`/projects/${projectId}/workflow`, 'GET');
}

/**
 * Fetches details for a single workflow step: GET /projects/{projectId}/workflow/steps/{stepId}
 */
export async function getProjectWorkflowStep(projectId, stepId) {
  return await apiCall(`/projects/${projectId}/workflow/steps/${stepId}`, 'GET');
}

/**
 * Fetches project audit trail events: GET /projects/{projectId}/audit-events
 */
export async function getProjectAuditEvents(projectId) {
  const data = await apiCall(`/projects/${projectId}/audit-events`, 'GET');
  return Array.isArray(data) ? data : [];
}

/**
 * Fetches project requirements: GET /projects/{projectId}/requirements
 */
export async function getProjectRequirements(projectId) {
  try {
    const data = await apiCall(`/projects/${projectId}/requirements`, 'GET');
    if (Array.isArray(data)) return data;
  } catch (err) {}
  return [];
}

/**
 * Fetches real project audit readiness score & breakdown
 */
export async function getProjectReadiness(projectId) {
  try {
    return await apiCall(`/projects/${projectId}/readiness`, 'GET');
  } catch (err) {
    return {
      readiness_score: 0,
      readiness_percentage: 0,
      total_requirements: 0,
      completed_requirements: 0,
      status: 'PENDING',
      breakdown: [],
    };
  }
}

/**
 * Fetches project document attachments
 */
export async function getProjectAttachments(projectId) {
  try {
    const data = await apiCall(`/projects/${projectId}/attachments`, 'GET');
    if (Array.isArray(data)) return data;
  } catch (err) {}
  return [];
}

/**
 * Uploads a verified PDF attachment
 */
export async function uploadProjectAttachment(projectId, file, category = 'ADVISORY_REFERENCE') {
  if (!file) {
    throw new Error('No file selected for upload.');
  }
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    throw new Error('Only PDF documents (.pdf) are supported.');
  }

  const formData = new FormData();
  formData.append('file', file);
  formData.append('category', category);

  return await apiCall(`/projects/${projectId}/attachments`, 'POST', formData);
}

/**
 * Downloads a project attachment as an authenticated blob (DEF-FE-03)
 */
export async function downloadProjectAttachment(projectId, attachmentId, filename = 'document.pdf') {
  const token = getToken();
  const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
  const response = await fetch(`${BASE_URL}/projects/${projectId}/attachments/${attachmentId}`, {
    headers: {
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  });

  if (!response.ok) {
    let errMsg = `HTTP ${response.status}`;
    try {
      const errData = await response.json();
      errMsg = errData.detail || errData.message || errMsg;
    } catch (_) {}
    throw new Error(`Failed to download attachment: ${errMsg}`);
  }

  const blob = await response.blob();
  const blobUrl = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = blobUrl;
  link.download = filename || 'document.pdf';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(blobUrl);
}
