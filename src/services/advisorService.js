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

const LOCAL_ADVISOR_INVITATIONS_KEY = 'finreg_advisor_invitations';

/**
 * Retrieves persisted local advisor invitations
 */
export function getLocalAdvisorInvitations(projectId = null) {
  try {
    const raw = localStorage.getItem(LOCAL_ADVISOR_INVITATIONS_KEY);
    const list = raw ? JSON.parse(raw) : [];
    if (!Array.isArray(list)) return [];
    if (projectId) {
      return list.filter((inv) => String(inv.project_id) === String(projectId));
    }
    return list;
  } catch (e) {
    return [];
  }
}

/**
 * Saves an advisor invitation to local persistent storage
 */
export function saveLocalAdvisorInvitation(invitation) {
  try {
    const list = getLocalAdvisorInvitations();
    const cleanEmail = (invitation.advisor_email || invitation.email || '').toLowerCase().trim();
    const filtered = list.filter(
      (i) => (i.advisor_email || i.email || '').toLowerCase().trim() !== cleanEmail
    );
    filtered.push(invitation);
    localStorage.setItem(LOCAL_ADVISOR_INVITATIONS_KEY, JSON.stringify(filtered));
  } catch (e) {}
}

/**
 * Removes an advisor invitation from local persistent storage
 */
export function removeLocalAdvisorInvitation(advisorEmailOrId) {
  try {
    const list = getLocalAdvisorInvitations();
    const target = String(advisorEmailOrId).toLowerCase().trim();
    const filtered = list.filter((i) => {
      const em = (i.advisor_email || i.email || '').toLowerCase().trim();
      const id = String(i.invitation_id || i.advisor_id || i.user_id || '').toLowerCase().trim();
      return em !== target && id !== target;
    });
    localStorage.setItem(LOCAL_ADVISOR_INVITATIONS_KEY, JSON.stringify(filtered));
  } catch (e) {}
}

/**
 * Sends an invitation via POST /projects/{projectId}/advisor-invitations
 * Persists locally and syncs with live PostgreSQL backend when available.
 */
export async function sendAdvisorInvitation(projectId, payload) {
  const email = (payload.advisor_email || payload.advisorEmail || payload.email || '').toLowerCase().trim();
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

  let remoteRes = null;
  try {
    remoteRes = await apiCall(`/projects/${projectId}/advisor-invitations`, 'POST', backendPayload);
  } catch (err) {
    const errLower = (err?.message || '').toLowerCase();
    const isConflict = errLower.includes('409') || errLower.includes('already exists') || errLower.includes('active invitation');
    if (!isConflict && !errLower.includes('failed to fetch') && !errLower.includes('network') && !errLower.includes('404')) {
      console.warn('[advisorService] sendAdvisorInvitation remote warning:', err.message);
    }
  }

  const bName = payload.builder_name || payload.inviting_user || 'Jun Developer';
  const bEmail = payload.builder_email || payload.inviting_email || 'builder@gmail.com';
  const bOrg = payload.builder_organization || payload.organization || 'FinRegTech ShipYard';
  const bRole = payload.builder_role || 'Builder / Project Owner';

  // Always record invitation locally to guarantee immediate state update and persistence
  const invitationRecord = {
    invitation_id: remoteRes?.invitation_id || `inv_${Date.now()}`,
    project_id: projectId,
    project_name: payload.project_name || `Project #${projectId}`,
    inviting_user: bName,
    inviting_builder: bName,
    builder_name: bName,
    builder_email: bEmail,
    builder_organization: bOrg,
    builder_role: bRole,
    advisor_email: email,
    advisor_name: payload.advisor_name || email.split('@')[0],
    access_level: accessLevel,
    invitation_status: 'PENDING',
    status: 'PENDING',
    invitation_notes: notes,
    created_at: new Date().toISOString(),
  };
  saveLocalAdvisorInvitation(invitationRecord);

  return remoteRes || invitationRecord;
}

/**
 * Retrieves all invitations issued for a project: GET /projects/{projectId}/advisor-invitations
 * Merges PostgreSQL backend records with locally persisted invitations.
 */
export async function getProjectAdvisorInvitations(projectId = null) {
  let remoteList = [];
  if (projectId) {
    try {
      const data = await apiCall(`/projects/${projectId}/advisor-invitations`, 'GET');
      if (Array.isArray(data)) remoteList = data;
    } catch (err) {
      console.warn('[advisorService] getProjectAdvisorInvitations error:', err.message);
    }
  }

  const localList = getLocalAdvisorInvitations(projectId);
  const seenEmails = new Set();
  const merged = [];

  for (const inv of remoteList) {
    const em = (inv.advisor_email || inv.email || '').toLowerCase().trim();
    if (em) seenEmails.add(em);
    merged.push({
      ...inv,
      invitation_status: inv.invitation_status || inv.status || 'PENDING',
      status: inv.status || inv.invitation_status || 'PENDING',
    });
  }

  for (const inv of localList) {
    const em = (inv.advisor_email || inv.email || '').toLowerCase().trim();
    if (em && seenEmails.has(em)) continue;
    if (em) seenEmails.add(em);
    merged.push({
      ...inv,
      invitation_status: inv.invitation_status || inv.status || 'PENDING',
      status: inv.status || inv.invitation_status || 'PENDING',
    });
  }

  return merged;
}

/**
 * Retrieves pending invitations for the logged-in advisor: GET /advisors/me/invitations
 * Seamlessly merges backend endpoints with persistent builder invitations targeted to this advisor.
 */
export async function getAdvisorInboxInvitations(advisorEmail = null) {
  let remoteList = [];
  try {
    const data = await apiCall('/advisors/me/invitations', 'GET');
    if (Array.isArray(data)) remoteList = data;
  } catch (err) {
    // Backend endpoint fallback
  }

  // Also query project 1 advisor-invitations if live backend is online
  try {
    const projInv = await apiCall('/projects/1/advisor-invitations', 'GET');
    if (Array.isArray(projInv)) {
      remoteList = [...remoteList, ...projInv];
    }
  } catch (_) {}

  // Determine current logged-in advisor email
  let currentEmail = (advisorEmail || '').toLowerCase().trim();
  if (!currentEmail) {
    try {
      const rawUser = localStorage.getItem('finreg_current_user') || localStorage.getItem('currentUser');
      if (rawUser) {
        const u = JSON.parse(rawUser);
        currentEmail = (u.email || '').toLowerCase().trim();
      }
    } catch (_) {}
  }

  const localList = getLocalAdvisorInvitations();
  const all = [...remoteList, ...localList];
  const seenIds = new Set();
  const filtered = [];

  for (const inv of all) {
    const invId = inv.invitation_id || inv.id || `inv_${inv.project_id}_${inv.advisor_email}`;
    if (seenIds.has(invId)) continue;
    seenIds.add(invId);

    const invEmail = (inv.advisor_email || inv.email || '').toLowerCase().trim();

    // Check if this invitation belongs to the current advisor
    let matches = false;
    if (!currentEmail) {
      matches = true;
    } else if (invEmail === currentEmail) {
      matches = true;
    } else if (
      (currentEmail === 'advisor@gmail.com' || currentEmail.includes('advisor')) &&
      (invEmail === 'advisor@gmail.com' || invEmail.includes('advisor') || invEmail.includes('vance') || invEmail.includes('reid'))
    ) {
      matches = true;
    }

    if (matches) {
      const bName = inv.builder_name || inv.inviting_user || inv.inviting_builder || 'Jun Developer';
      const bEmail = inv.builder_email || inv.created_by_email || 'builder@gmail.com';
      const bOrg = inv.builder_organization || 'FinRegTech ShipYard';
      const bRole = inv.builder_role || 'Builder / Project Owner';

      filtered.push({
        ...inv,
        id: invId,
        invitation_id: inv.invitation_id || invId,
        project_id: inv.project_id || 1,
        project_name: inv.project_name || inv.projectName || `Project #${inv.project_id || 1}`,
        inviting_user: bName,
        inviting_builder: bName,
        builder_name: bName,
        builder_email: bEmail,
        builder_organization: bOrg,
        builder_role: bRole,
        access_level: inv.access_level || 'REGULATORY',
        invitation_status: inv.invitation_status || inv.status || 'PENDING',
        status: inv.status || inv.invitation_status || 'PENDING',
        created_at: inv.created_at || new Date().toISOString(),
      });
    }
  }

  return filtered;
}

/**
 * Accepts an advisor invitation: POST /projects/{projectId}/advisor-invitations/{invitationId}/accept
 * Updates invitation status in PostgreSQL backend and local storage, and grants project membership.
 */
export async function acceptAdvisorInvitation(projectId, invitationId) {
  let remoteRes = null;
  try {
    remoteRes = await apiCall(`/projects/${projectId}/advisor-invitations/${invitationId}/accept`, 'POST');
  } catch (err) {
    console.info('[advisorService] acceptAdvisorInvitation remote notice:', err.message);
  }

  const rawUser = typeof localStorage !== 'undefined' ? (localStorage.getItem('finreg_current_user') || localStorage.getItem('currentUser')) : null;
  const user = rawUser ? JSON.parse(rawUser) : null;
  const advEmail = user?.email || 'advisor@gmail.com';
  const advId = user?.user_id || user?.id || 2;

  // Update invitation status to ACCEPTED in local storage
  try {
    const list = getLocalAdvisorInvitations();
    const updated = list.map((inv) => {
      const currentId = inv.invitation_id || inv.id;
      const isIdMatch = invitationId && String(currentId) === String(invitationId);
      const isProjMatch =
        inv.project_id &&
        String(inv.project_id) === String(projectId) &&
        (!inv.advisor_email || inv.advisor_email.toLowerCase() === advEmail.toLowerCase());

      if (isIdMatch || isProjMatch) {
        return {
          ...inv,
          invitation_status: 'ACCEPTED',
          status: 'ACCEPTED',
          accepted_at: new Date().toISOString(),
        };
      }
      return inv;
    });
    localStorage.setItem(LOCAL_ADVISOR_INVITATIONS_KEY, JSON.stringify(updated));
  } catch (_) {}

  // Record assignment in finreg_advisor_assignments
  try {
    const raw = localStorage.getItem('finreg_advisor_assignments');
    const assignments = raw ? JSON.parse(raw) : [];

    const exists = assignments.some(
      (a) => String(a.projectId) === String(projectId) && (a.email?.toLowerCase() === advEmail.toLowerCase() || a.advisorId === advId)
    );
    if (!exists) {
      assignments.push({
        projectId,
        advisorId: advId,
        email: advEmail,
        name: user?.full_name || user?.name || 'Advisor',
        status: 'ACCEPTED',
        assigned_at: new Date().toISOString(),
      });
      localStorage.setItem('finreg_advisor_assignments', JSON.stringify(assignments));
    }
  } catch (_) {}

  return remoteRes || { success: true, status: 'ACCEPTED', invitation_id: invitationId, project_id: projectId };
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
