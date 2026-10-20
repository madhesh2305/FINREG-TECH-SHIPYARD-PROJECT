import React, { useState } from 'react';
import { ArrowLeft, Check, Search, ShieldAlert, FileText, ChevronRight } from 'lucide-react';

export default function AiRagFindingsView({ isDarkMode, findings = [] }) {
  const [selectedFinding, setSelectedFinding] = useState(null);
  const [toastMsg, setToastMsg] = useState(null);

  // Findings master data - clean default ready for live backend integration
  const [findingsList, setFindingsList] = useState(findings);

  React.useEffect(() => {
    if (findings && findings.length > 0) {
      setFindingsList(findings);
    }
  }, [findings]);

  const handleOpenDetail = (item) => {
    setSelectedFinding(item);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const needsHumanReviewCount = findingsList.filter(
    (f) =>
      (f.humanReview && f.humanReview.toLowerCase().includes('needs')) ||
      (f.humanReview && f.humanReview.toLowerCase().includes('review'))
  ).length;

  const sourcesFoundCount = findingsList.filter(
    (f) =>
      f.supportingSource &&
      !f.supportingSource.toLowerCase().includes('no reliable source') &&
      f.supportingSource !== '-'
  ).length;

  const evidenceGapsCount = findingsList.filter(
    (f) => f.type && f.type.toLowerCase().includes('gap')
  ).length;

  const conflictsCount = findingsList.filter(
    (f) => f.type && f.type.toLowerCase().includes('conflict')
  ).length;

  // IF REVIEW DETAILS IS SELECTED, RENDER FULL PAGE VIEW
  if (selectedFinding) {
    return (
      <div className="space-y-6 animate-fadeIn text-left relative max-w-5xl">
        {/* Back navigation button */}
        <div className="pt-1">
          <button
            type="button"
            onClick={() => setSelectedFinding(null)}
            className="inline-flex items-center gap-2 text-xs sm:text-sm font-semibold text-slate-400 hover:text-slate-100 transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to findings</span>
          </button>
        </div>

        {/* Top Header metadata */}
        <div className="space-y-1.5">
          <div className="text-xs sm:text-sm font-mono text-slate-400 tracking-wide font-normal">
            {selectedFinding.requirement} · {selectedFinding.type}
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
            {selectedFinding.finding}
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 font-normal">
            AI-generated analysis for human review; not a legal opinion or compliance certification.
          </p>
        </div>

        {/* Main Card Container */}
        <div className="rounded-2xl border border-slate-800/90 bg-[#141417] p-6 sm:p-8 space-y-6 shadow-xl">
          {/* SECTION 1: FINDING TYPE */}
          <div className="pb-6 border-b border-slate-800/80">
            <div className="text-[11px] font-mono tracking-wider text-slate-400 uppercase font-semibold mb-2.5">
              FINDING TYPE
            </div>
            <div>
              <span
                className={`inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full text-xs font-mono uppercase tracking-wider border ${
                  selectedFinding.typeDetailBadge ||
                  'border-amber-800/80 bg-amber-950/40 text-amber-300'
                } font-medium`}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full ${
                    selectedFinding.typeDot || 'bg-amber-400'
                  } shrink-0`}
                />
                <span>{(selectedFinding.type || 'Finding').toUpperCase()}</span>
              </span>
            </div>
          </div>

          {/* SECTION 2: RELATED REQUIREMENT */}
          <div className="pb-6 border-b border-slate-800/80">
            <div className="text-[11px] font-mono tracking-wider text-slate-400 uppercase font-semibold mb-2.5">
              RELATED REQUIREMENT
            </div>
            <div className="text-sm sm:text-base font-semibold text-slate-100 font-mono">
              {selectedFinding.requirement}
            </div>
          </div>

          {/* SECTION 3: SUPPORTING SOURCE / CITATION */}
          <div className="pb-6 border-b border-slate-800/80">
            <div className="text-[11px] font-mono tracking-wider text-slate-400 uppercase font-semibold mb-2.5">
              SUPPORTING SOURCE / CITATION
            </div>
            <div className="text-sm sm:text-base font-semibold text-slate-100">
              {selectedFinding.supportingSource || 'None specified'}
            </div>
          </div>

          {/* SECTION 4: REVIEW DETAILS */}
          <div className="pb-6 border-b border-slate-800/80">
            <div className="text-[11px] font-mono tracking-wider text-slate-400 uppercase font-semibold mb-2.5">
              REVIEW DETAILS
            </div>
            <div className="text-sm sm:text-base font-medium text-slate-100 leading-relaxed">
              {selectedFinding.reviewDetails || 'No details provided.'}
            </div>
          </div>

          {/* SECTION 5: HUMAN REVIEW STATUS */}
          <div>
            <div className="text-[11px] font-mono tracking-wider text-slate-400 uppercase font-semibold mb-2.5">
              HUMAN REVIEW STATUS
            </div>
            <div className="mb-6">
              <span
                className={`inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full text-xs font-mono uppercase tracking-wider border ${
                  selectedFinding.detailStatusBadge ||
                  'border-amber-800/80 bg-amber-950/40 text-amber-300'
                } font-medium`}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full ${
                    selectedFinding.detailStatusDot || 'bg-amber-400'
                  } shrink-0`}
                />
                <span>{(selectedFinding.humanReview || 'Pending').toUpperCase()}</span>
              </span>
            </div>

            {/* SECTION 6: CALLOUT CARD */}
            <div className="rounded-xl border border-amber-900/60 bg-amber-950/20 p-5 sm:p-6 space-y-2">
              <div className="text-xs font-mono tracking-wider uppercase text-amber-400 font-bold">
                HUMAN REVIEW REQUIRED
              </div>
              <p className="text-xs sm:text-sm text-slate-300 leading-relaxed font-normal">
                This finding may summarize evidence, compare advice, or flag missing information.
                It does not certify readiness or determine legal applicability.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // MAIN AI / RAG FINDINGS DASHBOARD VIEW
  return (
    <div className="space-y-6 animate-fadeIn text-left relative">
      {/* Toast Notification Banner */}
      {toastMsg && (
        <div className="fixed top-16 right-6 z-50 bg-[#7c4a27] dark:bg-[#96562c] text-white px-4 py-3 rounded-xl shadow-2xl flex items-center gap-2.5 animate-fadeIn font-semibold text-xs sm:text-sm border-2 border-amber-300">
          <Check className="w-5 h-5 text-amber-300 shrink-0" />
          <span>{toastMsg}</span>
        </div>
      )}

      {/* HEADER SECTION */}
      <div>
        <div className="text-[11px] font-mono tracking-widest text-slate-500 uppercase font-semibold mb-1">
          BUILDER WORKSPACE
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-white">
          AI / RAG Findings
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1.5 font-normal max-w-3xl">
          Source-grounded findings, evidence gaps, and possible conflicts requiring human review.
        </p>
      </div>

      {/* 4 SUMMARY STAT CARDS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Needs human review */}
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800/90 bg-white dark:bg-[#161619] p-6 shadow-sm">
          <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">
            Needs human review
          </div>
          <div className="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white my-2.5">
            {String(needsHumanReviewCount).padStart(2, '0')}
          </div>
          <div className="text-xs text-slate-400 dark:text-slate-500">
            No automatic legal conclusions
          </div>
        </div>

        {/* Card 2: Sources found */}
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800/90 bg-white dark:bg-[#161619] p-6 shadow-sm">
          <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">
            Sources found
          </div>
          <div className="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white my-2.5">
            {String(sourcesFoundCount).padStart(2, '0')}
          </div>
          <div className="text-xs text-slate-400 dark:text-slate-500">
            Approved source set
          </div>
        </div>

        {/* Card 3: Evidence gaps */}
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800/90 bg-white dark:bg-[#161619] p-6 shadow-sm">
          <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">
            Evidence gaps
          </div>
          <div className="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white my-2.5">
            {String(evidenceGapsCount).padStart(2, '0')}
          </div>
          <div className="text-xs text-slate-400 dark:text-slate-500">
            Open project evidence
          </div>
        </div>

        {/* Card 4: Possible conflicts */}
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800/90 bg-white dark:bg-[#161619] p-6 shadow-sm">
          <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">
            Possible conflicts
          </div>
          <div className="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white my-2.5">
            {String(conflictsCount).padStart(2, '0')}
          </div>
          <div className="text-xs text-slate-400 dark:text-slate-500">
            Builder decision needed
          </div>
        </div>
      </div>

      {/* MAIN TABLE CONTAINER */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800/90 bg-white dark:bg-[#161619] shadow-xl overflow-hidden mt-6">
        <div className="overflow-x-auto custom-scrollbar">
          <table className="w-full text-left text-xs sm:text-sm border-collapse min-w-[950px]">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-800/80 bg-stone-50/50 dark:bg-[#111215]/50 text-[11px] font-mono font-medium tracking-wider text-slate-400 dark:text-slate-400/80 uppercase">
                <th className="py-4 px-6 min-w-[280px]">FINDING</th>
                <th className="py-4 px-6 min-w-[200px]">TYPE</th>
                <th className="py-4 px-6 min-w-[120px]">REQUIREMENT</th>
                <th className="py-4 px-6 min-w-[220px]">SUPPORTING SOURCE</th>
                <th className="py-4 px-6 min-w-[170px]">HUMAN REVIEW</th>
                <th className="py-4 px-6 text-right min-w-[140px]"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-medium">
              {findingsList.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    className="py-12 px-6 text-center text-slate-400 dark:text-slate-500 text-sm"
                  >
                    No AI / RAG findings generated. Run retrieval-augmented generation on regulatory documents to populate findings.
                  </td>
                </tr>
              ) : (
                findingsList.map((item) => (
                  <tr
                    key={item.id}
                    onClick={() => handleOpenDetail(item)}
                    className="transition-colors cursor-pointer hover:bg-stone-50 dark:hover:bg-white/[0.02]"
                  >
                    {/* FINDING Column */}
                    <td className="py-5 px-6 font-semibold text-slate-900 dark:text-slate-100 text-sm">
                      {item.finding}
                    </td>

                    {/* TYPE Column */}
                    <td className="py-5 px-6">
                      <span
                        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border ${
                          item.typeBadge || 'border-amber-800/80 bg-amber-950/40 text-amber-300'
                        }`}
                      >
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${
                            item.typeDot || 'bg-amber-400'
                          } shrink-0`}
                        />
                        <span>{item.type}</span>
                      </span>
                    </td>

                    {/* REQUIREMENT Column */}
                    <td className="py-5 px-6 text-slate-700 dark:text-slate-300 font-mono text-sm">
                      {item.requirement}
                    </td>

                    {/* SUPPORTING SOURCE Column */}
                    <td className="py-5 px-6 text-slate-600 dark:text-slate-300 text-sm">
                      {item.supportingSource}
                    </td>

                    {/* HUMAN REVIEW Column */}
                    <td className="py-5 px-6">
                      <span
                        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border ${
                          item.statusBadge || 'border-slate-700/80 bg-slate-800/50 text-slate-300'
                        }`}
                      >
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${
                            item.statusDot || 'bg-slate-400'
                          } shrink-0`}
                        />
                        <span>{item.humanReview}</span>
                      </span>
                    </td>

                    {/* ACTION Column */}
                    <td className="py-5 px-6 text-right">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleOpenDetail(item);
                        }}
                        className="inline-flex items-center gap-1 text-sm font-medium text-slate-300 hover:text-white transition-colors cursor-pointer group"
                      >
                        <span>Review details</span>
                        <span className="transition-transform group-hover:translate-x-0.5">→</span>
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
