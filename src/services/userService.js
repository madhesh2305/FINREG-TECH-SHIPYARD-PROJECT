import { apiCall } from './api';

/**
 * Updates user profile info via live backend API: PATCH /users/me
 * Backend expects: { full_name: string }
 */
export async function updateUserProfile(profileData) {
  const fullName = (profileData.full_name || profileData.name || '').trim();
  const res = await apiCall('/users/me', 'PATCH', { full_name: fullName });

  // Sync updated name into current user storage upon confirmed backend success
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
 * Strictly propagates backend response or error without simulating success.
 */
export async function updateNotificationPreferences(preferences) {
  return await apiCall('/user/notifications', 'PUT', preferences);
}

/**
 * Retrieves real user notifications from the backend
 * GET /users/me/notifications
 */
export async function getUserNotifications() {
  const data = await apiCall('/users/me/notifications', 'GET');
  return Array.isArray(data) ? data : [];
}
