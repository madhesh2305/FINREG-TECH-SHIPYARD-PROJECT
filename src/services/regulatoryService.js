import { apiCall } from './api';

/**
 * Fetches verified regulatory sources corpus via GET /regulatory/sources
 */
export async function getRegulatorySources(page = 1, pageSize = 50) {
  try {
    const data = await apiCall(`/regulatory/sources?page=${page}&page_size=${pageSize}`, 'GET');
    return data?.items || [];
  } catch (err) {
    console.warn('[regulatoryService] GET /regulatory/sources failed:', err);
    return [];
  }
}

/**
 * Compatibility alias for regulatory requirements / sources
 */
export async function getRegulatoryRequirements(projectId = null) {
  try {
    if (projectId) {
      const data = await apiCall(`/projects/${projectId}/requirements`, 'GET');
      return Array.isArray(data) ? data : [];
    }
    const data = await apiCall('/regulatory/sources?page=1&page_size=50', 'GET');
    return data?.items || [];
  } catch (err) {
    console.warn('[regulatoryService] getRegulatoryRequirements failed:', err);
    return [];
  }
}

/**
 * Fetches specific regulatory source details via GET /regulatory/sources/{sourceId}
 */
export async function getRequirementDetails(sourceId) {
  try {
    return await apiCall(`/regulatory/sources/${sourceId}`, 'GET');
  } catch (err) {
    console.error(`[regulatoryService] GET /regulatory/sources/${sourceId} failed:`, err);
    throw err;
  }
}
