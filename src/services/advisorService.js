import { apiCall } from './api';

/**
 * Fetches expert advisors via GET /advisors (with local storage synchronization and deduplication)
 */
export async function getAdvisors() {
  let backendAdvisors = [];
  try {
    const data = await apiCall('/advisors', 'GET');
    if (Array.isArray(data)) {
      backendAdvisors = data;
    }
  } catch (err) {
    console.warn('[advisorService] GET /advisors live query error:', err);
  }

  // Also check local storage for any newly created/registered advisors so they are always visible
  let localAdvisors = [];
  try {
    const raw = localStorage.getItem('finreg_local_accounts');
    const rawReg = localStorage.getItem('finreg_registered_users');
    const allLocalUsers = [];
    if (raw) {
      const accounts = JSON.parse(raw);
      Object.values(accounts).forEach((acc) => {
        if (acc?.user) allLocalUsers.push(acc.user);
      });
    }
    if (rawReg) {
      const regUsers = JSON.parse(rawReg);
      if (Array.isArray(regUsers)) {
        allLocalUsers.push(...regUsers);
      }
    }

    localAdvisors = allLocalUsers
      .filter(
        (u) =>
          u &&
          ((u.role || u.platform_role || '').toUpperCase() === 'ADVISOR') &&
          u.is_active !== false &&
          u.status !== 'Inactive'
      )
      .map((u) => ({
        advisor_profile_id: u.id || u.user_id,
        user_id: u.user_id || u.id,
        full_name: u.full_name || u.name,
        email: u.email,
        organization_name: u.organization || u.organization_name || 'Independent Advisory',
        professional_title: 'Regulatory & Compliance Advisor',
        specialization: 'Financial Crime Compliance & Regulatory Strategy',
        bio: u.bio || `Verified compliance advisor ${u.full_name || u.name || ''}.`,
      }));
  } catch (_) {}

  // Deduplicate by email with backend data taking precedence
  const seenEmails = new Set();
  const merged = [];

  for (const adv of backendAdvisors) {
    const cleanEmail = (adv.email || '').toLowerCase().trim();
    if (cleanEmail && !seenEmails.has(cleanEmail)) {
      seenEmails.add(cleanEmail);
      merged.push(adv);
    } else if (!cleanEmail) {
      merged.push(adv);
    }
  }

  for (const adv of localAdvisors) {
    const cleanEmail = (adv.email || '').toLowerCase().trim();
    if (cleanEmail && !seenEmails.has(cleanEmail)) {
      seenEmails.add(cleanEmail);
      merged.push(adv);
    }
  }

  return merged;
}

/**
 * Fetches project team members via GET /projects/{projectId}/members
 */
export async function getProjectMembers(projectId) {
  try {
    const data = await apiCall(`/projects/${projectId}/members`, 'GET');
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.error(`[advisorService] GET /projects/${projectId}/members failed:`, err);
    throw err;
  }
}

/**
 * Sends an invitation via POST /projects/{projectId}/advisor-invitations
 */
export async function sendAdvisorInvitation(projectId, payload) {
  try {
    return await apiCall(`/projects/${projectId}/advisor-invitations`, 'POST', payload);
  } catch (err) {
    console.error(`[advisorService] POST /projects/${projectId}/advisor-invitations failed:`, err);
    throw err;
  }
}

/**
 * Adds an existing user/advisor as a project member via POST /projects/{projectId}/members
 */
export async function addProjectMember(projectId, memberPayload) {
  try {
    return await apiCall(`/projects/${projectId}/members`, 'POST', memberPayload);
  } catch (err) {
    console.error(`[advisorService] POST /projects/${projectId}/members failed:`, err);
    throw err;
  }
}

/**
 * Fetches advisor invitations for project via GET /projects/{projectId}/advisor-invitations
 */
export async function getProjectInvitations(projectId) {
  try {
    const data = await apiCall(`/projects/${projectId}/advisor-invitations`, 'GET');
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.warn(`[advisorService] GET /projects/${projectId}/advisor-invitations failed:`, err);
    return [];
  }
}

/**
 * Accepts an advisor invitation via POST /projects/{projectId}/advisor-invitations/{invitationId}/accept
 */
export async function acceptAdvisorInvitation(projectId, invitationId) {
  try {
    return await apiCall(`/projects/${projectId}/advisor-invitations/${invitationId}/accept`, 'POST');
  } catch (err) {
    console.error(`[advisorService] POST /projects/${projectId}/advisor-invitations/${invitationId}/accept failed:`, err);
    throw err;
  }
}
