import React, { useState } from 'react';
import {
  Menu,
  Bell,
  ChevronDown,
  LayoutDashboard,
  FolderKanban,
  ShieldCheck,
  FileText,
  ArrowRight,
  LogOut,
  Sparkles,
  CheckCircle2,
  Clock,
  Check
} from 'lucide-react';
import { logoutUser } from '../services/authService';

export default function AdvisorDashboardView({ isDarkMode, onSignOut }) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [activeTab, setActiveTab] = useState('Dashboard'); // 'Dashboard' | 'Assigned Projects' | 'Requirements' | 'Advice / Review'
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [toastMsg, setToastMsg] = useState(null);

  // Form state for Advice / Review view matching media_1791365965767.png & media_1791365977324.png
  const [advisorComments, setAdvisorComments] = useState(
    'The control design covers standard customer due diligence, but the enhanced due diligence trigger should be made explicit for complex ownership structures.'
  );
  const [recommendation, setRecommendation] = useState(
    'Apply additional verification to high-risk customers and record the rationale for every enhanced due diligence decision.'
  );
  const [referenceAttachment, setReferenceAttachment] = useState('EDD control note · Section 4.2');

  const showToast = (msg) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(null), 3000);
  };

  // 4 Metric Stat Cards matching media_1791364498106.png
  const metricsData = [
    { label: 'Assigned projects', val: '03', sub: '2 active, 1 complete' },
    { label: 'Pending invitations', val: '02', sub: 'Awaiting your response' },
    { label: 'Pending reviews', val: '04', sub: '2 due this week' },
    { label: 'Reviews submitted', val: '05', sub: 'Across assigned projects' },
  ];

  // Advice & Reviews List matching media_1791364759914.png
  const reviewsList = [
    {
      id: 'REV-001',
      project: 'KYC Onboarding Controls',
      requirement: 'Customer identity verification',
      adviceSubmitted: 'Retain verification method, provider res...',
      date: '18 Sep 2026',
      status: 'Needs Clarification',
      statusColor: 'bg-rose-950/60 text-rose-400 border-rose-800/80',
      dotColor: 'bg-rose-500',
    },
    {
      id: 'REV-002',
      project: 'AML Compliance Framework',
      requirement: 'Suspicious activity escalation',
      adviceSubmitted: 'Name an accountable out-of-hours de...',
      date: '23 Sep 2026',
      status: 'Pending Review',
      statusColor: 'bg-amber-950/60 text-amber-400 border-amber-800/80',
      dotColor: 'bg-amber-500',
    },
    {
      id: 'REV-003',
      project: 'AML Compliance Framework',
      requirement: 'High-risk customer approval',
      adviceSubmitted: 'Proceed with the proposed control and...',
      date: '17 Sep 2026',
      status: 'Accepted',
      statusColor: 'bg-emerald-950/60 text-emerald-400 border-emerald-800/80',
      dotColor: 'bg-emerald-500',
    },
    {
      id: 'REV-004',
      project: 'AML Compliance Framework',
      requirement: 'Enhanced due diligence evidence',
      adviceSubmitted: 'Define mandatory evidence for each ris...',
      date: '24 Sep 2026',
      status: 'Needs Clarification',
      statusColor: 'bg-rose-950/60 text-rose-400 border-rose-800/80',
      dotColor: 'bg-rose-500',
    },
  ];

  // Assigned Projects list for bottom left card in media_1791364759914.png
  const assignedProjectsList = [
    {
      id: 'PRJ-001',
      name: 'AML Compliance Framework',
      type: 'AML / CTF',
      status: 'In Progress',
      statusColor: 'bg-amber-950/60 text-amber-400 border-amber-800/80',
      dotColor: 'bg-amber-500',
      owner: 'J. Nakamura',
      lastUpdated: '22 Sep 2026',
    },
    {
      id: 'PRJ-002',
      name: 'KYC Onboarding Controls',
      type: 'KYC / CDD',
      status: 'Under Review',
      statusColor: 'bg-slate-800 text-slate-300 border-slate-700',
      dotColor: 'bg-slate-400',
      owner: 'S. Okonkwo',
      lastUpdated: '21 Sep 2026',
    },
  ];

  // Complete list of assigned projects for the dedicated Assigned Projects view (media_1791365398325.png)
  const assignedProjectsFullList = [
    {
      id: 'PRJ-001',
      name: 'AML Compliance Framework',
      type: 'AML / CTF',
      status: 'In Progress',
      statusColor: 'bg-amber-950/60 text-amber-400 border-amber-800/80',
      dotColor: 'bg-amber-500',
      owner: 'J. Nakamura',
      lastUpdated: '22 Sep 2026',
    },
    {
      id: 'PRJ-002',
      name: 'KYC Onboarding Controls',
      type: 'KYC / CDD',
      status: 'Under Review',
      statusColor: 'bg-slate-800/80 text-slate-300 border-slate-700',
      dotColor: 'bg-slate-400',
      owner: 'S. Okonkwo',
      lastUpdated: '21 Sep 2026',
    },
    {
      id: 'PRJ-003',
      name: 'Regulatory Reporting Q3',
      type: 'Reporting',
      status: 'Draft',
      statusColor: 'bg-slate-800/60 text-slate-400 border-slate-700/60',
      dotColor: 'bg-slate-500',
      owner: 'A. Petrov',
      lastUpdated: '19 Sep 2026',
    },
  ];

  // Pending reviews for bottom right card in media_1791364759914.png
  const pendingReviewsList = [
    { id: 'PR-1', dueDate: 'DUE 24 SEP', title: 'Validate CDD requirement' },
    { id: 'PR-2', dueDate: 'DUE 27 SEP', title: 'Comment on AML escalation' },
  ];

  // Regulatory requirements list matching media_1791365697701.png
  const requirementsList = [
    {
      id: 'REQ-142',
      requirement: 'Risk-sensitive customer due diligence',
      source: 'FCA Handbook · SYSC 6.3.8',
      authority: 'FCA',
      status: 'Validated',
      statusColor: 'bg-emerald-950/60 text-emerald-400 border-emerald-800/80',
      dotColor: 'bg-emerald-500',
    },
    {
      id: 'REQ-157',
      requirement: 'Ongoing transaction monitoring',
      source: 'JMLSG Guidance · Part I, 5.7',
      authority: 'JMLSG',
      status: 'Review due',
      statusColor: 'bg-amber-950/60 text-amber-400 border-amber-800/80',
      dotColor: 'bg-amber-500',
    },
    {
      id: 'REQ-163',
      requirement: 'Suspicious activity escalation',
      source: 'SAR Guidance · Chapter 3',
      authority: 'NCA',
      status: 'Validated',
      statusColor: 'bg-emerald-950/60 text-emerald-400 border-emerald-800/80',
      dotColor: 'bg-emerald-500',
    },
  ];

  return (
    <div className="min-h-screen w-full flex flex-col font-sans bg-[#121214] text-slate-100">
      {/* Toast Notification Banner */}
      {toastMsg && (
        <div className="fixed top-16 right-6 z-50 bg-[#7c4a27] dark:bg-[#96562c] text-white px-4 py-3 rounded-xl shadow-2xl flex items-center gap-2.5 animate-fadeIn font-semibold text-xs sm:text-sm border-2 border-amber-300">
          <Check className="w-5 h-5 text-amber-300 shrink-0" />
          <span>{toastMsg}</span>
        </div>
      )}

      {/* Top Header Navbar */}
      <header className="w-full border-b border-slate-800 bg-[#1a1a1e] px-4 sm:px-6 py-3 flex items-center justify-between sticky top-0 z-40">
        {/* Left Section: Sidebar Toggle + FRT Logo */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="p-1.5 rounded-lg text-slate-300 hover:bg-slate-800 transition-colors cursor-pointer"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-[#96562c] text-white font-black text-xs flex items-center justify-center tracking-tighter shadow-sm border border-amber-400/30">
              F
            </div>
            <div className="flex flex-col text-left">
              <span className="font-extrabold tracking-wider text-xs sm:text-sm text-slate-100 leading-none">
                FinRegTech
              </span>
              <span className="text-[10px] font-mono tracking-widest text-amber-400/90 uppercase mt-0.5">
                SHIPYARD
              </span>
            </div>
          </div>
        </div>

        {/* Center Title Badge matching media_1791364498106.png */}
        <div className="hidden md:flex flex-col items-center justify-center">
          <span className="text-[10px] font-mono tracking-widest text-slate-400 uppercase">
            ADVISOR WORKSPACE
          </span>
          <span className="font-extrabold tracking-wider text-sm text-slate-100 uppercase mt-0.5">
            {activeTab}
          </span>
        </div>

        {/* Right Controls: Notifications & User Profile */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => showToast('No new notifications')}
            className="p-2 rounded-xl border border-slate-800 bg-slate-900/60 text-slate-200 hover:border-slate-700 transition-all cursor-pointer"
          >
            <Bell className="w-5 h-5 text-amber-400" />
          </button>

          {/* User Profile Dropdown */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
              className="flex items-center gap-2.5 p-1.5 rounded-xl border border-slate-800 bg-slate-900/60 hover:border-slate-700 transition-all cursor-pointer"
            >
              <div className="w-8 h-8 rounded-lg bg-[#7c4a27] text-white font-bold text-xs flex items-center justify-center border border-amber-300/40">
                MC
              </div>
              <span className="text-sm font-semibold hidden md:inline-block text-slate-100">
                Maya Chen
              </span>
              <ChevronDown className="w-4 h-4 text-slate-400" />
            </button>

            {/* User Dropdown Overlay (Name, Email, Log out alone) */}
            {isUserMenuOpen && (
              <div className="absolute right-0 mt-2 w-60 rounded-xl shadow-2xl border border-slate-800 bg-[#1a1a1e] text-slate-200 overflow-hidden z-50 animate-fadeIn">
                <div className="p-4 border-b border-slate-800 text-left">
                  <p className="font-bold text-sm text-slate-100">Maya Chen</p>
                  <p className="text-slate-400 text-xs mt-0.5 font-normal">advisor@gmail.com</p>
                  <div className="mt-2">
                    <span className="inline-block px-2.5 py-0.5 border border-slate-700 bg-slate-800 text-amber-400 text-[11px] font-mono rounded">
                      Advisor
                    </span>
                  </div>
                </div>

                <div className="py-1 text-left">
                  <button
                    type="button"
                    onClick={() => {
                      logoutUser();
                      if (onSignOut) onSignOut();
                    }}
                    className="w-full flex items-center gap-2 px-4 py-2.5 text-xs sm:text-sm font-semibold text-rose-500 hover:bg-rose-950/30 transition-colors cursor-pointer"
                  >
                    <LogOut className="w-4 h-4 shrink-0" />
                    <span>Log out</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Workspace Body */}
      <div className="flex-1 flex w-full">
        {/* Left Sidebar Navigation */}
        <aside
          className={`${
            isSidebarOpen ? 'w-64' : 'w-16'
          } transition-all duration-300 border-r border-slate-800 bg-[#161619] flex flex-col justify-between p-3 z-30 shrink-0`}
        >
          <div className="space-y-4">
            {isSidebarOpen && (
              <div className="px-3 pt-2 text-left">
                <span className="text-[10px] font-mono font-extrabold tracking-widest text-slate-500 uppercase">
                  ADVISOR NAVIGATION
                </span>
              </div>
            )}

            <nav className="space-y-1">
              {[
                { name: 'Dashboard', icon: LayoutDashboard },
                { name: 'Assigned Projects', icon: FolderKanban },
                { name: 'Requirements', icon: ShieldCheck },
                { name: 'Advice / Review', icon: FileText },
              ].map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.name;

                return (
                  <button
                    key={item.name}
                    type="button"
                    onClick={() => setActiveTab(item.name)}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer ${
                      isActive
                        ? 'bg-[#96562c]/20 text-amber-400 border border-[#96562c]/30'
                        : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                    }`}
                  >
                    <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-amber-400' : 'text-slate-400'}`} />
                    {isSidebarOpen && (
                      <span className="flex-1 text-left truncate">{item.name}</span>
                    )}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Bottom Footer Status Indicator */}
          {isSidebarOpen && (
            <div className="pt-4 border-t border-slate-800/80 text-left px-2">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-xs text-slate-400 font-medium">All systems operational</span>
              </div>
            </div>
          )}
        </aside>

        {/* Advisor Main Workspace Content Container */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6 overflow-x-hidden text-left">
          {/* TAB 1: ADVISOR DASHBOARD HOME */}
          {activeTab === 'Dashboard' && (
            <div className="space-y-6 animate-fadeIn">
              {/* Header Banner matching media_1791364498106.png */}
              <div>
                <span className="text-[11px] font-mono font-extrabold tracking-widest text-slate-500 uppercase block mb-1">
                  ADVISOR WORKSPACE
                </span>
                <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-100">
                  Welcome back, Maya
                </h1>
                <p className="text-xs sm:text-sm text-slate-400 mt-1.5 font-normal max-w-2xl">
                  Review assigned projects, pending invitations, and regulatory validation tasks.
                </p>
              </div>

              {/* 4 METRIC STAT CARDS GRID */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {metricsData.map((m) => (
                  <div
                    key={m.label}
                    className="p-5 rounded-2xl border border-slate-800 bg-[#161619] shadow-md hover:border-[#96562c] transition-all cursor-pointer"
                  >
                    <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      {m.label}
                    </p>
                    <p className="text-3xl sm:text-4xl font-black mt-2 tracking-tight text-slate-100">
                      {m.val}
                    </p>
                    <p className="text-xs mt-1.5 font-medium text-slate-400">
                      {m.sub}
                    </p>
                  </div>
                ))}
              </div>

              {/* MY REVIEWS SUMMARY CARD (Advice status) matching media_1791364498106.png */}
              <div className="rounded-2xl border border-slate-800 bg-[#161619] p-5 sm:p-6 shadow-lg flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div className="space-y-1">
                  <span className="text-[10px] font-mono font-extrabold tracking-widest text-slate-400 uppercase block">
                    MY REVIEWS
                  </span>
                  <h2 className="text-lg sm:text-xl font-bold tracking-tight text-slate-100">
                    Advice status
                  </h2>
                </div>

                {/* Inline Metrics Counter Grid matching screenshot */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 sm:gap-10">
                  <div>
                    <span className="text-[10px] font-mono font-extrabold tracking-widest text-slate-400 uppercase block mb-1">
                      PENDING REVIEWS
                    </span>
                    <span className="text-xl sm:text-2xl font-bold text-amber-400">
                      2
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] font-mono font-extrabold tracking-widest text-slate-400 uppercase block mb-1">
                      SUBMITTED
                    </span>
                    <span className="text-xl sm:text-2xl font-bold text-slate-200">
                      2
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] font-mono font-extrabold tracking-widest text-slate-400 uppercase block mb-1">
                      ACCEPTED
                    </span>
                    <span className="text-xl sm:text-2xl font-bold text-emerald-400">
                      1
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] font-mono font-extrabold tracking-widest text-slate-400 uppercase block mb-1">
                      NEEDS CLARIFICATION
                    </span>
                    <span className="text-xl sm:text-2xl font-bold text-amber-400">
                      2
                    </span>
                  </div>
                </div>

                {/* View reviews button */}
                <button
                  type="button"
                  onClick={() => setActiveTab('Advice / Review')}
                  className="px-4 py-2.5 rounded-xl border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-200 font-bold text-xs sm:text-sm cursor-pointer transition-colors shrink-0 self-start md:self-auto"
                >
                  <span>View reviews</span>
                  <span className="ml-1.5">→</span>
                </button>
              </div>

              {/* ADVICE & REVIEWS TABLE CONTAINER matching media_1791364759914.png */}
              <div className="rounded-2xl border border-slate-800 bg-[#161619] shadow-lg overflow-hidden">
                <div className="p-5 border-b border-slate-800">
                  <h2 className="text-base sm:text-lg font-bold tracking-tight text-slate-100">
                    Advice &amp; Reviews
                  </h2>
                  <p className="text-xs text-slate-400 font-normal mt-0.5">
                    Your submitted advice and the Builder's latest response.
                  </p>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs sm:text-sm border-collapse min-w-[850px]">
                    <thead>
                      <tr className="border-b border-slate-800 bg-slate-900/80 text-[11px] font-extrabold uppercase tracking-wider text-slate-400">
                        <th className="py-3.5 px-5">PROJECT</th>
                        <th className="py-3.5 px-5">REQUIREMENT</th>
                        <th className="py-3.5 px-5">ADVICE SUBMITTED</th>
                        <th className="py-3.5 px-5">DATE</th>
                        <th className="py-3.5 px-5">STATUS</th>
                        <th className="py-3.5 px-5 text-right">ACTION</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-medium">
                      {reviewsList.map((rev) => (
                        <tr key={rev.id} className="hover:bg-slate-800/40 transition-colors">
                          <td className="py-4 px-5 font-bold text-slate-100 text-sm">
                            {rev.project}
                          </td>
                          <td className="py-4 px-5 text-slate-300 font-medium text-xs sm:text-sm">
                            {rev.requirement}
                          </td>
                          <td className="py-4 px-5 text-slate-300 max-w-[280px] truncate" title={rev.adviceSubmitted}>
                            {rev.adviceSubmitted}
                          </td>
                          <td className="py-4 px-5 text-slate-400 font-mono text-xs">
                            {rev.date}
                          </td>
                          <td className="py-4 px-5">
                            <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border ${rev.statusColor}`}>
                              <span className={`w-1.5 h-1.5 rounded-full ${rev.dotColor}`} />
                              {rev.status}
                            </span>
                          </td>
                          <td className="py-4 px-5 text-right">
                            <button
                              type="button"
                              onClick={() => showToast(`Viewing status details for ${rev.requirement}`)}
                              className="text-xs font-bold text-slate-300 hover:text-white flex items-center justify-end gap-1 cursor-pointer"
                            >
                              <span>View status</span>
                              <span>→</span>
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* BOTTOM TWO CARDS GRID: Assigned projects + Pending reviews matching media_1791364759914.png */}
              <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
                {/* LEFT CARD: Assigned projects (3 cols on lg) */}
                <div className="lg:col-span-3 rounded-2xl border border-slate-800 bg-[#161619] shadow-lg overflow-hidden flex flex-col justify-between">
                  <div className="p-5 border-b border-slate-800 flex items-center justify-between">
                    <h2 className="text-base sm:text-lg font-bold tracking-tight text-slate-100">
                      Assigned projects
                    </h2>
                    <button
                      type="button"
                      onClick={() => setActiveTab('Assigned Projects')}
                      className="px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-200 text-xs font-bold cursor-pointer transition-colors"
                    >
                      View all
                    </button>
                  </div>

                  <div className="overflow-x-auto custom-scrollbar pb-2">
                    <table className="w-full text-left text-xs sm:text-sm border-collapse min-w-[600px]">
                      <thead>
                        <tr className="border-b border-slate-800 bg-slate-900/80 text-[11px] font-extrabold uppercase tracking-wider text-slate-400">
                          <th className="py-3 px-5">PROJECT</th>
                          <th className="py-3 px-5">TYPE</th>
                          <th className="py-3 px-5">STATUS</th>
                          <th className="py-3 px-5">OWNER</th>
                          <th className="py-3 px-5">LAST UPDATED</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 font-medium">
                        {assignedProjectsList.map((proj) => (
                          <tr key={proj.id} className="hover:bg-slate-800/40 transition-colors">
                            <td className="py-3.5 px-5">
                              <div className="font-bold text-slate-100 text-sm">
                                {proj.name}
                              </div>
                              <div className="text-[11px] font-mono text-slate-500">
                                {proj.id}
                              </div>
                            </td>
                            <td className="py-3.5 px-5 text-slate-300 font-medium text-xs">
                              {proj.type}
                            </td>
                            <td className="py-3.5 px-5">
                              <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold border ${proj.statusColor}`}>
                                <span className={`w-1.5 h-1.5 rounded-full ${proj.dotColor}`} />
                                {proj.status}
                              </span>
                            </td>
                            <td className="py-3.5 px-5 text-slate-300 text-xs">
                              {proj.owner}
                            </td>
                            <td className="py-3.5 px-5 text-slate-400 font-mono text-xs">
                              {proj.lastUpdated}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* RIGHT CARD: Pending reviews (2 cols on lg) */}
                <div className="lg:col-span-2 rounded-2xl border border-slate-800 bg-[#161619] p-5 shadow-lg flex flex-col justify-between">
                  <div>
                    <h2 className="text-base sm:text-lg font-bold tracking-tight text-slate-100 mb-4 border-b border-slate-800 pb-3">
                      Pending reviews
                    </h2>

                    <div className="divide-y divide-slate-800/80">
                      {pendingReviewsList.map((item) => (
                        <div key={item.id} className="py-3.5 flex items-center justify-between gap-3">
                          <div className="flex items-center gap-3">
                            <span className="text-[10px] font-mono font-extrabold tracking-widest text-amber-400 uppercase shrink-0">
                              {item.dueDate}
                            </span>
                            <span className="font-bold text-slate-100 text-xs sm:text-sm">
                              {item.title}
                            </span>
                          </div>
                          <button
                            type="button"
                            onClick={() => showToast(`Opening ${item.title}...`)}
                            className="text-xs font-semibold text-slate-400 hover:text-slate-200 cursor-pointer transition-colors"
                          >
                            Review
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: ASSIGNED PROJECTS PORTFOLIO VIEW matching media_1791365398325.png */}
          {activeTab === 'Assigned Projects' && (
            <div className="space-y-6 animate-fadeIn">
              <div>
                <span className="text-[11px] font-mono font-extrabold tracking-widest text-slate-500 uppercase block mb-1">
                  ADVISORY PORTFOLIO
                </span>
                <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-100">
                  Assigned Projects
                </h1>
                <p className="text-xs sm:text-sm text-slate-400 mt-1.5 font-normal">
                  Projects where you have an active advisory or review role.
                </p>
              </div>

              {/* Table Container Card */}
              <div className="rounded-2xl border border-slate-800 bg-[#161619] shadow-lg overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs sm:text-sm border-collapse min-w-[750px]">
                    <thead>
                      <tr className="border-b border-slate-800 bg-slate-900/60 text-[11px] font-extrabold uppercase tracking-wider text-slate-400">
                        <th className="py-4 px-6">PROJECT</th>
                        <th className="py-4 px-6">TYPE</th>
                        <th className="py-4 px-6">STATUS</th>
                        <th className="py-4 px-6">OWNER</th>
                        <th className="py-4 px-6">LAST UPDATED</th>
                        <th className="py-4 px-6 text-right"></th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-medium">
                      {assignedProjectsFullList.map((proj) => (
                        <tr key={proj.id} className="hover:bg-slate-800/30 transition-colors">
                          <td className="py-4 px-6">
                            <div className="font-bold text-slate-100 text-sm sm:text-base">
                              {proj.name}
                            </div>
                            <div className="text-xs font-mono text-slate-500 mt-0.5">
                              {proj.id}
                            </div>
                          </td>
                          <td className="py-4 px-6 text-slate-300 font-medium text-xs sm:text-sm">
                            {proj.type}
                          </td>
                          <td className="py-4 px-6">
                            <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold border ${proj.statusColor}`}>
                              <span className={`w-1.5 h-1.5 rounded-full ${proj.dotColor}`} />
                              {proj.status}
                            </span>
                          </td>
                          <td className="py-4 px-6 text-slate-300 text-xs sm:text-sm">
                            {proj.owner}
                          </td>
                          <td className="py-4 px-6 text-slate-400 font-mono text-xs sm:text-sm">
                            {proj.lastUpdated}
                          </td>
                          <td className="py-4 px-6 text-right">
                            <button
                              type="button"
                              onClick={() => showToast(`Opening ${proj.name}...`)}
                              className="text-xs sm:text-sm font-semibold text-slate-300 hover:text-white inline-flex items-center gap-1 cursor-pointer transition-colors"
                            >
                              <span>Open</span>
                              <span>→</span>
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: REGULATORY REQUIREMENTS VIEW matching media_1791365697701.png */}
          {activeTab === 'Requirements' && (
            <div className="space-y-6 animate-fadeIn">
              <div>
                <span className="text-[11px] font-mono font-extrabold tracking-widest text-slate-500 uppercase block mb-1">
                  AML COMPLIANCE FRAMEWORK
                </span>
                <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-100">
                  Regulatory Requirements
                </h1>
                <p className="text-xs sm:text-sm text-slate-400 mt-1.5 font-normal">
                  Review the project's source-linked requirements and record your validation.
                </p>
              </div>

              {/* Table Container Card */}
              <div className="rounded-2xl border border-slate-800 bg-[#161619] shadow-lg overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs sm:text-sm border-collapse min-w-[750px]">
                    <thead>
                      <tr className="border-b border-slate-800 bg-slate-900/60 text-[11px] font-extrabold uppercase tracking-wider text-slate-400">
                        <th className="py-4 px-6">REQUIREMENT</th>
                        <th className="py-4 px-6">SOURCE</th>
                        <th className="py-4 px-6">AUTHORITY</th>
                        <th className="py-4 px-6">STATUS</th>
                        <th className="py-4 px-6 text-right">REVIEW ACTION</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-medium">
                      {requirementsList.map((req) => (
                        <tr key={req.id} className="hover:bg-slate-800/30 transition-colors">
                          <td className="py-4 px-6">
                            <div className="font-bold text-slate-100 text-sm sm:text-base">
                              {req.requirement}
                            </div>
                            <div className="text-xs font-mono text-slate-500 mt-0.5">
                              {req.id}
                            </div>
                          </td>
                          <td className="py-4 px-6 text-slate-300 font-medium text-xs sm:text-sm">
                            {req.source}
                          </td>
                          <td className="py-4 px-6 text-slate-300 font-medium text-xs sm:text-sm">
                            {req.authority}
                          </td>
                          <td className="py-4 px-6">
                            <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold border ${req.statusColor}`}>
                              <span className={`w-1.5 h-1.5 rounded-full ${req.dotColor}`} />
                              {req.status}
                            </span>
                          </td>
                          <td className="py-4 px-6 text-right">
                            <button
                              type="button"
                              onClick={() => setActiveTab('Advice / Review')}
                              className="px-4 py-1.5 rounded-xl border border-slate-700 bg-slate-800/90 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-colors cursor-pointer"
                            >
                              Review
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: ADVICE / REVIEW MODULE matching media_1791365965767.png & media_1791365977324.png */}
          {activeTab === 'Advice / Review' && (
            <div className="space-y-6 animate-fadeIn max-w-4xl">
              {/* Back to requirements button */}
              <div>
                <button
                  type="button"
                  onClick={() => setActiveTab('Requirements')}
                  className="inline-flex items-center gap-2 text-xs sm:text-sm font-semibold text-slate-400 hover:text-slate-200 transition-colors cursor-pointer mb-3"
                >
                  <span>←</span>
                  <span>Back to requirements</span>
                </button>

                <span className="text-[11px] font-mono font-extrabold tracking-widest text-slate-500 uppercase block mb-1">
                  ADV-001 · FCA Handbook · SYSC 6.3.8
                </span>
                <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-100">
                  Advice / Review
                </h1>
                <p className="text-xs sm:text-sm text-slate-400 mt-1 font-normal">
                  Submit your independent regulatory interpretation and recommendation.
                </p>
              </div>

              {/* Main Card Container */}
              <div className="rounded-2xl border border-slate-800 bg-[#161619] shadow-lg p-6 sm:p-8 space-y-6">
                {/* Metadata Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 border-b border-slate-800/80 pb-6">
                  <div>
                    <span className="text-[10px] font-mono font-extrabold tracking-widest text-slate-400 uppercase block mb-1.5">
                      REQUIREMENT
                    </span>
                    <span className="font-bold text-slate-100 text-sm sm:text-base block">
                      Risk-sensitive customer due diligence
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] font-mono font-extrabold tracking-widest text-slate-400 uppercase block mb-1.5">
                      REGULATORY SOURCE
                    </span>
                    <span className="font-bold text-slate-100 text-sm sm:text-base block">
                      FCA Handbook · SYSC 6.3.8
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] font-mono font-extrabold tracking-widest text-slate-400 uppercase block mb-1.5">
                      AUTHORITY
                    </span>
                    <span className="font-bold text-slate-100 text-sm sm:text-base block">
                      Financial Conduct Authority
                    </span>
                  </div>
                </div>

                {/* Review Status Pill */}
                <div>
                  <span className="text-[10px] font-mono font-extrabold tracking-widest text-slate-400 uppercase block mb-2">
                    REVIEW STATUS
                  </span>
                  <span className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full text-xs font-bold font-mono tracking-wider bg-amber-950/60 text-amber-400 border border-amber-800/80">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                    PENDING REVIEW
                  </span>
                </div>

                {/* Form Fields */}
                <div className="space-y-6 pt-2">
                  {/* Advisor comments */}
                  <div>
                    <label className="block text-xs sm:text-sm font-bold text-slate-100 mb-2">
                      Advisor comments
                    </label>
                    <textarea
                      rows={3}
                      value={advisorComments}
                      onChange={(e) => setAdvisorComments(e.target.value)}
                      className="w-full bg-[#121214] border border-slate-700/80 rounded-xl p-4 text-xs sm:text-sm text-slate-100 focus:outline-none focus:border-amber-500 transition-colors resize-y leading-relaxed"
                    />
                  </div>

                  {/* Recommendation */}
                  <div>
                    <label className="block text-xs sm:text-sm font-bold text-slate-100 mb-2">
                      Recommendation
                    </label>
                    <textarea
                      rows={3}
                      value={recommendation}
                      onChange={(e) => setRecommendation(e.target.value)}
                      className="w-full bg-[#121214] border border-slate-700/80 rounded-xl p-4 text-xs sm:text-sm text-slate-100 focus:outline-none focus:border-amber-500 transition-colors resize-y leading-relaxed"
                    />
                  </div>

                  {/* Reference / attachment */}
                  <div>
                    <label className="block text-xs sm:text-sm font-bold text-slate-100 mb-2">
                      Reference / attachment
                    </label>
                    <input
                      type="text"
                      value={referenceAttachment}
                      onChange={(e) => setReferenceAttachment(e.target.value)}
                      className="w-full bg-[#121214] border border-slate-700/80 rounded-xl px-4 py-3 text-xs sm:text-sm text-slate-100 focus:outline-none focus:border-amber-500 transition-colors"
                    />
                  </div>

                  {/* Action Buttons */}
                  <div className="flex items-center justify-end gap-3 pt-4">
                    <button
                      type="button"
                      onClick={() => setActiveTab('Requirements')}
                      className="px-5 py-2.5 rounded-xl border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-200 text-xs sm:text-sm font-bold cursor-pointer transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={() => showToast('Advice & Review submitted successfully!')}
                      className="px-5 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs sm:text-sm font-extrabold cursor-pointer transition-colors shadow-md"
                    >
                      Submit review
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* FALLBACK FOR OTHER ADVISOR TABS */}
          {activeTab !== 'Dashboard' && activeTab !== 'Assigned Projects' && activeTab !== 'Requirements' && activeTab !== 'Advice / Review' && (
            <div className="p-8 rounded-2xl border border-slate-800 bg-[#161619] text-center animate-fadeIn">
              <h2 className="text-xl font-bold mb-2 text-slate-100">{activeTab} Module</h2>
              <p className="text-slate-400 text-sm mb-6">Detailed {activeTab.toLowerCase()} data for assigned projects.</p>
              <button
                type="button"
                onClick={() => setActiveTab('Dashboard')}
                className="px-4 py-2 bg-[#96562c] text-white font-semibold rounded-xl text-xs cursor-pointer"
              >
                ← Return to Dashboard
              </button>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
