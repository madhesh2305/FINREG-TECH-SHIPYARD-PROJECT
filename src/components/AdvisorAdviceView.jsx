import React, { useState, useEffect } from 'react';
import { ArrowLeft, Check, CheckCircle2 } from 'lucide-react';

const ADVISOR_REVIEWS_STORAGE_KEY = 'finreg_advisor_reviews';

// Advisor Advice list initialized to empty array (ready for live backend advice data)
const DEFAULT_ADVICE = [];

export default function AdvisorAdviceView({ isDarkMode }) {
  const [selectedAdvice, setSelectedAdvice] = useState(null);
  const [toastMsg, setToastMsg] = useState(null);

  // Dynamic advice loading from local storage / API with strict mock data purging
  const loadDynamicAdvice = () => {
    try {
      const raw = localStorage.getItem(ADVISOR_REVIEWS_STORAGE_KEY);
      const saved = raw ? JSON.parse(raw) : [];
      if (Array.isArray(saved) && saved.length > 0) {
        // Exclude all mock / prototype entries (including REV-001, REV-002, KYC Onboarding, and fallback items)
        const clean = saved.filter(
          (r) =>
            r &&
            typeof r === 'object' &&
            r.id &&
            r.id.startsWith('ADV-REV-') &&
            !r.id.startsWith('REV-') &&
            !r.id.startsWith('ADV-00') &&
            !r.id.includes('MOCK') &&
            r.project !== 'ABC Shield' &&
            r.project !== 'KYC Onboarding Controls' &&
            !r.advisor?.includes('Maya Chen') &&
            !r.requirement?.toLowerCase().includes('identity verification') &&
            !r.requirement?.toLowerCase().includes('cdd evidence') &&
            !r.adviceSubmitted?.toLowerCase().includes('contractual agreement') &&
            r.date !== '09 Oct 2026' &&
            r.date !== '12 Oct 2026' &&
            r.date !== '14 Oct 2026'
        );

        // Permanently purge any lingering mock records from localStorage
        try {
          localStorage.setItem(ADVISOR_REVIEWS_STORAGE_KEY, JSON.stringify(clean));
        } catch (e) {}

        return clean.map((r, idx) => ({
          id: r.id || `ADV-SUB-${idx + 1}`,
          advisor: r.advisor || r.advisorName || 'Advisor',
          expertise: r.expertise || r.advisorRole || 'Regulatory Advisory',
          requirement: r.requirement || 'Requirement Review',
          project: r.project || r.projectName || 'Project',
          source: r.source || 'Regulatory Standard',
          authority: r.authority || 'Supervisory Authority',
          adviceSummary: (r.adviceSubmitted || r.recommendation || '').slice(0, 42) + '...',
          recommendation: r.recommendation || r.adviceSubmitted || '',
          comments: r.adviceSubmitted || r.comments || '',
          attachment: r.referenceAttachment || r.attachment || 'Advisory-Notes.pdf',
          dateSubmitted: r.date || r.dateSubmitted || 'Recently',
          status: r.status === 'Submitted' ? 'Pending Review' : (r.status || 'Pending Review'),
          statusBadge: r.status === 'Accepted'
            ? 'border-emerald-800/80 bg-emerald-950/60 text-emerald-400'
            : 'border-amber-800/80 bg-amber-950/60 text-amber-400',
          dotColor: r.status === 'Accepted' ? 'bg-emerald-500' : 'bg-amber-500',
        }));
      }
    } catch (e) {}
    return [];
  };

  const [adviceList, setAdviceList] = useState(loadDynamicAdvice);

  useEffect(() => {
    // Purge mock records and re-sync on mount
    setAdviceList(loadDynamicAdvice());

    const handleStorageChange = () => {
      setAdviceList(loadDynamicAdvice());
    };
    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  const handleUpdateStatus = (id, newStatus) => {
    setAdviceList((prev) => {
      const updated = prev.map((item) =>
        item.id === id
          ? {
              ...item,
              status: newStatus,
              statusBadge:
                newStatus === 'Accepted'
                  ? 'border-emerald-800/80 bg-emerald-950/60 text-emerald-400'
                  : 'border-amber-800/80 bg-amber-950/60 text-amber-400',
              dotColor: newStatus === 'Accepted' ? 'bg-emerald-500' : 'bg-amber-500',
            }
          : item
      );

      try {
        const raw = localStorage.getItem(ADVISOR_REVIEWS_STORAGE_KEY);
        if (raw) {
          const list = JSON.parse(raw);
          const next = list.map((r) => (r.id === id ? { ...r, status: newStatus } : r));
          localStorage.setItem(ADVISOR_REVIEWS_STORAGE_KEY, JSON.stringify(next));
        }
      } catch (e) {}

      return updated;
    });

    if (selectedAdvice && selectedAdvice.id === id) {
      setSelectedAdvice((prev) => ({
        ...prev,
        status: newStatus,
        statusBadge:
          newStatus === 'Accepted'
            ? 'border-emerald-800/80 bg-emerald-950/60 text-emerald-400'
            : 'border-amber-800/80 bg-amber-950/60 text-amber-400',
        dotColor: newStatus === 'Accepted' ? 'bg-emerald-500' : 'bg-amber-500',
      }));
    }

    setToastMsg(`Status updated to "${newStatus}" for ${id}`);
  };

  // IF AN ADVICE IS SELECTED, RENDER FULL ADVICE DETAILS VIEW MATCHING media_1791738592058_78459760.png & media_1791738603315_95574266.png
  if (selectedAdvice) {
    return (
      <div className="space-y-6 animate-fadeIn text-left relative">
        {/* Toast Notification Banner */}
        {toastMsg && (
          <div className="fixed top-16 right-6 z-50 bg-[#7c4a27] dark:bg-[#96562c] text-white px-4 py-3 rounded-xl shadow-2xl flex items-center gap-2.5 animate-fadeIn font-semibold text-xs sm:text-sm border-2 border-amber-300">
            <Check className="w-5 h-5 text-amber-300 shrink-0" />
            <span>{toastMsg}</span>
          </div>
        )}

        {/* Back navigation button matching image */}
        <div className="pt-1">
          <button
            type="button"
            onClick={() => setSelectedAdvice(null)}
            className="inline-flex items-center gap-2 text-xs sm:text-sm font-semibold text-slate-400 hover:text-slate-100 transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to advisor advice</span>
          </button>
        </div>

        {/* Header Section matching Image 1 */}
        <div className="pt-2">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="text-xs font-mono font-semibold tracking-wider text-slate-400 uppercase">
              {selectedAdvice.id} · {selectedAdvice.requirement}
            </div>
            <div>
              <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border ${selectedAdvice.statusBadge}`}>
                <span className={`w-1.5 h-1.5 rounded-full ${selectedAdvice.dotColor}`} />
                {selectedAdvice.status}
              </span>
            </div>
          </div>

          <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-slate-100 tracking-tight mt-2">
            Advisor Advice Details
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 font-normal mt-1.5">
            Submitted by {selectedAdvice.advisor} for {selectedAdvice.project || 'Project'}.
          </p>
        </div>

        {/* Main 2-Column Card Container matching Images 1 & 2 */}
        <div className="rounded-2xl border border-slate-800/90 bg-[#161619] p-6 sm:p-8 space-y-8 text-left shadow-xl">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-14">
            {/* Left Column */}
            <div className="space-y-6">
              {/* ADVISOR NAME */}
              <div className="border-b border-slate-800/80 pb-5">
                <div className="text-[10px] font-extrabold tracking-wider text-slate-500 uppercase">
                  ADVISOR NAME
                </div>
                <div className="text-sm font-bold text-slate-100 mt-1">
                  {selectedAdvice.advisor}
                </div>
              </div>

              {/* ADVISOR EXPERTISE */}
              <div className="border-b border-slate-800/80 pb-5">
                <div className="text-[10px] font-extrabold tracking-wider text-slate-500 uppercase">
                  ADVISOR EXPERTISE
                </div>
                <div className="text-sm font-semibold text-slate-200 mt-1">
                  {selectedAdvice.expertise}
                </div>
              </div>

              {/* REQUIREMENT */}
              <div className="border-b border-slate-800/80 pb-5">
                <div className="text-[10px] font-extrabold tracking-wider text-slate-500 uppercase">
                  REQUIREMENT
                </div>
                <div className="text-sm font-semibold text-slate-200 mt-1">
                  {selectedAdvice.requirement}
                </div>
              </div>

              {/* REGULATORY SOURCE */}
              <div className="border-b border-slate-800/80 pb-5">
                <div className="text-[10px] font-extrabold tracking-wider text-slate-500 uppercase">
                  REGULATORY SOURCE
                </div>
                <div className="text-sm font-semibold text-slate-200 mt-1">
                  {selectedAdvice.source}
                </div>
              </div>

              {/* AUTHORITY */}
              <div>
                <div className="text-[10px] font-extrabold tracking-wider text-slate-500 uppercase">
                  AUTHORITY
                </div>
                <div className="text-sm font-semibold text-slate-200 mt-1">
                  {selectedAdvice.authority}
                </div>
              </div>
            </div>

            {/* Right Column */}
            <div className="space-y-6">
              {/* ADVISOR RECOMMENDATION */}
              <div className="border-b border-slate-800/80 pb-5">
                <div className="text-[10px] font-extrabold tracking-wider text-slate-500 uppercase">
                  ADVISOR RECOMMENDATION
                </div>
                <div className="text-sm font-medium text-slate-200 mt-1 leading-relaxed">
                  {selectedAdvice.recommendation}
                </div>
              </div>

              {/* ADVISOR COMMENTS */}
              <div className="border-b border-slate-800/80 pb-5">
                <div className="text-[10px] font-extrabold tracking-wider text-slate-500 uppercase">
                  ADVISOR COMMENTS
                </div>
                <div className="text-sm font-normal text-slate-300 mt-1 leading-relaxed">
                  {selectedAdvice.comments}
                </div>
              </div>

              {/* REFERENCE / ATTACHMENT */}
              <div className="border-b border-slate-800/80 pb-5">
                <div className="text-[10px] font-extrabold tracking-wider text-slate-500 uppercase">
                  REFERENCE / ATTACHMENT
                </div>
                <div className="text-sm font-semibold text-slate-200 mt-1">
                  {selectedAdvice.attachment}
                </div>
              </div>

              {/* SUBMITTED DATE */}
              <div className="border-b border-slate-800/80 pb-5">
                <div className="text-[10px] font-extrabold tracking-wider text-slate-500 uppercase">
                  SUBMITTED DATE
                </div>
                <div className="text-sm font-semibold text-slate-200 mt-1">
                  {selectedAdvice.dateSubmitted}
                </div>
              </div>

              {/* REVIEW STATUS */}
              <div>
                <div className="text-[10px] font-extrabold tracking-wider text-slate-500 uppercase">
                  REVIEW STATUS
                </div>
                <div className="mt-1.5">
                  <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold border ${selectedAdvice.statusBadge} uppercase tracking-wider`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${selectedAdvice.dotColor}`} />
                    {selectedAdvice.status}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* HISTORY & ACTIONS ROW matching Image 2 */}
          <div className="pt-6 border-t border-slate-800/80 space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-4">
                <span className="text-[11px] font-bold text-amber-500 uppercase tracking-wider">
                  HISTORY
                </span>
                <span className="text-xs sm:text-sm font-bold text-slate-200">
                  Submitted by {selectedAdvice.advisor} · {selectedAdvice.dateSubmitted}
                </span>
              </div>
              <div>
                <span className={`inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full text-[11px] font-bold border ${selectedAdvice.statusBadge}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${selectedAdvice.dotColor}`} />
                  {selectedAdvice.status}
                </span>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => {
                  setToastMsg(`Clarification request sent to ${selectedAdvice.advisor}`);
                  setTimeout(() => setToastMsg(null), 2500);
                }}
                className="px-6 py-2.5 rounded-xl border border-slate-700 hover:border-slate-600 bg-slate-900/60 hover:bg-slate-800 text-slate-200 font-bold text-xs sm:text-sm transition-colors cursor-pointer"
              >
                Request clarification
              </button>

              <button
                type="button"
                onClick={() => handleUpdateStatus(selectedAdvice.id, 'Accepted')}
                className="px-6 py-2.5 rounded-xl bg-[#e6a13d] hover:bg-[#d8932f] text-slate-950 font-bold text-xs sm:text-sm shadow-md transition-colors cursor-pointer"
              >
                Accept advice
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // MAIN ADVISOR ADVICE TABLE VIEW (Matching media_1791737929366_a3b12230.png)
  return (
    <div className="space-y-6 animate-fadeIn text-left relative">
      {/* Toast Notification Banner */}
      {toastMsg && (
        <div className="fixed top-16 right-6 z-50 bg-[#7c4a27] dark:bg-[#96562c] text-white px-4 py-3 rounded-xl shadow-2xl flex items-center gap-2.5 animate-fadeIn font-semibold text-xs sm:text-sm border-2 border-amber-300">
          <Check className="w-5 h-5 text-amber-300 shrink-0" />
          <span>{toastMsg}</span>
        </div>
      )}

      {/* Header Banner matching uploaded image media_1791737929366_a3b12230.png */}
      <div>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100 mt-1">
          Advisor Advice
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1.5 font-normal max-w-3xl">
          One shared record of submitted advice and the latest Builder response.
        </p>
      </div>

      {/* Main Card Container */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800/90 bg-white dark:bg-[#161619] shadow-lg overflow-hidden">
        {/* Card Header matching image */}
        <div className="p-6 pb-4 sm:p-7 sm:pb-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 dark:border-slate-800/80">
          <div>
            <h2 className="text-lg sm:text-xl font-bold text-slate-900 dark:text-slate-100">
              Advisor Advice
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Advice and regulatory reviews submitted for this project only.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border border-amber-800/80 bg-amber-950/60 text-amber-400">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
              <span>{adviceList.length} reviews</span>
            </span>
          </div>
        </div>

        {/* Table Container with Horizontal Scroll */}
        <div className="overflow-x-auto custom-scrollbar">
          <table className="w-full text-left text-xs sm:text-sm border-collapse min-w-[1100px]">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-800/80 bg-stone-50/50 dark:bg-[#111215]/50 text-[11px] font-bold tracking-wider text-slate-400 dark:text-slate-500 uppercase">
                <th className="py-4 px-6 min-w-[180px]">ADVISOR</th>
                <th className="py-4 px-6 min-w-[180px]">EXPERTISE</th>
                <th className="py-4 px-6 min-w-[240px]">REQUIREMENT / TOPIC</th>
                <th className="py-4 px-6 min-w-[280px]">ADVICE SUMMARY</th>
                <th className="py-4 px-6 min-w-[130px]">DATE SUBMITTED</th>
                <th className="py-4 px-6 min-w-[150px]">STATUS</th>
                <th className="py-4 px-6 text-right min-w-[100px]"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-medium">
              {adviceList.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-500 text-sm">
                    No advisor advice submitted for this project yet. Advice submitted by invited advisors will appear here.
                  </td>
                </tr>
              ) : (
                adviceList.map((item) => (
                <tr
                  key={item.id}
                  onClick={() => setSelectedAdvice(item)}
                  className="transition-colors cursor-pointer hover:bg-stone-50 dark:hover:bg-slate-800/40"
                >
                  {/* ADVISOR Column */}
                  <td className="py-4 sm:py-5 px-6 font-bold text-slate-900 dark:text-slate-100 text-sm">
                    {item.advisor}
                  </td>

                  {/* EXPERTISE Column */}
                  <td className="py-4 sm:py-5 px-6 text-slate-600 dark:text-slate-400 text-xs sm:text-sm">
                    {item.expertise}
                  </td>

                  {/* REQUIREMENT / TOPIC Column */}
                  <td className="py-4 sm:py-5 px-6 text-slate-800 dark:text-slate-300 text-xs sm:text-sm">
                    {item.requirement}
                  </td>

                  {/* ADVICE SUMMARY Column */}
                  <td className="py-4 sm:py-5 px-6 text-slate-600 dark:text-slate-400 text-xs sm:text-sm max-w-[300px] truncate" title={item.adviceSummary}>
                    {item.adviceSummary}
                  </td>

                  {/* DATE SUBMITTED Column */}
                  <td className="py-4 sm:py-5 px-6 text-slate-500 dark:text-slate-400 text-xs sm:text-sm">
                    {item.dateSubmitted}
                  </td>

                  {/* STATUS Column */}
                  <td className="py-4 sm:py-5 px-6">
                    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border ${item.statusBadge}`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${item.dotColor}`} />
                      {item.status}
                    </span>
                  </td>

                  {/* Action Column matching Image 1: View advice */}
                  <td className="py-4 sm:py-5 px-6 whitespace-nowrap text-right">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedAdvice(item);
                      }}
                      className="text-slate-400 hover:text-slate-200 font-medium text-xs sm:text-sm cursor-pointer transition-colors"
                    >
                      View advice
                    </button>
                  </td>
                </tr>
              ))
            )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
