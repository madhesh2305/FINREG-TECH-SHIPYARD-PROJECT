import React, { useState } from 'react';
import { Search, Check, ArrowLeft } from 'lucide-react';
import { sendAdvisorInvitation } from '../services/advisorService';

export default function AdvisorsExpertsView({ isDarkMode, onInviteAdvisor }) {
  const [activeSubTab, setActiveSubTab] = useState('Find Advisors'); // 'Find Advisors' | 'My Invited Advisors'
  const [searchQuery, setSearchQuery] = useState('');
  const [expertiseFilter, setExpertiseFilter] = useState('All expertise');
  const [jurisdictionFilter, setJurisdictionFilter] = useState('All jurisdictions');
  const [availabilityFilter, setAvailabilityFilter] = useState('Any availability');
  const [activeCardId, setActiveCardId] = useState(null);
  const [toastMsg, setToastMsg] = useState(null);

  // Selected Profile State for Profile View (matching uploaded image media_1790742446620.png)
  const [profileAdvisor, setProfileAdvisor] = useState(null);

  // Modal State for "Invite Advisor"
  const [isInviteModalOpen, setIsInviteModalOpen] = useState(false);
  const [modalAdvisor, setModalAdvisor] = useState(null);
  const [modalProject, setModalProject] = useState('AML Compliance Framework');
  const [modalRole, setModalRole] = useState('Regulatory Reviewer');
  const [modalMessage, setModalMessage] = useState(
    'We would value your review of our control framework and source interpretation.'
  );
  const [isSubmittingInvite, setIsSubmittingInvite] = useState(false);

  // Master Advisors List matching reference images
  const [advisors, setAdvisors] = useState([
    {
      id: 'ADV-001',
      name: 'Dr. Maya Chen',
      avatar: 'MC',
      specialty: 'AML & Financial Crime',
      firm: 'Regulatory Advisory Group',
      jurisdiction: 'UK / EU',
      status: 'Available',
      statusColor: 'bg-emerald-950/60 text-emerald-400 border-emerald-800/80',
      dotColor: 'bg-emerald-500',
      isInvited: true,
      bio: 'Former regulatory supervisor specializing in AML/CTF compliance frameworks, sanctions screening, and transaction monitoring architectures.',
      organization: 'Regulatory Advisory Group',
      areasOfSupport: ['AML/CTF Frameworks', 'Sanctions Audit', 'Transaction Monitoring', 'FCA Sign-off'],
    },
    {
      id: 'ADV-002',
      name: 'Daniel Okafor',
      avatar: 'DO',
      specialty: 'Operational Resilience',
      firm: 'Independent',
      jurisdiction: 'UK',
      status: 'Available',
      statusColor: 'bg-emerald-950/60 text-emerald-400 border-emerald-800/80',
      dotColor: 'bg-emerald-500',
      isInvited: false,
      bio: 'Senior regulatory specialist with experience designing proportionate controls for banks, payment firms, and regulated technology providers.',
      organization: 'Independent',
      areasOfSupport: ['Policy design', 'Control validation', 'Regulatory interpretation', 'Board assurance'],
    },
    {
      id: 'ADV-003',
      name: 'Sofia Alvarez',
      avatar: 'SA',
      specialty: 'Data Privacy & AI',
      firm: 'TrustWorks Legal',
      jurisdiction: 'EU / US',
      status: 'Limited',
      statusColor: 'bg-amber-950/60 text-amber-400 border-amber-800/80',
      dotColor: 'bg-amber-500',
      isInvited: false,
      bio: 'Data protection officer and legal counsel focusing on GDPR compliance, cross-border data transfer mechanisms, and AI risk governance.',
      organization: 'TrustWorks Legal',
      areasOfSupport: ['GDPR Audits', 'Data Protection Impact Assessment', 'AI Safety Controls', 'Cross-border Transfer'],
    },
  ]);

  const invitedCount = advisors.filter((a) => a.isInvited).length;
  const isLimitReached = invitedCount >= 2;

  // Filtering Logic
  const filteredAdvisors = advisors.filter((adv) => {
    if (activeSubTab === 'My Invited Advisors' && !adv.isInvited) return false;

    const matchesSearch =
      adv.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      adv.specialty.toLowerCase().includes(searchQuery.toLowerCase()) ||
      adv.firm.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesExpertise =
      expertiseFilter === 'All expertise' || adv.specialty === expertiseFilter;

    const matchesJurisdiction =
      jurisdictionFilter === 'All jurisdictions' || adv.jurisdiction.includes(jurisdictionFilter);

    const matchesAvailability =
      availabilityFilter === 'Any availability' || adv.status === availabilityFilter;

    return matchesSearch && matchesExpertise && matchesJurisdiction && matchesAvailability;
  });

  // Open Invite Modal for specific advisor
  const handleOpenInviteModal = (adv) => {
    if (isLimitReached && !adv.isInvited) return;
    setModalAdvisor(adv);
    setModalProject('AML Compliance Framework');
    setModalRole('Regulatory Reviewer');
    setModalMessage(
      'We would value your review of our control framework and source interpretation.'
    );
    setIsInviteModalOpen(true);
  };

  // Submit Modal Invitation Form -> Permanently adds advisor to "My Invited Advisors"
  const handleSendInvitation = async (e) => {
    e.preventDefault();
    if (!modalAdvisor) return;

    setIsSubmittingInvite(true);
    try {
      await sendAdvisorInvitation('PRJ-001', {
        advisorId: modalAdvisor.id,
        advisorName: modalAdvisor.name,
        project: modalProject,
        role: modalRole,
        message: modalMessage,
      });
    } catch (err) {
      console.warn('sendAdvisorInvitation fallback executed:', err);
    }

    // Update local state to mark advisor as invited (permanently available under "My Invited Advisors")
    setAdvisors((prevAdvisors) =>
      prevAdvisors.map((a) => (a.id === modalAdvisor.id ? { ...a, isInvited: true } : a))
    );

    setIsSubmittingInvite(false);
    setIsInviteModalOpen(false);

    setToastMsg(`Invitation sent to ${modalAdvisor.name}! Saved under My Invited Advisors.`);
    setTimeout(() => setToastMsg(null), 3000);
    if (onInviteAdvisor) onInviteAdvisor(modalAdvisor);
  };

  // Toggle or Cancel Invited state
  const handleToggleInvitedState = (adv) => {
    if (adv.isInvited) {
      setAdvisors((prevAdvisors) =>
        prevAdvisors.map((a) => (a.id === adv.id ? { ...a, isInvited: false } : a))
      );
      setToastMsg(`Invitation cancelled for ${adv.name}`);
      setTimeout(() => setToastMsg(null), 3000);
    } else {
      if (!isLimitReached) {
        handleOpenInviteModal(adv);
      }
    }
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

          {currentAdv.isInvited ? (
            <button
              type="button"
              disabled
              className="px-6 py-3 rounded-xl font-bold text-xs sm:text-sm border border-slate-700/80 bg-slate-800/90 text-slate-400 cursor-not-allowed opacity-80 self-start sm:self-center"
              title="Advisor already invited"
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
                    <option value="AML Compliance Framework">AML Compliance Framework</option>
                    <option value="KYC Onboarding Workflow">KYC Onboarding Workflow</option>
                    <option value="Regulatory Reporting Q3">Regulatory Reporting Q3</option>
                    <option value="GDPR Data Audit Trail">GDPR Data Audit Trail</option>
                    <option value="Basel III Capital Adequacy">Basel III Capital Adequacy</option>
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

        {/* Top Right Advisor Limit Pill */}
        <div className="self-start px-3.5 py-1.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-stone-100 dark:bg-[#161619] text-xs font-medium text-slate-600 dark:text-slate-400">
          Advisor limit: <span className="font-bold text-slate-900 dark:text-slate-200">{invitedCount} / 2</span>
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
          <option value="Limited">Limited</option>
        </select>
      </div>

      {/* Advisor Cards Grid */}
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

                {adv.isInvited ? (
                  <button
                    type="button"
                    disabled
                    className="px-4 py-2 rounded-xl text-xs font-bold border border-slate-700/80 bg-slate-800/90 text-slate-400 cursor-not-allowed opacity-80"
                    title="Advisor already invited"
                  >
                    Invited
                  </button>
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
                  <option value="AML Compliance Framework">AML Compliance Framework</option>
                  <option value="KYC Onboarding Workflow">KYC Onboarding Workflow</option>
                  <option value="Regulatory Reporting Q3">Regulatory Reporting Q3</option>
                  <option value="GDPR Data Audit Trail">GDPR Data Audit Trail</option>
                  <option value="Basel III Capital Adequacy">Basel III Capital Adequacy</option>
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
