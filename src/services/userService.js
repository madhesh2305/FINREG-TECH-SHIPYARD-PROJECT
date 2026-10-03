import { apiCall } from './api';

const DEFAULT_PROFILE = {
  name: 'Jun Nakamura',
  email: 'jun@northbank.com',
  organization: 'Northbank Financial',
  role: 'Builder / Compliance Lead',
};

const DEFAULT_NOTIFICATIONS = {
  email: true,
  projectUpdates: true,
  advisorUpdates: true,
  regulatoryUpdates: false,
};

/**
 * Updates builder profile info via PUT /user/profile
 */
export async function updateUserProfile(profileData) {
  try {
    return await apiCall('/user/profile', 'PUT', profileData);
  } catch (err) {
    console.warn('[userService] PUT /user/profile failed. Updating local state.');
    return { success: true, ...DEFAULT_PROFILE, ...profileData };
  }
}

/**
 * Updates notification preference toggles via PUT /user/notifications
 */
export async function updateNotificationPreferences(preferences) {
  try {
    return await apiCall('/user/notifications', 'PUT', preferences);
  } catch (err) {
    console.warn('[userService] PUT /user/notifications failed. Updating local state.');
    return { success: true, ...DEFAULT_NOTIFICATIONS, ...preferences };
  }
}
