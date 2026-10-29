const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Token Management Helpers
export const getToken = () => localStorage.getItem('authToken');
export const setToken = (token) => localStorage.setItem('authToken', token);
export const clearToken = () => localStorage.removeItem('authToken');

/**
 * Universal API Request Handler
 * @param {string} endpoint - API path (e.g. '/auth/login', '/projects')
 * @param {string} method - HTTP Method (GET, POST, PATCH, DELETE)
 * @param {object|FormData|null} body - Request payload object or FormData
 * @returns {Promise<any>} Response JSON data
 */
export async function apiCall(endpoint, method = 'GET', body = null) {
  const token = getToken();
  const isFormData = typeof FormData !== 'undefined' && body instanceof FormData;
  const headers = {
    ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
    ...(token && { Authorization: `Bearer ${token}` }),
  };

  const config = {
    method,
    headers,
  };

  if (body) {
    config.body = isFormData ? body : JSON.stringify(body);
  }

  try {
    const response = await fetch(`${BASE_URL}${endpoint}`, config);

    if (!response.ok) {
      let errorMessage = `HTTP Error ${response.status}`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || errorMessage;
      } catch (e) {
        // Fallback to text
      }

      // Handle inactive account or revoked session immediately (DEF-24)
      const errLower = (errorMessage || '').toLowerCase();
      const isDeactivatedOrUnauthorized =
        response.status === 401 ||
        (response.status === 403 &&
          (errLower.includes('deactivated') ||
            errLower.includes('inactive') ||
            errLower.includes('revoked') ||
            errLower.includes('session expired')));

      if (isDeactivatedOrUnauthorized && typeof window !== 'undefined') {
        clearToken();
        try {
          localStorage.removeItem('currentUser');
          localStorage.removeItem('finreg_current_user');
          localStorage.removeItem('finreg_projects');
        } catch (_) {}
        window.dispatchEvent(
          new CustomEvent('auth:unauthorized', {
            detail: { message: errorMessage, status: response.status },
          })
        );
      }

      throw new Error(errorMessage);
    }

    if (response.status === 204) {
      return null;
    }

    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/pdf') || contentType.includes('application/octet-stream')) {
      return await response.blob();
    }

    const text = await response.text();
    if (!text) return null;
    try {
      return JSON.parse(text);
    } catch (e) {
      return text;
    }
  } catch (err) {
    // Re-throw network or API errors for component error handling
    console.warn(`[API Client Warning] Call to ${endpoint} failed:`, err.message);
    throw err;
  }
}
