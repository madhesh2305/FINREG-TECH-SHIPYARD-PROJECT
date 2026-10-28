import { apiCall } from './api';

/**
 * Records an authoritative compliance decision for a project
 */
export async function recordDecision(projectId, payload) {
  try {
    return await apiCall(`/projects/${projectId}/decisions`, 'POST', payload);
  } catch (err) {
    const newDec = {
      decision_id: Date.now(),
      project_id: projectId,
      decision_type: payload.decision_type,
      decision_rationale: payload.decision_rationale,
      follow_up_action: payload.follow_up_action || null,
      decided_by: 1,
      decider_name: 'Project Owner',
      created_at: new Date().toISOString(),
    };
    try {
      const raw = localStorage.getItem(`finreg_decisions_${projectId}`);
      const list = raw ? JSON.parse(raw) : [];
      list.unshift(newDec);
      localStorage.setItem(`finreg_decisions_${projectId}`, JSON.stringify(list));
    } catch (e) {}
    return newDec;
  }
}

/**
 * Retrieves all compliance decisions for a project
 */
export async function getProjectDecisions(projectId) {
  try {
    const data = await apiCall(`/projects/${projectId}/decisions`, 'GET');
    if (Array.isArray(data)) return data;
  } catch (err) {
    const raw = localStorage.getItem(`finreg_decisions_${projectId}`);
    return raw ? JSON.parse(raw) : [];
  }
  return [];
}

/**
 * Retrieves a specific compliance decision by ID
 */
export async function getDecisionDetails(projectId, decisionId) {
  try {
    return await apiCall(`/projects/${projectId}/decisions/${decisionId}`, 'GET');
  } catch (err) {
    const raw = localStorage.getItem(`finreg_decisions_${projectId}`);
    const list = raw ? JSON.parse(raw) : [];
    const found = list.find((d) => d.decision_id === decisionId);
    return found || null;
  }
}
