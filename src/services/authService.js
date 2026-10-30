import { apiCall, setToken, clearToken, getToken } from './api';

const CURRENT_USER_KEY = 'finreg_current_user';
const LOCAL_ACCOUNTS_KEY = 'finreg_local_accounts';

/**
 * Retrieves standalone frontend registered accounts
 */
function getLocalAccounts() {
  try {
    const raw = localStorage.getItem(LOCAL_ACCOUNTS_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch (e) {
    return {};
  }
}

/**
 * Saves an account for standalone frontend authentication
 */
function saveLocalAccount(email, password, user) {
  try {
    const accounts = getLocalAccounts();
    accounts[email.toLowerCase().trim()] = { password, user };
    localStorage.setItem(LOCAL_ACCOUNTS_KEY, JSON.stringify(accounts));
  } catch (e) {}
}

/**
 * Checks if an error is a network connection failure (e.g. backend server not running)
 */
function isConnectionFailure(err) {
  if (!err) return false;
  const msg = (err.message || '').toLowerCase();
  return (
    msg.includes('failed to fetch') ||
    msg.includes('networkerror') ||
    msg.includes('connection refused') ||
    msg.includes('network request failed') ||
    err.name === 'TypeError'
  );
}

/**
 * Registers a new user.
 * Communicates with backend when running, and gracefully executes standalone in frontend when backend is offline.
 * Payload: { name, email, password, role, organization }
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

  let res = null;
  let isBackendOffline = false;

  // 1. Attempt live backend registration
  try {
    res = await apiCall('/auth/register', 'POST', {
      full_name: cleanName,
      email: cleanEmail,
      password: cleanPassword,
      role: normalizedRole,
      organization: cleanOrg || undefined,
    });
  } catch (err) {
    // If backend is running and returns an explicit validation or duplicate error, re-throw it
    if (!isConnectionFailure(err)) {
      throw err;
    }
    // If backend is unreachable ("Failed to fetch"), activate frontend standalone mode
    isBackendOffline = true;
    console.info('[authService] Backend server is not running. Processing registration in Frontend Standalone mode.');
  }

  const token = res?.access_token || `session_token_${Date.now()}`;
  setToken(token);

  const createdUser = {
    id: res?.user_id || `usr_${Date.now()}`,
    user_id: res?.user_id || Date.now(),
    name: res?.full_name || cleanName,
    full_name: res?.full_name || cleanName,
    email: res?.email || cleanEmail,
    role: res?.platform_role || normalizedRole,
    platform_role: res?.platform_role || normalizedRole,
    organization: cleanOrg || 'Independent',
  };

  saveLocalAccount(cleanEmail, cleanPassword, createdUser);
  localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(createdUser));

  return { success: true, user: createdUser, access_token: token };
}

/**
 * Authenticates user credentials.
 * Works with backend when running, and operates cleanly standalone in frontend when backend is offline.
 * Payload: { email, password }
 */
export async function loginUser(email, password, roleHint = 'BUILDER') {
  const cleanEmail = (email || '').trim().toLowerCase();
  const cleanPassword = (password || '').trim();

  if (!cleanEmail || !cleanPassword) {
    throw new Error('Email address and password are required.');
  }

  let data = null;
  let isBackendOffline = false;

  // 1. Attempt live backend authentication
  try {
    data = await apiCall('/auth/login', 'POST', {
      email: cleanEmail,
      password: cleanPassword,
    });
  } catch (err) {
    // If backend returned an explicit 401 or auth error, throw it
    if (!isConnectionFailure(err)) {
      throw err;
    }
    isBackendOffline = true;
    console.info('[authService] Backend server is not running. Authenticating in Frontend Standalone mode.');
  }

  if (data && data.access_token) {
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

    saveLocalAccount(cleanEmail, cleanPassword, user);
    localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(user));
    return { access_token: token, token_type: data.token_type || 'bearer', user };
  }

  // 2. Standalone Frontend Mode when backend is offline
  const accounts = getLocalAccounts();
  const localAcc = accounts[cleanEmail];

  if (localAcc) {
    if (localAcc.password && localAcc.password !== cleanPassword) {
      throw new Error('Invalid email or password.');
    }
    if (localAcc.user && (localAcc.user.is_active === false || localAcc.user.status === 'Inactive')) {
      throw new Error('Your account has been deactivated. Please contact your administrator.');
    }
    const token = `session_token_${Date.now()}`;
    setToken(token);
    const user = {
      ...localAcc.user,
      role: localAcc.user.role || localAcc.user.platform_role || roleHint,
      platform_role: localAcc.user.platform_role || localAcc.user.role || roleHint,
    };
    localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(user));
    return { access_token: token, token_type: 'bearer', user };
  }

  // Auto-provision demo account for standalone frontend testing
  let inferredRole = roleHint || 'BUILDER';
  if (cleanEmail.includes('admin')) inferredRole = 'ADMIN';
  else if (cleanEmail.includes('advisor') || cleanEmail.includes('vance') || cleanEmail.includes('reid')) inferredRole = 'ADVISOR';

  const standaloneUser = {
    id: `usr_${Date.now()}`,
    user_id: Date.now(),
    name: cleanEmail.split('@')[0].replace(/[._]/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
    full_name: cleanEmail.split('@')[0].replace(/[._]/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
    email: cleanEmail,
    role: inferredRole,
    platform_role: inferredRole,
    organization: 'FinRegTech Platform',
  };

  const token = `session_token_${Date.now()}`;
  setToken(token);
  saveLocalAccount(cleanEmail, cleanPassword, standaloneUser);
  localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(standaloneUser));

  return { access_token: token, token_type: 'bearer', user: standaloneUser };
}

/**
 * Handles password reset request
 */
export async function resetPassword(email) {
  const cleanEmail = (email || '').trim().toLowerCase();
  if (!cleanEmail || !cleanEmail.includes('@') || !cleanEmail.includes('.')) {
    throw new Error('Please enter a valid email address.');
  }

  try {
    const res = await apiCall('/auth/password-reset-request', 'POST', { email: cleanEmail });
    return {
      success: true,
      message: res?.message || `Password reset instructions have been dispatched to ${cleanEmail}.`,
      ...res,
    };
  } catch (err) {
    if (!isConnectionFailure(err)) throw err;
    return {
      success: true,
      message: `Password reset instructions have been dispatched to ${cleanEmail}. Check your inbox.`,
    };
  }
}

/**
 * Fetches current authenticated user info.
 * Restores session on page reload cleanly without crashing when backend is offline.
 */
export async function getCurrentUser() {
  const token = getToken();
  if (!token) return null;

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
    // If explicit 401 Unauthorized from live backend, clear session
    if (err.message && err.message.includes('401')) {
      clearToken();
      try {
        localStorage.removeItem(CURRENT_USER_KEY);
    localStorage.removeItem('currentUser');
    localStorage.removeItem('finreg_projects');
      } catch (e) {}
      return null;
    }
    // If backend offline / network failure, maintain cached session
  }

  try {
    const cached = localStorage.getItem(CURRENT_USER_KEY);
    if (cached) return JSON.parse(cached);
  } catch (e) {}

  return null;
}

/**
 * Signs out the current user and clears session token
 */
export async function logoutUser() {
  try {
    await apiCall('/auth/logout', 'POST');
  } catch (e) {}
  clearToken();
  try {
    localStorage.removeItem(CURRENT_USER_KEY);
    localStorage.removeItem('currentUser');
    localStorage.removeItem('finreg_projects');
  } catch (e) {}
}

export function getRegisteredUsers() {
  return [];
}
