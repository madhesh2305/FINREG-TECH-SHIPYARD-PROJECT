import React, { useState } from 'react';
import { ArrowLeft, Check, ChevronDown, Calendar } from 'lucide-react';

export default function AdviceDecisionsView({ isDarkMode }) {
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [toastMsg, setToastMsg] = useState(null);

  // Decision Records initialized to empty array (ready for live backend records)
  const [records, setRecords] = useState([]);

  // Form states for the detail view
  const [formData, setFormData] = useState({
    builderDecision: 'Open',
    decisionRationale: '',
    followUpAction: '',
    actionOwner: 'Jun Nakamura',
    dueDate: '',
  });

  const handleOpenDetail = (record) => {
    setSelectedRecord(record);
    setFormData({
      builderDecision: record.decisionStatus || 'Open',
      decisionRationale: record.decisionRationale || '',
      followUpAction: record.followUpAction || '',
      actionOwner: record.actionOwner || 'Jun Nakamura',
      dueDate: record.dueDate || '',
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleRecordDecision = (e) => {
    if (e) e.preventDefault();
    if (!selectedRecord) return;

    const newDecisionStatus = formData.builderDecision;
    const newDecisionType =
      newDecisionStatus === 'Open' ? 'open' : 'closed';

    setRecords((prev) =>
      prev.map((r) =>
        r.id === selectedRecord.id
          ? {
              ...r,
              decisionStatus: newDecisionStatus,
              decisionStatusType: newDecisionType,
              decisionRationale: formData.decisionRationale,
              followUpAction: formData.followUpAction,
              actionOwner: formData.actionOwner,
              dueDate: formData.dueDate,
            }
          : r
      )
    );

    setToastMsg(`Decision recorded for ${selectedRecord.id} · ${selectedRecord.requirement}`);
    setTimeout(() => setToastMsg(null), 3000);

    // Return to the decisions list
    setSelectedRecord(null);
  };

  // IF DETAIL VIEW IS SELECTED, RENDER FULL VIEW MATCHING media_1791739235781_5c0cd34f.png & media_1791739252730_5be21ee1.png
  if (selectedRecord) {
    return (
      <div className="space-y-6 animate-fadeIn text-left relative max-w-5xl">
        {/* Toast Notification Banner */}
        {toastMsg && (
          <div className="fixed top-16 right-6 z-50 bg-[#7c4a27] dark:bg-[#96562c] text-white px-4 py-3 rounded-xl shadow-2xl flex items-center gap-2.5 animate-fadeIn font-semibold text-xs sm:text-sm border-2 border-amber-300">
            <Check className="w-5 h-5 text-amber-300 shrink-0" />
            <span>{toastMsg}</span>
          </div>
        )}

        {/* Back navigation button matching media_1791739235781_5c0cd34f.png */}
        <div className="pt-1">
          <button
            type="button"
            onClick={() => setSelectedRecord(null)}
            className="inline-flex items-center gap-2 text-xs sm:text-sm font-semibold text-slate-400 hover:text-slate-100 transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to decisions</span>
          </button>
        </div>

        {/* Top Header metadata matching Image 1 */}
        <div className="space-y-1.5">
          <div className="text-xs sm:text-sm font-mono text-slate-400 tracking-wide font-normal">
            {selectedRecord.id} · {selectedRecord.requirement}
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
            Advice & Decision Details
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 font-normal">
            Advice acceptance and the project decision are recorded separately.
          </p>
        </div>

        {/* Main Card Container matching media_1791739235781_5c0cd34f.png & media_1791739252730_5be21ee1.png */}
        <div className="rounded-2xl border border-slate-800/90 bg-[#141417] p-6 sm:p-8 space-y-6 shadow-xl">
          {/* Metadata Row matching Image 1 */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 pb-6 border-b border-slate-800/80">
            {/* ADVISOR STATUS */}
            <div>
              <div className="text-[11px] font-mono tracking-wider text-slate-400 uppercase font-semibold mb-2.5">
                ADVISOR STATUS
              </div>
              <div>
                {selectedRecord.adviceStatusType === 'emerald' ? (
                  <span className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full text-xs font-mono uppercase tracking-wider border border-emerald-800/80 bg-emerald-950/40 text-emerald-300 font-medium">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0" />
                    <span>{selectedRecord.adviceStatus.toUpperCase()}</span>
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full text-xs font-mono uppercase tracking-wider border border-amber-800/80 bg-amber-950/40 text-amber-300 font-medium">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0" />
                    <span>{selectedRecord.adviceStatus.toUpperCase()}</span>
                  </span>
                )}
              </div>
            </div>

            {/* SOURCE */}
            <div>
              <div className="text-[11px] font-mono tracking-wider text-slate-400 uppercase font-semibold mb-2.5">
                SOURCE
              </div>
              <div className="text-sm sm:text-base font-semibold text-slate-100">
                {selectedRecord.citation}
              </div>
            </div>

            {/* ADVISOR */}
            <div>
              <div className="text-[11px] font-mono tracking-wider text-slate-400 uppercase font-semibold mb-2.5">
                ADVISOR
              </div>
              <div className="text-sm sm:text-base font-semibold text-slate-100">
                {selectedRecord.advisor}
              </div>
            </div>
          </div>

          {/* FORM FIELDS MATCHING IMAGE 1 & IMAGE 2 */}
          <form onSubmit={handleRecordDecision} className="space-y-6">
            {/* Field 1: Builder decision */}
            <div>
              <label className="block text-sm font-semibold text-slate-200 mb-2">
                Builder decision
              </label>
              <div className="relative">
                <select
                  value={formData.builderDecision}
                  onChange={(e) =>
                    setFormData({ ...formData, builderDecision: e.target.value })
                  }
                  className="w-full bg-[#101013] border border-slate-700/80 hover:border-slate-600 rounded-xl px-4 py-3.5 text-sm text-slate-100 focus:outline-none focus:border-amber-500 appearance-none cursor-pointer pr-10 transition-colors"
                >
                  <option value="Open">Open</option>
                  <option value="Closed">Closed</option>
                  <option value="Under Review">Under Review</option>
                  <option value="Deferred">Deferred</option>
                </select>
                <ChevronDown className="w-4 h-4 text-slate-400 absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none" />
              </div>
            </div>

            {/* Field 2: Decision rationale * */}
            <div>
              <label className="block text-sm font-semibold text-slate-200 mb-2">
                Decision rationale *
              </label>
              <textarea
                rows={5}
                value={formData.decisionRationale}
                onChange={(e) =>
                  setFormData({ ...formData, decisionRationale: e.target.value })
                }
                placeholder="Explain the project decision and evidence considered"
                className="w-full bg-[#101013] border border-slate-700/80 hover:border-slate-600 rounded-xl p-4 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-amber-500 min-h-[130px] resize-y transition-colors leading-relaxed"
              />
            </div>

            {/* Field 3: Follow-up action */}
            <div>
              <label className="block text-sm font-semibold text-slate-200 mb-2">
                Follow-up action
              </label>
              <input
                type="text"
                value={formData.followUpAction}
                onChange={(e) =>
                  setFormData({ ...formData, followUpAction: e.target.value })
                }
                placeholder="Required action, if any"
                className="w-full bg-[#101013] border border-slate-700/80 hover:border-slate-600 rounded-xl px-4 py-3.5 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-amber-500 transition-colors"
              />
            </div>

            {/* Field 4 & 5: Action owner and Due date (2 Columns) */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
              {/* Action owner */}
              <div>
                <label className="block text-sm font-semibold text-slate-200 mb-2">
                  Action owner
                </label>
                <input
                  type="text"
                  value={formData.actionOwner}
                  onChange={(e) =>
                    setFormData({ ...formData, actionOwner: e.target.value })
                  }
                  placeholder="Jun Nakamura"
                  className="w-full bg-[#101013] border border-slate-700/80 hover:border-slate-600 rounded-xl px-4 py-3.5 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-amber-500 transition-colors"
                />
              </div>

              {/* Due date */}
              <div>
                <label className="block text-sm font-semibold text-slate-200 mb-2">
                  Due date
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={formData.dueDate}
                    onChange={(e) =>
                      setFormData({ ...formData, dueDate: e.target.value })
                    }
                    placeholder="dd-mm-yyyy"
                    className="w-full bg-[#101013] border border-slate-700/80 hover:border-slate-600 rounded-xl px-4 py-3.5 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-amber-500 pr-11 transition-colors"
                  />
                  <Calendar className="w-4 h-4 text-slate-400 absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none" />
                </div>
              </div>
            </div>

            {/* Action Buttons matching Image 2 */}
            <div className="flex items-center justify-end gap-3 pt-4">
              <button
                type="button"
                onClick={() => setSelectedRecord(null)}
                className="px-6 py-2.5 rounded-md border border-slate-700/80 bg-[#1e2025] hover:bg-slate-800 text-slate-100 font-semibold text-sm transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-6 py-2.5 rounded-md bg-[#e6a13d] hover:bg-[#d8932f] text-slate-950 font-bold text-sm shadow-md transition-colors cursor-pointer"
              >
                Record decision
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  // MAIN ADVICE & DECISIONS TABLE VIEW MATCHING media_1791738876275_cf9f871c.png
  return (
    <div className="space-y-6 animate-fadeIn text-left relative">
      {/* Toast Notification Banner */}
      {toastMsg && (
        <div className="fixed top-16 right-6 z-50 bg-[#7c4a27] dark:bg-[#96562c] text-white px-4 py-3 rounded-xl shadow-2xl flex items-center gap-2.5 animate-fadeIn font-semibold text-xs sm:text-sm border-2 border-amber-300">
          <Check className="w-5 h-5 text-amber-300 shrink-0" />
          <span>{toastMsg}</span>
        </div>
      )}

      {/* HEADER SECTION MATCHING media_1791738876275_cf9f871c.png */}
      <div>
        <div className="text-[11px] font-mono tracking-widest text-slate-500 uppercase font-semibold mb-1">
          BUILDER DECISION WORKSPACE
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-white">
          Advice & Decisions
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1.5 font-normal max-w-3xl">
          Compare advisor inputs, record a reasoned decision, and assign follow-up actions.
        </p>
      </div>

      {/* MAIN TABLE CONTAINER MATCHING media_1791738876275_cf9f871c.png */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800/90 bg-white dark:bg-[#161619] shadow-xl overflow-hidden">
        <div className="overflow-x-auto custom-scrollbar">
          <table className="w-full text-left text-xs sm:text-sm border-collapse min-w-[950px]">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-800/80 bg-stone-50/50 dark:bg-[#111215]/50 text-[11px] font-mono font-medium tracking-wider text-slate-400 dark:text-slate-400/80 uppercase">
                <th className="py-4 px-6 min-w-[280px]">REQUIREMENT</th>
                <th className="py-4 px-6 min-w-[150px]">ADVISOR</th>
                <th className="py-4 px-6 min-w-[170px]">ADVICE STATUS</th>
                <th className="py-4 px-6 min-w-[180px]">POSSIBLE DIFFERENCE</th>
                <th className="py-4 px-6 min-w-[140px]">DECISION STATUS</th>
                <th className="py-4 px-6 text-right min-w-[130px]"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-medium">
              {records.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500 text-sm">
                    No advice decisions recorded yet. Decisions recorded on advisor inputs will appear here.
                  </td>
                </tr>
              ) : (
                records.map((item) => (
                <tr
                  key={item.id}
                  onClick={() => handleOpenDetail(item)}
                  className="transition-colors cursor-pointer hover:bg-stone-50 dark:hover:bg-white/[0.02]"
                >
                  {/* REQUIREMENT Column */}
                  <td className="py-5 px-6">
                    <div className="font-semibold text-slate-900 dark:text-slate-100 text-sm leading-snug">
                      {item.requirement}
                    </div>
                    <div className="text-xs text-slate-400 dark:text-slate-400 mt-0.5 font-normal">
                      {item.citation}
                    </div>
                  </td>

                  {/* ADVISOR Column */}
                  <td className="py-5 px-6 text-slate-700 dark:text-slate-200 text-sm">
                    {item.advisor}
                  </td>

                  {/* ADVICE STATUS Column */}
                  <td className="py-5 px-6">
                    {item.adviceStatusType === 'emerald' ? (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border border-emerald-800/80 bg-emerald-950/40 text-emerald-300">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0" />
                        <span>{item.adviceStatus}</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border border-amber-800/80 bg-amber-950/40 text-amber-300">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0" />
                        <span>{item.adviceStatus}</span>
                      </span>
                    )}
                  </td>

                  {/* POSSIBLE DIFFERENCE Column */}
                  <td className="py-5 px-6">
                    {item.hasDifferenceBadge ? (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border border-amber-800/80 bg-amber-950/40 text-amber-300">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0" />
                        <span>{item.possibleDifference}</span>
                      </span>
                    ) : (
                      <span className="text-slate-400 text-sm font-normal">
                        {item.possibleDifference}
                      </span>
                    )}
                  </td>

                  {/* DECISION STATUS Column */}
                  <td className="py-5 px-6">
                    {item.decisionStatusType === 'open' ? (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border border-slate-700/90 bg-slate-800/50 text-slate-300">
                        <span className="w-1.5 h-1.5 rounded-full bg-slate-400 shrink-0" />
                        <span>{item.decisionStatus}</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border border-slate-800 bg-slate-900/60 text-slate-400">
                        <span className="w-1.5 h-1.5 rounded-full bg-slate-500 shrink-0" />
                        <span>{item.decisionStatus}</span>
                      </span>
                    )}
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
                      <span>Open detail</span>
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
