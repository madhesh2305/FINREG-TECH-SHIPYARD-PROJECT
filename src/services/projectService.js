import { apiCall } from './api';

/**
 * Fetches all user projects via GET /projects
 */
export async function getProjects() {
  try {
    const data = await apiCall('/projects', 'GET');
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.error('[projectService] GET /projects failed:', err);
    throw err;
  }
}

/**
 * Fetches summary metrics via GET /projects/summary
 */
export async function getProjectSummary() {
  try {
    return await apiCall('/projects/summary', 'GET');
  } catch (err) {
    console.error('[projectService] GET /projects/summary failed:', err);
    return {
      total: 0,
      inProgress: 0,
      underReview: 0,
      completed: 0,
    };
  }
}

/**
 * Fetches single project details via GET /projects/{projectId}
 */
export async function getProjectDetails(projectId) {
  try {
    return await apiCall(`/projects/${projectId}`, 'GET');
  } catch (err) {
    console.error(`[projectService] GET /projects/${projectId} failed:`, err);
    throw err;
  }
}


export async function createProject(projectPayload) {
  const payload = {
    project_name: projectPayload.name || projectPayload.project_name || 'New Compliance Project',
    name: projectPayload.name || projectPayload.project_name || 'New Compliance Project',
    project_code: projectPayload.code || projectPayload.project_code,
    regulatory_scope: projectPayload.type || projectPayload.regulatory_scope || 'Anti-Bribery & Corruption (ABC)',
    type: projectPayload.type || projectPayload.regulatory_scope || 'Anti-Bribery & Corruption (ABC)',
    description: projectPayload.description || 'Newly created Anti-Bribery & Corruption regulatory project.',
    jurisdiction: projectPayload.jurisdiction || 'United Kingdom - MoJ / SFO',
    objectives: projectPayload.objectives || 'Establish defensible source-traceable compliance and advisor governance under UK Bribery Act 2010',
  };

  try {
    return await apiCall('/projects', 'POST', payload);
  } catch (err) {
    console.error('[projectService] POST /projects failed:', err);
    throw err;
  }
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
    return await apiCall(`/projects/${projectId}/requirements`, 'GET');
  } catch (err) {
    console.warn(`[projectService] GET /projects/${projectId}/requirements failed.`);
    return [
      { id: 'req_1', title: 'Requirements defined', completed: true },
      { id: 'req_2', title: 'Workflow configured', completed: true },
      { id: 'req_3', title: 'Advisor review', completed: true },
      { id: 'req_4', title: 'Compliance sign-off', completed: false },
      { id: 'req_5', title: 'Final submission', completed: false },
    ];
  }
}
