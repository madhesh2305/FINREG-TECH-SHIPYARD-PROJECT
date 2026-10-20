import { apiCall } from './api';

const MOCK_REQUIREMENTS = [];

/**
 * Fetches regulatory requirements list via GET /regulatory-requirements
 */
export async function getRegulatoryRequirements() {
  try {
    const data = await apiCall('/regulatory-requirements', 'GET');
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.warn('[regulatoryService] GET /regulatory-requirements failed.');
    return [];
  }
}

/**
 * Fetches specific regulatory requirement details & provenance via GET /regulatory-requirements/{reqId}
 */
export async function getRequirementDetails(reqId) {
  try {
    return await apiCall(`/regulatory-requirements/${reqId}`, 'GET');
  } catch (err) {
    console.warn(`[regulatoryService] GET /regulatory-requirements/${reqId} failed.`);
    return null;
  }
}
