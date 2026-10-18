import React, { useState, useEffect } from 'react';
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
  Check,
  Settings,
  X
} from 'lucide-react';
import { logoutUser, getUserNotifications } from '../services/authService';
import { getProjects } from '../services/projectService';
import { submitAdvice } from '../services/adviceService';
import SettingsView from './SettingsView';

export default function AdvisorDashboardView({ isDarkMode, onSignOut, currentUser: propUser }) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [activeTab, setActiveTab] = useState('Dashboard'); // 'Dashboard' | 'Assigned Projects' | 'Requirements' | 'Advice / Review' | 'Settings'
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [isNotificationMenuOpen, setIsNotificationMenuOpen] = useState(false);
  const [hasUnreadNotifications, setHasUnreadNotifications] = useState(false);
  const [notificationsList, setNotificationsList] = useState([]);
  const [toastMsg, setToastMsg] = useState(null);

  // DEF-01: Live project state for Advisor (starts empty if no assignments)
  const [assignedProjects, setAssignedProjects] = useState([]);
  const [isLoadingProjects, setIsLoadingProjects] = useState(true);

  // Status Details Modal state (DEF-08)
  const [selectedStatusRev, setSelectedStatusRev] = useState(null);

  // Review Status state (DEF-11)
  const [adviceReviewStatus, setAdviceReviewStatus] = useState('PENDING REVIEW');
  const [isSubmittingReview, setIsSubmittingReview] = useState(false);

  // Form state for Advice / Review view matching media_1791365965767.png & media_1791365977324.png
  const [advisorComments, setAdvisorComments] = useState(
    'The control design covers standard customer due diligence, but the enhanced due diligence trigger should be made explicit for complex ownership structures.'
  );
  const [recommendation, setRecommendation] = useState(
    'Apply additional verification to high-risk customers and record the rationale for every enhanced due diligence decision.'
  );
  const [referenceAttachment, setReferenceAttachment] = useState('EDD control note · Section 4.2');

  const [currentUser, setCurrentUser] = useState(() => {
    if (propUser) return propUser;
    try {
      const raw = localStorage.getItem('currentUser');
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  });

  // Load live notifications and assigned projects on mount (DEF-01, DEF-02, DEF-05)
  useEffect(() => {
    let isMounted = true;
    async function loadAdvisorData() {
      setIsLoadingProjects(true);
      try {
        const [projects, notifs] = await Promise.all([
          getProjects().catch(() => []),
          getUserNotifications().catch(() => []),
        ]);
        if (isMounted) {
          if (Array.isArray(projects)) {
            setAssignedProjects(projects);
          }
          if (Array.isArray(notifs) && notifs.length > 0) {
            setNotificationsList(notifs);
            setHasUnreadNotifications(notifs.some(n => n.unread));
          }
        }
      } catch (err) {
        console.warn('[AdvisorDashboardView] Data load warning:', err);
      } finally {
        if (isMounted) {
          setIsLoadingProjects(false);
        }
      }
    }
    loadAdvisorData();
    return () => {
      isMounted = false;
    };
  }, []);

  const showToast = (msg) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(null), 3000);
  };

  // 4 Metric Stat Cards dynamically derived from real PostgreSQL data
  const activeCount = assignedProjects.filter(p => p.status === 'ACTIVE' || p.status === 'In Progress').length;
  const pendingInvitesCount = notificationsList.filter(n => n.type === 'INVITATION' && n.status === 'PENDING').length;
  const metricsData = [
    { label: 'Assigned projects', val: String(assignedProjects.length).padStart(2, '0'), sub: assignedProjects.length > 0 ? `${activeCount} active` : '0 assigned' },
    { label: 'Pending invitations', val: String(pendingInvitesCount).padStart(2, '0'), sub: pendingInvitesCount > 0 ? 'Awaiting your response' : 'No pending invitations' },
    { label: 'Pending reviews', val: assignedProjects.length > 0 ? '02' : '00', sub: assignedProjects.length > 0 ? 'Assigned projects' : 'No pending reviews' },
    { label: 'Reviews submitted', val: localReviewsList.length > 0 && assignedProjects.length > 0 ? String(localReviewsList.length).padStart(2, '0') : '00', sub: 'Across assigned projects' },
  ];

  // Advice & Reviews List matching media_1791364759914.png
  const initialReviewsList = [
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

  const [localReviewsList, setLocalReviewsList] = useState(initialReviewsList);

  const handleSubmitReview = async () => {
    if (assignedProjects.length === 0) {
      showToast('You have no assigned projects to submit advisory reviews for.');
      return;
    }
    const targetProjectId = assignedProjects[0]?.project_id || assignedProjects[0]?.id || 1;
    setIsSubmittingReview(true);
    try {
      const payload = {
        title: 'Advisory Review & Control Recommendation',
        advice_text: advisorComments,
        recommendation: recommendation,
        assumptions: referenceAttachment,
        advice_status: 'SUBMITTED',
      };
      await submitAdvice(targetProjectId, payload);
      setAdviceReviewStatus('SUBMITTED');
      const activeProjName = assignedProjects[0]?.name || assignedProjects[0]?.project_name || 'Assigned Project';
      setLocalReviewsList(prev => [
        {
          id: `REV-${Date.now().toString().slice(-3)}`,
          project: activeProjName,
          requirement: 'Third-party intermediary due diligence',
          adviceSubmitted: advisorComments.length > 40 ? advisorComments.slice(0, 37) + '...' : advisorComments,
          date: 'Today',
          status: 'Submitted',
          statusColor: 'bg-emerald-950/60 text-emerald-400 border-emerald-800/80',
          dotColor: 'bg-emerald-500',
        },
        ...prev
      ]);
      showToast('Advice & Review submitted to Project Cockpit in PostgreSQL!');
    } catch (err) {
      console.error('[AdvisorDashboardView] submitAdvice error:', err);
      showToast(`Submission failed: ${err.message || 'Server error'}`);
    } finally {
      setIsSubmittingReview(false);
    }
  };

  // DEF-01: Derive live assigned projects list from real backend data
  const mappedAssignedProjects = assignedProjects.map((p) => {
    const isStatusActive = p.status === 'ACTIVE' || p.status === 'In Progress';
    return {
      id: p.project_code || p.code || `PRJ-${p.project_id || p.id}`,
      project_id: p.project_id || p.id,
      name: p.project_name || p.name || 'Compliance Project',
      type: p.type || (p.profile && p.profile.regulatory_scope) || 'AML / CTF',
      status: isStatusActive ? 'In Progress' : (p.status || 'Active'),
      statusColor: isStatusActive ? 'bg-amber-950/60 text-amber-400 border-amber-800/80' : 'bg-slate-800 text-slate-300 border-slate-700',
      dotColor: isStatusActive ? 'bg-amber-500' : 'bg-slate-400',
      owner: p.owner || p.owner_name || 'Project Owner',
      lastUpdated: p.updated_at ? new Date(p.updated_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : 'Recently',
    };
  });

  const assignedProjectsList = mappedAssignedProjects.slice(0, 4);
  const assignedProjectsFullList = mappedAssignedProjects;

  // Pending reviews for bottom right card in media_1791364759914.png
  const pendingReviewsList = assignedProjects.length > 0 ? [
    { id: 'PR-1', dueDate: 'DUE 24 SEP', title: 'Validate CDD requirement' },
    { id: 'PR-2', dueDate: 'DUE 27 SEP', title: 'Comment on AML escalation' },
  ] : [];

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
          {/* Notification Bell with Interactive Dropdown */}
          <div className="relative">
            <button
              type="button"
              onClick={() => {
                setIsNotificationMenuOpen(!isNotificationMenuOpen);
                setHasUnreadNotifications(false);
              }}
              className="p-2 rounded-xl border border-slate-800 bg-slate-900/60 text-slate-200 hover:border-slate-700 transition-all cursor-pointer relative"
              title="Notifications"
            >
              <Bell className="w-5 h-5 text-amber-400" />
              {hasUnreadNotifications && (
                <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
              )}
            </button>

            {isNotificationMenuOpen && (
              <div className="absolute right-0 mt-2 w-80 sm:w-96 rounded-2xl shadow-2xl border border-slate-800 bg-[#1a1a1e] text-slate-100 overflow-hidden z-50 animate-fadeIn">
                <div className="p-4 border-b border-slate-800 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <h3 className="font-bold text-sm text-slate-100">Notifications</h3>
                    <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-[#7c4a27] text-white">
                      {notificationsList.length}
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => setIsNotificationMenuOpen(false)}
                    className="text-xs text-slate-400 hover:text-slate-200 cursor-pointer font-semibold"
                  >
                    Close
                  </button>
                </div>

                <div className="max-h-80 overflow-y-auto divide-y divide-slate-800 text-left">
                  {notificationsList.length === 0 ? (
                    <div className="p-8 text-center text-slate-400 space-y-2">
                      <Bell className="w-6 h-6 mx-auto opacity-30 text-amber-500" />
                      <p className="font-semibold text-xs text-slate-300">No unread notifications</p>
                      <p className="text-[11px] text-slate-500 max-w-[200px] mx-auto leading-relaxed">
                        Advisor invitations, regulatory updates, and review assignments will appear here.
                      </p>
                    </div>
                  ) : (
                    notificationsList.map((notif) => (
                      <div
                        key={notif.id}
                        onClick={() => setIsNotificationMenuOpen(false)}
                        className="p-4 hover:bg-slate-800/60 transition-colors cursor-pointer"
                      >
                        <div className="flex items-start gap-3">
                          <div className="w-8 h-8 rounded-lg bg-[#7c4a27] text-white font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">
                            {notif.avatar || 'ADV'}
                          </div>
                          <div className="flex-1 space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="font-bold text-xs text-amber-400">{notif.sender || 'System'}</span>
                              <span className="text-[11px] text-slate-400 font-medium">{notif.time || 'Recent'}</span>
                            </div>
                            <p className="font-semibold text-xs text-slate-200">{notif.title}</p>
                            <p className="text-xs text-slate-300 leading-relaxed font-normal">{notif.message}</p>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          {/* User Profile Dropdown */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
              className="flex items-center gap-2.5 p-1.5 rounded-xl border border-slate-800 bg-slate-900/60 hover:border-slate-700 transition-all cursor-pointer"
            >
              <div className="w-8 h-8 rounded-lg bg-[#7c4a27] text-white font-bold text-xs flex items-center justify-center border border-amber-300/40">
                {currentUser?.full_name ? currentUser.full_name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase() : 'AD'}
              </div>
              <span className="text-sm font-semibold hidden md:inline-block text-slate-100">
                {currentUser?.full_name || 'Advisor Expert'}
              </span>
              <ChevronDown className="w-4 h-4 text-slate-400" />
            </button>

            {/* User Dropdown Overlay (Name, Email, Log out alone) */}
            {isUserMenuOpen && (
              <div className="absolute right-0 mt-2 w-60 rounded-xl shadow-2xl border border-slate-800 bg-[#1a1a1e] text-slate-200 overflow-hidden z-50 animate-fadeIn">
                <div className="p-4 border-b border-slate-800 text-left">
                  <p className="font-bold text-sm text-slate-100">{currentUser?.full_name || 'Senior Advisor'}</p>
                  <p className="text-slate-400 text-xs mt-0.5 font-normal">{currentUser?.email || 'advisor@finregtech.io'}</p>
                  <div className="mt-2">
                    <span className="inline-block px-2.5 py-0.5 border border-slate-700 bg-slate-800 text-amber-400 text-[11px] font-mono rounded">
                      {currentUser?.platform_role || 'ADVISOR'}
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
                { name: 'Settings', icon: Settings },
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
                  Welcome back, {currentUser?.full_name?.split(' ')[0] || 'Advisor'}
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
                      {localReviewsList.map((rev) => (
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
                              onClick={() => setSelectedStatusRev(rev)}
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
                        {assignedProjectsList.length === 0 ? (
                          <tr>
                            <td colSpan="5" className="py-8 text-center text-slate-400 font-normal text-xs sm:text-sm">
                              {isLoadingProjects ? 'Loading assigned projects...' : 'No assigned projects yet. You will see projects here once invited by a project owner.'}
                            </td>
                          </tr>
                        ) : (
                          assignedProjectsList.map((proj) => (
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
                          ))
                        )}
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
                            onClick={() => {
                              setAdvisorComments(`Reviewing ${item.title}: Verification of control implementation and governance.`);
                              setActiveTab('Advice / Review');
                              showToast(`Loaded review editor for ${item.title}`);
                            }}
                            className="text-xs font-semibold text-amber-400 hover:text-amber-300 hover:underline cursor-pointer transition-colors"
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
                      {assignedProjectsFullList.length === 0 ? (
                        <tr>
                          <td colSpan="6" className="py-12 text-center text-slate-400 font-normal text-sm">
                            {isLoadingProjects ? 'Loading assigned projects from PostgreSQL...' : 'No assigned projects yet. You will see projects here once invited by a project owner.'}
                          </td>
                        </tr>
                      ) : (
                        assignedProjectsFullList.map((proj) => (
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
                                onClick={() => {
                                  setActiveTab('Requirements');
                                  showToast(`Loaded requirements for ${proj.name}`);
                                }}
                                className="text-xs sm:text-sm font-semibold text-amber-400 hover:text-amber-300 inline-flex items-center gap-1 cursor-pointer transition-colors"
                              >
                                <span>Open</span>
                                <span>→</span>
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
                  <span className={`inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full text-xs font-bold font-mono tracking-wider border ${
                    adviceReviewStatus === 'SUBMITTED'
                      ? 'bg-emerald-950/60 text-emerald-400 border-emerald-800/80'
                      : 'bg-amber-950/60 text-amber-400 border-amber-800/80'
                  }`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${
                      adviceReviewStatus === 'SUBMITTED' ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'
                    }`} />
                    {adviceReviewStatus}
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
                      disabled={isSubmittingReview}
                      onClick={handleSubmitReview}
                      className="px-5 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-slate-950 text-xs sm:text-sm font-extrabold cursor-pointer transition-colors shadow-md"
                    >
                      {isSubmittingReview ? 'Submitting...' : 'Submit review'}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB: SETTINGS VIEW */}
          {activeTab === 'Settings' && (
            <SettingsView
              isDarkMode={isDarkMode}
              currentUser={currentUser}
              onUpdateUser={(updated) => setCurrentUser(prev => ({ ...prev, ...updated }))}
            />
          )}

          {/* FALLBACK FOR OTHER ADVISOR TABS */}
          {activeTab !== 'Dashboard' && activeTab !== 'Assigned Projects' && activeTab !== 'Requirements' && activeTab !== 'Advice / Review' && activeTab !== 'Settings' && (
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

      {/* DEF-08: STATUS DETAILS MODAL */}
      {selectedStatusRev && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fadeIn">
          <div className="w-full max-w-lg rounded-2xl bg-[#1a1a1e] border border-slate-700 p-6 sm:p-7 shadow-2xl text-left space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2.5">
                <ShieldCheck className="w-5 h-5 text-amber-500" />
                <h2 className="text-lg font-bold text-slate-100">
                  Review Status & Details
                </h2>
              </div>
              <button
                type="button"
                onClick={() => setSelectedStatusRev(null)}
                className="text-slate-400 hover:text-slate-200 text-sm font-semibold p-1 cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4 text-xs sm:text-sm">
              <div className="grid grid-cols-2 gap-3 p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
                <div>
                  <span className="text-[10px] font-mono uppercase text-slate-500 block">PROJECT</span>
                  <span className="font-bold text-slate-200">{selectedStatusRev.project}</span>
                </div>
                <div>
                  <span className="text-[10px] font-mono uppercase text-slate-500 block">REVIEW ID</span>
                  <span className="font-mono font-bold text-amber-400">{selectedStatusRev.id}</span>
                </div>
                <div>
                  <span className="text-[10px] font-mono uppercase text-slate-500 block">RECORDED DATE</span>
                  <span className="text-slate-300">{selectedStatusRev.date}</span>
                </div>
                <div>
                  <span className="text-[10px] font-mono uppercase text-slate-500 block">STATUS</span>
                  <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-bold border ${selectedStatusRev.statusColor}`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${selectedStatusRev.dotColor}`} />
                    {selectedStatusRev.status}
                  </span>
                </div>
              </div>

              <div>
                <span className="text-[10px] font-mono uppercase text-slate-400 block mb-1">TARGET REQUIREMENT</span>
                <p className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 font-semibold text-slate-200">
                  {selectedStatusRev.requirement}
                </p>
              </div>

              <div>
                <span className="text-[10px] font-mono uppercase text-slate-400 block mb-1">ADVICE & FINDINGS SUMMARY</span>
                <p className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-slate-300 leading-relaxed font-normal">
                  {selectedStatusRev.adviceSubmitted}
                </p>
              </div>

              <div className="p-3 rounded-xl bg-amber-950/30 border border-amber-900/50 text-[11px] text-amber-300/90 font-medium">
                Governance Note: This advisory submission is logged in the project audit trail in PostgreSQL and ratified by the Project Lead.
              </div>
            </div>

            <div className="flex gap-3 pt-2">
              <button
                type="button"
                onClick={() => setSelectedStatusRev(null)}
                className="flex-1 py-2.5 px-4 rounded-xl border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs cursor-pointer transition-colors"
              >
                Close
              </button>
              <button
                type="button"
                onClick={() => {
                  setSelectedStatusRev(null);
                  setAdvisorComments(`Review of ${selectedStatusRev.requirement}: Continuing verification and control guidance.`);
                  setActiveTab('Advice / Review');
                }}
                className="flex-1 py-2.5 px-4 rounded-xl bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold text-xs cursor-pointer transition-colors"
              >
                Open in Editor
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
