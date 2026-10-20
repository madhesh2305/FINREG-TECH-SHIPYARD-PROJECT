import React from 'react';
import { ArrowRight } from 'lucide-react';

export default function ReadinessView({ isDarkMode, onOpenRelatedItem, items = [] }) {
  // Empty default to be populated dynamically by backend / database
  const readinessItems = items;

  const completedCount = readinessItems.filter(
    (i) => i.statusType === 'emerald' || (i.status && i.status.toLowerCase() === 'completed')
  ).length;

  const openCount = readinessItems.filter(
    (i) => i.statusType === 'blue' || (i.status && i.status.toLowerCase() === 'open')
  ).length;

  const blockedCount = readinessItems.filter(
    (i) => i.statusType === 'rose' || (i.status && i.status.toLowerCase() === 'blocked')
  ).length;

  const reviewCount = readinessItems.filter(
    (i) => i.statusType === 'amber' || (i.status && i.status.toLowerCase().includes('review'))
  ).length;

  const totalCount = readinessItems.length;
  const progressPercent = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

  return (
    <div className="space-y-6 animate-fadeIn text-left relative">
      {/* TOP HEADER SECTION MATCHING media_1791739750674_a1d6ca4d.png */}
      <div>
        <div className="text-[11px] font-mono tracking-widest text-slate-500 uppercase font-semibold mb-1">
          PROJECT READINESS
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-white">
          Readiness
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1.5 font-normal max-w-4xl">
          Project progress derived from underlying requirements, advice, decisions, and follow-up actions—not a compliance certificate.
        </p>
      </div>

      {/* OVERALL READINESS STATUS CARD */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800/90 bg-white dark:bg-[#161619] p-6 sm:p-8 shadow-xl relative">
        <div className="text-[11px] font-mono tracking-widest text-slate-500 dark:text-slate-400 uppercase font-semibold mb-2">
          OVERALL READINESS STATUS
        </div>

        <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-4">
          <div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white leading-tight">
              {totalCount === 0
                ? 'Awaiting project readiness items'
                : progressPercent === 100
                ? 'All readiness items completed'
                : 'Progressing with review items'}
            </h2>
            <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-2 font-normal">
              Readiness updates as shared advice statuses change.
            </p>
          </div>

          <div className="text-3xl sm:text-4xl font-extrabold text-[#e6a13d] dark:text-[#f59e0b] shrink-0">
            {progressPercent}%
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-6 w-full h-2.5 bg-slate-100 dark:bg-slate-800/80 rounded-full overflow-hidden">
          <div
            className="h-full bg-[#e6a13d] dark:bg-[#f59e0b] rounded-full transition-all duration-700 ease-out"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      {/* 4 SUMMARY STAT CARDS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Completed items */}
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800/90 bg-white dark:bg-[#161619] p-6 shadow-sm">
          <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">
            Completed items
          </div>
          <div className="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white my-2.5">
            {String(completedCount).padStart(2, '0')}
          </div>
          <div className="text-xs text-slate-400 dark:text-slate-500">
            Evidence recorded
          </div>
        </div>

        {/* Card 2: Open items */}
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800/90 bg-white dark:bg-[#161619] p-6 shadow-sm">
          <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">
            Open items
          </div>
          <div className="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white my-2.5">
            {String(openCount).padStart(2, '0')}
          </div>
          <div className="text-xs text-slate-400 dark:text-slate-500">
            Action required
          </div>
        </div>

        {/* Card 3: Blocked items */}
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800/90 bg-white dark:bg-[#161619] p-6 shadow-sm">
          <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">
            Blocked items
          </div>
          <div className="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white my-2.5">
            {String(blockedCount).padStart(2, '0')}
          </div>
          <div className="text-xs text-slate-400 dark:text-slate-500">
            Owner needed
          </div>
        </div>

        {/* Card 4: Requires review */}
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800/90 bg-white dark:bg-[#161619] p-6 shadow-sm">
          <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">
            Requires review
          </div>
          <div className="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white my-2.5">
            {String(reviewCount).padStart(2, '0')}
          </div>
          <div className="text-xs text-slate-400 dark:text-slate-500">
            Human decision pending
          </div>
        </div>
      </div>

      {/* READINESS ITEMS CARD */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800/90 bg-white dark:bg-[#161619] shadow-xl overflow-hidden mt-6">
        {/* Header */}
        <div className="p-6 pb-4 sm:p-7 sm:pb-5 flex items-center justify-between border-b border-slate-100 dark:border-slate-800/80">
          <h2 className="text-lg sm:text-xl font-bold text-slate-900 dark:text-white">
            Readiness items
          </h2>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border border-amber-800/80 bg-amber-950/40 text-amber-300">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0" />
            <span>Live workflow status</span>
          </div>
        </div>

        {/* List of items */}
        <div className="divide-y divide-slate-100 dark:divide-slate-800/60">
          {readinessItems.length === 0 ? (
            <div className="p-10 text-center text-slate-400 dark:text-slate-500 text-sm">
              No readiness items found. Connect requirements and advice records to track readiness.
            </div>
          ) : (
            readinessItems.map((item, idx) => (
              <div
                key={idx}
                className="p-5 sm:p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-stone-50 dark:hover:bg-white/[0.02] transition-colors"
              >
                {/* Left: Code & Title */}
                <div className="flex items-center gap-6 min-w-[320px]">
                  <span className="font-mono text-xs font-semibold text-[#e6a13d] dark:text-[#f59e0b] min-w-[70px]">
                    {item.code}
                  </span>
                  <span className="font-semibold text-slate-900 dark:text-slate-100 text-sm">
                    {item.title}
                  </span>
                </div>

                {/* Center: Status Badge */}
                <div>
                  {item.statusType === 'amber' && (
                    <span className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full text-xs font-medium border border-amber-800/80 bg-amber-950/40 text-amber-300">
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0" />
                      <span>{item.status}</span>
                    </span>
                  )}
                  {item.statusType === 'emerald' && (
                    <span className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full text-xs font-medium border border-emerald-800/80 bg-emerald-950/40 text-emerald-300">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0" />
                      <span>{item.status}</span>
                    </span>
                  )}
                  {item.statusType === 'rose' && (
                    <span className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full text-xs font-medium border border-rose-900/80 bg-rose-950/40 text-rose-300">
                      <span className="w-1.5 h-1.5 rounded-full bg-rose-400 shrink-0" />
                      <span>{item.status}</span>
                    </span>
                  )}
                  {!['amber', 'emerald', 'rose'].includes(item.statusType) && (
                    <span className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full text-xs font-medium border border-slate-700 bg-slate-800 text-slate-300">
                      <span className="w-1.5 h-1.5 rounded-full bg-slate-400 shrink-0" />
                      <span>{item.status || 'Pending'}</span>
                    </span>
                  )}
                </div>

                {/* Right: Open related item button */}
                <div className="flex justify-end">
                  <button
                    type="button"
                    onClick={() => onOpenRelatedItem && onOpenRelatedItem(item)}
                    className="px-5 py-2.5 rounded-md border border-slate-700/80 bg-[#1e2025] hover:bg-slate-800 text-slate-200 hover:text-white text-sm font-semibold transition-colors cursor-pointer shadow-sm"
                  >
                    Open related item
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
