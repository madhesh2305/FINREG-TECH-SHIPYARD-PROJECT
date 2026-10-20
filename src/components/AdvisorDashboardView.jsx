import React, { useState, useEffect } from 'react';
import {
  Menu,
  Bell,
  ChevronDown,
  LayoutGrid,
  Folder,
  Shield,
  FileText,
  Settings,
  ArrowRight,
  LogOut,
  Sparkles,
  CheckCircle2,
  Clock,
  Check,
  Search,
  ExternalLink,
  Sliders,
  Filter
} from 'lucide-react';
import { logoutUser, getCurrentUser } from '../services/authService';
import { ADVISOR_PROFILES } from './AdvisorExpertiseView';

const ADVISOR_REVIEWS_STORAGE_KEY = 'finreg_advisor_reviews';

const INITIAL_REVIEWS = [];

export default function AdvisorDashboardView({
  isDarkMode = true,
  onSignOut,
  activeExpertise = null,
  onChangeExpertise,
  currentUser,
}) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [activeTab, setActiveTab] = useState('Dashboard'); // 'Dashboard' | 'My Projects' | 'Requirements' | 'My Advice & Reviews' | 'Settings'
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [isNotificationOpen, setIsNotificationOpen] = useState(false);
  const [toastMsg, setToastMsg] = useState(null);
  const [notificationPref, setNotificationPref] = useState('Project and clarification alerts');
  const [selectedProject, setSelectedProject] = useState(null); // 'PRJ-001' or null
  const [searchQuery, setSearchQuery] = useState('');

  // Dynamic User Profile state (DEF-03)
  const [userProfile, setUserProfile] = useState(currentUser || null);

  useEffect(() => {
    if (currentUser) {
      setUserProfile(currentUser);
    } else {
      async function loadUser() {
        const u = await getCurrentUser();
        if (u) setUserProfile(u);
      }
      loadUser();
    }
  }, [currentUser]);

  const userName = userProfile?.name || 'Dr. Maya Chen';
  const userFirstName = userName.split(' ')[0] || 'Maya';
  const userEmail = userProfile?.email || 'advisor@gmail.com';
  const userInitials = userName
    .split(' ')
    .filter(Boolean)
    .map((n) => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase() || 'MC';

  // Active Expertise Profile (default to Legal Partner if not provided)
  const currentExpertise =
    activeExpertise ||
    ADVISOR_PROFILES[0]; // Legal Partner

  // Form state for Advice / Review view (DEF-11: start clean/empty for new submissions)
  const [advisorComments, setAdvisorComments] = useState('');
  const [recommendation, setRecommendation] = useState('');
  const [referenceAttachment, setReferenceAttachment] = useState('');

  const showToast = (msg) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(null), 3000);
  };

  // Persistent Reviews List from localStorage (DEF-11, DEF-12)
  const [reviewsList, setReviewsList] = useState(() => {
    try {
      const saved = localStorage.getItem(ADVISOR_REVIEWS_STORAGE_KEY);
      if (saved) return JSON.parse(saved);
    } catch (e) {}
    return INITIAL_REVIEWS;
  });

  useEffect(() => {
    try {
      localStorage.setItem(ADVISOR_REVIEWS_STORAGE_KEY, JSON.stringify(reviewsList));
    } catch (e) {}
  }, [reviewsList]);

  // Handle Advice Submission with persistent save and authoritative status (DEF-11, DEF-12)
  const handleSubmitAdvice = () => {
    if (!advisorComments.trim() && !recommendation.trim()) {
      showToast('Please provide comments or recommendations before submitting.');
      return;
    }

    const todayStr = new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
    const targetProjName = activeProject?.name || 'ABC Shield';
    const targetProjId = activeProject?.id || 'PRJ-001';

    const newReview = {
      id: `ADV-REV-${Date.now()}`,
      project: targetProjName,
      projectId: targetProjId,
      requirement: 'Risk-sensitive customer due diligence',
      reqCode: 'ADV-001',
      source: 'FCA Handbook · SYSC 6.3.8',
      authority: 'Financial Conduct Authority',
      adviceSubmitted: advisorComments.trim(),
      recommendation: recommendation.trim(),
      comments: advisorComments.trim(),
      referenceAttachment: referenceAttachment.trim() || 'FCA-Advisory-Interpretations.pdf',
      attachment: referenceAttachment.trim() || 'FCA-Advisory-Interpretations.pdf',
      date: todayStr,
      dateSubmitted: todayStr,
      status: 'Submitted',
      statusColor: 'bg-blue-950/60 text-blue-400 border-blue-800/80',
      dotColor: 'bg-blue-400',
      advisor: userName,
      advisorName: userName,
      expertise: currentExpertise.name,
      advisorRole: currentExpertise.name,
      advisorEmail: userEmail,
    };

    const updated = [newReview, ...reviewsList];
    setReviewsList(updated);
    try {
      localStorage.setItem(ADVISOR_REVIEWS_STORAGE_KEY, JSON.stringify(updated));
    } catch (e) {}

    // Reset Form fields to empty (DEF-11)
    setAdvisorComments('');
    setRecommendation('');
    setReferenceAttachment('');

    showToast('Advice submitted successfully and saved to audit trail!');
    setActiveTab('Dashboard');
  };

  // Interactive Notifications State initialized to empty array
  const [notificationsList, setNotificationsList] = useState([]);

  const unreadCount = notificationsList.filter((n) => !n.read).length;

  const handleNotificationClick = (item) => {
    setNotificationsList((prev) =>
      prev.map((n) => (n.id === item.id ? { ...n, read: true } : n))
    );
    setIsNotificationOpen(false);
    if (item.tab) {
      setActiveTab(item.tab);
    }
  };

  const handleMarkAllRead = () => {
    setNotificationsList((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  // Seeded advisor projects initialized to empty array (ready for live backend project assignments)
  const SEEDED_ADVISOR_PROJECTS = [];

  // Load dynamically assigned projects for this specific advisor account
  const [assignedProjectsFullList, setAssignedProjectsFullList] = useState(() => {
    try {
      const email = (currentUser?.email || '').toLowerCase();
      const name = currentUser?.name || '';
      const rawAssignments = localStorage.getItem('finreg_advisor_assignments');
      const assignments = rawAssignments ? JSON.parse(rawAssignments) : [];

      const myAssignments = assignments.filter((a) => {
        const matchesEmail = email && a.advisorEmail && a.advisorEmail.toLowerCase() === email;
        const matchesName = name && a.advisorName && a.advisorName.toLowerCase() === name.toLowerCase();
        const matchesId = a.advisorId && (a.advisorId === currentUser?.id);
        return matchesEmail || matchesName || matchesId;
      });

      if (myAssignments.length > 0) {
        return myAssignments.map((a) => ({
          id: a.projectId || 'PRJ-001',
          name: a.project || a.projectName || 'Assigned Project',
          company: a.company || 'Northbank Financial',
          domain: a.role || currentExpertise?.domain || 'Regulatory Advisory',
          nextAction: 'Review project requirements & provide compliance guidance',
          type: a.projectType || 'AML / CTF',
          status: 'In Progress',
          statusColor: 'bg-amber-950/40 text-amber-400 border-amber-800/50',
          dotColor: 'bg-amber-400',
          owner: a.invitedBy || 'Project Owner',
          lastUpdated: 'Recently assigned',
        }));
      }

      return [];
    } catch (e) {
      return [];
    }
  });

  // Re-sync assignments whenever currentUser updates
  useEffect(() => {
    try {
      const email = (currentUser?.email || userProfile?.email || '').toLowerCase();
      const name = currentUser?.name || userProfile?.name || '';
      const rawAssignments = localStorage.getItem('finreg_advisor_assignments');
      const assignments = rawAssignments ? JSON.parse(rawAssignments) : [];

      const myAssignments = assignments.filter((a) => {
        const matchesEmail = email && a.advisorEmail && a.advisorEmail.toLowerCase() === email;
        const matchesName = name && a.advisorName && a.advisorName.toLowerCase() === name.toLowerCase();
        const matchesId = a.advisorId && (a.advisorId === currentUser?.id || a.advisorId === userProfile?.id);
        return matchesEmail || matchesName || matchesId;
      });

      if (myAssignments.length > 0) {
        setAssignedProjectsFullList(
          myAssignments.map((a) => ({
            id: a.projectId || 'PRJ-001',
            name: a.project || a.projectName || 'Assigned Project',
            company: a.company || 'Northbank Financial',
            domain: a.role || currentExpertise?.domain || 'Regulatory Advisory',
            nextAction: 'Review project requirements & provide compliance guidance',
            type: a.projectType || 'AML / CTF',
            status: 'In Progress',
            statusColor: 'bg-amber-950/40 text-amber-400 border-amber-800/50',
            dotColor: 'bg-amber-400',
            owner: a.invitedBy || 'Project Owner',
            lastUpdated: 'Recently assigned',
          }))
        );
      } else {
        setAssignedProjectsFullList([]);
      }
    } catch (e) {}
  }, [currentUser, userProfile, currentExpertise]);

  // 4 Metric Stat Cards matching media_1791949893756_6c538f7d.png
  const submittedCount = reviewsList.filter((r) => r.status === 'Submitted' || r.status === 'Accepted').length;
  const assignedCount = assignedProjectsFullList.length;
  const metricsData = [
    {
      label: 'Assigned Projects',
      val: String(assignedCount).padStart(2, '0'),
      sub: assignedCount > 0 ? 'Explicitly granted access' : 'No projects assigned yet',
    },
    {
      label: 'Pending Advice',
      val: assignedCount > 0 ? '01' : '00',
      sub: assignedCount > 0 ? 'Requirements awaiting advice' : 'No requirements pending',
    },
    {
      label: 'Submitted Advice',
      val: String(submittedCount).padStart(2, '0'),
      sub: 'Current expertise profile',
    },
    {
      label: 'Pending Invitations',
      val: assignedCount > 0 ? '01' : '00',
      sub: 'Shown here instead of separate navigation',
    },
  ];

  // Authoritative active project based on selectedProject ID (DEF-08, DEF-10)
  const activeProject = assignedProjectsFullList.find((p) => p.id === selectedProject) || assignedProjectsFullList[0] || null;

  // Requirements List initialized to empty array (ready for live backend requirements)
  const requirementsList = [];



  return (
    <div className="min-h-screen w-full flex flex-col font-sans bg-[#0f1013] text-slate-100">
      {/* Toast Notification Banner */}
      {toastMsg && (
        <div className="fixed top-16 right-6 z-50 bg-[#1e1c18] text-white px-4 py-3 rounded-md shadow-2xl flex items-center gap-2.5 animate-fadeIn font-semibold text-xs sm:text-sm border border-amber-500/50">
          <Check className="w-5 h-5 text-amber-400 shrink-0" />
          <span>{toastMsg}</span>
        </div>
      )}

      {/* Top Header Navbar */}
      <header className="w-full border-b border-slate-800 bg-[#16181d] px-4 sm:px-6 py-3 flex items-center justify-between sticky top-0 z-40">
        {/* Left Section: Sidebar Toggle + FRT Logo */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="p-1.5 rounded-md text-slate-300 hover:bg-slate-800 transition-colors cursor-pointer"
            title="Toggle Sidebar"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-md bg-[#7c4a27] text-white font-black text-xs flex items-center justify-center tracking-tighter shadow-sm border border-amber-400/30">
              F
            </div>
            <div className="flex flex-col text-left">
              <span className="font-extrabold tracking-wider text-xs sm:text-sm text-slate-100 leading-none">
                FinRegTech
              </span>
              <span className="text-[10px] font-mono tracking-widest text-amber-400 uppercase mt-0.5">
                SHIPYARD
              </span>
            </div>
          </div>
        </div>

        {/* Center Title Badge */}
        {/* Center Search Bar matching media_1791957465637_d7afbed5.png */}
        <div className="hidden md:flex items-center relative w-64 lg:w-80">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search accessible proj"
            className="w-full bg-[#101216] border border-slate-800 rounded-md pl-9 pr-4 py-1.5 text-xs text-slate-300 placeholder-slate-500 focus:outline-none focus:border-amber-500/60"
          />
        </div>

        {/* Right Controls: Expertise Badge, Change Expertise, Notifications & User Profile */}
        <div className="flex items-center gap-3">
          {/* Active Expertise Pill Badge */}
          <div className="hidden sm:inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-[#241c12] border border-amber-600/40 text-amber-400">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
            <span>{currentExpertise.name}</span>
          </div>

          {/* Change Expertise Button */}
          {onChangeExpertise && (
            <button
              type="button"
              onClick={onChangeExpertise}
              className="px-3 py-1.5 rounded-md border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-colors cursor-pointer"
            >
              Change Expertise
            </button>
          )}

          {/* Notification Bell with interactive dropdown (DEF-05) */}
          <div className="relative">
            <button
              type="button"
              onClick={() => {
                setIsNotificationOpen(!isNotificationOpen);
                setIsUserMenuOpen(false);
              }}
              title="Notifications"
              className="p-2 text-slate-400 hover:text-white transition-colors cursor-pointer relative"
            >
              <Bell className="w-5 h-5 text-slate-300" />
              {unreadCount > 0 && (
                <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 rounded-full bg-amber-400 border-2 border-[#16181d] animate-pulse" />
              )}
            </button>

            {isNotificationOpen && (
              <div className="absolute right-0 mt-3 w-80 sm:w-[350px] rounded-2xl bg-[#16181d] border border-slate-700/80 shadow-2xl overflow-hidden z-50 text-left animate-fadeIn">
                <div className="px-6 pt-5 pb-3 flex items-center justify-between border-b border-slate-800">
                  <h3 className="text-base sm:text-lg font-bold text-white">Notifications</h3>
                  {unreadCount > 0 && (
                    <button
                      type="button"
                      onClick={handleMarkAllRead}
                      className="text-xs text-amber-400 hover:text-amber-300 font-semibold cursor-pointer"
                    >
                      Mark all as read
                    </button>
                  )}
                </div>
                <div className="divide-y divide-slate-800/80 max-h-80 overflow-y-auto">
                  {notificationsList.map((item) => (
                    <div
                      key={item.id}
                      onClick={() => handleNotificationClick(item)}
                      className={`px-6 py-4 flex items-center justify-between gap-3 text-sm transition-colors cursor-pointer ${
                        item.read
                          ? 'text-slate-400 hover:bg-white/[0.04]'
                          : 'text-slate-100 font-semibold bg-amber-500/[0.04] hover:bg-amber-500/[0.08]'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <span
                          className={`w-2 h-2 rounded-full shrink-0 ${
                            item.read ? 'bg-slate-600' : 'bg-amber-400'
                          }`}
                        />
                        <span>{item.text}</span>
                      </div>
                      {!item.read && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono">
                          New
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* User Profile Dropdown (DEF-03) */}
          <div className="relative">
            <button
              type="button"
              onClick={() => {
                setIsUserMenuOpen(!isUserMenuOpen);
                setIsNotificationOpen(false);
              }}
              className="flex items-center gap-2.5 p-1.5 rounded-md border border-slate-800 bg-slate-900/60 hover:border-slate-700 transition-all cursor-pointer"
            >
              <div className="w-8 h-8 rounded-md bg-[#7c4a27] text-white font-bold text-xs flex items-center justify-center border border-amber-300/40">
                {userInitials}
              </div>
              <span className="text-sm font-semibold hidden md:inline-block text-slate-100">
                {userName}
              </span>
              <ChevronDown className="w-4 h-4 text-slate-400" />
            </button>

            {isUserMenuOpen && (
              <div className="absolute right-0 mt-2 w-64 rounded-xl shadow-2xl border border-slate-800 bg-[#1a1c22] text-slate-200 overflow-hidden z-50 animate-fadeIn text-left">
                <div className="p-4 border-b border-slate-800">
                  <p className="font-bold text-sm text-slate-100">{userName}</p>
                  <p className="text-slate-400 text-xs mt-0.5">{userEmail}</p>
                  <div className="mt-2.5 flex items-center gap-2">
                    <span className="inline-block px-2.5 py-0.5 border border-amber-600/40 bg-amber-500/10 text-amber-400 text-[11px] font-mono rounded">
                      {currentExpertise.name}
                    </span>
                  </div>
                </div>

                <div className="py-1">
                  {onChangeExpertise && (
                    <button
                      type="button"
                      onClick={() => {
                        setIsUserMenuOpen(false);
                        onChangeExpertise();
                      }}
                      className="w-full flex items-center gap-2 px-4 py-2 text-xs text-slate-300 hover:bg-slate-800 cursor-pointer"
                    >
                      <Sliders className="w-3.5 h-3.5 text-amber-400" />
                      <span>Configure Expertise Profile</span>
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => {
                      logoutUser();
                      if (onSignOut) onSignOut();
                    }}
                    className="w-full flex items-center gap-2 px-4 py-2.5 text-xs sm:text-sm font-semibold text-rose-400 hover:bg-rose-950/30 transition-colors cursor-pointer"
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
        {/* Left Sidebar Navigation matching media_1791949893756_6c538f7d.png */}
        <aside
          className={`${
            isSidebarOpen ? 'w-64' : 'w-16'
          } transition-all duration-300 border-r border-slate-800 bg-[#121316] flex flex-col justify-between p-3 z-30 shrink-0`}
        >
          <div className="space-y-4">
            {isSidebarOpen && (
              <div className="px-3 pt-3 text-left">
                <span className="text-[10px] font-mono font-extrabold tracking-widest text-slate-500 uppercase">
                  ADVISOR NAVIGATION
                </span>
              </div>
            )}

            <nav className="space-y-1 text-left">
              {[
                { name: 'Dashboard', icon: LayoutGrid },
                { name: 'My Projects', icon: Folder },
                { name: 'Requirements', icon: Shield },
                { name: 'My Advice & Reviews', icon: FileText },
                { name: 'Settings', icon: Settings },
              ].map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.name;

                return (
                  <button
                    key={item.name}
                    type="button"
                    onClick={() => setActiveTab(item.name)}
                    className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-md text-xs sm:text-sm font-semibold transition-all cursor-pointer ${
                      isActive
                        ? 'bg-[#2a1d12] text-amber-400 border border-amber-600/50 shadow-sm'
                        : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200 border border-transparent'
                    }`}
                  >
                    <Icon
                      className={`w-4 h-4 shrink-0 ${
                        isActive ? 'text-amber-400' : 'text-slate-400'
                      }`}
                    />
                    {isSidebarOpen && (
                      <span className="flex-1 text-left truncate">{item.name}</span>
                    )}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Bottom Sidebar Status matching media_1791954134407_7946b208.png */}
          {isSidebarOpen && (
            <div className="pt-4 border-t border-slate-800/80 text-left px-3 space-y-1.5">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-xs text-slate-300 font-medium">
                  All systems operational
                </span>
              </div>
              <div className="text-[10px] text-slate-500 font-mono leading-tight">
                <p>FinRegTech ShipYard</p>
                <p className="text-slate-600">Prototype · September 2026</p>
              </div>
              <div className="pt-2">
                <button
                  type="button"
                  onClick={() => {
                    logoutUser();
                    if (onSignOut) onSignOut();
                  }}
                  className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-rose-400 transition-colors cursor-pointer"
                >
                  <span>←</span>
                  <span>Logout</span>
                </button>
              </div>
            </div>
          )}
        </aside>

        {/* Advisor Main Workspace Content Container */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6 overflow-x-hidden text-left">
          {/* TAB 1: UNIFIED ADVISOR DASHBOARD matching media_1791949893756_6c538f7d.png */}
          {activeTab === 'Dashboard' && (
            <div className="space-y-6 animate-fadeIn">
              {/* Header Titles matching screenshot */}
              <div>
                <span className="text-[11px] font-mono font-bold tracking-widest text-slate-400 uppercase block mb-1">
                  UNIFIED ADVISOR DASHBOARD
                </span>
                <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
                  Welcome back, {userFirstName}
                </h1>
                <p className="text-xs sm:text-sm text-slate-400 mt-1 font-normal">
                  {currentExpertise.name} · {currentExpertise.subtitle}
                </p>
              </div>

              {/* 4 Metric Stat Cards matching media_1791949893756_6c538f7d.png */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {metricsData.map((m) => (
                  <div
                    key={m.label}
                    className="p-5 rounded-2xl border border-slate-800/90 bg-[#16181d] shadow-md hover:border-slate-700 transition-all text-left"
                  >
                    <p className="text-xs font-semibold text-slate-400">
                      {m.label}
                    </p>
                    <p className="text-3xl sm:text-4xl font-black mt-2 tracking-tight text-white">
                      {m.val}
                    </p>
                    <p className="text-xs mt-1.5 font-normal text-slate-500">
                      {m.sub}
                    </p>
                  </div>
                ))}
              </div>

              {/* My Assigned Projects Section matching media_1791949893756_6c538f7d.png */}
              <div className="rounded-2xl border border-slate-800/90 bg-[#16181d] p-6 shadow-lg text-left">
                {/* Header row with Title and 'View all projects' button */}
                <div className="flex items-center justify-between pb-4 border-b border-slate-800/80 mb-4">
                  <div>
                    <h2 className="text-lg sm:text-xl font-bold tracking-tight text-white">
                      My Assigned Projects
                    </h2>
                    <p className="text-xs text-slate-400 mt-0.5 font-normal">
                      {currentExpertise.workspaceText ||
                        `Projects permitted for the active ${currentExpertise.name} workspace.`}
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={() => setActiveTab('My Projects')}
                    className="px-3.5 py-1.5 rounded-md border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-200 text-xs font-semibold cursor-pointer transition-colors"
                  >
                    View all projects
                  </button>
                </div>

                {/* Table or Empty State (DEF-01) */}
                {assignedProjectsFullList.length === 0 ? (
                  <div className="py-12 px-6 text-center border border-dashed border-slate-800 rounded-xl bg-slate-900/30">
                    <Folder className="w-10 h-10 text-slate-600 mx-auto mb-3 stroke-[1.5]" />
                    <h3 className="text-base font-bold text-slate-200">No Projects Assigned Yet</h3>
                    <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
                      You are not currently assigned to any regulatory compliance projects. When a Project Owner invites you to review their project, it will appear here.
                    </p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs sm:text-sm border-collapse min-w-[700px]">
                      <thead>
                        <tr className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-500 pb-3">
                          <th className="py-2.5 px-3">PROJECT NAME</th>
                          <th className="py-2.5 px-3">COMPANY</th>
                          <th className="py-2.5 px-3">PROJECT STATUS</th>
                          <th className="py-2.5 px-3">RELEVANT EXPERTISE / DOMAIN</th>
                          <th className="py-2.5 px-3">NEXT ACTION</th>
                          <th className="py-2.5 px-3 text-right"></th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 font-medium">
                        {assignedProjectsFullList.map((proj) => (
                          <tr key={proj.id} className="hover:bg-slate-800/20 transition-colors">
                            {/* Project Name */}
                            <td className="py-4 px-3">
                              <div className="font-bold text-white text-sm">
                                {proj.name}
                              </div>
                              <div className="text-[11px] font-mono text-slate-500 mt-0.5">
                                {proj.id}
                              </div>
                            </td>

                            {/* Company */}
                            <td className="py-4 px-3 text-slate-300 font-medium text-xs sm:text-sm">
                              {proj.company}
                            </td>

                            {/* Project Status */}
                            <td className="py-4 px-3">
                              <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold border ${proj.statusColor}`}>
                                <span className={`w-1.5 h-1.5 rounded-full ${proj.dotColor}`} />
                                <span>{proj.status}</span>
                              </span>
                            </td>

                            {/* Relevant Expertise / Domain */}
                            <td className="py-4 px-3 text-slate-300 font-medium text-xs sm:text-sm">
                              {proj.domain}
                            </td>

                            {/* Next Action */}
                            <td className="py-4 px-3 text-slate-300 font-medium text-xs sm:text-sm">
                              {proj.nextAction}
                            </td>

                            {/* Action link */}
                            <td className="py-4 px-3 text-right">
                              <button
                                type="button"
                                onClick={() => {
                                  setSelectedProject(proj.id);
                                  setActiveTab('My Projects');
                                }}
                                className="text-xs sm:text-sm font-semibold text-slate-300 hover:text-white inline-flex items-center gap-1 cursor-pointer transition-colors"
                              >
                                <span>Open Project</span>
                                <span>→</span>
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Bottom Two Cards: Recent Activity & Pending Work matching screenshot */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* LEFT CARD: Recent Activity */}
                <div className="rounded-2xl border border-slate-800/90 bg-[#16181d] p-6 shadow-lg flex flex-col justify-between text-left">
                  <div>
                    <div className="flex items-center justify-between pb-4 border-b border-slate-800/80 mb-4">
                      <h2 className="text-base sm:text-lg font-bold tracking-tight text-white">
                        Recent Activity
                      </h2>
                      <button
                        type="button"
                        onClick={() => setActiveTab('My Advice & Reviews')}
                        className="px-3 py-1.5 rounded-md border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-200 text-xs font-semibold cursor-pointer transition-colors"
                      >
                        View advice history
                      </button>
                    </div>

                    <div className="space-y-3.5 text-xs sm:text-sm">
                      <div className="flex items-start gap-3 text-slate-300">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 shrink-0" />
                        <div>
                          <p className="font-semibold text-white">Project invitation accepted by Dr. Chen</p>
                          <p className="text-xs text-slate-500 mt-0.5">Northbank Financial · PRJ-001</p>
                        </div>
                      </div>

                      <div className="flex items-start gap-3 text-slate-300">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 shrink-0" />
                        <div>
                          <p className="font-semibold text-white">New FCA source version available for ABC Shield</p>
                          <p className="text-xs text-slate-500 mt-0.5">FCA Handbook · SYSC 6.3.8 update</p>
                        </div>
                      </div>

                      <div className="flex items-start gap-3 text-slate-300">
                        <span className="w-1.5 h-1.5 rounded-full bg-slate-500 mt-1.5 shrink-0" />
                        <div>
                          <p className="font-semibold text-slate-300">Workspace initialized for {currentExpertise.name}</p>
                          <p className="text-xs text-slate-500 mt-0.5">Default advisory permissions applied</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* RIGHT CARD: Pending Work */}
                <div className="rounded-2xl border border-slate-800/90 bg-[#16181d] p-6 shadow-lg flex flex-col justify-between text-left">
                  <div>
                    <div className="flex items-center justify-between pb-4 border-b border-slate-800/80 mb-4">
                      <h2 className="text-base sm:text-lg font-bold tracking-tight text-white">
                        Pending Work
                      </h2>
                      <button
                        type="button"
                        onClick={() => setActiveTab('Requirements')}
                        className="px-3 py-1.5 rounded-md border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-200 text-xs font-semibold cursor-pointer transition-colors"
                      >
                        Open requirements
                      </button>
                    </div>

                    <div className="space-y-3.5 text-xs sm:text-sm">
                      {assignedProjectsFullList.length === 0 ? (
                        <div className="py-8 text-center text-xs text-slate-500 font-medium">
                          No pending advisor reviews or actions at this time.
                        </div>
                      ) : (
                        <>
                          <div className="flex items-center justify-between gap-3 p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="text-[10px] font-mono font-bold text-amber-400 uppercase">
                                  {currentExpertise?.dueDate || 'DUE 24 SEP'}
                                </span>
                                <span className="text-xs text-slate-500">· {assignedProjectsFullList[0]?.name || 'Assigned Project'}</span>
                              </div>
                              <p className="font-bold text-white text-xs sm:text-sm mt-0.5">
                                {currentExpertise?.nextAction || 'Review regulatory requirements'}
                              </p>
                            </div>
                            <button
                              type="button"
                              onClick={() => setActiveTab('Requirements')}
                              className="px-3 py-1 rounded-md bg-amber-500/20 text-amber-300 border border-amber-500/40 hover:bg-amber-500/30 text-xs font-bold cursor-pointer transition-colors"
                            >
                              Review
                            </button>
                          </div>

                          <div className="flex items-center justify-between gap-3 p-3 rounded-xl bg-slate-900/60 border border-slate-800">
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="text-[10px] font-mono font-bold text-amber-400 uppercase">
                                  DUE 27 SEP
                                </span>
                                <span className="text-xs text-slate-500">· {assignedProjectsFullList[0]?.name || 'Assigned Project'}</span>
                              </div>
                              <p className="font-bold text-white text-xs sm:text-sm mt-0.5">
                                Validate CDD requirement on ownership structures
                              </p>
                            </div>
                            <button
                              type="button"
                              onClick={() => setActiveTab('Requirements')}
                              className="px-3 py-1 rounded-md bg-slate-800 text-slate-300 hover:text-white text-xs font-bold cursor-pointer transition-colors"
                            >
                              Review
                            </button>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: MY PROJECTS VIEW matching media_1791957465637_d7afbed5.png & media_1791957478401_7ffb2d4c.png */}
          {activeTab === 'My Projects' && (
            selectedProject ? (
              /* PROJECT OVERVIEW VIEW matching Images 1 & 2 (DEF-08, DEF-10) */
              <div className="space-y-6 animate-fadeIn w-full">
                {/* Top Back Navigation */}
                <div>
                  <button
                    type="button"
                    onClick={() => setSelectedProject(null)}
                    className="inline-flex items-center gap-1.5 text-xs sm:text-sm font-medium text-slate-400 hover:text-slate-200 transition-colors cursor-pointer mb-2.5"
                  >
                    <span>←</span>
                    <span>Back to my projects</span>
                  </button>

                  <span className="text-xs font-mono text-slate-500 uppercase tracking-widest block mb-1">
                    {activeProject.id}
                  </span>

                  <div className="flex items-center justify-between gap-4">
                    <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
                      {activeProject.name}
                    </h1>
                    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border ${activeProject.statusColor}`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${activeProject.dotColor}`} />
                      <span>{activeProject.status}</span>
                    </span>
                  </div>

                  <p className="text-xs sm:text-sm text-slate-400 mt-1 font-normal max-w-3xl">
                    Permitted project overview for {currentExpertise.name}. Restricted documents and unrelated requirements are not shown.
                  </p>
                </div>

                {/* 4 Metadata Columns Grid matching Image 1 */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-6 py-6 border-y border-slate-800/80 my-4">
                  <div>
                    <span className="text-[10px] font-mono font-bold tracking-widest text-slate-500 uppercase block mb-1.5">
                      COMPANY
                    </span>
                    <p className="text-sm font-semibold text-white">
                      {activeProject.company}
                    </p>
                  </div>
                  <div>
                    <span className="text-[10px] font-mono font-bold tracking-widest text-slate-500 uppercase block mb-1.5">
                      RELEVANT DOMAIN
                    </span>
                    <p className="text-sm font-semibold text-white">
                      {currentExpertise.cleanDomain || 'Financial Crime Compliance'}
                    </p>
                  </div>
                  <div>
                    <span className="text-[10px] font-mono font-bold tracking-widest text-slate-500 uppercase block mb-1.5">
                      PERMISSION
                    </span>
                    <p className="text-sm font-semibold text-white">
                      Requirements, shared resources, and advice submission
                    </p>
                  </div>
                  <div>
                    <span className="text-[10px] font-mono font-bold tracking-widest text-slate-500 uppercase block mb-1.5">
                      LAST UPDATED
                    </span>
                    <p className="text-sm font-semibold text-white">
                      22 Sep 2026
                    </p>
                  </div>
                </div>

                {/* Two Cards Side-by-Side: Expertise-relevant requirements & Next action */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Left Card: Expertise-relevant requirements */}
                  <div className="rounded-2xl border border-slate-800/90 bg-[#131519] p-6 shadow-lg flex flex-col justify-between text-left">
                    <div>
                      <h2 className="text-base sm:text-lg font-bold tracking-tight text-white mb-4">
                        Expertise-relevant requirements
                      </h2>
                      <div className="p-4 rounded-xl bg-[#0c0e12] border border-slate-800/80 flex items-center justify-between gap-4">
                        <div className="flex items-center gap-3">
                          <span className="text-xs font-mono font-bold text-[#c58d31] uppercase shrink-0">
                            LEG-101
                          </span>
                          <span className="font-semibold text-white text-xs sm:text-sm">
                            Contractual responsibilities and liability allocation
                          </span>
                        </div>
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#281d11] border border-amber-700/50 text-amber-400 shrink-0">
                          <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                          <span>Review due</span>
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Right Card: Next action with Open Requirements button */}
                  <div className="rounded-2xl border border-slate-800/90 bg-[#131519] p-6 shadow-lg flex flex-col justify-between text-left">
                    <div>
                      <h2 className="text-base sm:text-lg font-bold tracking-tight text-white mb-2">
                        Next action
                      </h2>
                      <p className="text-xs sm:text-sm text-slate-400 font-normal leading-relaxed mb-6">
                        {currentExpertise.subtitle} Open the shared Requirements page to submit advice against an exact assigned item.
                      </p>
                    </div>
                    <div className="pt-2">
                      <button
                        type="button"
                        onClick={() => {
                          setActiveTab('Requirements');
                        }}
                        className="px-5 py-2.5 rounded-md bg-[#e3a63a] hover:bg-[#d6982e] active:scale-[0.99] text-slate-950 font-bold text-xs sm:text-sm transition-all cursor-pointer shadow-md inline-flex items-center gap-1.5"
                      >
                        <span>Open Requirements</span>
                        <span>→</span>
                      </button>
                    </div>
                  </div>
                </div>

                {/* Bottom Card: Permitted Project Resources matching Image 2 */}
                <div className="rounded-2xl border border-slate-800/90 bg-[#131519] p-6 shadow-lg text-left">
                  <span className="text-[10px] font-mono font-bold tracking-widest text-slate-500 uppercase block mb-1">
                    PERMITTED PROJECT RESOURCES
                  </span>
                  <h2 className="text-base sm:text-lg font-bold tracking-tight text-white mb-4">
                    Documents and supporting references
                  </h2>
                  <div className="p-4 rounded-xl bg-[#0c0e12] border border-slate-800/80 flex items-center justify-between gap-4">
                    <div className="flex items-center gap-3.5">
                      <div className="w-10 h-10 rounded-lg border border-amber-500/40 bg-amber-500/10 text-amber-400 flex items-center justify-center shrink-0">
                        <FileText className="w-5 h-5" />
                      </div>
                      <div>
                        <p className="font-bold text-white text-xs sm:text-sm">
                          Project Services Agreement
                        </p>
                        <p className="text-xs text-slate-400 mt-0.5">
                          ABC Shield · Contractual responsibilities and liability allocation
                        </p>
                        <p className="text-[11px] text-slate-500 mt-0.5">
                          Shared project reference
                        </p>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => showToast('Viewing Project Services Agreement resource...')}
                      className="text-xs sm:text-sm font-semibold text-slate-300 hover:text-white cursor-pointer transition-colors shrink-0"
                    >
                      View Resource
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              /* MY PROJECTS PORTFOLIO LIST */
              <div className="space-y-6 animate-fadeIn">
                <div>
                  <span className="text-[11px] font-mono font-extrabold tracking-widest text-slate-500 uppercase block mb-1">
                    ADVISORY PORTFOLIO
                  </span>
                  <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
                    My Projects
                  </h1>
                  <p className="text-xs sm:text-sm text-slate-400 mt-1 font-normal">
                    Projects permitted for your active {currentExpertise.name} advisory workspace.
                  </p>
                </div>

                <div className="rounded-2xl border border-slate-800 bg-[#16181d] shadow-lg overflow-hidden">
                  {assignedProjectsFullList.length === 0 ? (
                    <div className="py-16 px-6 text-center">
                      <Folder className="w-12 h-12 text-slate-600 mx-auto mb-3 stroke-[1.5]" />
                      <h3 className="text-lg font-bold text-slate-200">No Assigned Projects</h3>
                      <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-md mx-auto">
                        There are no active projects associated with your advisor identity. Project invitations received from builders will be displayed here.
                      </p>
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs sm:text-sm border-collapse min-w-[750px]">
                        <thead>
                          <tr className="border-b border-slate-800 bg-slate-900/60 text-[11px] font-extrabold uppercase tracking-wider text-slate-400">
                            <th className="py-4 px-6">PROJECT</th>
                            <th className="py-4 px-6">COMPANY</th>
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
                                {proj.company}
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
                                    setSelectedProject(proj.id);
                                  }}
                                  className="text-xs sm:text-sm font-semibold text-slate-300 hover:text-white inline-flex items-center gap-1 cursor-pointer transition-colors"
                                >
                                  <span>Open Project</span>
                                  <span>→</span>
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </div>
            )
          )}

          {/* TAB 3: REGULATORY REQUIREMENTS VIEW matching media_1791957523546_e3a2b054.png */}
          {activeTab === 'Requirements' && (
            <div className="space-y-6 animate-fadeIn w-full text-left">
              <div>
                <span className="text-[11px] font-mono font-bold tracking-widest text-slate-500 uppercase block mb-1">
                  {currentExpertise.name.toUpperCase()} · ASSIGNED CONTENT
                </span>
                <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
                  Requirements
                </h1>
                <p className="text-xs sm:text-sm text-slate-400 mt-1 font-normal">
                  Requirements and topics filtered by selected expertise and assigned project access.
                </p>
              </div>

              {/* Requirements Table Card matching Image 3 (DEF-01) */}
              <div className="rounded-2xl border border-slate-800/90 bg-[#131519] shadow-lg p-6 overflow-hidden">
                {assignedProjectsFullList.length === 0 ? (
                  <div className="py-14 px-6 text-center">
                    <Shield className="w-12 h-12 text-slate-600 mx-auto mb-3 stroke-[1.5]" />
                    <h3 className="text-lg font-bold text-slate-200">No Requirements to Review</h3>
                    <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-md mx-auto">
                      You have not been assigned to any project requirements yet. Once assigned to a compliance project, relevant requirements and topics will appear here.
                    </p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs sm:text-sm border-collapse min-w-[780px]">
                      <thead>
                        <tr className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-500 pb-4">
                          <th className="py-3 px-4">RELEVANT REQUIREMENT OR TOPIC</th>
                          <th className="py-3 px-4">ASSIGNED PROJECT</th>
                          <th className="py-3 px-4">DESCRIPTION</th>
                          <th className="py-3 px-4">SUPPORTING SOURCE / REFERENCE</th>
                          <th className="py-3 px-4 text-right"></th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 font-medium">
                        <tr className="hover:bg-slate-800/20 transition-colors">
                          <td className="py-4 px-4">
                            <div className="font-bold text-white text-sm">
                              Contractual responsibilities and liability allocation
                            </div>
                            <div className="text-xs font-mono text-slate-500 mt-0.5">
                              LEG-101
                            </div>
                          </td>
                          <td className="py-4 px-4 text-slate-300 font-medium text-xs sm:text-sm">
                            {assignedProjectsFullList[0]?.name || 'Assigned Project'}
                          </td>
                          <td className="py-4 px-4 text-slate-300 font-normal text-xs sm:text-sm max-w-[240px]">
                            Review contractual responsibilities, liability caps, and supervisory audit access provisions.
                          </td>
                          <td className="py-4 px-4 text-slate-300 font-medium text-xs sm:text-sm">
                            Project Services Agreement · Section 8
                          </td>
                          <td className="py-4 px-4 text-right">
                            <button
                              type="button"
                              onClick={() => setActiveTab('My Advice & Reviews')}
                              className="px-4 py-1.5 rounded-md border border-slate-700/80 bg-[#1e222a] hover:bg-slate-700 text-slate-200 text-xs font-semibold cursor-pointer transition-colors"
                            >
                              Review
                            </button>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 4: MY ADVICE & REVIEWS matching media_1791952670487_5285f173.png & media_1791952687524_9321f5a4.png */}
          {activeTab === 'My Advice & Reviews' && (
            <div className="space-y-6 animate-fadeIn w-full">
              {/* Top Navigation & Headings */}
              <div>
                <button
                  type="button"
                  onClick={() => setActiveTab('Dashboard')}
                  className="inline-flex items-center gap-1.5 text-xs sm:text-sm font-medium text-slate-400 hover:text-slate-200 transition-colors cursor-pointer mb-2.5"
                >
                  <span>←</span>
                  <span>Back to dashboard</span>
                </button>

                <span className="text-[11px] font-mono font-bold tracking-widest text-slate-400 uppercase block mb-1">
                  ADV-001 · FCA HANDBOOK · SYSC 6.3.8
                </span>
                <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
                  My Advice &amp; Reviews
                </h1>
                <p className="text-xs sm:text-sm text-slate-400 mt-1 font-normal">
                  Submit independent advisory interpretation and review notes for ABC Shield.
                </p>
              </div>

              {/* Main Card Container */}
              <div className="rounded-2xl border border-slate-800/90 bg-[#131519] shadow-lg p-6 sm:p-8 space-y-6">
                {/* 3-Column Metadata Row */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 border-b border-slate-800/80 pb-6">
                  <div>
                    <span className="text-[10px] font-mono font-bold tracking-widest text-slate-400 uppercase block mb-1.5">
                      REQUIREMENT
                    </span>
                    <span className="font-bold text-white text-sm sm:text-base block">
                      Risk-sensitive customer due diligence
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] font-mono font-bold tracking-widest text-slate-400 uppercase block mb-1.5">
                      REGULATORY SOURCE
                    </span>
                    <span className="font-bold text-white text-sm sm:text-base block">
                      FCA Handbook · SYSC 6.3.8
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] font-mono font-bold tracking-widest text-slate-400 uppercase block mb-1.5">
                      ADVISOR ROLE
                    </span>
                    <span className="font-bold text-[#e59b3c] text-sm sm:text-base block">
                      {currentExpertise.name}
                    </span>
                  </div>
                </div>

                {/* Form Fields matching screenshots */}
                <div className="space-y-6 pt-1">
                  {/* Field 1: Advisor Comments & Rationale */}
                  <div>
                    <label className="block text-xs sm:text-sm font-semibold text-slate-200 mb-2">
                      Advisor Comments &amp; Rationale
                    </label>
                    <textarea
                      rows={4}
                      value={advisorComments}
                      onChange={(e) => setAdvisorComments(e.target.value)}
                      placeholder="Enter your independent advisory comments, control evaluation, and compliance rationale..."
                      className="w-full bg-[#0c0e12] border border-slate-800 rounded-md p-4 text-xs sm:text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500/60 transition-colors resize-y leading-relaxed"
                    />
                  </div>

                  {/* Field 2: Recommendation */}
                  <div>
                    <label className="block text-xs sm:text-sm font-semibold text-slate-200 mb-2">
                      Recommendation
                    </label>
                    <textarea
                      rows={4}
                      value={recommendation}
                      onChange={(e) => setRecommendation(e.target.value)}
                      placeholder="Specify concrete remediation recommendations or sign-off conditions..."
                      className="w-full bg-[#0c0e12] border border-slate-800 rounded-md p-4 text-xs sm:text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500/60 transition-colors resize-y leading-relaxed"
                    />
                  </div>

                  {/* Field 3: Reference / Attachment */}
                  <div>
                    <label className="block text-xs sm:text-sm font-semibold text-slate-200 mb-2">
                      Reference / Attachment
                    </label>
                    <input
                      type="text"
                      value={referenceAttachment}
                      onChange={(e) => setReferenceAttachment(e.target.value)}
                      placeholder="Optional reference note / attachment name (e.g. EDD-Guidance-Notes.pdf)"
                      className="w-full bg-[#0c0e12] border border-slate-800 rounded-md px-4 py-3 text-xs sm:text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500/60 transition-colors"
                    />
                  </div>

                  {/* Action Buttons matching media_1791952687524_9321f5a4.png */}
                  <div className="flex items-center justify-end gap-3 pt-4">
                    <button
                      type="button"
                      onClick={() => setActiveTab('Dashboard')}
                      className="px-5 py-2.5 rounded-md border border-slate-700/80 bg-[#1b2637] hover:bg-[#233147] text-slate-200 text-xs sm:text-sm font-semibold cursor-pointer transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={handleSubmitAdvice}
                      className="px-6 py-2.5 rounded-md bg-[#e59b3c] hover:bg-[#d68a2b] active:scale-[0.99] text-slate-950 text-xs sm:text-sm font-bold cursor-pointer transition-colors shadow-md"
                    >
                      Submit Advice
                    </button>
                  </div>
                </div>

                {/* Authoritative Advice Lifecycle & Audit Log Section (DEF-11, DEF-12) */}
                <div className="pt-6 border-t border-slate-800">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="text-base sm:text-lg font-bold text-white">
                        Authoritative Advice Submissions &amp; Lifecycle Status
                      </h3>
                      <p className="text-xs text-slate-400 mt-0.5">
                        Traceable audit records persisted for project review sign-off.
                      </p>
                    </div>
                    <span className="text-xs font-mono px-2.5 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700">
                      {reviewsList.length} records
                    </span>
                  </div>

                  <div className="overflow-x-auto rounded-xl border border-slate-800 bg-[#0c0e12]">
                    <table className="w-full text-left text-xs sm:text-sm border-collapse min-w-[700px]">
                      <thead>
                        <tr className="border-b border-slate-800 bg-slate-900/60 text-[10px] font-mono font-bold uppercase tracking-wider text-slate-500">
                          <th className="py-3 px-4">RECORD ID</th>
                          <th className="py-3 px-4">PROJECT</th>
                          <th className="py-3 px-4">REQUIREMENT</th>
                          <th className="py-3 px-4">ADVICE SUBMISSION</th>
                          <th className="py-3 px-4">DATE</th>
                          <th className="py-3 px-4">LIFECYCLE STATUS</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 font-medium">
                        {reviewsList.map((rev) => (
                          <tr key={rev.id} className="hover:bg-slate-800/20 transition-colors">
                            <td className="py-3.5 px-4 font-mono font-bold text-amber-400">
                              {rev.id}
                            </td>
                            <td className="py-3.5 px-4 text-white font-semibold">
                              {rev.project}
                            </td>
                            <td className="py-3.5 px-4 text-slate-300">
                              {rev.requirement}
                            </td>
                            <td className="py-3.5 px-4 text-slate-300 max-w-xs truncate" title={rev.adviceSubmitted}>
                              {rev.adviceSubmitted}
                            </td>
                            <td className="py-3.5 px-4 font-mono text-slate-400">
                              {rev.date}
                            </td>
                            <td className="py-3.5 px-4">
                              <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold border ${rev.statusColor}`}>
                                <span className={`w-1.5 h-1.5 rounded-full ${rev.dotColor}`} />
                                <span>{rev.status}</span>
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: SETTINGS matching media_1791954134407_7946b208.png */}
          {activeTab === 'Settings' && (
            <div className="space-y-6 animate-fadeIn w-full text-left">
              <div>
                <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
                  Settings
                </h1>
                <p className="text-xs sm:text-sm text-slate-400 mt-1 font-normal max-w-3xl">
                  Profile, expertise, session, and notification information. Project access and privileged roles cannot be self-assigned.
                </p>
              </div>

              {/* Main Settings Card */}
              <div className="rounded-2xl border border-slate-800/90 bg-[#131519] shadow-lg p-6 sm:p-8 space-y-7">
                {/* 2x2 Metadata Grid matching screenshot */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-y-7 gap-x-12">
                  {/* Item 1: Profile Information */}
                  <div>
                    <span className="text-[10px] sm:text-[11px] font-mono font-bold tracking-widest text-slate-500 uppercase block mb-1.5">
                      PROFILE INFORMATION
                    </span>
                    <p className="font-semibold text-white text-xs sm:text-sm">
                      {userName} · {userEmail}
                    </p>
                  </div>

                  {/* Item 2: Active Expertise */}
                  <div>
                    <span className="text-[10px] sm:text-[11px] font-mono font-bold tracking-widest text-slate-500 uppercase block mb-1.5">
                      ACTIVE EXPERTISE
                    </span>
                    <p className="font-semibold text-white text-xs sm:text-sm">
                      {currentExpertise.name}
                    </p>
                  </div>

                  {/* Item 3: Authorized Expertise Profiles */}
                  <div>
                    <span className="text-[10px] sm:text-[11px] font-mono font-bold tracking-widest text-slate-500 uppercase block mb-1.5">
                      AUTHORIZED EXPERTISE PROFILES
                    </span>
                    <p className="font-semibold text-white text-xs sm:text-sm">
                      {currentExpertise.name}
                    </p>
                  </div>

                  {/* Item 4: Account and Session */}
                  <div>
                    <span className="text-[10px] sm:text-[11px] font-mono font-bold tracking-widest text-slate-500 uppercase block mb-1.5">
                      ACCOUNT AND SESSION
                    </span>
                    <p className="font-semibold text-white text-xs sm:text-sm">
                      Advisor account · Active session · Assigned projects only
                    </p>
                  </div>
                </div>

                {/* Notification Preferences */}
                <div className="pt-2">
                  <label className="block text-xs sm:text-sm font-semibold text-slate-200 mb-2">
                    Notification preferences
                  </label>
                  <div className="relative w-full">
                    <select
                      value={notificationPref}
                      onChange={(e) => setNotificationPref(e.target.value)}
                      className="w-full bg-[#0c0e12] border border-slate-800 rounded-md px-4 py-3 text-xs sm:text-sm text-slate-200 focus:outline-none focus:border-amber-500/60 appearance-none cursor-pointer pr-10"
                    >
                      <option value="Project and clarification alerts">
                        Project and clarification alerts
                      </option>
                      <option value="All notifications and regulatory updates">
                        All notifications and regulatory updates
                      </option>
                      <option value="Urgent escalation alerts only">
                        Urgent escalation alerts only
                      </option>
                      <option value="Muted / In-app only">
                        Muted / In-app only
                      </option>
                    </select>
                    <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                  </div>
                </div>

                {/* ACCESS CONTROL Callout Banner */}
                <div className="bg-[#2e2414] border border-[#684d1e] rounded-md p-4 sm:p-5 text-left">
                  <span className="text-[10px] sm:text-[11px] font-mono font-bold tracking-widest text-[#9c752d] uppercase block mb-1.5">
                    ACCESS CONTROL
                  </span>
                  <p className="text-xs sm:text-sm text-[#d4b486] font-normal leading-relaxed">
                    Expertise profiles do not grant project membership, Admin permissions, or access to unrelated project information.
                  </p>
                </div>
              </div>

              {/* Logout Button matching bottom right */}
              <div className="flex justify-end pt-2">
                <button
                  type="button"
                  onClick={() => {
                    logoutUser();
                    if (onSignOut) onSignOut();
                  }}
                  className="px-6 py-2.5 rounded-md border border-[#632828] bg-[#301919] hover:bg-[#3d2020] active:scale-[0.99] text-[#d46255] text-xs sm:text-sm font-semibold cursor-pointer transition-colors shadow-sm"
                >
                  Logout
                </button>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
