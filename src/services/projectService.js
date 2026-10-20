import { apiCall } from './api';

// Projects List initialized to empty array (ready for live backend API data)
const MOCK_PROJECTS = [];

export const PROJECTS_STORAGE_KEY = 'finreg_projects';

/**
 * Retrieves persisted custom projects from local storage
 */
export function getLocalProjects() {
  try {
    const raw = localStorage.getItem(PROJECTS_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    const clean = parsed.filter(
      (p) =>
        p &&
        p.id !== 'PRJ-001' &&
        p.name !== 'ABC Shield' &&
        p.name !== 'KYC Onboarding Controls' &&
        !p.id?.includes('MOCK')
    );
    try {
      localStorage.setItem(PROJECTS_STORAGE_KEY, JSON.stringify(clean));
    } catch (e) {}
    return clean;
  } catch (e) {
    return [];
  }
}

/**
 * Fetches all user projects via GET /projects
 */
export async function getProjects() {
  try {
    const data = await apiCall('/projects', 'GET');
    if (Array.isArray(data) && data.length > 0) return data;
  } catch (err) {
    console.warn('[projectService] GET /projects failed. Reading persisted and fixture projects.');
  }
  const local = getLocalProjects();
  return local.length > 0 ? [...local, ...MOCK_PROJECTS] : MOCK_PROJECTS;
}

/**
 * Fetches summary metrics via GET /projects/summary
 */
export async function getProjectSummary() {
  try {
    return await apiCall('/projects/summary', 'GET');
  } catch (err) {
    console.warn('[projectService] GET /projects/summary failed. Computing fallback summary.');
    const projects = await getProjects();
    return {
      total: projects.length,
      inProgress: projects.filter((p) => p.status === 'In Progress').length,
      underReview: projects.filter((p) => p.status === 'Under Review').length,
      completed: projects.filter((p) => p.status === 'Completed').length,
    };
  }
}

/**
 * Fetches single project details via GET /projects/{projectId}
 */
export async function getProjectDetails(projectId) {
  try {
    const data = await apiCall(`/projects/${projectId}`, 'GET');
    if (data) return data;
  } catch (err) {
    console.warn(`[projectService] GET /projects/${projectId} failed. Checking local projects.`);
  }
  const all = [...getLocalProjects(), ...MOCK_PROJECTS];
  return all.find((p) => p.id === projectId) || all[0];
}

/**
 * Creates a new project via POST /projects
 * DEF-08: Explicitly derive owner identity from payload / authenticated principal rather than defaulting to fixture names
 */
export async function createProject(projectPayload) {
  const newProjectObj = {
    id: `PRJ-00${Math.floor(Math.random() * 900) + 100}`,
    name: projectPayload.name,
    type: projectPayload.type || 'AML/CTF',
    status: 'Draft',
    statusColor: 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700',
    dotColor: 'bg-slate-400',
    lastUpdated: 'Just now',
    owner: projectPayload.owner || 'Project Owner',
    ownerEmail: projectPayload.ownerEmail || '',
    progress: 0,
    description: projectPayload.description || 'Newly created regulatory project.',
    created: 'Today',
    jurisdiction: projectPayload.jurisdiction || 'United Kingdom - FCA',
    members: [],
  };

  try {
    const res = await apiCall('/projects', 'POST', projectPayload);
    if (res && res.id) {
      newProjectObj.id = res.id;
      if (res.owner) newProjectObj.owner = res.owner;
    }
  } catch (err) {
    console.warn('[projectService] POST /projects failed. Persisting project to local storage.');
  }

  // Persist locally so new projects survive browser reloads and scoping checks
  try {
    const existing = getLocalProjects();
    existing.unshift(newProjectObj);
    localStorage.setItem(PROJECTS_STORAGE_KEY, JSON.stringify(existing));
  } catch (e) {
    console.error('Failed to persist project locally:', e);
  }

  return newProjectObj;
}

/**
 * Updates an existing project via PATCH /projects/{projectId}
 */
export async function updateProject(projectId, updatePayload) {
  try {
    return await apiCall(`/projects/${projectId}`, 'PATCH', updatePayload);
  } catch (err) {
    console.warn(`[projectService] PATCH /projects/${projectId} failed.`);
    return updatePayload;
  }
}

/**
 * Fetches project requirements via GET /projects/{projectId}/requirements
 */
export async function getProjectRequirements(projectId) {
  try {
    const data = await apiCall(`/projects/${projectId}/requirements`, 'GET');
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.warn(`[projectService] GET /projects/${projectId}/requirements failed.`);
    return [];
  }
}
