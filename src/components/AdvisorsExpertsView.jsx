import React, { useState, useEffect, useCallback } from 'react';
import { Search, Check, CheckCircle2, ArrowLeft, UserX, RefreshCw } from 'lucide-react';
import {
  sendAdvisorInvitation,
  getAdvisors,
  getProjectAdvisorInvitations,
  getLocalAdvisorInvitations,
  removeLocalAdvisorInvitation,
  getProjectMembers,
} from '../services/advisorService';

// Master advisors list initialized to empty array (ready for live registered advisors / backend data)
const DEFAULT_ADVISORS = [];

export default function AdvisorsExpertsView({ isDarkMode, onInviteAdvisor, availableProjects = [], activeProject, currentUser }) {
  const [activeSubTab, setActiveSubTab] = useState('Find Advisors'); // 'Find Advisors' | 'My Invited Advisors'
  const [searchQuery, setSearchQuery] = useState('');
  const [expertiseFilter, setExpertiseFilter] = useState('All expertise');
  const [jurisdictionFilter, setJurisdictionFilter] = useState('All jurisdictions');
  const [availabilityFilter, setAvailabilityFilter] = useState('Any availability');
  const [activeCardId, setActiveCardId] = useState(null);
  const [toastMsg, setToastMsg] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Available projects for the invite dropdown
  const projectOptions = availableProjects.length > 0 ? availableProjects : [];

  // Selected Profile State for Profile View (matching uploaded image media_1790742446620.png)
  const [profileAdvisor, setProfileAdvisor] = useState(null);

  // Modal State for "Invite Advisor"
  const [isInviteModalOpen, setIsInviteModalOpen] = useState(false);
  const [modalAdvisor, setModalAdvisor] = useState(null);
  const [modalProject, setModalProject] = useState(projectOptions[0]?.name || '');
  const [modalRole, setModalRole] = useState('Regulatory Reviewer');
  const [modalMessage, setModalMessage] = useState(
    'We would value your review of our control framework and source interpretation.'
  );
  const [isSubmittingInvite, setIsSubmittingInvite] = useState(false);

  // Master Advisors List loaded live from backend GET /advisors
  const [advisors, setAdvisors] = useState([]);

  const fetchLiveAdvisors = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const pid = activeProject?.id || activeProject?.project_id || availableProjects[0]?.id || availableProjects[0]?.project_id;
      const [live, invites, members] = await Promise.all([
        getAdvisors(),
        getProjectAdvisorInvitations(pid).catch(() => []),
        pid ? getProjectMembers(pid).catch(() => []) : Promise.resolve([]),
      ]);

      const localInvites = getLocalAdvisorInvitations();
      const allInvites = [...(Array.isArray(invites) ? invites : []), ...localInvites];

      // 1. Accepted invitations & project assignments
      const acceptedEmails = new Set(
        allInvites
          .filter((inv) => {
            const st = (inv.invitation_status || inv.status || '').toUpperCase();
            return st === 'ACCEPTED';
          })
          .map((inv) => (inv.advisor_email || inv.email || '').toLowerCase().trim())
          .filter(Boolean)
      );

      try {
        const rawAssignments = localStorage.getItem('finreg_advisor_assignments');
        if (rawAssignments) {
          const assignments = JSON.parse(rawAssignments);
          assignments.forEach((a) => {
            if (a.email) acceptedEmails.add(a.email.toLowerCase().trim());
          });
        }
      } catch (e) {}

      // 2. Pending invitations (excluding already accepted)
      const pendingEmails = new Set(
        allInvites
          .filter((inv) => {
            const st = (inv.invitation_status || inv.status || 'PENDING').toUpperCase();
            return st === 'PENDING' || st === 'INVITED';
          })
          .map((inv) => (inv.advisor_email || inv.email || '').toLowerCase().trim())
          .filter((e) => Boolean(e) && !acceptedEmails.has(e))
      );

      // 3. Project members
      const memberEmails = new Set(
        (Array.isArray(members) ? members : [])
          .map((m) => (m.email || m.user_email || '').toLowerCase().trim())
          .filter(Boolean)
      );

      if (Array.isArray(live)) {
        setAdvisors(
          live.map((u) => {
            const emailLower = (u.email || u.contact_email || '').toLowerCase().trim();
            const isAccepted = acceptedEmails.has(emailLower) || memberEmails.has(emailLower);
            const isPending = !isAccepted && pendingEmails.has(emailLower);
            const isInvited = isAccepted || isPending;
            const isMember = isAccepted;

            const displayStatus = isAccepted ? 'Accepted' : isPending ? 'Invited' : 'Available';
            const statusColor = isAccepted
              ? 'bg-emerald-950/60 text-emerald-400 border-emerald-800/80'
              : isPending
              ? 'bg-amber-950/60 text-amber-300 border-amber-800/80'
              : 'bg-emerald-950/60 text-emerald-400 border-emerald-800/80';
            const dotColor = isAccepted ? 'bg-emerald-400' : isPending ? 'bg-amber-400' : 'bg-emerald-500';

            return {
              id: u.advisor_profile_id || u.user_id,
              user_id: u.user_id,
              name: u.full_name || u.name || 'Advisor',
              avatar: (u.full_name || u.name || 'AD')
                .split(' ')
                .filter(Boolean)
                .map((n) => n[0])
                .join('')
                .slice(0, 2)
                .toUpperCase(),
              specialty: u.specialization || u.professional_title || 'Regulatory Compliance & Advisory',
              firm: u.organization_name || u.firm || 'Independent Advisory',
              jurisdiction: u.jurisdiction || 'UK / EU',
              status: displayStatus,
              statusColor,
              dotColor,
              isMember,
              isAccepted,
              isPending,
              isInvited,
              bio: u.bio || 'Registered compliance advisor specializing in regulatory risk and governance.',
              organization: u.organization_name || u.firm || 'Independent Advisory',
              areasOfSupport: u.areasOfSupport || ['Policy design', 'Control validation', 'Regulatory interpretation', 'Board assurance'],
              email: emailLower,
            };
          })
        );
      }
    } catch (err) {
      console.warn('[AdvisorsExpertsView] Failed to fetch advisors:', err.message);
    } finally {
      setIsRefreshing(false);
    }
  }, [activeProject, availableProjects]);

  useEffect(() => {
    fetchLiveAdvisors();
  }, [fetchLiveAdvisors, activeSubTab]);

  const invitedCount = advisors.filter((a) => a.isAccepted || a.isMember || a.isPending || a.isInvited).length;
  const isLimitReached = invitedCount >= 2;

  // Filtering Logic
  const filteredAdvisors = advisors.filter((adv) => {
    if (activeSubTab === 'My Invited Advisors' && !adv.isInvited && !adv.isPending && !adv.isMember && !adv.isAccepted) return false;

    const q = (searchQuery || '').trim().toLowerCase();
    const matchesSearch =
      !q ||
      (adv.name || '').toLowerCase().includes(q) ||
      (adv.email || '').toLowerCase().includes(q) ||
      (adv.specialty || '').toLowerCase().includes(q) ||
      (adv.firm || '').toLowerCase().includes(q) ||
      (adv.organization || '').toLowerCase().includes(q);

    const matchesExpertise =
      expertiseFilter === 'All expertise' || adv.specialty === expertiseFilter;

    const matchesJurisdiction =
      jurisdictionFilter === 'All jurisdictions' || adv.jurisdiction.includes(jurisdictionFilter);

    const matchesAvailability =
      availabilityFilter === 'Any availability' ||
      adv.status === availabilityFilter ||
      (availabilityFilter === 'Invited' && (adv.status === 'Invited' || adv.isInvited || adv.isPending)) ||
      (availabilityFilter === 'Accepted' && (adv.status === 'Accepted' || adv.isAccepted)) ||
      (availabilityFilter === 'Available' && adv.status === 'Available');

    return matchesSearch && matchesExpertise && matchesJurisdiction && matchesAvailability;
  });

  // Open Invite Modal for specific advisor
  const handleOpenInviteModal = (adv) => {
    if (isLimitReached || adv.isMember || adv.isPending || adv.isInvited) return;
    setModalAdvisor(adv);
    setModalProject(projectOptions[0]?.name || activeProject?.name || 'AML Compliance Framework');
    setModalRole('Regulatory Reviewer');
    setModalMessage(
      'We would value your review of our control framework and source interpretation.'
    );
    setIsInviteModalOpen(true);
  };

  // Submit Modal Invitation Form -> Sends invitation via live backend POST /projects/{projectId}/advisor-invitations
  const handleSendInvitation = async (e) => {
    if (e) e.preventDefault();
    if (!modalAdvisor || isSubmittingInvite) return;

    setIsSubmittingInvite(true);
    const targetProjectObj = projectOptions.find((p) => p.name === modalProject) || activeProject || projectOptions[0];
    const targetProjectId = targetProjectObj?.id || targetProjectObj?.project_id || 1;

    try {
      // 1. Optimistically update advisor state IMMEDIATELY so UI responds instantly
      setAdvisors((prevAdvisors) =>
        prevAdvisors.map((a) => {
          if (
            a.id === modalAdvisor.id ||
            (a.email && modalAdvisor.email && a.email.toLowerCase() === modalAdvisor.email.toLowerCase())
          ) {
            return {
              ...a,
              isPending: true,
              isInvited: true,
              status: 'Invited',
              statusColor: 'bg-amber-950/60 text-amber-300 border-amber-800/80',
              dotColor: 'bg-amber-400',
            };
          }
          return a;
        })
      );

      // 2. Dispatch invitation via service (handles both PostgreSQL backend and persistent local storage)
      let builderUser = currentUser;
      if (!builderUser) {
        try {
          const raw = localStorage.getItem('finreg_current_user') || localStorage.getItem('currentUser');
          if (raw) builderUser = JSON.parse(raw);
        } catch (e) {}
      }

      const projName = modalProject || targetProjectObj?.name || targetProjectObj?.project_name || 'AML Compliance Framework';
      const invitingBuilderName = builderUser?.name || builderUser?.full_name || targetProjectObj?.owner || targetProjectObj?.owner_name || activeProject?.owner || 'Jun Developer';
      const invitingBuilderEmail = builderUser?.email || 'builder@gmail.com';
      const invitingBuilderOrg = builderUser?.organization || 'FinRegTech ShipYard';
      const invitingBuilderRole = builderUser?.role || builderUser?.platform_role || 'Builder / Project Owner';

      await sendAdvisorInvitation(targetProjectId, {
        advisor_email: modalAdvisor.email,
        advisor_name: modalAdvisor.name,
        project_name: projName,
        project_id: targetProjectId,
        inviting_user: invitingBuilderName,
        builder_name: invitingBuilderName,
        builder_email: invitingBuilderEmail,
        builder_organization: invitingBuilderOrg,
        builder_role: invitingBuilderRole,
        access_level: modalRole?.toUpperCase().includes('READ') ? 'READ_ONLY' : 'CONTRIBUTOR',
        invitation_notes: modalMessage,
      });

      setToastMsg(`Invitation issued to ${modalAdvisor.name}! Status updated to Invited.`);
      setTimeout(() => setToastMsg(null), 3500);
      setIsInviteModalOpen(false);
      if (onInviteAdvisor) onInviteAdvisor(modalAdvisor);
      await fetchLiveAdvisors();
    } catch (err) {
      console.warn('sendAdvisorInvitation notice:', err);
      // Ensure advisor stays marked as Invited in local state
      setAdvisors((prevAdvisors) =>
        prevAdvisors.map((a) =>
          a.id === modalAdvisor.id ||
          (a.email && modalAdvisor.email && a.email.toLowerCase() === modalAdvisor.email.toLowerCase())
            ? {
                ...a,
                isPending: true,
                isInvited: true,
                status: 'Invited',
                statusColor: 'bg-amber-950/60 text-amber-300 border-amber-800/80',
                dotColor: 'bg-amber-400',
              }
            : a
        )
      );
      setToastMsg(`Invitation issued to ${modalAdvisor.name}. Status updated to Invited.`);
      setIsInviteModalOpen(false);
      setTimeout(() => setToastMsg(null), 3500);
    } finally {
      setIsSubmittingInvite(false);
    }
  };

  // Cancel Invitation -> Removes advisor from "My Invited Advisors" and re-enables "Invite" button
  const handleCancelInvitation = (adv) => {
    // 1. Remove from local persistent storage
    removeLocalAdvisorInvitation(adv.email || adv.id);
    try {
      const raw = localStorage.getItem('finreg_advisor_assignments');
      if (raw) {
        const assignments = JSON.parse(raw).filter(
          (a) => a.advisorId !== adv.id && a.email?.toLowerCase() !== adv.email?.toLowerCase()
        );
        localStorage.setItem('finreg_advisor_assignments', JSON.stringify(assignments));
      }
    } catch (e) {}

    // 2. Update state immediately
    setAdvisors((prevAdvisors) =>
      prevAdvisors.map((a) =>
        a.id === adv.id || (a.email && adv.email && a.email.toLowerCase() === adv.email.toLowerCase())
          ? {
              ...a,
              isInvited: false,
              isPending: false,
              isAccepted: false,
              isMember: false,
              status: 'Available',
              statusColor: 'bg-emerald-950/60 text-emerald-400 border-emerald-800/80',
              dotColor: 'bg-emerald-500',
            }
          : a
      )
    );
    setToastMsg(`Invitation cancelled for ${adv.name}. "Invite" button re-enabled.`);
    setTimeout(() => setToastMsg(null), 3000);
  };

  const handleProfileClick = (adv) => {
    setProfileAdvisor(adv);
  };

  // -------------------------------------------------------------
  // VIEW B: ADVISOR PROFILE DETAIL VIEW (Matching media_1790742446620.png)
  // -------------------------------------------------------------
  if (profileAdvisor) {
    const currentAdv = advisors.find((a) => a.id === profileAdvisor.id) || profileAdvisor;

    return (
      <div className="space-y-8 animate-fadeIn text-left relative">
        {/* Toast Notification Banner */}
        {toastMsg && (
          <div className="fixed top-16 right-6 z-50 bg-[#7c4a27] dark:bg-[#96562c] text-white px-4 py-3 rounded-xl shadow-2xl flex items-center gap-2.5 animate-fadeIn font-semibold text-xs sm:text-sm border-2 border-amber-300">
            <Check className="w-5 h-5 text-amber-300 shrink-0" />
            <span>{toastMsg}</span>
          </div>
        )}

        {/* Top Back Navigation Link */}
        <div>
          <button
            type="button"
            onClick={() => setProfileAdvisor(null)}
            className="inline-flex items-center gap-2 text-xs sm:text-sm font-semibold text-slate-300 hover:text-white transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4 stroke-[2.5]" />
            <span>Back to advisor directory</span>
          </button>
        </div>

        {/* Profile Header Row */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 pb-6 border-b border-slate-800">
          <div className="flex items-center gap-5">
            {/* Initials Square Badge */}
            <div className="w-16 h-16 rounded-2xl bg-[#7c4a27]/30 dark:bg-[#96562c]/30 text-amber-300 border-2 border-[#96562c]/60 font-bold text-xl flex items-center justify-center shrink-0 shadow-md">
              {currentAdv.avatar}
            </div>

            <div>
              <span className="text-[11px] font-extrabold tracking-widest text-[#7c4a27] dark:text-amber-400 uppercase">
                VERIFIED EXPERT
              </span>
              <h1 className="text-3xl sm:text-4xl font-black tracking-tight text-slate-100 mt-0.5">
                {currentAdv.name}
              </h1>
              <p className="text-xs sm:text-sm text-slate-400 mt-1 font-medium">
                {currentAdv.specialty} · {currentAdv.firm}
              </p>
            </div>
          </div>

          {/* Top Right Action Button */}
          {currentAdv.isMember ? (
            <button
              type="button"
              disabled
              className="px-6 py-3 rounded-xl font-bold text-xs sm:text-sm border border-emerald-800/80 bg-emerald-950/60 text-emerald-400 cursor-not-allowed opacity-80 self-start sm:self-center"
            >
              Active Member
            </button>
          ) : currentAdv.isPending || currentAdv.isInvited ? (
            <button
              type="button"
              disabled
              className="px-6 py-3 rounded-xl font-bold text-xs sm:text-sm border border-amber-800/80 bg-amber-950/60 text-amber-300 cursor-not-allowed opacity-90 self-start sm:self-center shadow-xs"
            >
              Invited
            </button>
          ) : isLimitReached ? (
            <button
              type="button"
              disabled
              className="px-6 py-3 rounded-xl font-bold text-xs sm:text-sm border border-slate-800 bg-slate-900 text-slate-500 cursor-not-allowed opacity-60 self-start sm:self-center"
              title="Advisor limit of 2 / 2 reached"
            >
              Limit Reached
            </button>
          ) : (
            <button
              type="button"
              onClick={() => handleOpenInviteModal(currentAdv)}
              className="px-6 py-3 rounded-xl bg-[#f59e0b] hover:bg-[#d97706] text-slate-950 font-extrabold text-xs sm:text-sm shadow-md transition-all cursor-pointer border border-amber-300/60 hover:scale-[1.03] self-start sm:self-center"
            >
              Invite advisor
            </button>
          )}
        </div>

        {/* Content Cards Grid (2 Columns: Left Bio & Org, Right Areas of Support) */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Advisor Profile Details (Spans 2 columns) */}
          <div className="lg:col-span-2 rounded-2xl border border-slate-800 bg-[#161619] p-6 sm:p-8 space-y-6">
            <h2 className="text-xl font-bold text-slate-100 tracking-tight">
              Advisor profile
            </h2>

            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed font-normal">
              {currentAdv.bio}
            </p>

            {/* Metadata Rows */}
            <div className="space-y-5 pt-4 border-t border-slate-800/80">
              <div>
                <span className="block text-[11px] font-extrabold tracking-widest text-slate-500 uppercase mb-1">
                  ORGANIZATION
                </span>
                <p className="text-sm font-bold text-slate-200">
                  {currentAdv.organization}
                </p>
              </div>

              <div className="pt-3 border-t border-slate-800/60">
                <span className="block text-[11px] font-extrabold tracking-widest text-slate-500 uppercase mb-1">
                  JURISDICTION
                </span>
                <p className="text-sm font-bold text-slate-200">
                  {currentAdv.jurisdiction}
                </p>
              </div>
            </div>
          </div>

          {/* Right Column: Areas of Support (Spans 1 column) */}
          <div className="rounded-2xl border border-slate-800 bg-[#161619] p-6 sm:p-8 space-y-6">
            <h2 className="text-xl font-bold text-slate-100 tracking-tight">
              Areas of support
            </h2>

            <div className="flex flex-wrap gap-2.5 pt-2">
              {currentAdv.areasOfSupport?.map((area, idx) => (
                <div
                  key={idx}
                  className="inline-flex items-center gap-2 px-3.5 py-2 rounded-full border border-slate-800 bg-[#1e2026] text-xs font-semibold text-slate-300"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
                  <span>{area}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* INVITE ADVISOR MODAL */}
        {isInviteModalOpen && modalAdvisor && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-xs flex items-center justify-center p-4 sm:p-6 overflow-y-auto animate-fadeIn">
            <div
              className="w-full max-w-xl rounded-2xl border border-slate-700/80 bg-[#16171c] text-slate-100 shadow-2xl overflow-hidden animate-scaleUp"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Modal Header */}
              <div className="flex items-center justify-between px-6 py-5 border-b border-slate-800">
                <h2 className="text-lg sm:text-xl font-bold tracking-tight text-slate-100">
                  Invite Advisor
                </h2>
                <button
                  type="button"
                  onClick={() => setIsInviteModalOpen(false)}
                  className="text-xs sm:text-sm font-semibold text-slate-400 hover:text-slate-100 transition-colors cursor-pointer"
                >
                  Close
                </button>
              </div>

              {/* Modal Form */}
              <form onSubmit={handleSendInvitation} className="p-6 space-y-5 text-left">
                {/* Advisor Limit Pill Badge */}
                <div>
                  <div className="inline-block px-3.5 py-1.5 rounded-xl border border-slate-800 bg-[#1e2026] text-xs font-medium text-slate-400">
                    Advisor limit: <span className="font-bold text-slate-200">{invitedCount} / 2</span>
                  </div>
                </div>

                {/* Advisor Name Field */}
                <div className="space-y-1.5">
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-300">
                    Advisor name
                  </label>
                  <input
                    type="text"
                    readOnly
                    value={modalAdvisor.name}
                    className="w-full px-4 py-3 rounded-xl border border-slate-800 bg-[#111216] text-slate-200 text-sm font-semibold focus:outline-none cursor-default"
                  />
                </div>

                {/* Project Dropdown Field */}
                <div className="space-y-1.5">
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-300">
                    Project
                  </label>
                  <select
                    value={modalProject}
                    onChange={(e) => setModalProject(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl border border-slate-800 bg-[#111216] text-slate-200 text-sm font-semibold focus:outline-none focus:border-[#96562c] cursor-pointer transition-colors"
                  >
                    {projectOptions.map((p) => (
                      <option key={p.id || p.name} value={p.name}>
                        {p.name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Role / Access Level Dropdown Field */}
                <div className="space-y-1.5">
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-300">
                    Role / access level
                  </label>
                  <select
                    value={modalRole}
                    onChange={(e) => setModalRole(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl border border-slate-800 bg-[#111216] text-slate-200 text-sm font-semibold focus:outline-none focus:border-[#96562c] cursor-pointer transition-colors"
                  >
                    <option value="Regulatory Reviewer">Regulatory Reviewer</option>
                    <option value="Compliance Advisor">Compliance Advisor</option>
                    <option value="Audit Observer">Audit Observer</option>
                  </select>
                </div>

                {/* Message Textarea Field */}
                <div className="space-y-1.5">
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-300">
                    Message
                  </label>
                  <textarea
                    rows={3}
                    value={modalMessage}
                    onChange={(e) => setModalMessage(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl border border-slate-800 bg-[#111216] text-slate-200 text-sm font-normal focus:outline-none focus:border-[#96562c] resize-none transition-colors"
                  />
                </div>

                {/* Modal Footer Actions */}
                <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800/80">
                  <button
                    type="button"
                    onClick={() => setIsInviteModalOpen(false)}
                    className="px-5 py-2.5 rounded-xl border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-200 font-bold text-xs cursor-pointer transition-colors"
                  >
                    Cancel
                  </button>

                  <button
                    type="submit"
                    disabled={isSubmittingInvite}
                    className="px-6 py-2.5 rounded-xl bg-[#f59e0b] hover:bg-[#d97706] text-slate-950 font-extrabold text-xs shadow-md transition-all cursor-pointer border border-amber-300/60 hover:scale-[1.02] flex items-center gap-2"
                  >
                    {isSubmittingInvite ? 'Sending...' : 'Send invitation'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    );
  }

  // -------------------------------------------------------------
  // VIEW A: ADVISORS DIRECTORY CARDS GRID
  // -------------------------------------------------------------
  return (
    <div className="space-y-6 animate-fadeIn text-left relative">
      {/* Toast Notification Banner */}
      {toastMsg && (
        <div className="fixed top-16 right-6 z-50 bg-[#7c4a27] dark:bg-[#96562c] text-white px-4 py-3 rounded-xl shadow-2xl flex items-center gap-2.5 animate-fadeIn font-semibold text-xs sm:text-sm border-2 border-amber-300">
          <Check className="w-5 h-5 text-amber-300 shrink-0" />
          <span>{toastMsg}</span>
        </div>
      )}

      {/* Header Banner matching reference image */}
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
        <div>
          <span className="text-[11px] font-extrabold tracking-widest text-[#7c4a27] dark:text-amber-400/90 uppercase">
            TRUSTED NETWORK
          </span>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100 mt-1">
            Advisors &amp; Experts
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1.5 font-normal max-w-2xl">
            Find verified specialists and invite them into a controlled project role.
          </p>
        </div>

        {/* Top Right Advisor Limit Pill & Refresh */}
        <div className="flex items-center gap-2 self-start">
          <button
            type="button"
            onClick={fetchLiveAdvisors}
            disabled={isRefreshing}
            className="px-3 py-1.5 rounded-xl border border-slate-300 dark:border-slate-800 bg-white dark:bg-[#161619] hover:bg-slate-100 dark:hover:bg-slate-800 text-xs font-semibold text-slate-700 dark:text-slate-300 transition-colors flex items-center gap-1.5 cursor-pointer shadow-xs"
            title="Refresh Advisor Directory"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-amber-400' : ''}`} />
            <span>{isRefreshing ? 'Refreshing...' : 'Refresh'}</span>
          </button>
          <div className="px-3.5 py-1.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-stone-100 dark:bg-[#161619] text-xs font-medium text-slate-600 dark:text-slate-400">
            Advisor limit: <span className="font-bold text-slate-900 dark:text-slate-200">{invitedCount} / 2</span>
          </div>
        </div>
      </div>

      {/* Sub-Tabs Row (Find Advisors | My Invited Advisors) */}
      <div className="border-b border-slate-200 dark:border-slate-800 flex items-center gap-6 pt-2">
        <button
          type="button"
          onClick={() => setActiveSubTab('Find Advisors')}
          className={`pb-3 text-xs sm:text-sm font-bold transition-all relative cursor-pointer ${
            activeSubTab === 'Find Advisors'
              ? 'text-slate-900 dark:text-slate-100 border-b-2 border-amber-400'
              : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
          }`}
        >
          Find Advisors
        </button>

        <button
          type="button"
          onClick={() => setActiveSubTab('My Invited Advisors')}
          className={`pb-3 text-xs sm:text-sm font-semibold transition-all flex items-center gap-2 cursor-pointer ${
            activeSubTab === 'My Invited Advisors'
              ? 'text-slate-900 dark:text-slate-100 border-b-2 border-amber-400'
              : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
          }`}
        >
          <span>My Invited Advisors</span>
          <span className="w-5 h-5 rounded-full bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-bold text-[11px] flex items-center justify-center">
            {invitedCount}
          </span>
        </button>
      </div>

      {/* Filter Controls Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5 pt-1">
        {/* Search Input */}
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
            <Search className="w-4 h-4" />
          </div>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search advisors or expertise"
            className="w-full pl-10 pr-4 py-2.5 text-xs sm:text-sm rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#161619] text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:border-[#96562c] focus:ring-2 focus:ring-[#96562c]/30 transition-all"
          />
        </div>

        {/* Expertise Dropdown */}
        <select
          value={expertiseFilter}
          onChange={(e) => setExpertiseFilter(e.target.value)}
          className="px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#161619] text-slate-800 dark:text-slate-200 text-xs sm:text-sm font-medium focus:outline-none focus:border-[#96562c] cursor-pointer transition-all"
        >
          <option value="All expertise">All expertise</option>
          <option value="AML & Financial Crime">AML &amp; Financial Crime</option>
          <option value="Operational Resilience">Operational Resilience</option>
          <option value="Data Privacy & AI">Data Privacy &amp; AI</option>
        </select>

        {/* Jurisdiction Dropdown */}
        <select
          value={jurisdictionFilter}
          onChange={(e) => setJurisdictionFilter(e.target.value)}
          className="px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#161619] text-slate-800 dark:text-slate-200 text-xs sm:text-sm font-medium focus:outline-none focus:border-[#96562c] cursor-pointer transition-all"
        >
          <option value="All jurisdictions">All jurisdictions</option>
          <option value="UK">UK</option>
          <option value="EU">EU</option>
          <option value="US">US</option>
        </select>

        {/* Availability Dropdown */}
        <select
          value={availabilityFilter}
          onChange={(e) => setAvailabilityFilter(e.target.value)}
          className="px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#161619] text-slate-800 dark:text-slate-200 text-xs sm:text-sm font-medium focus:outline-none focus:border-[#96562c] cursor-pointer transition-all"
        >
          <option value="Any availability">Any availability</option>
          <option value="Available">Available</option>
          <option value="Invited">Invited</option>
          <option value="Limited">Limited</option>
        </select>
      </div>

      {/* Empty State for My Invited Advisors if none invited */}
      {activeSubTab === 'My Invited Advisors' && filteredAdvisors.length === 0 && (
        <div className="p-12 rounded-2xl border border-slate-800 bg-[#161619] text-center space-y-3">
          <div className="w-12 h-12 rounded-2xl bg-slate-800 text-slate-400 flex items-center justify-center mx-auto">
            <UserX className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold text-slate-200">No invited advisors</h3>
          <p className="text-xs sm:text-sm text-slate-400 max-w-md mx-auto">
            You have not invited any advisors yet. Switch to "Find Advisors" to browse specialists and send invitations.
          </p>
          <button
            type="button"
            onClick={() => setActiveSubTab('Find Advisors')}
            className="px-4 py-2 rounded-xl bg-[#7c4a27] text-white font-semibold text-xs cursor-pointer hover:bg-[#633a1e] transition-colors"
          >
            Browse Advisors
          </button>
        </div>
      )}

      {/* Empty State for Find Advisors if no matches (DEF-07) */}
      {activeSubTab === 'Find Advisors' && filteredAdvisors.length === 0 && (
        <div className="p-12 rounded-2xl border border-slate-800 bg-[#161619] text-center space-y-3">
          <div className="w-12 h-12 rounded-2xl bg-slate-800 text-slate-400 flex items-center justify-center mx-auto">
            <UserX className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold text-slate-200">No advisors found</h3>
          <p className="text-xs sm:text-sm text-slate-400 max-w-md mx-auto">
            No compliance advisors match your search or filter criteria. Try adjusting your search query or filter options.
          </p>
        </div>
      )}

      {/* Advisor Cards Grid */}
      {filteredAdvisors.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 pt-2">
          {filteredAdvisors.map((adv) => {
            const isActive = activeCardId === adv.id;

            return (
              <div
                key={adv.id}
                onClick={() => setActiveCardId(isActive ? null : adv.id)}
                title="Click box to toggle brown border, cream edge lighting glow & zoom-in"
                className={`rounded-2xl border p-5 flex flex-col justify-between transition-all duration-300 cursor-pointer ${
                  isActive
                    ? isDarkMode
                      ? 'bg-[#1e1e24] border-[#96562c] scale-[1.015] shadow-[0_0_35px_rgba(251,191,36,0.25),0_12px_36px_rgba(150,86,44,0.35)] ring-2 ring-[#96562c]/40'
                      : 'bg-[#fdfdf9] border-[#7c4a27] scale-[1.015] shadow-[0_0_40px_rgba(254,243,199,0.95),0_14px_40px_rgba(124,74,39,0.22)] ring-4 ring-amber-100/90'
                    : isDarkMode
                    ? 'bg-[#161619] border-slate-800/90 shadow-md hover:border-[#96562c] hover:scale-[1.01]'
                    : 'bg-white border-stone-200/90 shadow-xs hover:border-[#7c4a27] hover:scale-[1.01]'
                }`}
              >
                <div>
                  {/* Header Row: Initials Badge & Status Pill */}
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-8 h-8 rounded-md bg-[#7c4a27]/30 dark:bg-[#96562c]/30 text-amber-700 dark:text-amber-300 border border-amber-300/30 dark:border-[#96562c]/50 font-bold text-xs flex items-center justify-center">
                      {adv.avatar}
                    </div>
                    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border ${adv.statusColor}`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${adv.dotColor}`} />
                      {adv.status}
                    </span>
                  </div>

                  {/* Name, Specialty & Firm */}
                  <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 tracking-tight">
                    {adv.name}
                  </h3>
                  <p className="text-xs sm:text-sm font-semibold text-slate-700 dark:text-slate-300 mt-1">
                    {adv.specialty}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 font-normal">
                    {adv.firm}
                  </p>

                  {/* Jurisdiction */}
                  <p className="text-xs text-slate-400 dark:text-slate-500 font-mono mt-4">
                    {adv.jurisdiction}
                  </p>
                </div>

                {/* Bottom Actions Row */}
                <div className="flex items-center justify-between gap-3 pt-5 mt-5 border-t border-slate-100 dark:border-slate-800/80">
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleProfileClick(adv);
                    }}
                    className="px-4 py-2 rounded-xl text-xs font-bold border border-slate-300 dark:border-slate-700/80 bg-stone-50 dark:bg-slate-800/60 hover:bg-slate-700 text-slate-700 dark:text-slate-200 transition-colors cursor-pointer"
                  >
                    View profile
                  </button>

                  {adv.isAccepted ? (
                    <span className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold border border-emerald-800/80 bg-emerald-950/60 text-emerald-400 shadow-xs">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                      <span>Accepted</span>
                    </span>
                  ) : adv.isMember ? (
                    <button
                      type="button"
                      disabled
                      className="px-4 py-2 rounded-xl text-xs font-bold border border-emerald-800/80 bg-emerald-950/60 text-emerald-400 cursor-not-allowed opacity-80"
                    >
                      Active Member
                    </button>
                  ) : adv.isPending || adv.isInvited ? (
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        disabled
                        className="px-4 py-2 rounded-xl text-xs font-bold border border-amber-800/80 bg-amber-950/60 text-amber-300 cursor-not-allowed opacity-90 shadow-xs"
                      >
                        Invited
                      </button>
                      {activeSubTab === 'My Invited Advisors' && (
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleCancelInvitation(adv);
                          }}
                          className="px-3 py-2 rounded-xl text-xs font-semibold border border-rose-900/60 bg-rose-950/40 hover:bg-rose-900/60 text-rose-300 transition-colors cursor-pointer"
                          title="Cancel this advisor invitation"
                        >
                          Cancel
                        </button>
                      )}
                    </div>
                  ) : isLimitReached ? (
                    <button
                      type="button"
                      disabled
                      className="px-4 py-2 rounded-xl text-xs font-bold border border-slate-800 bg-slate-900 text-slate-500 cursor-not-allowed opacity-60"
                      title="Advisor limit of 2 / 2 reached"
                    >
                      Limit Reached
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleOpenInviteModal(adv);
                      }}
                      className="px-5 py-2 rounded-xl text-xs font-bold bg-[#f59e0b] hover:bg-[#d97706] text-slate-950 shadow-sm transition-all cursor-pointer border border-amber-300/60 hover:scale-[1.03]"
                    >
                      Invite
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* INVITE ADVISOR MODAL */}
      {isInviteModalOpen && modalAdvisor && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-xs flex items-center justify-center p-4 sm:p-6 overflow-y-auto animate-fadeIn">
          <div
            className="w-full max-w-xl rounded-2xl border border-slate-700/80 bg-[#16171c] text-slate-100 shadow-2xl overflow-hidden animate-scaleUp"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-5 border-b border-slate-800">
              <h2 className="text-lg sm:text-xl font-bold tracking-tight text-slate-100">
                Invite Advisor
              </h2>
              <button
                type="button"
                onClick={() => setIsInviteModalOpen(false)}
                className="text-xs sm:text-sm font-semibold text-slate-400 hover:text-slate-100 transition-colors cursor-pointer"
              >
                Close
              </button>
            </div>

            {/* Modal Form */}
            <form onSubmit={handleSendInvitation} className="p-6 space-y-5 text-left">
              {/* Advisor Limit Pill Badge */}
              <div>
                <div className="inline-block px-3.5 py-1.5 rounded-xl border border-slate-800 bg-[#1e2026] text-xs font-medium text-slate-400">
                  Advisor limit: <span className="font-bold text-slate-200">{invitedCount} / 2</span>
                </div>
              </div>

              {/* Advisor Name Field */}
              <div className="space-y-1.5">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-300">
                  Advisor name
                </label>
                <input
                  type="text"
                  readOnly
                  value={modalAdvisor.name}
                  className="w-full px-4 py-3 rounded-xl border border-slate-800 bg-[#111216] text-slate-200 text-sm font-semibold focus:outline-none cursor-default"
                />
              </div>

              {/* Project Dropdown Field */}
              <div className="space-y-1.5">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-300">
                  Project
                </label>
                <select
                  value={modalProject}
                  onChange={(e) => setModalProject(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-slate-800 bg-[#111216] text-slate-200 text-sm font-semibold focus:outline-none focus:border-[#96562c] cursor-pointer transition-colors"
                >
                  {projectOptions.map((p) => (
                    <option key={p.id || p.name} value={p.name}>
                      {p.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Role / Access Level Dropdown Field */}
              <div className="space-y-1.5">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-300">
                  Role / access level
                </label>
                <select
                  value={modalRole}
                  onChange={(e) => setModalRole(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-slate-800 bg-[#111216] text-slate-200 text-sm font-semibold focus:outline-none focus:border-[#96562c] cursor-pointer transition-colors"
                >
                  <option value="Regulatory Reviewer">Regulatory Reviewer</option>
                  <option value="Compliance Advisor">Compliance Advisor</option>
                  <option value="Audit Observer">Audit Observer</option>
                </select>
              </div>

              {/* Message Textarea Field */}
              <div className="space-y-1.5">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-300">
                  Message
                </label>
                <textarea
                  rows={3}
                  value={modalMessage}
                  onChange={(e) => setModalMessage(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-slate-800 bg-[#111216] text-slate-200 text-sm font-normal focus:outline-none focus:border-[#96562c] resize-none transition-colors"
                />
              </div>

              {/* Modal Footer Actions */}
              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800/80">
                <button
                  type="button"
                  onClick={() => setIsInviteModalOpen(false)}
                  className="px-5 py-2.5 rounded-xl border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-200 font-bold text-xs cursor-pointer transition-colors"
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  disabled={isSubmittingInvite}
                  className="px-6 py-2.5 rounded-xl bg-[#f59e0b] hover:bg-[#d97706] text-slate-950 font-extrabold text-xs shadow-md transition-all cursor-pointer border border-amber-300/60 hover:scale-[1.02] flex items-center gap-2"
                >
                  {isSubmittingInvite ? 'Sending...' : 'Send invitation'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
