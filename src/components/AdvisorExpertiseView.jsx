import React, { useState } from 'react';
import { FileText, Shield, Key, Folder, Users, ArrowRight, Check } from 'lucide-react';
import Navbar from './Navbar';

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
    icon: Key,
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
  initialSelectedId = null,
}) {
  const [selectedId, setSelectedId] = useState(initialSelectedId || 'legal-partner');

  const selectedProfile =
    ADVISOR_PROFILES.find((p) => p.id === selectedId) || ADVISOR_PROFILES[0];

  const handleCardClick = (profile) => {
    setSelectedId(profile.id);
  };

  const handleSelectPillClick = (e, profile) => {
    e.stopPropagation();
    if (selectedId === profile.id) {
      // If user clicks on already selected button, proceed to dashboard
      if (onSelectExpertise) onSelectExpertise(profile);
    } else {
      setSelectedId(profile.id);
    }
  };

  const handleContinue = () => {
    if (onSelectExpertise && selectedProfile) {
      onSelectExpertise(selectedProfile);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#0b0c0e] text-slate-100 font-sans">
      {/* Top Navbar */}
      <Navbar />

      {/* Main Container matching media_1791950620810_ec218efe.png */}
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

            {/* Selected Counter Pill */}
            <div className="self-start md:self-auto pt-1">
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-[#221c14] border border-amber-900/60 text-amber-400">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                <span>{selectedId ? '1 selected' : '0 selected'}</span>
              </div>
            </div>
          </div>

          {/* 5 Tools / Expertise Profile Cards Grid matching exact styling in media_1791950620810_ec218efe.png */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 pt-2">
            {ADVISOR_PROFILES.map((profile) => {
              const Icon = profile.icon;
              const isSelected = selectedId === profile.id;

              return (
                <div
                  key={profile.id}
                  onClick={() => handleCardClick(profile)}
                  onDoubleClick={() => {
                    setSelectedId(profile.id);
                    if (onSelectExpertise) onSelectExpertise(profile);
                  }}
                  className={`rounded-2xl p-6 flex flex-col justify-between transition-all duration-200 cursor-pointer group min-h-[195px] ${
                    isSelected
                      ? 'bg-[#2e2414] border border-[#a37b34]'
                      : 'bg-[#181b20] border border-[#2b2e35] hover:border-slate-700'
                  }`}
                >
                  <div>
                    {/* Top Icon Badge */}
                    <div
                      className={`w-9 h-9 rounded-lg flex items-center justify-center mb-5 border transition-colors ${
                        isSelected
                          ? 'border-[#a37b34] bg-[#2e2414] text-[#c58d31]'
                          : 'border-[#8f6a2b] bg-[#181b20] text-[#c58d31]'
                      }`}
                    >
                      <Icon className="w-4 h-4 stroke-[2.2]" />
                    </div>

                    {/* Profile Title */}
                    <h3
                      className={`text-base sm:text-lg font-bold tracking-tight transition-colors ${
                        isSelected ? 'text-[#c58d31]' : 'text-white group-hover:text-amber-100'
                      }`}
                    >
                      {profile.name}
                    </h3>

                    {/* Subtitle Description */}
                    <p
                      className={`text-xs sm:text-sm mt-1.5 font-normal leading-relaxed ${
                        isSelected ? 'text-[#9ca3af]' : 'text-slate-400'
                      }`}
                    >
                      {profile.subtitle}
                    </p>
                  </div>

                  {/* Select / Selected Pill Button matching screenshot */}
                  <div className="pt-6">
                    <button
                      type="button"
                      onClick={(e) => handleSelectPillClick(e, profile)}
                      className={`inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs transition-all cursor-pointer ${
                        isSelected
                          ? 'bg-[#2e2414] border border-[#a37b34] text-[#c58d31] font-semibold hover:brightness-110'
                          : 'bg-[#181b20] border border-slate-700/80 text-slate-300 font-medium hover:border-slate-600 hover:text-white'
                      }`}
                    >
                      <span
                        className={`w-1.5 h-1.5 rounded-full ${
                          isSelected ? 'bg-[#c58d31]' : 'bg-slate-500'
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

        {/* Bottom Section */}
        <div className="border-t border-slate-800/80 pt-6 mt-12 flex flex-col sm:flex-row sm:items-center justify-between gap-6 text-left">
          <p className="text-xs sm:text-sm text-slate-400 max-w-2xl font-normal leading-relaxed">
            Project membership and permissions are managed separately by the inviting Builder and
            platform access controls.
          </p>

          <button
            type="button"
            onClick={handleContinue}
            className="px-6 py-3 rounded-md bg-[#e59b3c] hover:bg-[#d68a2b] active:scale-[0.99] text-slate-950 font-bold text-sm shadow-md transition-all cursor-pointer shrink-0"
          >
            Continue to Advisor Dashboard
          </button>
        </div>
      </main>
    </div>
  );
}
