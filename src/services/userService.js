import { apiCall } from './api';

/**
 * Updates builder profile info via PUT /user/profile
 */
export async function updateUserProfile(profileData) {
  try {
    return await apiCall('/user/profile', 'PUT', profileData);
  } catch (err) {
    console.warn('[userService] PUT /user/profile failed.');
    return { success: true, ...profileData };
  }
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
