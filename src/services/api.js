const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// In-flight request deduplication map for concurrent GET requests
const inFlightGetRequests = new Map();

// Short-lived cache (1.5s TTL) for frequent polling endpoints
const fastGetCache = new Map();
const CACHEABLE_GET_PREFIXES = ['/projects', '/advisors', '/admin/users', '/admin/roles-permissions'];

export const clearApiCache = () => {
  fastGetCache.clear();
  inFlightGetRequests.clear();
};

// Token Management Helpers
export const getToken = () => localStorage.getItem('authToken');
export const setToken = (token) => localStorage.setItem('authToken', token);
export const clearToken = () => {
  localStorage.removeItem('authToken');
  clearApiCache();
};

/**
 * Universal API Request Handler
 * @param {string} endpoint - API path (e.g. '/auth/login', '/projects')
 * @param {string} method - HTTP Method (GET, POST, PATCH, DELETE)
 * @param {object|null} body - Request payload object
 * @returns {Promise<any>} Response JSON data
 */
export async function apiCall(endpoint, method = 'GET', body = null) {
  const normMethod = method.toUpperCase();

  // Invalidate read cache on any mutating request
  if (normMethod !== 'GET') {
    fastGetCache.clear();
  }

  // Deduplicate and short-cache concurrent GET requests
  if (normMethod === 'GET') {
    const isCacheable = CACHEABLE_GET_PREFIXES.some((p) => endpoint.startsWith(p));
    const now = Date.now();
    if (isCacheable && fastGetCache.has(endpoint)) {
      const entry = fastGetCache.get(endpoint);
      if (now - entry.timestamp < 1500) {
        return entry.data;
      }
    }

    if (inFlightGetRequests.has(endpoint)) {
      return await inFlightGetRequests.get(endpoint);
    }
  }

  const token = getToken();
  const isFormData = typeof FormData !== 'undefined' && body instanceof FormData;

  const headers = {
    ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
    ...(token && { Authorization: `Bearer ${token}` }),
  };

  const config = {
    method: normMethod,
    headers,
  };

  if (body) {
    config.body = isFormData ? body : JSON.stringify(body);
  }

  const executeFetch = async () => {
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
        // Handle inactive account or revoked session immediately (DEF-24, DEF-36)
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
          const deactMsg = errLower.includes('deactivated') || errLower.includes('revoked')
            ? 'Your account has been deactivated by an administrator.'
            : errorMessage;
          try {
            localStorage.removeItem('currentUser');
            localStorage.removeItem('finreg_current_user');
            localStorage.removeItem('finreg_projects');
            sessionStorage.setItem('auth_deactivated_notice', deactMsg);
          } catch (_) {}
          window.dispatchEvent(
            new CustomEvent('auth:unauthorized', {
              detail: { message: deactMsg, status: response.status },
            })
          );
        }

        throw new Error(errorMessage);
      }

      // Handle 204 No Content or empty bodies
      if (response.status === 204) {
        return null;
      }

      const data = await response.json();

      // Store in fast cache if cacheable
      if (normMethod === 'GET' && CACHEABLE_GET_PREFIXES.some((p) => endpoint.startsWith(p))) {
        fastGetCache.set(endpoint, { data, timestamp: Date.now() });
      }

      return data;
    } catch (err) {
      console.warn(`[API Client Warning] Call to ${endpoint} failed:`, err.message);
      throw err;
    } finally {
      if (normMethod === 'GET') {
        inFlightGetRequests.delete(endpoint);
      }
    }
  };

  if (normMethod === 'GET') {
    const fetchPromise = executeFetch();
    inFlightGetRequests.set(endpoint, fetchPromise);
    return await fetchPromise;
  }

  return await executeFetch();
}
