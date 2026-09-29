import React, { useState } from 'react';
import { Search, UserPlus, Check } from 'lucide-react';

export default function AdvisorsExpertsView({ isDarkMode, onInviteAdvisor }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [expertiseFilter, setExpertiseFilter] = useState('All expertise');
  const [jurisdictionFilter, setJurisdictionFilter] = useState('All jurisdictions');
  const [availabilityFilter, setAvailabilityFilter] = useState('Any availability');
  const [activeCardId, setActiveCardId] = useState(null);
  const [toastMsg, setToastMsg] = useState(null);

  // Master Advisors List matching uploaded reference image
  const advisors = [
    {
      id: 'ADV-001',
      name: 'Dr. Maya Chen',
      avatar: 'MC',
      specialty: 'AML & Financial Crime',
      firm: 'Regulatory Advisory Group',
      jurisdiction: 'UK / EU',
      status: 'Available',
      statusColor: 'bg-emerald-950/70 text-emerald-400 border-emerald-800/80',
      dotColor: 'bg-emerald-500',
    },
    {
      id: 'ADV-002',
      name: 'Daniel Okafor',
      avatar: 'DO',
      specialty: 'Operational Resilience',
      firm: 'Independent',
      jurisdiction: 'UK',
      status: 'Available',
      statusColor: 'bg-emerald-950/70 text-emerald-400 border-emerald-800/80',
      dotColor: 'bg-emerald-500',
    },
    {
      id: 'ADV-003',
      name: 'Sofia Alvarez',
      avatar: 'SA',
      specialty: 'Data Privacy & AI',
      firm: 'TrustWorks Legal',
      jurisdiction: 'EU / US',
      status: 'Limited',
      statusColor: 'bg-amber-950/70 text-amber-400 border-amber-800/80',
      dotColor: 'bg-amber-500',
    },
    {
      id: 'ADV-004',
      name: 'Alexander Petrov',
      avatar: 'AP',
      specialty: 'Regulatory Reporting',
      firm: 'Global Compliance Advisory',
      jurisdiction: 'Global / EBA',
      status: 'Available',
      statusColor: 'bg-emerald-950/70 text-emerald-400 border-emerald-800/80',
      dotColor: 'bg-emerald-500',
    },
  ];

  // Filtering Logic
  const filteredAdvisors = advisors.filter((adv) => {
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

  const handleInviteClick = (adv) => {
    setToastMsg(`Invitation sent to ${adv.name}!`);
    setTimeout(() => setToastMsg(null), 3000);
    if (onInviteAdvisor) onInviteAdvisor(adv);
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

      {/* Top Header Banner matching uploaded image */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <span className="text-[11px] font-extrabold tracking-widest text-[#7c4a27] dark:text-amber-400 uppercase">
            TRUSTED NETWORK
          </span>
          <h1 className="text-3xl sm:text-4xl font-black tracking-tight text-slate-100 mt-1">
            Advisors &amp; Experts
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1.5 font-normal max-w-xl">
            Find verified specialists and invite them into a controlled project role.
          </p>
        </div>

        {/* Invite Advisor Button */}
        <button
          type="button"
          onClick={() => {
            setToastMsg('Opening Invite Advisor Modal...');
            setTimeout(() => setToastMsg(null), 2500);
          }}
          className="px-5 py-3 rounded-xl bg-[#f59e0b] hover:bg-[#d97706] text-slate-950 font-extrabold text-xs sm:text-sm shadow-md flex items-center justify-center gap-2 transition-all duration-300 cursor-pointer border-2 border-amber-200/50 hover:scale-[1.03]"
        >
          <UserPlus className="w-4 h-4 stroke-[2.5]" />
          <span>Invite advisor</span>
        </button>
      </div>

      {/* Filter Controls Row matching uploaded image */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5 pt-2">
        {/* Search Field */}
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
            <Search className="w-4 h-4" />
          </div>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search advisors or expertise"
            className="w-full pl-10 pr-4 py-2.5 text-xs sm:text-sm rounded-xl border border-slate-800 bg-[#161619] text-slate-100 placeholder-slate-500 focus:outline-none focus:border-[#96562c] focus:ring-2 focus:ring-[#96562c]/30 transition-all"
          />
        </div>

        {/* Expertise Dropdown */}
        <select
          value={expertiseFilter}
          onChange={(e) => setExpertiseFilter(e.target.value)}
          className="px-3 py-2.5 rounded-xl border border-slate-800 bg-[#161619] text-slate-200 text-xs sm:text-sm font-semibold focus:outline-none focus:border-[#96562c] cursor-pointer transition-all"
        >
          <option value="All expertise">All expertise</option>
          <option value="AML & Financial Crime">AML &amp; Financial Crime</option>
          <option value="Operational Resilience">Operational Resilience</option>
          <option value="Data Privacy & AI">Data Privacy &amp; AI</option>
          <option value="Regulatory Reporting">Regulatory Reporting</option>
        </select>

        {/* Jurisdiction Dropdown */}
        <select
          value={jurisdictionFilter}
          onChange={(e) => setJurisdictionFilter(e.target.value)}
          className="px-3 py-2.5 rounded-xl border border-slate-800 bg-[#161619] text-slate-200 text-xs sm:text-sm font-semibold focus:outline-none focus:border-[#96562c] cursor-pointer transition-all"
        >
          <option value="All jurisdictions">All jurisdictions</option>
          <option value="UK">UK</option>
          <option value="EU">EU</option>
          <option value="US">US</option>
          <option value="Global">Global</option>
        </select>

        {/* Availability Dropdown */}
        <select
          value={availabilityFilter}
          onChange={(e) => setAvailabilityFilter(e.target.value)}
          className="px-3 py-2.5 rounded-xl border border-slate-800 bg-[#161619] text-slate-200 text-xs sm:text-sm font-semibold focus:outline-none focus:border-[#96562c] cursor-pointer transition-all"
        >
          <option value="Any availability">Any availability</option>
          <option value="Available">Available</option>
          <option value="Limited">Limited</option>
        </select>
      </div>

      {/* Advisor Cards Grid (3 cards per row on large screens) */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 pt-2">
        {filteredAdvisors.map((adv) => {
          const isActive = activeCardId === adv.id;

          return (
            <div
              key={adv.id}
              onClick={() => setActiveCardId(isActive ? null : adv.id)}
              title="Click box to toggle brown border, cream edge lighting glow & zoom-in"
              className={`rounded-2xl border p-6 flex flex-col justify-between transition-all duration-300 cursor-pointer ${
                isActive
                  ? 'bg-[#1e1e24] border-[#96562c] scale-[1.02] shadow-[0_0_35px_rgba(251,191,36,0.25),0_12px_36px_rgba(150,86,44,0.35)] ring-2 ring-[#96562c]/40'
                  : 'bg-[#1a1a1e] border-slate-800/90 shadow-md hover:border-[#96562c] hover:scale-[1.01]'
              }`}
            >
              <div>
                {/* Header Row: Avatar Badge & Status Pill */}
                <div className="flex items-center justify-between mb-5">
                  <div className="w-9 h-9 rounded-lg bg-[#96562c]/30 text-amber-300 border border-[#96562c]/50 font-bold text-xs flex items-center justify-center">
                    {adv.avatar}
                  </div>
                  <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border ${adv.statusColor}`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${adv.dotColor}`} />
                    {adv.status}
                  </span>
                </div>

                {/* Advisor Details */}
                <h3 className="text-xl font-bold text-slate-100 tracking-tight">
                  {adv.name}
                </h3>
                <p className="text-sm font-semibold text-slate-300 mt-1">
                  {adv.specialty}
                </p>
                <p className="text-xs text-slate-400 mt-0.5 font-medium">
                  {adv.firm}
                </p>

                {/* Jurisdiction */}
                <p className="text-xs text-slate-500 font-mono mt-4">
                  {adv.jurisdiction}
                </p>
              </div>

              {/* Action Buttons Row */}
              <div className="flex items-center justify-between gap-3 pt-6 mt-6 border-t border-slate-800/80">
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleProfileClick(adv);
                  }}
                  className="px-4 py-2 rounded-xl text-xs sm:text-sm font-bold border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-200 transition-colors cursor-pointer"
                >
                  View profile
                </button>

                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleInviteClick(adv);
                  }}
                  className="px-5 py-2 rounded-xl text-xs sm:text-sm font-extrabold bg-[#f59e0b] hover:bg-[#d97706] text-slate-950 shadow-md transition-all cursor-pointer border border-amber-300/60 hover:scale-[1.03]"
                >
                  Invite
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
