import React, { useState } from 'react';
import { FileText, Shield, Wrench, Folder, Users } from 'lucide-react';

export const ADVISOR_PROFILES = [
  {
    id: 'legal-partner',
    name: 'Legal Partner',
    cleanDomain: 'Financial Crime Compliance',
    subtitle: 'Legal guidance and contractual considerations.',
    icon: FileText,
    domain: 'Legal Partner · Financial Crime Compliance',
    nextAction: 'Review legal requirements',
    workspaceText: 'Projects permitted for the active Legal Partner workspace.',
    projectStatus: 'In Progress',
    dueDate: 'DUE 24 SEP',
  },
  {
    id: 'regulatory-compliance',
    name: 'Regulatory Compliance Expert',
    cleanDomain: 'AML / KYC Obligations',
    subtitle: 'Regulatory requirements, compliance, and obligations.',
    icon: Shield,
    domain: 'Regulatory Compliance Expert · AML / KYC Obligations',
    nextAction: 'Validate regulatory requirements',
    workspaceText: 'Projects permitted for the active Regulatory Compliance Expert workspace.',
    projectStatus: 'In Progress',
    dueDate: 'DUE 26 SEP',
  },
  {
    id: 'tech-expert',
    name: 'Tech Expert',
    cleanDomain: 'Security & Architecture',
    subtitle: 'Technical implementation, architecture, and integration guidance.',
    icon: Wrench,
    domain: 'Tech Expert · Security & Architecture',
    nextAction: 'Review technical implementation',
    workspaceText: 'Projects permitted for the active Tech Expert workspace.',
    projectStatus: 'In Progress',
    dueDate: 'DUE 28 SEP',
  },
  {
    id: 'funding-business',
    name: 'Funding / Business Support',
    cleanDomain: 'Capital & Commercial Strategy',
    subtitle: 'Funding opportunities, business planning, and financial support guidance.',
    icon: Folder,
    domain: 'Funding / Business Support · Capital & Commercial Strategy',
    nextAction: 'Review business planning model',
    workspaceText: 'Projects permitted for the active Funding / Business Support workspace.',
    projectStatus: 'In Progress',
    dueDate: 'DUE 30 SEP',
  },
  {
    id: 'marketing-service',
    name: 'Marketing Service',
    cleanDomain: 'Compliance Marketing & Comms',
    subtitle: 'Marketing strategy and go-to-market suggestions.',
    icon: Users,
    domain: 'Marketing Service · Compliance Marketing & Comms',
    nextAction: 'Review go-to-market strategy',
    workspaceText: 'Projects permitted for the active Marketing Service workspace.',
    projectStatus: 'In Progress',
    dueDate: 'DUE 02 OCT',
  },
];

export default function AdvisorExpertiseView({
  isDarkMode = true,
  onSelectExpertise,
  onBackToLogin,
  initialSelectedId = null,
}) {
  const [selectedIds, setSelectedIds] = useState(
    initialSelectedId ? [initialSelectedId] : []
  );

  const handleCardClick = (profile) => {
    setSelectedIds((prev) => {
      if (prev.includes(profile.id)) {
        return prev.filter((id) => id !== profile.id);
      } else {
        return [...prev, profile.id];
      }
    });
  };

  const handleSelectPillClick = (e, profile) => {
    e.stopPropagation();
    handleCardClick(profile);
  };

  const handleContinue = () => {
    const selectedProfile =
      ADVISOR_PROFILES.find((p) => selectedIds.includes(p.id)) ||
      ADVISOR_PROFILES[0];
    if (onSelectExpertise) {
      onSelectExpertise(selectedProfile);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#08090b] text-slate-100 font-sans relative selection:bg-amber-500/30">
      {/* Top Navbar matching media_1793976544662_719bd4c5.png */}
      <header className="w-full border-b border-slate-800/80 bg-[#090a0d] text-slate-100 px-6 py-4 flex items-center justify-between sticky top-0 z-50">
        {/* Left Branding */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg border border-amber-600/70 bg-[#1e170e] flex items-center justify-center font-black text-amber-500 text-lg font-serif shadow-sm">
            F
          </div>
          <div className="flex flex-col text-left">
            <span className="font-extrabold text-white text-base tracking-tight leading-tight">FinRegTech</span>
            <span className="font-mono text-[9px] font-bold text-amber-500 uppercase tracking-widest leading-none">SHIPYARD</span>
          </div>
        </div>

        {/* Center: ADVISOR PROFILE SETUP / Choose expertise */}
        <div className="text-center hidden sm:block">
          <span className="text-[10px] font-mono font-bold tracking-widest text-slate-500 uppercase block">
            ADVISOR PROFILE SETUP
          </span>
          <span className="text-sm font-bold text-white block">
            Choose expertise
          </span>
        </div>

        {/* Right: Back to login */}
        <div>
          <button
            type="button"
            onClick={onBackToLogin || (() => window.location.reload())}
            className="text-xs sm:text-sm font-medium text-slate-400 hover:text-white transition-colors cursor-pointer"
          >
            Back to login
          </button>
        </div>
      </header>

      {/* Main Container matching media_1793976544662_719bd4c5.png & media_1793976670380_f03e0032.png */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-10 py-8 sm:py-12 flex flex-col justify-between">
        <div className="space-y-8 animate-fadeIn text-left">
          {/* Header Section */}
          <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
            <div>
              <span className="text-[11px] font-mono font-extrabold tracking-widest text-slate-500 uppercase block mb-2">
                WELCOME TO FINREGTECH SHIPYARD
              </span>
              <h1 className="text-3xl sm:text-4xl md:text-[40px] font-extrabold tracking-tight text-white leading-tight">
                Configure your Advisor expertise
              </h1>
              <p className="text-xs sm:text-sm text-slate-400 mt-2 max-w-2xl font-normal leading-relaxed">
                Choose one or more company-authorized expertise profiles. Expertise selection does
                not grant project access or privileged roles.
              </p>
            </div>

            {/* Selected Counter Pill matching media_1793976544662_719bd4c5.png (• 0 selected) */}
            <div className="self-start md:self-auto pt-1">
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-[#1a140a] border border-amber-600/50 text-amber-400 shadow-sm">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                <span>{selectedIds.length} selected</span>
              </div>
            </div>
          </div>

          {/* 5 Tools / Expertise Profile Cards Grid matching exact styling in Image 1 */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 pt-2">
            {ADVISOR_PROFILES.map((profile) => {
              const Icon = profile.icon;
              const isSelected = selectedIds.includes(profile.id);

              return (
                <div
                  key={profile.id}
                  onClick={() => handleCardClick(profile)}
                  className={`rounded-2xl p-6 flex flex-col justify-between transition-all duration-200 cursor-pointer group min-h-[200px] border ${
                    isSelected
                      ? 'bg-[#1e170e] border-amber-500/80 shadow-[0_0_20px_rgba(245,158,11,0.15)] ring-1 ring-amber-500/40'
                      : 'bg-[#12151c] border-[#222630] hover:border-slate-700 hover:bg-[#151922]'
                  }`}
                >
                  <div>
                    {/* Top Icon Badge */}
                    <div
                      className={`w-9 h-9 rounded-lg flex items-center justify-center mb-5 border transition-colors ${
                        isSelected
                          ? 'border-amber-500 bg-[#291e10] text-amber-400'
                          : 'border-amber-600/50 bg-[#1a140a] text-amber-400'
                      }`}
                    >
                      <Icon className="w-4 h-4 stroke-[2.2]" />
                    </div>

                    {/* Profile Title */}
                    <h3
                      className={`text-base sm:text-lg font-bold tracking-tight transition-colors ${
                        isSelected ? 'text-amber-300' : 'text-white group-hover:text-amber-100'
                      }`}
                    >
                      {profile.name}
                    </h3>

                    {/* Subtitle Description */}
                    <p
                      className={`text-xs sm:text-sm mt-1.5 font-normal leading-relaxed ${
                        isSelected ? 'text-slate-300' : 'text-slate-400'
                      }`}
                    >
                      {profile.subtitle}
                    </p>
                  </div>

                  {/* Select / Selected Pill Button matching Image 1 */}
                  <div className="pt-6">
                    <button
                      type="button"
                      onClick={(e) => handleSelectPillClick(e, profile)}
                      className={`inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs transition-all cursor-pointer ${
                        isSelected
                          ? 'bg-[#291e10] border border-amber-500 text-amber-300 font-semibold shadow-xs'
                          : 'bg-[#161a22] border border-slate-700/80 text-slate-300 font-medium hover:border-slate-500 hover:text-white'
                      }`}
                    >
                      <span
                        className={`w-1.5 h-1.5 rounded-full ${
                          isSelected ? 'bg-amber-400' : 'bg-slate-500'
                        }`}
                      />
                      <span>{isSelected ? 'Selected' : 'Select'}</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Bottom Section matching media_1793976670380_f03e0032.png */}
        <div className="border-t border-slate-800/80 pt-6 mt-12 flex flex-col sm:flex-row sm:items-center justify-between gap-6 text-left">
          <p className="text-xs sm:text-sm text-slate-400 max-w-2xl font-normal leading-relaxed">
            Project membership and permissions are managed separately by the inviting Builder and
            platform access controls.
          </p>

          <button
            type="button"
            onClick={handleContinue}
            className="px-6 py-3 rounded-lg bg-[#e59b3c] hover:bg-[#d68a2b] active:scale-[0.99] text-slate-950 font-bold text-sm shadow-md transition-all cursor-pointer shrink-0"
          >
            Continue to Advisor Dashboard
          </button>
        </div>
      </main>

      {/* Floating Help Button (?) in bottom right corner matching media_1793976670380_f03e0032.png */}
      <button
        type="button"
        aria-label="Help"
        onClick={() => alert('FinRegTech ShipYard: Select one or more advisor expertise domains to access your permitted project workspace.')}
        className="fixed bottom-6 right-6 w-8 h-8 rounded-full bg-white hover:bg-slate-100 text-slate-950 font-bold flex items-center justify-center text-sm shadow-2xl transition-all cursor-pointer z-50"
      >
        ?
      </button>
    </div>
  );
}
