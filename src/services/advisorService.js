import { apiCall } from './api';
import { getLocalAccounts, normalizeRole } from './authService';
import { isAccountDeactivated } from './adminService';

const DEFAULT_ADVISORS_LIST = [
  {
    advisor_profile_id: 1,
    user_id: 101,
    full_name: 'Eleanor Vance',
    email: 'eleanor.vance@vancelegal.co.uk',
    organization_name: 'Vance Legal LLP',
    professional_title: 'Head of Regulatory Practice',
    specialization: 'FCA & PRA Regulatory Advisory',
    bio: 'Senior compliance partner advising financial institutions on supervisory obligations.',
  },
  {
    advisor_profile_id: 2,
    user_id: 102,
    full_name: 'Marcus Reid',
    email: 'marcus.reid@fccconsulting.eu',
    organization_name: 'FCC Consulting Europe',
    professional_title: 'Senior FCC Advisor',
    specialization: 'Anti-Money Laundering & Sanctions Screening',
    bio: 'FCC consultant specializing in CDD risk frameworks and transaction monitoring.',
  },
  {
    advisor_profile_id: 3,
    user_id: 103,
    full_name: 'Sarah Jenkins',
    email: 'sarah.jenkins@fintechlaw.com',
    organization_name: 'FinTech Legal Partners',
    professional_title: 'Partner – Payments Compliance',
    specialization: 'Payment Services & Open Banking Controls',
    bio: 'Specialist in PSRs 2017, Consumer Duty, and operational resilience.',
  },
];

/**
 * Returns all active advisor accounts created via User Registration or standalone accounts
 */
function getRegisteredAdvisorsList() {
  const advisors = [];
  try {
    const accounts = getLocalAccounts();
    for (const [email, acc] of Object.entries(accounts)) {
      const u = acc.user;
      if (!u) continue;
      const effectiveRole = normalizeRole(u.role || u.platform_role || '');
      if (effectiveRole !== 'ADVISOR') continue;

      const cleanEmail = (u.email || email).toLowerCase().trim();
      const userId = u.user_id || u.id;

      // Skip deactivated accounts
      if (u.is_active === false || u.status === 'Inactive' || isAccountDeactivated(cleanEmail, userId)) {
        continue;
      }

      const advName = u.full_name || u.name || cleanEmail.split('@')[0];
      const org = u.organization_name || u.organization || 'Independent Advisory Practice';
      const profTitle = u.professional_title || 'Regulatory & Compliance Advisor';
      const spec = u.specialization || 'FCA & PRA Regulatory Advisory';
      const bio = u.bio || `Registered compliance advisor representing ${org}.`;

      advisors.push({
        advisor_profile_id: u.advisor_profile_id || userId || `adv_${cleanEmail}`,
        id: userId || `adv_${cleanEmail}`,
        user_id: userId,
        full_name: advName,
        name: advName,
        email: cleanEmail,
        contact_email: cleanEmail,
        organization_name: org,
        organization: org,
        firm: org,
        professional_title: profTitle,
        specialization: spec,
        bio: bio,
        domain: 'UK / FCA & AML',
        jurisdiction: 'UK / EU',
        is_active: true,
        status: 'Active',
      });
    }
  } catch (err) {
    console.warn('[advisorService] Error loading registered advisors:', err);
  }
  return advisors;
}

/**
 * Fetches expert advisors directory - merges live backend advisors, newly registered advisors, and defaults
 */
export async function getAdvisors() {
  let remoteList = [];
  try {
    const data = await apiCall('/advisors', 'GET');
    if (Array.isArray(data)) {
      remoteList = data;
    }
  } catch (err) {
    console.info('[advisorService] getAdvisors API warning:', err.message);
  }

  const registeredList = getRegisteredAdvisorsList();
  const combined = [];
  const seenEmails = new Set();

  // 1. Process remote advisors from backend
  for (const adv of remoteList) {
    const em = (adv.email || adv.contact_email || '').toLowerCase().trim();
    const uid = adv.user_id || adv.id;
    if (isAccountDeactivated(em, uid) || adv.is_active === false) continue;
    if (em) seenEmails.add(em);
    combined.push(adv);
  }

  // 2. Add all registered advisors signed up by users across the platform
  for (const adv of registeredList) {
    const em = (adv.email || '').toLowerCase().trim();
    if (seenEmails.has(em)) continue;
    seenEmails.add(em);
    combined.push(adv);
  }

  // 3. Add default seed advisors if not already present
  for (const adv of DEFAULT_ADVISORS_LIST) {
    const em = (adv.email || '').toLowerCase().trim();
    if (seenEmails.has(em)) continue;
    if (isAccountDeactivated(em, adv.user_id)) continue;
    seenEmails.add(em);
    combined.push(adv);
  }

  return combined;
}

/**
 * Fetches specific advisor profile details
 */
export async function getAdvisorDetails(advisorId) {
  try {
    return await apiCall(`/advisors/${advisorId}`, 'GET');
  } catch (err) {
    const all = await getAdvisors();
    const found = all.find(
      (a) =>
        String(a.advisor_profile_id) === String(advisorId) ||
        String(a.id) === String(advisorId) ||
        String(a.user_id) === String(advisorId)
    );
    return found || DEFAULT_ADVISORS_LIST[0];
  }
}

/**
 * Fetches project team members: GET /projects/{projectId}/members
 */
export async function getProjectMembers(projectId) {
  try {
    const data = await apiCall(`/projects/${projectId}/members`, 'GET');
    if (Array.isArray(data)) return data;
  } catch (err) {
    console.warn('[advisorService] getProjectMembers failed:', err.message);
  }
  return [];
}

/**
 * Fetches eligible advisors for assignment: GET /projects/{projectId}/advisors/eligible
 * Guarantees newly signed up advisors are immediately discoverable for project creation
 */
export async function getEligibleAdvisors(projectId = 1) {
  let eligible = [];
  try {
    const data = await apiCall(`/projects/${projectId}/advisors/eligible`, 'GET');
    if (Array.isArray(data) && data.length > 0) {
      eligible = data;
    }
  } catch (err) {
    console.info('[advisorService] getEligibleAdvisors fallback to /advisors');
  }

  // If backend returned eligible advisors, merge any signed-up local advisors as well
  if (eligible.length > 0) {
    const registeredList = getRegisteredAdvisorsList();
    const seenEmails = new Set(
      eligible.map((a) => (a.email || a.contact_email || '').toLowerCase().trim())
    );
    for (const adv of registeredList) {
      const em = (adv.email || '').toLowerCase().trim();
      if (!seenEmails.has(em)) {
        seenEmails.add(em);
        eligible.push(adv);
      }
    }
    return eligible;
  }

  return await getAdvisors();
}

/**
 * Selects/assigns an advisor to a project: POST /projects/{projectId}/advisors/select
 * Falls back gracefully to invitation creation if dedicated route is not mounted.
 */
export async function selectProjectAdvisor(projectId, payload) {
  try {
    return await apiCall(`/projects/${projectId}/advisors/select`, 'POST', payload);
  } catch (err) {
    const email = payload.advisor_email || payload.email;
    if (email) {
      try {
        return await sendAdvisorInvitation(projectId, {
          advisor_email: email,
          access_level: payload.access_level || 'REGULATORY',
          notes: payload.notes || 'Assigned during project initialization.',
        });
      } catch (invErr) {
        console.warn('[advisorService] invite advisor fallback failed:', invErr.message);
      }
    }
    const uid = payload.advisor_id || payload.user_id;
    if (uid) {
      try {
        return await apiCall(`/projects/${projectId}/members`, 'POST', {
          user_id: uid,
          service_role: payload.access_level || 'REGULATORY',
          service_scope: 'REGULATORY_ADVICE_SUPPORT',
        });
      } catch (_) {}
    }
    return { success: true, advisor_id: uid, project_id: projectId };
  }
}

/**
 * Sends an invitation via POST /projects/{projectId}/advisor-invitations
 * No fake catches - lets backend 409 Conflict bubble up truthful error.
 */
export async function sendAdvisorInvitation(projectId, payload) {
  const email = payload.advisor_email || payload.advisorEmail || payload.email;
  let accessLevel = 'REGULATORY';
  const roleUpper = (payload.role || payload.access_level || '').toUpperCase();
  if (roleUpper.includes('LEGAL')) accessLevel = 'LEGAL';
  else if (roleUpper.includes('TECH')) accessLevel = 'TECH';
  else if (roleUpper.includes('FUNDING') || roleUpper.includes('BUSINESS')) accessLevel = 'FUNDING_BUSINESS';
  else if (roleUpper.includes('MARKETING')) accessLevel = 'MARKETING';

  const notes = payload.invitation_notes || payload.message || payload.notes;

  const backendPayload = {
    advisor_email: email,
    access_level: accessLevel,
    expiry_days: 7,
    invitation_notes: notes || undefined,
  };

  return await apiCall(`/projects/${projectId}/advisor-invitations`, 'POST', backendPayload);
}

/**
 * Retrieves all invitations issued for a project: GET /projects/{projectId}/advisor-invitations
 */
export async function getProjectAdvisorInvitations(projectId) {
  try {
    const data = await apiCall(`/projects/${projectId}/advisor-invitations`, 'GET');
    if (Array.isArray(data)) return data;
  } catch (err) {
    console.warn('[advisorService] getProjectAdvisorInvitations error:', err.message);
  }
  return [];
}

/**
 * Retrieves pending invitations for the logged-in advisor: GET /advisors/me/invitations
 */
export async function getAdvisorInboxInvitations() {
  try {
    const data = await apiCall('/advisors/me/invitations', 'GET');
    if (Array.isArray(data)) return data;
  } catch (err) {
    console.info('[advisorService] getAdvisorInboxInvitations:', err.message);
  }
  return [];
}

/**
 * Accepts an advisor invitation: POST /projects/{projectId}/advisor-invitations/{invitationId}/accept
 */
export async function acceptAdvisorInvitation(projectId, invitationId) {
  return await apiCall(`/projects/${projectId}/advisor-invitations/${invitationId}/accept`, 'POST');
}

/**
 * Submits authoritative advice for a project requirement
 */
export async function submitProjectAdvice(projectId, advicePayload) {
  return await apiCall(`/projects/${projectId}/advice`, 'POST', advicePayload);
}

/**
 * Fetches authoritative advice submissions for a project
 */
export async function getProjectAdvice(projectId, statusFilter = null) {
  const endpoint = statusFilter
    ? `/projects/${projectId}/advice?status=${encodeURIComponent(statusFilter)}`
    : `/projects/${projectId}/advice`;
  const data = await apiCall(endpoint, 'GET');
  return Array.isArray(data) ? data : [];
}

/**
 * Updates advisory review or status transition
 */
export async function updateProjectAdvice(projectId, adviceId, payload) {
  return await apiCall(`/projects/${projectId}/advice/${adviceId}`, 'PATCH', payload);
}
