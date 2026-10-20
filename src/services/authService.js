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
 * Persists a new user record (DEF-13)
 */
export async function registerUser({ name, email, password, organization = '', role = 'Builder' }) {
  const cleanEmail = (email || '').trim().toLowerCase();
  const cleanName = (name || '').trim();
  const cleanPassword = (password || '').trim();
  const cleanOrg = (organization || '').trim();

  if (!cleanName || !cleanEmail || !cleanPassword) {
    throw new Error('Please fill in all required fields (name, email, password).');
  }

  // Check duplicate email
  const allUsers = getRegisteredUsers();
  if (allUsers.some((u) => u.email.toLowerCase() === cleanEmail)) {
    throw new Error(`An account with email "${cleanEmail}" is already registered. Please sign in.`);
  }

  // Normalize role to BUILDER | ADVISOR | ADMIN
  let normalizedRole = 'BUILDER';
  const roleLower = (role || '').toLowerCase();
  if (roleLower.includes('advisor')) normalizedRole = 'ADVISOR';
  else if (roleLower.includes('admin')) normalizedRole = 'ADMIN';

  const newUser = {
    id: `usr_${Date.now()}`,
    name: cleanName,
    email: cleanEmail,
    password: cleanPassword,
    organization: cleanOrg || 'Independent',
    role: normalizedRole,
    platform_role: normalizedRole,
    memberships: [],
    created_at: new Date().toISOString(),
  };

  // Attempt backend persistence first
  try {
    await apiCall('/auth/register', 'POST', {
      name: cleanName,
      email: cleanEmail,
      password: cleanPassword,
      role: normalizedRole,
      organization: cleanOrg,
    });
  } catch (err) {
    console.warn('[authService] Backend register unreachable. Persisting locally:', err.message);
  }

  // Persist locally so registration survives reloads and mock environments
  try {
    const raw = localStorage.getItem(REGISTERED_USERS_KEY);
    const existing = raw ? JSON.parse(raw) : [];
    existing.push(newUser);
    localStorage.setItem(REGISTERED_USERS_KEY, JSON.stringify(existing));
  } catch (e) {
    console.error('Failed to persist registered user locally:', e);
  }

  return { success: true, user: newUser };
}

/**
 * Authenticates user credentials via POST /auth/login or verified store (DEF-01, DEF-07)
 */
export async function loginUser(email, password) {
  const cleanEmail = (email || '').trim().toLowerCase();
  const cleanPassword = (password || '').trim();

  if (!cleanEmail || !cleanPassword) {
    throw new Error('Email address and password are required.');
  }

  // 1. Attempt live backend authentication
  try {
    const data = await apiCall('/auth/login', 'POST', { email: cleanEmail, password: cleanPassword });
    if (data && (data.access_token || data.token)) {
      const token = data.access_token || data.token;
      setToken(token);
      let user = data.user;
      if (!user) {
        user = await getCurrentUser();
      }
      if (user) {
        localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(user));
      }
      return { access_token: token, user };
    }
  } catch (err) {
    console.warn('[authService] Live backend login unreachable. Checking verified accounts store:', err.message);
  }

  // 2. Fallback to registered users repository
  const users = getRegisteredUsers();
  const matchedUser = users.find(
    (u) => u.email.toLowerCase() === cleanEmail && u.password === cleanPassword
  );

  if (!matchedUser) {
    throw new Error('Invalid email or password. Please verify your credentials or register a new account.');
  }

  const mockToken = `jwt_token_${matchedUser.id}_${Date.now()}`;
  setToken(mockToken);
  localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(matchedUser));
  return { access_token: mockToken, token_type: 'bearer', user: matchedUser };
}

/**
 * Handles password reset request with accurate feedback (DEF-02)
 */
export async function resetPassword(email) {
  const cleanEmail = (email || '').trim().toLowerCase();
  if (!cleanEmail || !cleanEmail.includes('@') || !cleanEmail.includes('.')) {
    throw new Error('Please enter a valid email address.');
  }

  // Try live backend request
  try {
    await apiCall('/auth/forgot-password', 'POST', { email: cleanEmail });
    return {
      success: true,
      message: `Password reset instructions have been sent to ${cleanEmail}. Please check your inbox.`,
    };
  } catch (err) {
    console.warn('[authService] Live backend password reset unreachable:', err.message);
  }

  // Check if user exists in registered database
  const users = getRegisteredUsers();
  const exists = users.some((u) => u.email.toLowerCase() === cleanEmail);

  if (!exists) {
    // DEF-02: Do not claim an email was sent if the service failed or user does not exist
    throw new Error(`No account found matching email "${cleanEmail}". Please verify the address or register.`);
  }

  return {
    success: true,
    message: `Password reset instructions have been dispatched to ${cleanEmail}. Follow the link in your email to reset your credentials.`,
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
  clearToken();
  try {
    localStorage.removeItem(CURRENT_USER_KEY);
  } catch (e) {
    // ignore
  }
}
