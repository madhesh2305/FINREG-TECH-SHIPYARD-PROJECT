const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Token Management Helpers
export const getToken = () => localStorage.getItem('authToken');
export const setToken = (token) => localStorage.setItem('authToken', token);
export const clearToken = () => localStorage.removeItem('authToken');

/**
 * Universal API Request Handler
 * @param {string} endpoint - API path (e.g. '/auth/login', '/projects')
 * @param {string} method - HTTP Method (GET, POST, PATCH, DELETE)
 * @param {object|null} body - Request payload object
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
        if (Array.isArray(errorData.detail)) {
          errorMessage = errorData.detail.map((d) => d.msg || JSON.stringify(d)).join(', ');
        } else {
          errorMessage = errorData.detail || errorData.message || errorMessage;
        }
      } catch (e) {
        // Fallback to text
      }
      throw new Error(errorMessage);
    }

    // Handle 204 No Content or empty bodies
    if (response.status === 204) {
      return null;
    }

    return await response.json();
  } catch (err) {
    if (err.name === 'TypeError' && err.message?.toLowerCase().includes('fetch')) {
      const connectionError = new Error(
        `Unable to reach backend server at ${BASE_URL}. Please ensure the backend server is running on port 8000.`
      );
      console.warn(`[API Client Warning] Call to ${endpoint} failed: Backend server offline.`);
      throw connectionError;
    }
    // Re-throw network or API errors for component error handling
    console.warn(`[API Client Warning] Call to ${endpoint} failed:`, err.message);
    throw err;
  }
}
