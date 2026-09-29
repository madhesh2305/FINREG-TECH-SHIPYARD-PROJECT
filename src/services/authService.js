import { apiCall, setToken, clearToken, getToken } from './api';

// Fallback Mock User Profile if Backend is Offline
const MOCK_USER = {
  id: 'usr_001',
  name: 'J. Nakamura',
  email: 'jun@finregtech.io',
  role: 'Builder',
  platform_role: 'BUILDER',
  memberships: [
    { projectId: 'PRJ-001', role: 'OWNER' },
    { projectId: 'PRJ-005', role: 'OWNER' },
  ],
};

/**
 * Authenticates user credentials via POST /auth/login
 */
export async function loginUser(email, password) {
  try {
    const data = await apiCall('/auth/login', 'POST', { email, password });
    if (data && data.access_token) {
      setToken(data.access_token);
    } else if (data && data.token) {
      setToken(data.token);
    }
    return data;
  } catch (err) {
    console.warn('[authService] Live backend login unreachable. Using dev fallback login token.');
    // Demo fallback token for dev mode testing when backend is offline
    const fakeToken = 'mock_jwt_token_jun_nakamura';
    setToken(fakeToken);
    return { access_token: fakeToken, token_type: 'bearer', user: MOCK_USER };
  }
}

/**
 * Fetches current authenticated user info via GET /users/me
 */
export async function getCurrentUser() {
  if (!getToken()) return MOCK_USER;

  try {
    const data = await apiCall('/users/me', 'GET');
    return data || MOCK_USER;
  } catch (err) {
    console.warn('[authService] GET /users/me unreachable. Returning mock user profile.');
    return MOCK_USER;
  }
}

/**
 * Signs out the current user and clears session token
 */
export function logoutUser() {
  clearToken();
}
