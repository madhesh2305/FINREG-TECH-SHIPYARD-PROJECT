import React, { useState, useEffect } from 'react';
import { Search, ShieldCheck, Check, ArrowLeft, ArrowRight } from 'lucide-react';
import { getRegulatoryRequirements } from '../services/regulatoryService';

export default function RegulatorySupportView({ isDarkMode, initialRequirementId }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [jurisdictionFilter, setJurisdictionFilter] = useState('All jurisdictions');
  const [authorityFilter, setAuthorityFilter] = useState('All authorities');
  const [topicFilter, setTopicFilter] = useState('All topics');
  const [statusFilter, setStatusFilter] = useState('Validation status');
  const [layerFilter, setLayerFilter] = useState('Regulatory layer');

  const [activeRowId, setActiveRowId] = useState(null);
  const [toastMsg, setToastMsg] = useState(null);
  const [selectedRequirement, setSelectedRequirement] = useState(null);
  const [isSourceModalOpen, setIsSourceModalOpen] = useState(false);

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
      applicability: 'Applicable to all UK-authorised firms conducting customer onboarding',
      validationStatus: 'Validated',
      validationBadge: 'border-emerald-800/80 bg-emerald-950/60 text-emerald-400',
      dotColor: 'bg-emerald-500',
      description: 'Firms must establish and maintain effective systems and controls for compliance with applicable financial crime requirements.',
      officialSource: 'Linked source record available in prototype',
      notesLimitations: 'This prototype does not claim legal validation. Interpretation and final applicability require appropriate human review.',
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
      applicability: 'Applicable to UK financial services firms conducting ongoing customer activity',
      validationStatus: 'Review due',
      validationBadge: 'border-amber-800/80 bg-amber-950/60 text-amber-400',
      dotColor: 'bg-amber-500',
      description: 'Continuous monitoring of customer accounts and transactions to detect unusual patterns and potential money laundering indicators.',
      officialSource: 'Linked source record available in prototype',
      notesLimitations: 'This prototype does not claim legal validation. Interpretation and final applicability require appropriate human review.',
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
      applicability: 'Applicable to all UK-based firms subject to the Money Laundering Regulations',
      validationStatus: 'Validated',
      validationBadge: 'border-emerald-800/80 bg-emerald-950/60 text-emerald-400',
      dotColor: 'bg-emerald-500',
      description: 'Mandatory obligation to report suspicious activity reports (SARs) directly to the UK National Crime Agency without tipping off.',
      officialSource: 'Linked source record available in prototype',
      notesLimitations: 'This prototype does not claim legal validation. Interpretation and final applicability require appropriate human review.',
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
      officialSource: 'Linked source record available in prototype',
      notesLimitations: 'This prototype does not claim legal validation. Interpretation and final applicability require appropriate human review.',
      topic: 'PEP Screening',
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
      officialSource: 'Linked source record available in prototype',
      notesLimitations: 'This prototype does not claim legal validation. Interpretation and final applicability require appropriate human review.',
      topic: 'Consumer Duty',
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
            dateVersion: item.dateVersion || item.lastReviewed || 'Release 126 · Sep 2026',
            layer: item.category || item.layer || 'FCA Rules / Principles',
            applicability: item.applicability || 'Applicable to all UK-authorised firms conducting customer onboarding',
            validationStatus: item.validationStatus || item.status || 'Validated',
            validationBadge: (item.validationStatus === 'Review due' || item.status === 'Review due')
              ? 'border-amber-800/80 bg-amber-950/60 text-amber-400'
              : 'border-emerald-800/80 bg-emerald-950/60 text-emerald-400',
            dotColor: (item.validationStatus === 'Review due' || item.status === 'Review due') ? 'bg-amber-500' : 'bg-emerald-500',
            description: item.description || '',
            officialSource: item.officialSource || 'Linked source record available in prototype',
            notesLimitations: item.notesLimitations || 'This prototype does not claim legal validation. Interpretation and final applicability require appropriate human review.',
            topic: item.topic || 'General',
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

  useEffect(() => {
    if (initialRequirementId) {
      // Highlight the related requirement on the Regulatory Support screen and keep table view active
      setActiveRowId(initialRequirementId);
      setSelectedRequirement(null);
    }
  }, [initialRequirementId]);

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

    const matchesTopic =
      topicFilter === 'All topics' ||
      req.topic === topicFilter ||
      req.requirement.toLowerCase().includes(topicFilter.toLowerCase());

    const matchesStatus =
      statusFilter === 'Validation status' || req.validationStatus === statusFilter;

    const matchesLayer =
      layerFilter === 'Regulatory layer' || req.layer === layerFilter;

    return matchesSearch && matchesJurisdiction && matchesAuthority && matchesTopic && matchesStatus && matchesLayer;
  });

  const handleRowClick = (req) => {
    setActiveRowId(activeRowId === req.id ? null : req.id);
  };

  // If a requirement is selected (e.g., clicking "Review REQ-142"), render images 2 & 3 detail view
  if (selectedRequirement) {
    return (
      <div className="space-y-6 animate-fadeIn text-left relative">
        {/* Toast Notification Banner */}
        {toastMsg && (
          <div className="fixed top-16 right-6 z-50 bg-[#7c4a27] dark:bg-[#96562c] text-white px-4 py-3 rounded-xl shadow-2xl flex items-center gap-2.5 animate-fadeIn font-semibold text-xs sm:text-sm border-2 border-amber-300">
            <Check className="w-5 h-5 text-amber-300 shrink-0" />
            <span>{toastMsg}</span>
          </div>
        )}

        {/* Back navigation button */}
        <div className="pt-1">
          <button
            type="button"
            onClick={() => setSelectedRequirement(null)}
            className="inline-flex items-center gap-2 text-xs sm:text-sm font-semibold text-slate-400 hover:text-slate-100 transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Regulatory Requirements</span>
          </button>
        </div>

        {/* Header matching Image 2 */}
        <div className="space-y-1.5 pt-1">
          <div className="text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
            {selectedRequirement.id}
          </div>
          <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-slate-100 tracking-tight">
            {selectedRequirement.requirement}
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 font-normal max-w-4xl pt-1 leading-relaxed">
            {selectedRequirement.description ||
              'Firms must establish and maintain effective systems and controls for compliance with applicable financial crime requirements.'}
          </p>
        </div>

        {/* 2-Column Grid Layout matching Images 2 & 3 */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-3 items-start">
          {/* Left Column (lg:col-span-2): Requirement details */}
          <div className="lg:col-span-2 rounded-2xl border border-slate-800/90 bg-[#161619] p-6 sm:p-8 space-y-5 shadow-xl text-left">
            <h2 className="text-base sm:text-lg font-bold text-slate-100 pb-1">
              Requirement details
            </h2>

            {/* AUTHORITY */}
            <div className="border-b border-slate-800/80 pb-4">
              <div className="text-[10px] font-extrabold tracking-wider text-slate-500 uppercase">
                AUTHORITY
              </div>
              <div className="text-sm font-bold text-slate-200 mt-1">
                {selectedRequirement.authority}
              </div>
            </div>

            {/* JURISDICTION */}
            <div className="border-b border-slate-800/80 pb-4">
              <div className="text-[10px] font-extrabold tracking-wider text-slate-500 uppercase">
                JURISDICTION
              </div>
              <div className="text-sm font-semibold text-slate-200 mt-1">
                {selectedRequirement.jurisdiction}
              </div>
            </div>

            {/* SOURCE DOCUMENT */}
            <div className="border-b border-slate-800/80 pb-4">
              <div className="text-[10px] font-extrabold tracking-wider text-slate-500 uppercase">
                SOURCE DOCUMENT
              </div>
              <div className="text-sm font-semibold text-slate-200 mt-1">
                {selectedRequirement.source}
              </div>
            </div>

            {/* SECTION / REFERENCE */}
            <div className="border-b border-slate-800/80 pb-4">
              <div className="text-[10px] font-extrabold tracking-wider text-slate-500 uppercase">
                SECTION / REFERENCE
              </div>
              <div className="text-sm font-semibold text-slate-200 mt-1">
                {selectedRequirement.reference}
              </div>
            </div>

            {/* DATE / VERSION */}
            <div className="border-b border-slate-800/80 pb-4">
              <div className="text-[10px] font-extrabold tracking-wider text-slate-500 uppercase">
                DATE / VERSION
              </div>
              <div className="text-sm text-slate-200 mt-1">
                {selectedRequirement.dateVersion}
              </div>
            </div>

            {/* REGULATORY LAYER */}
            <div className="border-b border-slate-800/80 pb-4">
              <div className="text-[10px] font-extrabold tracking-wider text-slate-500 uppercase">
                REGULATORY LAYER
              </div>
              <div className="mt-2">
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-semibold border border-slate-700/80 bg-slate-800/40 text-slate-300 uppercase tracking-wider">
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
                  {selectedRequirement.layer}
                </span>
              </div>
            </div>

            {/* APPLICABILITY */}
            <div className="border-b border-slate-800/80 pb-4">
              <div className="text-[10px] font-extrabold tracking-wider text-slate-500 uppercase">
                APPLICABILITY
              </div>
              <div className="text-sm text-slate-200 mt-1">
                {selectedRequirement.applicability}
              </div>
            </div>

            {/* VALIDATION STATUS */}
            <div className="border-b border-slate-800/80 pb-4">
              <div className="text-[10px] font-extrabold tracking-wider text-slate-500 uppercase">
                VALIDATION STATUS
              </div>
              <div className="mt-2">
                <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold border ${selectedRequirement.validationBadge || 'border-emerald-800/80 bg-emerald-950/60 text-emerald-400'} uppercase tracking-wider`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${selectedRequirement.dotColor || 'bg-emerald-500'}`} />
                  {selectedRequirement.validationStatus}
                </span>
              </div>
            </div>

            {/* OFFICIAL SOURCE */}
            <div className="border-b border-slate-800/80 pb-4">
              <div className="text-[10px] font-extrabold tracking-wider text-slate-500 uppercase">
                OFFICIAL SOURCE
              </div>
              <div className="text-sm text-slate-200 mt-1">
                {selectedRequirement.officialSource || 'Linked source record available in prototype'}
              </div>
            </div>

            {/* NOTES / LIMITATIONS */}
            <div className="pt-1">
              <div className="text-[10px] font-extrabold tracking-wider text-slate-500 uppercase">
                NOTES / LIMITATIONS
              </div>
              <div className="text-sm text-slate-300 mt-1 leading-relaxed">
                {selectedRequirement.notesLimitations ||
                  'This prototype does not claim legal validation. Interpretation and final applicability require appropriate human review.'}
              </div>
            </div>
          </div>

          {/* Right Column (lg:col-span-1): SOURCE TRACEABILITY */}
          <div className="lg:col-span-1 rounded-2xl border border-slate-800/90 bg-[#161619] p-6 sm:p-8 flex flex-col justify-between shadow-xl text-left min-h-[460px]">
            <div>
              <div className="text-[10px] font-extrabold tracking-widest text-slate-500 uppercase">
                SOURCE TRACEABILITY
              </div>
              <h2 className="text-base sm:text-lg font-bold text-slate-100 mt-1 mb-6">
                Origin of this requirement
              </h2>

              {/* Connected Stepper matching Images 2 & 3 */}
              <div className="space-y-6 relative pl-1">
                {[
                  { step: 1, label: 'Requirement', value: selectedRequirement.requirement },
                  { step: 2, label: 'Source', value: selectedRequirement.source },
                  { step: 3, label: 'Authority', value: selectedRequirement.authority },
                  { step: 4, label: 'Document / section', value: selectedRequirement.reference },
                ].map((item, idx, arr) => (
                  <div key={item.step} className="relative flex items-start gap-4">
                    {idx < arr.length - 1 && (
                      <div className="absolute left-3.5 top-7 w-[1px] h-[calc(100%+14px)] bg-slate-700/80 pointer-events-none" />
                    )}
                    <div className="w-7 h-7 rounded-full border border-amber-500/80 text-amber-400 flex items-center justify-center text-xs font-bold shrink-0 bg-[#161619] z-10">
                      {item.step}
                    </div>
                    <div className="pt-0.5">
                      <div className="text-xs font-bold text-slate-200">{item.label}</div>
                      <div className="text-xs text-slate-400 mt-0.5">
                        {item.value}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Bottom Button matching Images 2 & 3 */}
            <div className="pt-8">
              <button
                type="button"
                onClick={() => setIsSourceModalOpen(true)}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-[#e6a13d] hover:bg-[#d8932f] text-slate-950 font-bold text-xs sm:text-sm shadow-md transition-all cursor-pointer"
              >
                <span>View source document</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Source Document Modal matching uploaded image media_1791736519874_38775e2b.png */}
        {isSourceModalOpen && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-xs animate-fadeIn"
            onClick={() => setIsSourceModalOpen(false)}
          >
            <div
              className="w-full max-w-xl rounded-2xl border border-slate-800 bg-[#161619] shadow-2xl overflow-hidden text-left animate-scaleIn"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Modal Header */}
              <div className="px-6 sm:px-8 py-5 border-b border-slate-800/90 flex items-center justify-between">
                <h3 className="text-xl font-bold text-slate-100">
                  Source Document
                </h3>
                <button
                  type="button"
                  onClick={() => setIsSourceModalOpen(false)}
                  className="text-xs sm:text-sm font-semibold text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
                >
                  Close
                </button>
              </div>

              {/* Modal Body */}
              <div className="px-6 sm:px-8 py-6 space-y-6">
                {/* Source Document Eyebrow, Section Title & Description */}
                <div>
                  <div className="text-xs font-semibold tracking-wider text-slate-400 uppercase">
                    {selectedRequirement.source || 'FCA Handbook'}
                  </div>
                  <h4 className="text-2xl font-bold text-slate-100 mt-2">
                    {selectedRequirement.reference || 'SYSC 6.3.8'}
                  </h4>
                  <p className="text-xs sm:text-sm text-slate-400 mt-3.5 leading-relaxed font-normal">
                    Official source maintained by {selectedRequirement.authority || 'FCA'}. This prototype record links the interpreted requirement to its authoritative document and section.
                  </p>
                </div>

                {/* VERSION */}
                <div className="border-b border-slate-800/80 pb-4">
                  <div className="text-[10px] font-extrabold tracking-wider text-slate-500 uppercase">
                    VERSION
                  </div>
                  <div className="text-sm font-bold text-slate-200 mt-1">
                    {selectedRequirement.dateVersion || 'Release 126 · Sep 2026'}
                  </div>
                </div>

                {/* JURISDICTION */}
                <div className="border-b border-slate-800/80 pb-4">
                  <div className="text-[10px] font-extrabold tracking-wider text-slate-500 uppercase">
                    JURISDICTION
                  </div>
                  <div className="text-sm font-semibold text-slate-200 mt-1">
                    {selectedRequirement.jurisdiction || 'United Kingdom'}
                  </div>
                </div>

                {/* TRACEABILITY STATUS */}
                <div className="pb-2">
                  <div className="text-[10px] font-extrabold tracking-wider text-slate-500 uppercase">
                    TRACEABILITY STATUS
                  </div>
                  <div className="mt-2.5">
                    <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-[11px] font-bold border border-emerald-800/80 bg-emerald-950/60 text-emerald-400 uppercase tracking-wider">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                      <span>SOURCE LINKED</span>
                    </span>
                  </div>
                </div>
              </div>

              {/* Modal Footer with Done Button */}
              <div className="px-6 sm:px-8 pb-7 pt-2 flex items-center justify-end">
                <button
                  type="button"
                  onClick={() => setIsSourceModalOpen(false)}
                  className="px-7 py-2.5 rounded-xl bg-[#e6a13d] hover:bg-[#d8932f] text-slate-950 font-bold text-xs sm:text-sm shadow-md transition-all cursor-pointer"
                >
                  Done
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn text-left relative">
      {/* Toast Notification Banner */}
      {toastMsg && (
        <div className="fixed top-16 right-6 z-50 bg-[#7c4a27] dark:bg-[#96562c] text-white px-4 py-3 rounded-xl shadow-2xl flex items-center gap-2.5 animate-fadeIn font-semibold text-xs sm:text-sm border-2 border-amber-300">
          <Check className="w-5 h-5 text-amber-300 shrink-0" />
          <span>{toastMsg}</span>
        </div>
      )}

      {/* Header matching uploaded image media_1791735227219_197125ed.png */}
      <div>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100 mt-1">
          Regulatory Support
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1.5 font-normal max-w-3xl">
          Find requirements with clear provenance and source-level traceability.
        </p>
      </div>

      {/* Filter Controls Row matching uploaded image */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3 pt-1">
        {/* Search Field */}
        <div className="relative">
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

        {/* All Topics Dropdown */}
        <select
          value={topicFilter}
          onChange={(e) => setTopicFilter(e.target.value)}
          className="px-3 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#161619] text-slate-800 dark:text-slate-200 text-xs font-semibold focus:outline-none focus:border-[#96562c] cursor-pointer transition-all"
        >
          <option value="All topics">All topics</option>
          <option value="Customer Due Diligence">Customer Due Diligence</option>
          <option value="Transaction Monitoring">Transaction Monitoring</option>
          <option value="Suspicious Activity Reporting">Suspicious Activity Reporting</option>
          <option value="PEP Screening">PEP Screening</option>
          <option value="Consumer Duty">Consumer Duty</option>
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
                <th className="py-5 px-7 text-right"></th>
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
                      <div className="text-[11px] font-semibold text-slate-400 dark:text-slate-500 mt-1">
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
                    <td className="py-5 px-5 text-slate-700 dark:text-slate-300 text-xs sm:text-sm">
                      {req.reference}
                    </td>

                    {/* DATE / VERSION Column */}
                    <td className="py-5 px-5 text-slate-500 dark:text-slate-400 text-xs sm:text-sm">
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

                    {/* Action Column matching Image 1: Review REQ-xxx */}
                    <td className="py-5 px-7 whitespace-nowrap text-right">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedRequirement(req);
                        }}
                        className="text-slate-300 hover:text-white font-medium text-xs sm:text-sm cursor-pointer transition-colors"
                      >
                        Review {req.id}
                      </button>
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
