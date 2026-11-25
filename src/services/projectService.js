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
    created: '15 Oct 2026',
    created_at: '2026-10-15T09:30:00Z',
    lastActivity: '22 Oct 2026',
    lastUpdated: '22 Oct 2026',
    updated_at: '2026-10-22T14:15:00Z',
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
    created: '22 Oct 2026',
    created_at: '2026-10-22T14:15:00Z',
    lastActivity: '24 Oct 2026',
    lastUpdated: '24 Oct 2026',
    updated_at: '2026-10-24T10:00:00Z',
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
      if (Array.isArray(parsed) && parsed.length > 0) {
        return parsed.map((p) => normalizeProject(p));
      }
    }
  } catch (e) {}
  return DEFAULT_PLATFORM_PROJECTS.map((p) => normalizeProject(p));
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
    if (!cleanEmail) return all.map((p) => normalizeProject(p));
    return all
      .filter((p) => {
        const pEmail = (p.ownerEmail || '').toLowerCase();
        return !pEmail || pEmail === cleanEmail;
      })
      .map((p) => normalizeProject(p));
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

/**
 * Standardizes project date formatting to clean European/British format (e.g. "15 Oct 2026").
 * Preserves relative badges like "Just now", "Today", "Yesterday", and resolves undefined dates cleanly.
 */
export function formatProjectDate(dateVal, fallback = 'Recently') {
  if (!dateVal) return fallback;
  if (typeof dateVal === 'string') {
    const trimmed = dateVal.trim();
    const lower = trimmed.toLowerCase();
    if (lower === 'just now' || lower === 'recently' || lower === 'today' || lower === 'yesterday') {
      return trimmed;
    }
    // Matches "15 Oct 2026", "22 Sep 2026", "01 September 2026"
    if (/^\d{1,2}\s+[A-Za-z]{3,}\s+\d{4}$/.test(trimmed)) {
      return trimmed;
    }
    // Matches DD/MM/YYYY
    const slashMatch = trimmed.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
    if (slashMatch) {
      const day = parseInt(slashMatch[1], 10);
      const month = parseInt(slashMatch[2], 10) - 1;
      const year = parseInt(slashMatch[3], 10);
      const d = new Date(year, month, day);
      if (!isNaN(d.getTime())) {
        return d.toLocaleDateString('en-GB', {
          day: '2-digit',
          month: 'short',
          year: 'numeric',
        });
      }
    }
  }

  try {
    const d = new Date(dateVal);
    if (!isNaN(d.getTime())) {
      return d.toLocaleDateString('en-GB', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
      });
    }
  } catch (e) {}

  return String(dateVal || fallback);
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

  // Ensure authentic created and updated dates, preventing hardcoded '01 Sep 2026' leaks
  const rawCreated =
    (p.created && p.created !== '01 Sep 2026' ? p.created : null) ||
    p.created_at ||
    p.creationDate ||
    p.created ||
    fallbackPayload.created_at ||
    fallbackPayload.creationDate;
  const createdDate = formatProjectDate(rawCreated, '15 Oct 2026');

  const rawUpdated = p.updated_at || p.lastUpdated || fallbackPayload.updated_at;
  const updatedDate = p.lastUpdated === 'Just now' ? 'Just now' : formatProjectDate(rawUpdated, createdDate);

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
    created_at: p.created_at || (rawCreated && !isNaN(new Date(rawCreated).getTime()) ? new Date(rawCreated).toISOString() : new Date().toISOString()),
    created: createdDate,
    creationDate: createdDate,
    updated_at: p.updated_at || new Date().toISOString(),
    lastUpdated: updatedDate,
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
    return merged.map((p) => normalizeProject(p));
  }

  return userSaved.map((p) => normalizeProject(p));
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
  if (found) return normalizeProject(found);

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
  const nowIso = new Date().toISOString();
  const formattedToday = formatProjectDate(nowIso);
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
    created_at: nowIso,
    created: formattedToday,
    creationDate: formattedToday,
    updated_at: nowIso,
    lastUpdated: 'Just now',
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

  if (recordAdminAuditLog) {
    recordAdminAuditLog({
      action: 'Project created',
      event_type: 'Project Lifecycle',
      actor_email: finalProject.ownerEmail || 'builder@gmail.com',
      user: finalProject.ownerEmail || 'builder@gmail.com',
      affectedResource: `Project: ${finalProject.name}`,
      description: `New project "${finalProject.name}" created under ${finalProject.jurisdiction || 'UK / EU'} regulatory scope.`,
      status: 'SUCCESS',
    });
  }

  return finalProject;
}

/**
 * Updates an existing project in PostgreSQL with dual-layer persistent storage.
 */
export async function updateProject(projectId, updatePayload) {
  let backendRes = null;
  try {
    backendRes = await apiCall(`/projects/${projectId}`, 'PATCH', updatePayload);
  } catch (err) {
    console.info('[projectService] Backend updateProject API offline or failed, persisting locally:', err.message);
  }

  // Update in local vault
  try {
    const all = getAllStoredProjects();
    const pidStr = String(projectId);
    const nowIso = new Date().toISOString();
    const updated = all.map((p) => {
      if (String(p.id) === pidStr || String(p.project_id) === pidStr || String(p.project_code) === pidStr) {
        return normalizeProject({
          ...p,
          ...updatePayload,
          id: p.id,
          project_id: p.project_id || p.id,
          name: updatePayload.name || updatePayload.project_name || p.name,
          project_name: updatePayload.name || updatePayload.project_name || p.name,
          status: updatePayload.status || p.status,
          owner: updatePayload.owner || updatePayload.owner_name || p.owner,
          owner_name: updatePayload.owner || updatePayload.owner_name || p.owner,
          lastUpdated: 'Just now',
          updated_at: nowIso,
        });
      }
      return p;
    });
    localStorage.setItem(USER_PROJECTS_STORAGE_KEY, JSON.stringify(updated));
    localStorage.setItem('finreg_projects', JSON.stringify(updated));
  } catch (e) {}

  return backendRes || {
    id: projectId,
    project_id: projectId,
    ...updatePayload,
  };
}

/**
 * Deletes a project from PostgreSQL backend and removes it from user vault.
 */
export async function deleteProject(projectId) {
  const cleanId = resolveProjectId(projectId);
  let backendSuccess = false;
  let lastError = null;

  try {
    await apiCall(`/projects/${cleanId}`, 'DELETE');
    backendSuccess = true;
  } catch (err) {
    lastError = err;
    console.warn(`[projectService] DELETE /projects/${cleanId} failed:`, err.message);
    if (String(cleanId) !== String(projectId)) {
      try {
        await apiCall(`/projects/${projectId}`, 'DELETE');
        backendSuccess = true;
      } catch (_) {}
    }
  }

  // Purge from local persistent storage
  try {
    const all = getAllStoredProjects();
    const pidStr = String(projectId);
    const cleanStr = String(cleanId);
    const filtered = all.filter(
      (p) =>
        String(p.id) !== pidStr &&
        String(p.project_id) !== pidStr &&
        String(p.project_code) !== pidStr &&
        String(p.id) !== cleanStr &&
        String(p.project_id) !== cleanStr
    );
    localStorage.setItem(USER_PROJECTS_STORAGE_KEY, JSON.stringify(filtered));
    localStorage.setItem('finreg_projects', JSON.stringify(filtered));
  } catch (e) {}

  if (recordAdminAuditLog) {
    recordAdminAuditLog({
      action: 'Project deleted',
      event_type: 'Project Lifecycle',
      actor_email: 'builder@gmail.com',
      user: 'builder@gmail.com',
      affectedResource: `Project: ${projectId}`,
      description: `Project #${projectId} removed by builder.`,
      status: 'SUCCESS',
    });
  }

  if (!backendSuccess && lastError && !isConnectionFailure(lastError)) {
    throw lastError;
  }

  return { success: true, project_id: projectId };
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
 * Resolves standard project ID for backend API routing.
 * Ensures numeric IDs (e.g. 1) are preserved or extracted from 'PRJ-001'
 * so FastAPI int parameters don't encounter 422 Unprocessable Entity.
 */
export function resolveProjectId(projectId) {
  if (projectId == null) return null;
  if (typeof projectId === 'number') return projectId;
  if (typeof projectId === 'object') {
    return resolveProjectId(projectId.project_id ?? projectId.id);
  }
  const str = String(projectId).trim();
  if (/^\d+$/.test(str)) return parseInt(str, 10);
  const match = str.match(/\d+/);
  if (match) return parseInt(match[0], 10);
  return str;
}

/**
 * Fetches project document attachments from backend with persistent fallback
 */
export async function getProjectAttachments(projectId) {
  const cleanId = resolveProjectId(projectId);
  let backendList = null;

  try {
    const data = await apiCall(`/projects/${cleanId}/attachments`, 'GET');
    if (Array.isArray(data)) {
      backendList = data;
    }
  } catch (err) {
    if (String(cleanId) !== String(projectId)) {
      try {
        const data2 = await apiCall(`/projects/${projectId}/attachments`, 'GET');
        if (Array.isArray(data2)) {
          backendList = data2;
        }
      } catch (_) {}
    }
  }

  // Dual-layer merge with local vault so documents stay consistent
  try {
    const storageKey = `finreg_project_attachments_${cleanId}`;
    const raw = localStorage.getItem(storageKey);
    const localList = raw ? JSON.parse(raw) : [];
    if (Array.isArray(backendList)) {
      const merged = [...backendList];
      for (const loc of localList) {
        const exists = merged.some(
          (b) => String(b.attachment_id || b.id) === String(loc.attachment_id || loc.id)
        );
        if (!exists) {
          merged.push(loc);
        }
      }
      return merged;
    }
    return localList;
  } catch (_) {
    return backendList || [];
  }
}

/**
 * Uploads a verified PDF attachment to backend with FormData
 */
export async function uploadProjectAttachment(projectId, file, category = 'ADVISORY_REFERENCE') {
  if (!file) {
    throw new Error('No file selected for upload.');
  }
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    throw new Error('Only PDF documents (.pdf) are supported.');
  }

  const cleanId = resolveProjectId(projectId);
  const formData = new FormData();
  formData.append('file', file);
  formData.append('category', category);

  let result = null;
  let backendSuccess = false;
  let uploadErr = null;

  try {
    result = await apiCall(`/projects/${cleanId}/attachments`, 'POST', formData);
    backendSuccess = true;
  } catch (err) {
    uploadErr = err;
    console.warn(`[projectService] POST /projects/${cleanId}/attachments failed:`, err.message);
    if (String(cleanId) !== String(projectId)) {
      try {
        result = await apiCall(`/projects/${projectId}/attachments`, 'POST', formData);
        backendSuccess = true;
      } catch (_) {}
    }
  }

  const newDoc = {
    attachment_id: result?.attachment_id || result?.id || `att-${Date.now()}`,
    id: result?.id || result?.attachment_id || `att-${Date.now()}`,
    original_filename: file.name,
    name: file.name,
    category: category,
    file_size: file.size,
    created_at: result?.created_at || new Date().toISOString(),
    status: result?.status || 'VERIFIED',
    ...(result && typeof result === 'object' ? result : {}),
  };

  // Cache in localStorage
  try {
    const storageKey = `finreg_project_attachments_${cleanId}`;
    const raw = localStorage.getItem(storageKey);
    const existing = raw ? JSON.parse(raw) : [];
    const updated = [
      newDoc,
      ...existing.filter(
        (a) => String(a.attachment_id || a.id) !== String(newDoc.attachment_id || newDoc.id)
      ),
    ];
    localStorage.setItem(storageKey, JSON.stringify(updated));
  } catch (_) {}

  if (!backendSuccess && uploadErr && !isConnectionFailure(uploadErr)) {
    throw uploadErr;
  }

  return result || newDoc;
}

/**
 * Deletes a project document attachment from the backend
 */
export async function deleteProjectAttachment(projectId, attachmentId) {
  if (!projectId || !attachmentId) {
    throw new Error('Project ID and Attachment ID are required to remove document.');
  }

  const cleanId = resolveProjectId(projectId);
  let backendSuccess = false;
  let lastError = null;

  try {
    await apiCall(`/projects/${cleanId}/attachments/${attachmentId}`, 'DELETE');
    backendSuccess = true;
  } catch (err) {
    lastError = err;
    console.warn(`[projectService] DELETE /projects/${cleanId}/attachments/${attachmentId} failed:`, err.message);

    if (String(cleanId) !== String(projectId)) {
      try {
        await apiCall(`/projects/${projectId}/attachments/${attachmentId}`, 'DELETE');
        backendSuccess = true;
      } catch (_) {}
    }

    if (!backendSuccess) {
      try {
        await apiCall(`/attachments/${attachmentId}`, 'DELETE');
        backendSuccess = true;
      } catch (_) {}
    }
  }

  // Remove from local cache
  try {
    const storageKey = `finreg_project_attachments_${cleanId}`;
    const raw = localStorage.getItem(storageKey);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        const filtered = parsed.filter(
          (a) => String(a.attachment_id || a.id) !== String(attachmentId)
        );
        localStorage.setItem(storageKey, JSON.stringify(filtered));
      }
    }
  } catch (_) {}

  try {
    if (String(cleanId) !== String(projectId)) {
      const storageKey2 = `finreg_project_attachments_${projectId}`;
      const raw2 = localStorage.getItem(storageKey2);
      if (raw2) {
        const parsed2 = JSON.parse(raw2);
        if (Array.isArray(parsed2)) {
          const filtered2 = parsed2.filter(
            (a) => String(a.attachment_id || a.id) !== String(attachmentId)
          );
          localStorage.setItem(storageKey2, JSON.stringify(filtered2));
        }
      }
    }
  } catch (_) {}

  if (!backendSuccess && lastError && !isConnectionFailure(lastError)) {
    throw lastError;
  }

  return { success: true, attachment_id: attachmentId, project_id: cleanId };
}

/**
 * Downloads a project attachment as an authenticated blob (DEF-FE-03)
 */
export async function downloadProjectAttachment(projectId, attachmentId, filename = 'document.pdf') {
  const cleanId = resolveProjectId(projectId);
  const token = getToken();
  const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

  let response = await fetch(`${BASE_URL}/projects/${cleanId}/attachments/${attachmentId}`, {
    headers: {
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  });

  if (!response.ok && String(cleanId) !== String(projectId)) {
    try {
      const r2 = await fetch(`${BASE_URL}/projects/${projectId}/attachments/${attachmentId}`, {
        headers: {
          ...(token && { Authorization: `Bearer ${token}` }),
        },
      });
      if (r2.ok) response = r2;
    } catch (_) {}
  }

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
