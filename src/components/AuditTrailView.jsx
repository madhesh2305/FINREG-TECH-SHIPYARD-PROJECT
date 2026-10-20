import React, { useState, useEffect } from 'react';
import { Search, Calendar, ChevronDown, X } from 'lucide-react';
import { getAuditEvents } from '../services/auditService';

export default function AuditTrailView({ isDarkMode, events = [] }) {
  const [selectedEvent, setSelectedEvent] = useState(null);

  // Filter states
  const [searchQuery, setSearchQuery] = useState('');
  const [projectFilter, setProjectFilter] = useState('All projects');
  const [roleFilter, setRoleFilter] = useState('All roles');
  const [eventTypeFilter, setEventTypeFilter] = useState('All event types');
  const [dateFilter, setDateFilter] = useState('');

  // Master Audit Trail items - clean default ready for live backend integration
  const [auditEvents, setAuditEvents] = useState(events);

  useEffect(() => {
    if (events && events.length > 0) {
      setAuditEvents(events);
    } else {
      getAuditEvents().then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setAuditEvents(data);
        }
      });
    }
  }, [events]);

  const projectOptions = Array.from(
    new Set(auditEvents.map((e) => e.relatedProject).filter(Boolean))
  );

  // Filtering
  const filteredEvents = auditEvents.filter((item) => {
    const action = item.action || '';
    const user = item.user || '';
    const relatedProject = item.relatedProject || '';
    const eventType = item.eventType || '';

    const matchesSearch =
      action.toLowerCase().includes(searchQuery.toLowerCase()) ||
      user.toLowerCase().includes(searchQuery.toLowerCase()) ||
      relatedProject.toLowerCase().includes(searchQuery.toLowerCase()) ||
      eventType.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesProject =
      projectFilter === 'All projects' || relatedProject === projectFilter;

    const matchesRole =
      roleFilter === 'All roles' || item.role === roleFilter;

    const matchesEventType =
      eventTypeFilter === 'All event types' || eventType === eventTypeFilter;

    const matchesDate = !dateFilter || (item.dateTime && item.dateTime.includes(dateFilter));

    return matchesSearch && matchesProject && matchesRole && matchesEventType && matchesDate;
  });

  return (
    <div className="space-y-6 animate-fadeIn text-left relative">
      {/* HEADER SECTION MATCHING media_1791740746094_bb421bec.png */}
      <div>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-white">
          Audit Trail
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1.5 font-normal max-w-3xl">
          Immutable chronological record of important workflow and access events.
        </p>
      </div>

      {/* FILTER BAR CONTROLS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 pt-1">
        {/* Search Field */}
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
            <Search className="w-4 h-4" />
          </div>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search events"
            className="w-full pl-10 pr-4 py-2.5 text-xs sm:text-sm rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#161619] text-slate-900 dark:text-slate-100 placeholder-slate-500 focus:outline-none focus:border-[#96562c] focus:ring-1 focus:ring-[#96562c] transition-all"
          />
        </div>

        {/* All projects dropdown */}
        <div className="relative">
          <select
            value={projectFilter}
            onChange={(e) => setProjectFilter(e.target.value)}
            className="w-full px-4 py-2.5 text-xs sm:text-sm rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#161619] text-slate-900 dark:text-slate-100 focus:outline-none focus:border-[#96562c] appearance-none cursor-pointer pr-10 transition-all"
          >
            <option value="All projects">All projects</option>
            {projectOptions.map((proj) => (
              <option key={proj} value={proj}>
                {proj}
              </option>
            ))}
          </select>
          <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
        </div>

        {/* All roles dropdown */}
        <div className="relative">
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="w-full px-4 py-2.5 text-xs sm:text-sm rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#161619] text-slate-900 dark:text-slate-100 focus:outline-none focus:border-[#96562c] appearance-none cursor-pointer pr-10 transition-all"
          >
            <option value="All roles">All roles</option>
            <option value="Advisor">Advisor</option>
            <option value="Builder">Builder</option>
            <option value="Admin">Admin</option>
            <option value="System">System</option>
          </select>
          <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
        </div>

        {/* All event types dropdown */}
        <div className="relative">
          <select
            value={eventTypeFilter}
            onChange={(e) => setEventTypeFilter(e.target.value)}
            className="w-full px-4 py-2.5 text-xs sm:text-sm rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#161619] text-slate-900 dark:text-slate-100 focus:outline-none focus:border-[#96562c] appearance-none cursor-pointer pr-10 transition-all"
          >
            <option value="All event types">All event types</option>
            <option value="Advice">Advice</option>
            <option value="Clarification">Clarification</option>
            <option value="Permission">Permission</option>
            <option value="AI Review">AI Review</option>
            <option value="Project">Project</option>
          </select>
          <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
        </div>

        {/* Date picker field */}
        <div className="relative">
          <input
            type="text"
            value={dateFilter}
            onChange={(e) => setDateFilter(e.target.value)}
            placeholder="dd-mm-yyyy"
            className="w-full px-4 py-2.5 text-xs sm:text-sm rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#161619] text-slate-900 dark:text-slate-100 placeholder-slate-500 focus:outline-none focus:border-[#96562c] pr-10 transition-all"
          />
          <Calendar className="w-4 h-4 text-slate-400 absolute right-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
        </div>
      </div>

      {/* AUDIT EVENTS TABLE */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800/90 bg-white dark:bg-[#161619] shadow-xl overflow-hidden mt-6">
        <div className="overflow-x-auto custom-scrollbar">
          <table className="w-full text-left text-xs sm:text-sm border-collapse min-w-[950px]">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-800/80 bg-stone-50/50 dark:bg-[#111215]/50 text-[11px] font-mono font-medium tracking-wider text-slate-400 dark:text-slate-400/80 uppercase">
                <th className="py-4 px-6 min-w-[170px]">DATE / TIME</th>
                <th className="py-4 px-6 min-w-[150px]">USER</th>
                <th className="py-4 px-6 min-w-[100px]">ROLE</th>
                <th className="py-4 px-6 min-w-[130px]">EVENT TYPE</th>
                <th className="py-4 px-6 min-w-[260px]">ACTION</th>
                <th className="py-4 px-6 min-w-[130px]">RELATED PROJECT</th>
                <th className="py-4 px-6 min-w-[120px]">RESULT</th>
                <th className="py-4 px-6 text-right min-w-[110px]"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-medium">
              {filteredEvents.length === 0 ? (
                <tr>
                  <td
                    colSpan={8}
                    className="py-12 px-6 text-center text-slate-400 dark:text-slate-500 text-sm"
                  >
                    No audit trail events found. System and workflow actions will be recorded here automatically.
                  </td>
                </tr>
              ) : (
                filteredEvents.map((item) => (
                  <tr
                    key={item.id}
                    onClick={() => setSelectedEvent(item)}
                    className="transition-colors cursor-pointer hover:bg-stone-50 dark:hover:bg-white/[0.02]"
                  >
                    {/* DATE / TIME */}
                    <td className="py-5 px-6 text-slate-400 dark:text-slate-400 text-xs sm:text-sm">
                      {item.dateTime}
                    </td>

                    {/* USER */}
                    <td className="py-5 px-6 font-semibold text-slate-900 dark:text-white text-sm">
                      {item.user}
                    </td>

                    {/* ROLE */}
                    <td className="py-5 px-6 text-slate-600 dark:text-slate-400 text-sm">
                      {item.role}
                    </td>

                    {/* EVENT TYPE */}
                    <td className="py-5 px-6 text-slate-700 dark:text-slate-300 text-sm">
                      {item.eventType}
                    </td>

                    {/* ACTION */}
                    <td className="py-5 px-6 text-slate-800 dark:text-slate-300 text-sm">
                      {item.action}
                    </td>

                    {/* RELATED PROJECT */}
                    <td className="py-5 px-6 text-slate-700 dark:text-slate-300 text-sm">
                      {item.relatedProject}
                    </td>

                    {/* RESULT */}
                    <td className="py-5 px-6">
                      {item.resultType === 'success' && (
                        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border border-emerald-800/80 bg-emerald-950/40 text-emerald-300">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0" />
                          <span>{item.result}</span>
                        </span>
                      )}
                      {item.resultType === 'recorded' && (
                        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border border-emerald-800/80 bg-emerald-950/40 text-emerald-300">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0" />
                          <span>{item.result}</span>
                        </span>
                      )}
                      {item.resultType === 'open' && (
                        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border border-amber-800/80 bg-amber-950/40 text-amber-300">
                          <span className="w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0" />
                          <span>{item.result}</span>
                        </span>
                      )}
                      {!['success', 'recorded', 'open'].includes(item.resultType) && (
                        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border border-slate-700 bg-slate-800 text-slate-300">
                          <span className="w-1.5 h-1.5 rounded-full bg-slate-400 shrink-0" />
                          <span>{item.result || 'Logged'}</span>
                        </span>
                      )}
                    </td>

                    {/* VIEW DETAILS ACTION */}
                    <td className="py-5 px-6 text-right">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedEvent(item);
                        }}
                        className="text-sm font-medium text-slate-300 hover:text-white transition-colors cursor-pointer"
                      >
                        View details
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* AUDIT EVENT DETAILS MODAL */}
      {selectedEvent && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-xs animate-fadeIn"
          onClick={() => setSelectedEvent(null)}
        >
          <div
            className="w-full max-w-xl rounded-2xl border border-slate-800 bg-[#141518] text-slate-100 shadow-2xl overflow-hidden animate-scaleIn flex flex-col max-h-[90vh]"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="px-6 sm:px-8 py-5 border-b border-slate-800/80 flex items-center justify-between bg-[#121316]">
              <h2 className="text-xl font-bold text-white">
                Audit Event Details
              </h2>
              <button
                type="button"
                onClick={() => setSelectedEvent(null)}
                className="text-xs sm:text-sm font-semibold text-slate-400 hover:text-white transition-colors cursor-pointer"
              >
                Close
              </button>
            </div>

            {/* Modal Body */}
            <div className="px-6 sm:px-8 py-6 space-y-5 overflow-y-auto custom-scrollbar flex-1">
              {/* TIMESTAMP */}
              <div className="pb-5 border-b border-slate-800/80">
                <div className="text-[10px] font-mono tracking-wider text-slate-400 uppercase font-semibold mb-1">
                  TIMESTAMP
                </div>
                <div className="text-sm sm:text-base font-semibold text-white">
                  {selectedEvent.dateTime}
                </div>
              </div>

              {/* PERFORMED BY */}
              <div className="pb-5 border-b border-slate-800/80">
                <div className="text-[10px] font-mono tracking-wider text-slate-400 uppercase font-semibold mb-1">
                  PERFORMED BY
                </div>
                <div className="text-sm sm:text-base font-semibold text-white">
                  {selectedEvent.user} · {selectedEvent.role}
                </div>
              </div>

              {/* EVENT TYPE */}
              <div className="pb-5 border-b border-slate-800/80">
                <div className="text-[10px] font-mono tracking-wider text-slate-400 uppercase font-semibold mb-1">
                  EVENT TYPE
                </div>
                <div className="text-sm sm:text-base font-semibold text-white">
                  {selectedEvent.eventType}
                </div>
              </div>

              {/* RECORDED ACTION */}
              <div className="pb-5 border-b border-slate-800/80">
                <div className="text-[10px] font-mono tracking-wider text-slate-400 uppercase font-semibold mb-1">
                  RECORDED ACTION
                </div>
                <div className="text-sm sm:text-base font-semibold text-white leading-relaxed">
                  {selectedEvent.action}
                </div>
              </div>

              {/* RELATED PROJECT */}
              <div className="pb-5 border-b border-slate-800/80">
                <div className="text-[10px] font-mono tracking-wider text-slate-400 uppercase font-semibold mb-1">
                  RELATED PROJECT
                </div>
                <div className="text-sm sm:text-base font-semibold text-white">
                  {selectedEvent.relatedProject}
                </div>
              </div>

              {/* RESULT */}
              <div className="pb-5 border-b border-slate-800/80">
                <div className="text-[10px] font-mono tracking-wider text-slate-400 uppercase font-semibold mb-1">
                  RESULT
                </div>
                <div className="text-sm sm:text-base font-semibold text-white">
                  {selectedEvent.result}
                </div>
              </div>

              {/* Read-only Disclaimer */}
              <div className="pt-2 text-xs text-slate-400">
                Audit records are read-only and cannot be edited or deleted through this interface.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
