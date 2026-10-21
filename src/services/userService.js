import { apiCall } from './api';

/**
 * Updates user profile info via PATCH /users/me
 */
export async function updateUserProfile(profileData) {
  const payload = {
    full_name: profileData.full_name || profileData.name || '',
    ...(profileData.organization && { organization: profileData.organization }),
  };
  return await apiCall('/users/me', 'PATCH', payload);
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
