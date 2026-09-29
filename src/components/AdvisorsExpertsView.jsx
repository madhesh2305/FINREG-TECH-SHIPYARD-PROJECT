import React, { useState } from 'react';
import { Search, Check } from 'lucide-react';

export default function AdvisorsExpertsView({ isDarkMode, onInviteAdvisor }) {
  const [activeSubTab, setActiveSubTab] = useState('Find Advisors'); // 'Find Advisors' | 'My Invited Advisors'
  const [searchQuery, setSearchQuery] = useState('');
  const [expertiseFilter, setExpertiseFilter] = useState('All expertise');
  const [jurisdictionFilter, setJurisdictionFilter] = useState('All jurisdictions');
  const [availabilityFilter, setAvailabilityFilter] = useState('Any availability');
  const [activeCardId, setActiveCardId] = useState(null);
  const [toastMsg, setToastMsg] = useState(null);

  // Master Advisors List matching uploaded reference image
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
    },
  ]);

  const invitedCount = advisors.filter((a) => a.isInvited).length;

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

  const handleInviteClick = (advId) => {
    setAdvisors(
      advisors.map((a) => (a.id === advId ? { ...a, isInvited: !a.isInvited } : a))
    );
    const adv = advisors.find((a) => a.id === advId);
    if (adv) {
      const msg = adv.isInvited
        ? `Invitation cancelled for ${adv.name}`
        : `Invitation sent to ${adv.name}!`;
      setToastMsg(msg);
      setTimeout(() => setToastMsg(null), 3000);
      if (onInviteAdvisor) onInviteAdvisor(adv);
    }
  };

  const handleProfileClick = (adv) => {
    setToastMsg(`Opening profile for ${adv.name}...`);
    setTimeout(() => setToastMsg(null), 2500);
  };

  return (
    <div className="space-y-6 animate-fadeIn text-left">
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

      {/* Advisor Cards Grid (3 cards per row on large screen) */}
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
                  className="px-4 py-2 rounded-xl text-xs font-bold border border-slate-300 dark:border-slate-700/80 bg-stone-50 dark:bg-slate-800/60 hover:bg-stone-100 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 transition-colors cursor-pointer"
                >
                  View profile
                </button>

                {adv.isInvited ? (
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleInviteClick(adv.id);
                    }}
                    className="px-4 py-2 rounded-xl text-xs font-bold border border-slate-300 dark:border-slate-700 bg-stone-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 transition-colors cursor-pointer"
                  >
                    Invited
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleInviteClick(adv.id);
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
    </div>
  );
}
