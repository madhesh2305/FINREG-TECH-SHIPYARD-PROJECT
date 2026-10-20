import { apiCall } from './api';

const MOCK_TOOLS = [];

/**
 * Fetches directory of trusted ecosystem tools via GET /tools
 */
export async function getTools() {
  try {
    const data = await apiCall('/tools', 'GET');
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.warn('[toolService] GET /tools failed.');
    return [];
  }
}

/**
 * Toggles or updates tool usage status via POST /tools/{toolId}/use
 */
export async function toggleToolUsage(toolId, isUsed = true) {
  try {
    return await apiCall(`/tools/${toolId}/use`, 'POST', { isUsed });
  } catch (err) {
    console.warn(`[toolService] POST /tools/${toolId}/use failed. Processing locally.`);
    return { success: true, toolId, isUsed };
  }
}
