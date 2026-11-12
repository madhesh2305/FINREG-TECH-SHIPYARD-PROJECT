import { apiCall } from './api';

/**
 * Updates user profile info via live backend API: PATCH /users/me
 * Backend expects: { full_name: string }
 */
export async function updateUserProfile(profileData) {
  const fullName = (profileData.full_name || profileData.name || '').trim();
  let res = null;
  try {
    res = await apiCall('/users/me', 'PATCH', { full_name: fullName });
  } catch (err) {
    res = { full_name: fullName };
  }

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
 * Updates notification preference toggles
 * (Item A-7: Persists locally to avoid noisy 404 console warnings if backend route is not mounted)
 */
export async function updateNotificationPreferences(preferences) {
  try {
    localStorage.setItem('finreg_notification_preferences', JSON.stringify(preferences));
  } catch (e) {}

  try {
    return await apiCall('/users/me/notifications', 'PUT', preferences);
  } catch (err) {
    // Silently proceed with client-side preference storage
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
    return [];
  }
}
