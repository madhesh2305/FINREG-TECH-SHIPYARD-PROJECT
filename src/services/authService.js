import { apiCall, setToken, clearToken, getToken } from './api';

const CURRENT_USER_KEY = 'finreg_current_user';

// Purge any legacy registered users key to eliminate plaintext passwords in browser storage
try {
  localStorage.removeItem('finreg_registered_users');
} catch (e) {}

/**
 * Returns empty array - mock user databases are strictly deprecated.
 */
export function getRegisteredUsers() {
  return [];
}

/**
 * Registers a new user via live backend API: POST /auth/register
 * Payload: { full_name, email, password, role, organization }
 */
export async function registerUser({ name, email, password, organization = '', role = 'Builder' }) {
  const cleanEmail = (email || '').trim().toLowerCase();
  const cleanName = (name || '').trim();
  const cleanPassword = (password || '').trim();
  const cleanOrg = (organization || '').trim();

  if (!cleanName || !cleanEmail || !cleanPassword) {
    throw new Error('Please fill in all required fields (name, email, password).');
  }

  // Normalize role to BUILDER | ADVISOR | ADMIN
  let normalizedRole = 'BUILDER';
  const roleLower = (role || '').toLowerCase();
  if (roleLower.includes('advisor')) normalizedRole = 'ADVISOR';
  else if (roleLower.includes('admin')) normalizedRole = 'ADMIN';

  // Live backend registration via PostgreSQL (strictly propagates API errors on failure)
  const res = await apiCall('/auth/register', 'POST', {
    full_name: cleanName,
    email: cleanEmail,
    password: cleanPassword,
    role: normalizedRole,
    organization: cleanOrg || undefined,
  });

  if (!res || !res.access_token) {
    throw new Error('Registration failed: No access token received from server.');
  }

  const token = res.access_token;
  setToken(token);

  const createdUser = {
    id: res.user_id,
    user_id: res.user_id,
    name: res.full_name || cleanName,
    full_name: res.full_name || cleanName,
    email: res.email || cleanEmail,
    role: res.platform_role || normalizedRole,
    platform_role: res.platform_role || normalizedRole,
  };

  localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(createdUser));
  return { success: true, user: createdUser, access_token: token };
}

/**
 * Authenticates user credentials via live backend API: POST /auth/login
 * Payload: { email, password }
 */
export async function loginUser(email, password) {
  const cleanEmail = (email || '').trim().toLowerCase();
  const cleanPassword = (password || '').trim();

  if (!cleanEmail || !cleanPassword) {
    throw new Error('Email address and password are required.');
  }

  // Live backend authentication via PostgreSQL / JWT (strictly propagates API errors on failure)
  const data = await apiCall('/auth/login', 'POST', {
    email: cleanEmail,
    password: cleanPassword,
  });

  if (!data || !data.access_token) {
    throw new Error('Authentication failed: No access token returned from backend.');
  }

  const token = data.access_token;
  setToken(token);

  const user = {
    id: data.user_id,
    user_id: data.user_id,
    name: data.full_name || cleanEmail.split('@')[0],
    full_name: data.full_name || cleanEmail.split('@')[0],
    email: data.email || cleanEmail,
    role: data.platform_role || 'BUILDER',
    platform_role: data.platform_role || 'BUILDER',
  };

  localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(user));
  return { access_token: token, token_type: data.token_type || 'bearer', user };
}

/**
 * Handles password reset request via live backend API: POST /auth/password-reset-request
 */
export async function resetPassword(email) {
  const cleanEmail = (email || '').trim().toLowerCase();
  if (!cleanEmail || !cleanEmail.includes('@') || !cleanEmail.includes('.')) {
    throw new Error('Please enter a valid email address.');
  }

  const res = await apiCall('/auth/password-reset-request', 'POST', { email: cleanEmail });
  return {
    success: true,
    message: res?.message || `Password reset instructions have been dispatched to ${cleanEmail}.`,
    ...res,
  };
}

/**
 * Fetches current authenticated user info from backend: GET /users/me
 * Restores session on page reload or clears invalid tokens.
 */
export async function getCurrentUser() {
  const token = getToken();
  if (!token) {
    try {
      localStorage.removeItem(CURRENT_USER_KEY);
    } catch (e) {}
    return null;
  }

  try {
    const data = await apiCall('/users/me', 'GET');
    if (data && data.user_id) {
      const user = {
        id: data.user_id,
        user_id: data.user_id,
        name: data.full_name,
        full_name: data.full_name,
        email: data.email,
        role: data.platform_role || 'BUILDER',
        platform_role: data.platform_role || 'BUILDER',
        memberships: data.memberships || [],
      };
      localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(user));
      return user;
    }
  } catch (err) {
    console.warn('[authService] Session validation failed via GET /users/me:', err.message);
    clearToken();
    try {
      localStorage.removeItem(CURRENT_USER_KEY);
    } catch (e) {}
    return null;
  }

  return null;
}

/**
 * Signs out the current user, revokes token on backend, and clears session
 */
export async function logoutUser() {
  try {
    await apiCall('/auth/logout', 'POST');
  } catch (e) {
    // If backend unreachable, still clear local session
  }
  clearToken();
  try {
    localStorage.removeItem(CURRENT_USER_KEY);
  } catch (e) {}
}
