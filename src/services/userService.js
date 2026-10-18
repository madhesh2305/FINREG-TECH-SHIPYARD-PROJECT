import { apiCall } from './api';

/**
 * Updates builder profile info via PATCH /users/me
 */
export async function updateUserProfile(profileData) {
  try {
    const payload = {
      full_name: profileData.name || profileData.full_name,
    };
    return await apiCall('/users/me', 'PATCH', payload);
  } catch (err) {
    console.error('[userService] PATCH /users/me failed:', err);
    throw err;
  }
}

/**
 * Updates notification preference toggles via local state / persistence
 */
export async function updateNotificationPreferences(preferences) {
  try {
    localStorage.setItem('userNotificationPreferences', JSON.stringify(preferences));
    return { success: true, ...preferences };
  } catch (err) {
    console.error('[userService] saving preferences failed:', err);
    throw err;
  }
}
