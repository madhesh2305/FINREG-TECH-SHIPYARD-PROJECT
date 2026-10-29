import { apiCall, setToken, clearToken, getToken } from './api';

/**
 * Registers a new user via POST /auth/register
 * @param {object} param0 - { email, password, full_name, role, organization }
 */
export async function registerUser({ email, password, full_name, role = 'BUILDER', organization = '' }) {
  const payload = {
    email: email.trim().toLowerCase(),
    password: password.trim(),
    full_name: full_name.trim(),
    role: role.toUpperCase(),
    organization: organization.trim(),
  };

  const data = await apiCall('/auth/register', 'POST', payload);
  if (data && data.access_token) {
    setToken(data.access_token);
    localStorage.setItem('currentUser', JSON.stringify({
      user_id: data.user_id,
      email: data.email,
      full_name: data.full_name,
      platform_role: data.platform_role,
    }));
  }
  return data;
}

/**
 * Authenticates user credentials via POST /auth/login
 */
export async function loginUser(email, password) {
  const payload = {
    email: email.trim().toLowerCase(),
    password: password.trim(),
  };

  const data = await apiCall('/auth/login', 'POST', payload);
  if (data && data.access_token) {
    setToken(data.access_token);
    localStorage.setItem('currentUser', JSON.stringify({
      user_id: data.user_id,
      email: data.email,
      full_name: data.full_name,
      platform_role: data.platform_role,
    }));
  }
  return data;
}

/**
 * Fetches current authenticated user info via GET /users/me
 */
export async function getCurrentUser() {
  const token = getToken();
  if (!token) return null;

  try {
    const data = await apiCall('/users/me', 'GET');
    if (data) {
      localStorage.setItem('currentUser', JSON.stringify(data));
      return data;
    }
    return null;
  } catch (err) {
    console.warn('[authService] Token expired or invalid. Clearing session.');
    clearToken();
    try {
    localStorage.removeItem('currentUser');
    localStorage.removeItem('finreg_current_user');
    localStorage.removeItem('finreg_projects');
    localStorage.removeItem('finreg_local_accounts');
  } catch (_) {}
    return null;
  }
}

/**
 * Signs out the current user and clears session token
 */
export function logoutUser() {
  clearToken();
  try {
    localStorage.removeItem('currentUser');
    localStorage.removeItem('finreg_current_user');
    localStorage.removeItem('finreg_projects');
    localStorage.removeItem('finreg_local_accounts');
  } catch (_) {}
}

/**
 * Changes authenticated user password via POST /auth/change-password
 */
export async function changePassword(currentPassword, newPassword) {
  return await apiCall('/auth/change-password', 'POST', {
    current_password: currentPassword,
    new_password: newPassword,
  });
}

/**
 * Requests password reset via POST /auth/password-reset-request
 */
export async function requestPasswordReset(email) {
  return await apiCall('/auth/password-reset-request', 'POST', {
    email: email.trim().toLowerCase(),
  });
}

/**
 * Fetches real activity and workflow notifications for current user via GET /users/me/notifications
 */
export async function getUserNotifications() {
  try {
    const data = await apiCall('/users/me/notifications', 'GET');
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.warn('[authService] getUserNotifications warning:', err);
    return [];
  }
}

/**
 * Confirms password reset via POST /auth/password-reset-confirm (DEF-15)
 */
export async function confirmPasswordReset(token, newPassword) {
  return await apiCall('/auth/password-reset-confirm', 'POST', {
    token: token.trim(),
    new_password: newPassword.trim(),
  });
}
