import { apiCall, setToken, clearToken, getToken } from './api';

const REGISTERED_USERS_KEY = 'finreg_registered_users';
const CURRENT_USER_KEY = 'finreg_current_user';

// Seed / Demo Accounts - initialized to empty array (ready for live backend authentication)
export const DEFAULT_USERS = [];

/**
 * Retrieves all registered users from local persistence merged with defaults
 */
export function getRegisteredUsers() {
  try {
    const raw = localStorage.getItem(REGISTERED_USERS_KEY);
    if (!raw) return DEFAULT_USERS;
    const customUsers = JSON.parse(raw);
    if (!Array.isArray(customUsers)) return DEFAULT_USERS;

    // Purge any lingering demo / seed accounts
    const mockEmails = new Set([
      'builder@gmail.com',
      'advisor@gmail.com',
      'admin@gmail.com',
      'jun@finregtech.io',
      'demo@finregtech.io',
    ]);

    const cleanUsers = customUsers.filter(
      (u) =>
        u &&
        u.email &&
        !mockEmails.has(u.email.toLowerCase()) &&
        !u.id?.startsWith('usr_builder_') &&
        !u.id?.startsWith('usr_advisor_') &&
        !u.id?.startsWith('usr_admin_') &&
        !u.id?.startsWith('usr_00') &&
        !u.name?.includes('Jun Nakamura') &&
        !u.name?.includes('Maya Chen')
    );

    try {
      localStorage.setItem(REGISTERED_USERS_KEY, JSON.stringify(cleanUsers));
    } catch (e) {}

    return cleanUsers;
  } catch (e) {
    return DEFAULT_USERS;
  }
}

/**
 * Persists a new user record via POST /auth/register
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

  // Persist directly to backend PostgreSQL database
  const res = await apiCall('/auth/register', 'POST', {
    full_name: cleanName,
    email: cleanEmail,
    password: cleanPassword,
    role: normalizedRole,
    organization: cleanOrg,
  });

  if (res && res.access_token) {
    setToken(res.access_token);
  }

  const createdUser = {
    id: res?.user_id || res?.id,
    user_id: res?.user_id || res?.id,
    name: res?.full_name || cleanName,
    full_name: res?.full_name || cleanName,
    email: res?.email || cleanEmail,
    organization: cleanOrg || 'Independent',
    role: res?.platform_role || normalizedRole,
    platform_role: res?.platform_role || normalizedRole,
    created_at: new Date().toISOString(),
  };

  localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(createdUser));

  return { success: true, user: createdUser, access_token: res?.access_token };
}

/**
 * Authenticates user credentials via POST /auth/login
 */
export async function loginUser(email, password) {
  const cleanEmail = (email || '').trim().toLowerCase();
  const cleanPassword = (password || '').trim();

  if (!cleanEmail || !cleanPassword) {
    throw new Error('Email address and password are required.');
  }

  // Live backend authentication via PostgreSQL / JWT
  const data = await apiCall('/auth/login', 'POST', {
    email: cleanEmail,
    password: cleanPassword,
  });

  if (!data || (!data.access_token && !data.token)) {
    throw new Error('Authentication succeeded but no access token was returned.');
  }

  const token = data.access_token || data.token;
  setToken(token);

  let user = data.user;
  if (!user && data.user_id) {
    user = {
      id: data.user_id,
      user_id: data.user_id,
      name: data.full_name || cleanEmail.split('@')[0],
      full_name: data.full_name || cleanEmail.split('@')[0],
      email: data.email || cleanEmail,
      role: data.platform_role || 'BUILDER',
      platform_role: data.platform_role || 'BUILDER',
    };
  }

  if (!user) {
    user = await getCurrentUser();
  }

  if (user) {
    localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(user));
  }

  return { access_token: token, token_type: 'bearer', user };
}

/**
 * Handles password reset request via POST /auth/password-reset-request
 */
export async function resetPassword(email) {
  const cleanEmail = (email || '').trim().toLowerCase();
  if (!cleanEmail || !cleanEmail.includes('@') || !cleanEmail.includes('.')) {
    throw new Error('Please enter a valid email address.');
  }

  const res = await apiCall('/auth/password-reset-request', 'POST', { email: cleanEmail });

  return {
    success: true,
    message: res?.message || `Password reset instructions have been sent to ${cleanEmail}. Please check your inbox.`,
    ...res,
  };
}

/**
 * Fetches current authenticated user info (DEF-03)
 */
export async function getCurrentUser() {
  try {
    const cached = localStorage.getItem(CURRENT_USER_KEY);
    if (cached) {
      return JSON.parse(cached);
    }
  } catch (e) {
    // fallback
  }

  if (!getToken()) return null;

  try {
    const data = await apiCall('/users/me', 'GET');
    if (data) {
      localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(data));
      return data;
    }
  } catch (err) {
    console.warn('[authService] GET /users/me unreachable.');
  }

  return null;
}

/**
 * Signs out the current user and clears session token & stored user state (DEF-03)
 */
export function logoutUser() {
  apiCall('/auth/logout', 'POST').catch(() => {});
  clearToken();
  try {
    localStorage.removeItem(CURRENT_USER_KEY);
  } catch (e) {
    // ignore
  }
}
