import { apiCall } from './api';

// Fallback Mock Projects List matching user design specifications
const MOCK_PROJECTS = [
  {
    id: 'PRJ-001',
    name: 'AML Compliance Framework',
    type: 'AML/CTF',
    status: 'In Progress',
    statusColor: 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/50 dark:text-blue-400 dark:border-blue-900',
    dotColor: 'bg-blue-600',
    lastUpdated: '22 Sep 2026',
    owner: 'J. Nakamura',
    description: 'End-to-end anti-money laundering workflow for retail banking operations.',
    created: '01 Sep 2026',
    jurisdiction: 'United Kingdom - FCA',
  },
  {
    id: 'PRJ-002',
    name: 'KYC Onboarding Workflow',
    type: 'KYC/CDD',
    status: 'Under Review',
    statusColor: 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/50 dark:text-amber-400 dark:border-amber-900',
    dotColor: 'bg-amber-600',
    lastUpdated: '21 Sep 2026',
    owner: 'S. Okonkwo',
    description: 'Digital identity verification and customer due diligence flow.',
    created: '05 Sep 2026',
    jurisdiction: 'United Kingdom - FCA',
  },
  {
    id: 'PRJ-003',
    name: 'Regulatory Reporting Q3',
    type: 'Regulatory Reporting',
    status: 'Draft',
    statusColor: 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700',
    dotColor: 'bg-slate-400',
    lastUpdated: '19 Sep 2026',
    owner: 'A. Petrov',
    description: 'Quarterly compliance and prudential reporting submission pack.',
    created: '10 Sep 2026',
    jurisdiction: 'European Union - EBA',
  },
  {
    id: 'PRJ-004',
    name: 'GDPR Data Audit Trail',
    type: 'Data Governance',
    status: 'Completed',
    statusColor: 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/50 dark:text-emerald-400 dark:border-emerald-900',
    dotColor: 'bg-emerald-600',
    lastUpdated: '15 Sep 2026',
    owner: 'M. Chen',
    description: 'Data mapping, consent tracking, and regulatory audit log system.',
    created: '12 Sep 2026',
    jurisdiction: 'European Union - GDPR',
  },
  {
    id: 'PRJ-005',
    name: 'Basel III Capital Adequacy',
    type: 'Regulatory Reporting',
    status: 'In Progress',
    statusColor: 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/50 dark:text-blue-400 dark:border-blue-900',
    dotColor: 'bg-blue-600',
    lastUpdated: '10 Sep 2026',
    owner: 'J. Nakamura',
    description: 'Capital requirement calculations and risk-weighted assets framework.',
    created: '14 Sep 2026',
    jurisdiction: 'Global / BIS',
  },
];

/**
 * Fetches all user projects via GET /projects
 */
export async function getProjects() {
  try {
    const data = await apiCall('/projects', 'GET');
    return Array.isArray(data) && data.length > 0 ? data : MOCK_PROJECTS;
  } catch (err) {
    console.warn('[projectService] GET /projects failed. Returning mock projects.');
    return MOCK_PROJECTS;
  }
}

/**
 * Fetches summary metrics via GET /projects/summary
 */
export async function getProjectSummary() {
  try {
    return await apiCall('/projects/summary', 'GET');
  } catch (err) {
    console.warn('[projectService] GET /projects/summary failed. Computing fallback summary.');
    return {
      total: MOCK_PROJECTS.length,
      inProgress: MOCK_PROJECTS.filter((p) => p.status === 'In Progress').length,
      underReview: MOCK_PROJECTS.filter((p) => p.status === 'Under Review').length,
      completed: MOCK_PROJECTS.filter((p) => p.status === 'Completed').length,
    };
  }
}

/**
 * Fetches single project details via GET /projects/{projectId}
 */
export async function getProjectDetails(projectId) {
  try {
    const data = await apiCall(`/projects/${projectId}`, 'GET');
    return data || MOCK_PROJECTS.find((p) => p.id === projectId) || MOCK_PROJECTS[0];
  } catch (err) {
    console.warn(`[projectService] GET /projects/${projectId} failed. Returning mock project details.`);
    return MOCK_PROJECTS.find((p) => p.id === projectId) || MOCK_PROJECTS[0];
  }
}

/**
 * Creates a new project via POST /projects
 */
export async function createProject(projectPayload) {
  try {
    return await apiCall('/projects', 'POST', projectPayload);
  } catch (err) {
    console.warn('[projectService] POST /projects failed. Constructing local project object.');
    return {
      id: `PRJ-00${Math.floor(Math.random() * 900) + 100}`,
      name: projectPayload.name,
      type: projectPayload.type || 'AML/CTF',
      status: 'Draft',
      statusColor: 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700',
      dotColor: 'bg-slate-400',
      lastUpdated: 'Just now',
      owner: 'J. Nakamura',
      description: projectPayload.description || 'Newly created regulatory project.',
      created: 'Today',
      jurisdiction: projectPayload.jurisdiction || 'United Kingdom - FCA',
    };
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
