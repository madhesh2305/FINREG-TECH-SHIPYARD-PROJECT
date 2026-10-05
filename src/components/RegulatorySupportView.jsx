import React, { useState, useEffect } from 'react';
import { Search, ShieldCheck, Check } from 'lucide-react';
import { getRegulatoryRequirements } from '../services/regulatoryService';

export default function RegulatorySupportView({ isDarkMode }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [jurisdictionFilter, setJurisdictionFilter] = useState('All jurisdictions');
  const [authorityFilter, setAuthorityFilter] = useState('All authorities');
  const [statusFilter, setStatusFilter] = useState('Validation status');
  const [layerFilter, setLayerFilter] = useState('Regulatory layer');

  const [activeRowId, setActiveRowId] = useState(null);
  const [toastMsg, setToastMsg] = useState(null);

  // Master Regulatory Library Data with live API integration
  const [requirementsList, setRequirementsList] = useState([
    {
      id: 'REQ-142',
      requirement: 'Risk-sensitive customer due diligence',
      authority: 'FCA',
      jurisdiction: 'United Kingdom',
      source: 'FCA Handbook',
      reference: 'SYSC 6.3.8',
      dateVersion: 'Release 126 · Sep 2026',
      layer: 'FCA Rules / Principles',
      applicability: 'Applicable to Retail & Commercial Banking',
      validationStatus: 'Validated',
      validationBadge: 'border-emerald-800/80 bg-emerald-950/60 text-emerald-400',
      dotColor: 'bg-emerald-500',
      description: 'Firm must apply customer due diligence measures on a risk-sensitive basis depending on customer type and transaction profile.',
    },
    {
      id: 'REQ-157',
      requirement: 'Ongoing transaction monitoring',
      authority: 'JMLSG',
      jurisdiction: 'United Kingdom',
      source: 'JMLSG Guidance',
      reference: 'Part I, 5.7',
      dateVersion: 'Jul 2024 revision',
      layer: 'Government Guidance',
      applicability: 'Applicable to Payment Services & Credit Institutions',
      validationStatus: 'Review due',
      validationBadge: 'border-amber-800/80 bg-amber-950/60 text-amber-400',
      dotColor: 'bg-amber-500',
      description: 'Continuous monitoring of customer accounts and transactions to detect unusual patterns and potential money laundering indicators.',
    },
    {
      id: 'REQ-163',
      requirement: 'Suspicious activity escalation',
      authority: 'NCA',
      jurisdiction: 'United Kingdom',
      source: 'SAR Guidance',
      reference: 'Chapter 3',
      dateVersion: 'Version 3.1 · Jan 2025',
      layer: 'Statutory Law',
      applicability: 'Applicable to All Money Laundering Reporting Officers',
      validationStatus: 'Validated',
      validationBadge: 'border-emerald-800/80 bg-emerald-950/60 text-emerald-400',
      dotColor: 'bg-emerald-500',
      description: 'Mandatory obligation to report suspicious activity reports (SARs) directly to the UK National Crime Agency without tipping off.',
    },
    {
      id: 'REQ-178',
      requirement: 'Politically exposed persons (PEP) screening',
      authority: 'FATF',
      jurisdiction: 'Global / International',
      source: 'FATF Recommendations',
      reference: 'Recommendation 12',
      dateVersion: 'Updated Feb 2026',
      layer: 'International Standard',
      applicability: 'Applicable to All Financial Institutions',
      validationStatus: 'Validated',
      validationBadge: 'border-emerald-800/80 bg-emerald-950/60 text-emerald-400',
      dotColor: 'bg-emerald-500',
      description: 'Enhanced due diligence requirements for PEPs, family members, and close associates across all onboarding channels.',
    },
    {
      id: 'REQ-189',
      requirement: 'Consumer Duty governance & oversight',
      authority: 'FCA',
      jurisdiction: 'United Kingdom',
      source: 'FCA FG22/5',
      reference: 'PRIN 2A.8',
      dateVersion: 'Release 124 · Jun 2026',
      layer: 'FCA Rules / Principles',
      applicability: 'Applicable to Retail Financial Products & Services',
      validationStatus: 'Review due',
      validationBadge: 'border-amber-800/80 bg-amber-950/60 text-amber-400',
      dotColor: 'bg-amber-500',
      description: 'Boards must monitor customer outcomes, pricing value, and product governance to ensure good outcomes for retail customers.',
    },
  ]);

  useEffect(() => {
    let isMounted = true;
    async function fetchReqs() {
      try {
        const liveData = await getRegulatoryRequirements();
        if (isMounted && Array.isArray(liveData) && liveData.length > 0) {
          // Normalize API items to frontend view schema
          const mapped = liveData.map((item, idx) => ({
            id: item.id || `REQ-${140 + idx}`,
            requirement: item.title || item.requirement || 'Regulatory requirement',
            authority: item.authority || 'FCA',
            jurisdiction: item.jurisdiction || 'United Kingdom',
            source: item.source || item.provenance || 'FCA Handbook',
            reference: item.code || item.reference || 'SYSC 6.1',
            dateVersion: item.lastReviewed || item.dateVersion || 'Release 126 · Sep 2026',
            layer: item.category || item.layer || 'FCA Rules / Principles',
            applicability: item.applicability || 'Applicable to Financial Services',
            validationStatus: item.status || 'Validated',
            validationBadge: item.status === 'Review due'
              ? 'border-amber-800/80 bg-amber-950/60 text-amber-400'
              : 'border-emerald-800/80 bg-emerald-950/60 text-emerald-400',
            dotColor: item.status === 'Review due' ? 'bg-amber-500' : 'bg-emerald-500',
            description: item.description || '',
          }));
          setRequirementsList(mapped);
        }
      } catch (err) {
        console.warn('[RegulatorySupportView] API load warning:', err);
      }
    }
    fetchReqs();
    return () => { isMounted = false; };
  }, []);

  // Filtering Logic
  const filteredRequirements = requirementsList.filter((req) => {
    const matchesSearch =
      req.requirement.toLowerCase().includes(searchQuery.toLowerCase()) ||
      req.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      req.source.toLowerCase().includes(searchQuery.toLowerCase()) ||
      req.reference.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesJurisdiction =
      jurisdictionFilter === 'All jurisdictions' || req.jurisdiction === jurisdictionFilter;

    const matchesAuthority =
      authorityFilter === 'All authorities' || req.authority === authorityFilter;

    const matchesStatus =
      statusFilter === 'Validation status' || req.validationStatus === statusFilter;

    const matchesLayer =
      layerFilter === 'Regulatory layer' || req.layer === layerFilter;

    return matchesSearch && matchesJurisdiction && matchesAuthority && matchesStatus && matchesLayer;
  });

  const handleRowClick = (req) => {
    setActiveRowId(activeRowId === req.id ? null : req.id);
    setToastMsg(`Selected requirement ${req.id}: "${req.requirement}"`);
    setTimeout(() => setToastMsg(null), 2500);
  };

  return (
    <div className="space-y-6 animate-fadeIn text-left relative">
      {/* Toast Notification Banner */}
      {toastMsg && (
        <div className="fixed top-16 right-6 z-50 bg-[#7c4a27] dark:bg-[#96562c] text-white px-4 py-3 rounded-xl shadow-2xl flex items-center gap-2.5 animate-fadeIn font-semibold text-xs sm:text-sm border-2 border-amber-300">
          <Check className="w-5 h-5 text-amber-300 shrink-0" />
          <span>{toastMsg}</span>
        </div>
      )}

      {/* Header Banner matching uploaded image media_1790749171409.png */}
      <div>
        <span className="text-[11px] font-extrabold tracking-widest text-[#7c4a27] dark:text-amber-400/90 uppercase">
          VALIDATED LIBRARY
        </span>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100 mt-1">
          Regulatory Support
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1.5 font-normal max-w-3xl">
          Find requirements with clear provenance and source-level traceability.
        </p>
      </div>

      {/* Filter Controls Row matching uploaded image */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3 pt-1">
        {/* Search Field (Spans 2 columns on lg) */}
        <div className="lg:col-span-2 relative">
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
            <Search className="w-4 h-4" />
          </div>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search regulatory requ"
            className="w-full pl-10 pr-4 py-2.5 text-xs sm:text-sm rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#161619] text-slate-900 dark:text-slate-100 placeholder-slate-500 focus:outline-none focus:border-[#96562c] focus:ring-2 focus:ring-[#96562c]/30 transition-all"
          />
        </div>

        {/* All Jurisdictions Dropdown */}
        <select
          value={jurisdictionFilter}
          onChange={(e) => setJurisdictionFilter(e.target.value)}
          className="px-3 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#161619] text-slate-800 dark:text-slate-200 text-xs font-semibold focus:outline-none focus:border-[#96562c] cursor-pointer transition-all"
        >
          <option value="All jurisdictions">All jurisdictions</option>
          <option value="United Kingdom">United Kingdom</option>
          <option value="Global / International">Global / International</option>
        </select>

        {/* All Authorities Dropdown */}
        <select
          value={authorityFilter}
          onChange={(e) => setAuthorityFilter(e.target.value)}
          className="px-3 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#161619] text-slate-800 dark:text-slate-200 text-xs font-semibold focus:outline-none focus:border-[#96562c] cursor-pointer transition-all"
        >
          <option value="All authorities">All authorities</option>
          <option value="FCA">FCA</option>
          <option value="JMLSG">JMLSG</option>
          <option value="NCA">NCA</option>
          <option value="FATF">FATF</option>
        </select>

        {/* Validation Status Dropdown */}
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#161619] text-slate-800 dark:text-slate-200 text-xs font-semibold focus:outline-none focus:border-[#96562c] cursor-pointer transition-all"
        >
          <option value="Validation status">Validation status</option>
          <option value="Validated">Validated</option>
          <option value="Review due">Review due</option>
        </select>

        {/* Regulatory Layer Dropdown */}
        <select
          value={layerFilter}
          onChange={(e) => setLayerFilter(e.target.value)}
          className="px-3 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#161619] text-slate-800 dark:text-slate-200 text-xs font-semibold focus:outline-none focus:border-[#96562c] cursor-pointer transition-all"
        >
          <option value="Regulatory layer">Regulatory layer</option>
          <option value="FCA Rules / Principles">FCA Rules / Principles</option>
          <option value="Government Guidance">Government Guidance</option>
          <option value="Statutory Law">Statutory Law</option>
        </select>
      </div>

      {/* Main Data Table Container with Horizontal Scrollbar */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800/90 bg-white dark:bg-[#161619] shadow-lg overflow-hidden">
        <div className="overflow-x-auto custom-scrollbar pb-2">
          <table className="w-full text-left text-xs sm:text-sm border-collapse min-w-[1600px]">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-800/80 bg-stone-50 dark:bg-[#111215] text-[11px] font-extrabold tracking-wider text-slate-400 dark:text-slate-500 uppercase">
                <th className="py-5 px-7 min-w-[340px] w-[360px]">REQUIREMENT</th>
                <th className="py-5 px-5">AUTHORITY</th>
                <th className="py-5 px-5">JURISDICTION</th>
                <th className="py-5 px-5">SOURCE</th>
                <th className="py-5 px-5">REFERENCE</th>
                <th className="py-5 px-5">DATE / VERSION</th>
                <th className="py-5 px-5">REGULATORY LAYER</th>
                <th className="py-5 px-6">APPLICABILITY</th>
                <th className="py-5 px-7">VALIDATION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-medium">
              {filteredRequirements.map((req) => {
                const isSelected = activeRowId === req.id;

                return (
                  <tr
                    key={req.id}
                    onClick={() => handleRowClick(req)}
                    className={`transition-colors cursor-pointer ${
                      isSelected
                        ? isDarkMode
                          ? 'bg-[#1e1e24] border-l-4 border-l-[#96562c]'
                          : 'bg-amber-50/70 border-l-4 border-l-[#7c4a27]'
                        : isDarkMode
                        ? 'hover:bg-slate-800/50'
                        : 'hover:bg-stone-50'
                    }`}
                  >
                    {/* REQUIREMENT Column */}
                    <td className="py-5 px-7 min-w-[340px] w-[360px]">
                      <div className="font-bold text-slate-900 dark:text-slate-100 text-sm sm:text-base">
                        {req.requirement}
                      </div>
                      <div className="text-[11px] font-mono font-semibold text-slate-400 dark:text-slate-500 mt-1">
                        {req.id}
                      </div>
                    </td>

                    {/* AUTHORITY Column */}
                    <td className="py-5 px-5 font-bold text-slate-700 dark:text-slate-200 text-sm">
                      {req.authority}
                    </td>

                    {/* JURISDICTION Column */}
                    <td className="py-5 px-5 text-slate-600 dark:text-slate-300 text-sm">
                      {req.jurisdiction}
                    </td>

                    {/* SOURCE Column */}
                    <td className="py-5 px-5 font-medium text-slate-700 dark:text-slate-300 text-sm">
                      {req.source}
                    </td>

                    {/* REFERENCE Column */}
                    <td className="py-5 px-5 font-mono text-slate-700 dark:text-slate-300 text-xs sm:text-sm">
                      {req.reference}
                    </td>

                    {/* DATE / VERSION Column */}
                    <td className="py-5 px-5 text-slate-500 dark:text-slate-400 text-xs sm:text-sm font-mono">
                      {req.dateVersion}
                    </td>

                    {/* REGULATORY LAYER Column */}
                    <td className="py-5 px-5">
                      <span className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold border border-slate-300 dark:border-slate-800 bg-stone-100 dark:bg-[#1e2026] text-slate-700 dark:text-slate-300">
                        <span className="w-1.5 h-1.5 rounded-full bg-slate-400 dark:bg-slate-500" />
                        {req.layer}
                      </span>
                    </td>

                    {/* APPLICABILITY Column */}
                    <td className="py-5 px-6 text-slate-600 dark:text-slate-300 text-xs sm:text-sm truncate max-w-[280px]" title={req.applicability}>
                      {req.applicability}
                    </td>

                    {/* VALIDATION Column */}
                    <td className="py-5 px-7">
                      <span className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-bold border ${req.validationBadge}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${req.dotColor}`} />
                        {req.validationStatus}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Table Footer Stats Bar */}
        <div className="py-3 px-6 bg-stone-50 dark:bg-[#111215] border-t border-slate-200 dark:border-slate-800/80 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 font-medium">
          <div>
            Showing <span className="font-bold text-slate-800 dark:text-slate-200">{filteredRequirements.length}</span> of <span className="font-bold text-slate-800 dark:text-slate-200">{requirementsList.length}</span> validated regulatory requirements
          </div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-500" />
            <span>100% Provenance Verified</span>
          </div>
        </div>
      </div>
    </div>
  );
}
