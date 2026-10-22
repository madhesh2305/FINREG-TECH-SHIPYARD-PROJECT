import { apiCall } from './api';

/**
 * Updates user profile info via PATCH /users/me
 */
export async function updateUserProfile(profileData) {
  const fullName = (profileData.full_name || profileData.name || '').trim();
  const res = await apiCall('/users/me', 'PATCH', { full_name: fullName });

  // Sync updated name into current user storage
  try {
    const raw = localStorage.getItem('finreg_current_user');
    if (raw) {
      const current = JSON.parse(raw);
      localStorage.setItem(
        'finreg_current_user',
        JSON.stringify({
          ...current,
          name: fullName,
          full_name: fullName,
        })
      );
    }
  } catch (e) {}

  return res;
}

/**
 * Updates notification preference toggles via PUT /user/notifications
 */
export async function updateNotificationPreferences(preferences) {
  try {
    return await apiCall('/user/notifications', 'PUT', preferences);
  } catch (err) {
    console.warn('[userService] PUT /user/notifications failed.');
    return { success: true, ...preferences };
  }
}

/**
 * Retrieves real user notifications from the backend
 * GET /users/me/notifications
 */
export async function getUserNotifications() {
  try {
    const data = await apiCall('/users/me/notifications', 'GET');
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.warn('[userService] GET /users/me/notifications failed:', err.message);
    return [];
  }
}
