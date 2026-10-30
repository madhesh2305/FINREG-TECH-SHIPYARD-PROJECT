import { apiCall } from './api';

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
 * Fetches expert advisors
 */
export async function getAdvisors() {
  let backendAdvisors = [];
  try {
    const data = await apiCall('/advisors', 'GET');
    if (Array.isArray(data)) {
      backendAdvisors = data;
    }
  } catch (err) {
    console.info('[advisorService] Backend offline or request failed:', err);
  }

  let localAdvisors = [];
  try {
    const raw = localStorage.getItem('finreg_local_accounts');
    const rawReg = localStorage.getItem('finreg_registered_users');
    const allLocalUsers = [];
    if (raw) {
      const accounts = JSON.parse(raw);
      Object.values(accounts).forEach((acc) => {
        if (acc && acc.user) allLocalUsers.push(acc.user);
      });
    }
    if (rawReg) {
      const reg = JSON.parse(rawReg);
      if (Array.isArray(reg)) allLocalUsers.push(...reg);
    }

    localAdvisors = allLocalUsers
      .filter(
        (acc) =>
          acc &&
          ((acc.role || acc.platform_role || '').toUpperCase() === 'ADVISOR') &&
          acc.is_active !== false &&
          acc.status !== 'Inactive'
      )
      .map((acc) => ({
        advisor_profile_id: acc.id || acc.user_id,
        user_id: acc.id || acc.user_id,
        full_name: acc.name || acc.full_name,
        email: acc.email,
        organization_name: acc.organization || acc.organization_name || 'Independent Advisory',
        professional_title: 'Regulatory & Compliance Advisor',
        specialization: 'Financial Crime Compliance & Regulatory Strategy',
        bio: acc.bio || `Verified compliance advisor ${acc.name || acc.full_name || ''}.`,
      }));
  } catch (_) {}

  // Merge backend and local advisors, prioritizing backend data and deduplicating by email
  const seenEmails = new Set();
  const merged = [];

  for (const adv of backendAdvisors) {
    const emailKey = (adv.email || '').toLowerCase().trim();
    if (emailKey && !seenEmails.has(emailKey)) {
      seenEmails.add(emailKey);
      merged.push(adv);
    } else if (!emailKey) {
      merged.push(adv);
    }
  }

  for (const adv of localAdvisors) {
    const emailKey = (adv.email || '').toLowerCase().trim();
    if (emailKey && !seenEmails.has(emailKey)) {
      seenEmails.add(emailKey);
      merged.push(adv);
    }
  }

  if (merged.length > 0) return merged;
  return DEFAULT_ADVISORS_LIST;
}

/**
 * Fetches specific advisor profile details
 */
export async function getAdvisorDetails(advisorId) {
  try {
    return await apiCall(`/advisors/${advisorId}`, 'GET');
  } catch (err) {
    const found = DEFAULT_ADVISORS_LIST.find((a) => a.advisor_profile_id === Number(advisorId));
    return found || DEFAULT_ADVISORS_LIST[0];
  }
}

/**
 * Fetches project team members
 */
export async function getProjectMembers(projectId) {
  try {
    const data = await apiCall(`/projects/${projectId}/members`, 'GET');
    if (Array.isArray(data)) return data;
  } catch (err) {}
  return [];
}

/**
 * Submits authoritative advice for a project requirement
 */
export async function submitProjectAdvice(projectId, advicePayload) {
  try {
    return await apiCall(`/projects/${projectId}/advice`, 'POST', advicePayload);
  } catch (err) {
    console.info('[advisorService] Backend offline. Saving advice locally.');
    const newAdvice = {
      advice_id: Date.now(),
      project_id: projectId,
      title: advicePayload.title,
      advice_text: advicePayload.advice_text,
      recommendation: advicePayload.recommendation,
      assumptions: advicePayload.assumptions || '',
      advice_status: 'SUBMITTED',
      display_status: 'Pending Review',
      submitted_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      source_links: advicePayload.source_links || [],
    };
    try {
      const raw = localStorage.getItem(`finreg_advice_${projectId}`);
      const list = raw ? JSON.parse(raw) : [];
      list.unshift(newAdvice);
      localStorage.setItem(`finreg_advice_${projectId}`, JSON.stringify(list));
    } catch (e) {}
    return newAdvice;
  }
}

/**
 * Fetches authoritative advice submissions for a project
 */
export async function getProjectAdvice(projectId, statusFilter = null) {
  try {
    const endpoint = statusFilter
      ? `/projects/${projectId}/advice?status=${encodeURIComponent(statusFilter)}`
      : `/projects/${projectId}/advice`;
    const data = await apiCall(endpoint, 'GET');
    if (Array.isArray(data)) return data;
  } catch (err) {
    const raw = localStorage.getItem(`finreg_advice_${projectId}`);
    return raw ? JSON.parse(raw) : [];
  }
  return [];
}

/**
 * Updates advisory review or status transition
 */
export async function updateProjectAdvice(projectId, adviceId, payload) {
  try {
    return await apiCall(`/projects/${projectId}/advice/${adviceId}`, 'PATCH', payload);
  } catch (err) {
    const raw = localStorage.getItem(`finreg_advice_${projectId}`);
    if (raw) {
      const list = JSON.parse(raw);
      const idx = list.findIndex((a) => a.advice_id === adviceId);
      if (idx >= 0) {
        list[idx] = { ...list[idx], ...payload };
        localStorage.setItem(`finreg_advice_${projectId}`, JSON.stringify(list));
        return list[idx];
      }
    }
    return payload;
  }
}

/**
 * Sends an invitation via POST /projects/{projectId}/advisor-invitations
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
  };

  try {
    return await apiCall(`/projects/${projectId}/advisor-invitations`, 'POST', backendPayload);
  } catch (err) {
    return {
      invitation_id: Date.now(),
      project_id: projectId,
      advisor_email: email,
      access_level: accessLevel,
      invitation_status: 'PENDING',
      created_at: new Date().toISOString(),
    };
  }
}

/**
 * Retrieves all invitations issued for a project
 */
export async function getProjectAdvisorInvitations(projectId) {
  try {
    const data = await apiCall(`/projects/${projectId}/advisor-invitations`, 'GET');
    if (Array.isArray(data)) return data;
  } catch (err) {}
  return [];
}
