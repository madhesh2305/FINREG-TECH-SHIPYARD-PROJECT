import React, { useState, useEffect } from 'react';
import { getProjects, getProjectDetails, createProject } from '../services/projectService';
import { getCurrentUser, logoutUser } from '../services/authService';
import { getAdvisors } from '../services/advisorService';
import AdvisorsExpertsView from './AdvisorsExpertsView';
import RegulatorySupportView from './RegulatorySupportView';



import {
  Menu,
  Sun,
  Moon,
  Bell,
  ChevronDown,
  LayoutDashboard,
  FolderKanban,
  PlusCircle,
  Users,
  ShieldCheck,
  Wrench,
  Settings,
  ArrowRight,
  LogOut,
  Plus,
  BookOpen,
  FileText,
  FolderPlus,
  Clock,
  Sparkles,
  Search,
  List,
  LayoutGrid,
  ChevronRight,
  CheckCircle2,
  CheckSquare,
  Square,
  Edit3,
  ExternalLink
} from 'lucide-react';

export default function DashboardView({ isDarkMode, onToggleTheme, onSignOut }) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [activeTab, setActiveTab] = useState('Dashboard'); // 'Dashboard' | 'My Projects' | 'Create Project' | 'Project Details'
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [isNotificationMenuOpen, setIsNotificationMenuOpen] = useState(false);
  const [hasUnreadNotifications, setHasUnreadNotifications] = useState(true);

  // Selected Project State for Project Details View
  const [selectedProject, setSelectedProject] = useState(null);
  const [projectSubTab, setProjectSubTab] = useState('Overview');

  // Box Click & Active States for Cream Glow + Zoom-in
  const [isCreateProjectTouched, setIsCreateProjectTouched] = useState(false);
  const [isFormCardActive, setIsFormCardActive] = useState(false);
  const [activeMetricId, setActiveMetricId] = useState(null);
  const [isRecentProjectsActive, setIsRecentProjectsActive] = useState(false);
  const [isMyProjectsBoxActive, setIsMyProjectsBoxActive] = useState(false);
  const [isQuickActionsActive, setIsQuickActionsActive] = useState(false);
  const [activeQuickActionId, setActiveQuickActionId] = useState(null);
  const [isActivityFeedActive, setIsActivityFeedActive] = useState(false);
  const [isProjectDetailsCardActive, setIsProjectDetailsCardActive] = useState(false);
  const [isCompletionCardActive, setIsCompletionCardActive] = useState(false);
  const [isTeamCardActive, setIsTeamCardActive] = useState(false);

  // Search & Filter States for My Projects View
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('All Statuses');
  const [typeFilter, setTypeFilter] = useState('All Types');
  const [viewMode, setViewMode] = useState('list'); // 'list' | 'grid'

  // Create Project Form States
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectType, setNewProjectType] = useState('');
  const [newProjectDescription, setNewProjectDescription] = useState('');
  const [newProjectJurisdiction, setNewProjectJurisdiction] = useState('');
  const [newProjectDomain, setNewProjectDomain] = useState('');
  const [toastMessage, setToastMessage] = useState(null);

  // Master Projects List matching the reference image
  const [allProjects, setAllProjects] = useState([
    {
      id: 'PRJ-001',
      name: 'AML Compliance Framework',
      type: 'AML/CTF',
      status: 'In Progress',
      statusColor: 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/50 dark:text-blue-400 dark:border-blue-900',
      dotColor: 'bg-blue-600',
      lastUpdated: '22 Sep 2026',
      owner: 'J. Nakamura',
      description: 'End-to-end anti-money laundering workflow for retail banking operations.',
      created: '01 Sep 2026',
      jurisdiction: 'United Kingdom - FCA',
    },
    {
      id: 'PRJ-002',
      name: 'KYC Onboarding Workflow',
      type: 'KYC/CDD',
      status: 'Under Review',
      statusColor: 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/50 dark:text-amber-400 dark:border-amber-900',
      dotColor: 'bg-amber-600',
      lastUpdated: '21 Sep 2026',
      owner: 'S. Okonkwo',
      description: 'Digital identity verification and customer due diligence flow.',
      created: '05 Sep 2026',
      jurisdiction: 'United Kingdom - FCA',
    },
    {
      id: 'PRJ-003',
      name: 'Regulatory Reporting Q3',
      type: 'Regulatory Reporting',
      status: 'Draft',
      statusColor: 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700',
      dotColor: 'bg-slate-400',
      lastUpdated: '19 Sep 2026',
      owner: 'A. Petrov',
      description: 'Quarterly compliance and prudential reporting submission pack.',
      created: '10 Sep 2026',
      jurisdiction: 'European Union - EBA',
    },
    {
      id: 'PRJ-004',
      name: 'GDPR Data Audit Trail',
      type: 'Data Governance',
      status: 'Completed',
      statusColor: 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/50 dark:text-emerald-400 dark:border-emerald-900',
      dotColor: 'bg-emerald-600',
      lastUpdated: '15 Sep 2026',
      owner: 'M. Chen',
      description: 'Data mapping, consent tracking, and regulatory audit log system.',
      created: '12 Sep 2026',
      jurisdiction: 'European Union - GDPR',
    },
    {
      id: 'PRJ-005',
      name: 'Basel III Capital Adequacy',
      type: 'Regulatory Reporting',
      status: 'In Progress',
      statusColor: 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/50 dark:text-blue-400 dark:border-blue-900',
      dotColor: 'bg-blue-600',
      lastUpdated: '10 Sep 2026',
      owner: 'J. Nakamura',
      description: 'Capital requirement calculations and risk-weighted assets framework.',
      created: '14 Sep 2026',
      jurisdiction: 'Global / BIS',
    },
  ]);

  // Load user & live projects from backend API on mount
  useEffect(() => {
    let isMounted = true;
    async function loadBackendData() {
      try {
        const liveProjects = await getProjects();
        if (isMounted && Array.isArray(liveProjects) && liveProjects.length > 0) {
          setAllProjects(liveProjects);
        }
      } catch (err) {
        console.warn('[DashboardView] API load warning, using static fallbacks:', err);
      }
    }
    loadBackendData();
    return () => {
      isMounted = false;
    };
  }, []);

  // Open Project Details Page (fetches live details from API)
  const handleOpenProject = async (project) => {
    setSelectedProject(project);
    setProjectSubTab('Overview');
    setActiveTab('Project Details');
    try {
      const details = await getProjectDetails(project.id);
      if (details) setSelectedProject(details);
    } catch (err) {
      console.warn('[DashboardView] getProjectDetails warning:', err);
    }
  };

  // Handle New Project Creation via POST /projects
  const handleCreateProjectSubmit = async (e) => {
    e.preventDefault();
    if (!newProjectName || !newProjectType) return;

    const payload = {
      name: newProjectName,
      type: newProjectType,
      description: newProjectDescription || 'Newly created regulatory project.',
      jurisdiction: newProjectJurisdiction || 'United Kingdom - FCA',
    };

    let createdProject;
    try {
      createdProject = await createProject(payload);
    } catch (err) {
      console.warn('[DashboardView] POST /projects failed, fallback to local state:', err);
      createdProject = {
        id: `PRJ-00${allProjects.length + 1}`,
        ...payload,
        status: 'Draft',
        statusColor: 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700',
        dotColor: 'bg-slate-400',
        lastUpdated: 'Just now',
        owner: 'J. Nakamura',
        created: 'Today',
      };
    }

    const newEntry = {
      id: createdProject.id || `PRJ-00${allProjects.length + 1}`,
      name: createdProject.name || payload.name,
      type: createdProject.type || payload.type,
      status: createdProject.status || 'Draft',
      statusColor: createdProject.statusColor || 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700',
      dotColor: createdProject.dotColor || 'bg-slate-400',
      lastUpdated: createdProject.lastUpdated || 'Just now',
      owner: createdProject.owner || 'J. Nakamura',
      description: createdProject.description || payload.description,
      created: createdProject.created || 'Today',
      jurisdiction: createdProject.jurisdiction || payload.jurisdiction,
    };

    setAllProjects([newEntry, ...allProjects]);
    setToastMessage(`Project "${newProjectName}" created successfully!`);

    // Reset Form
    setNewProjectName('');
    setNewProjectType('');
    setNewProjectDescription('');
    setNewProjectJurisdiction('');
    setNewProjectDomain('');

    // Automatically navigate to My Projects View
    setTimeout(() => {
      setActiveTab('My Projects');
      setToastMessage(null);
    }, 1200);
  };


  // Filtered projects computation
  const filteredProjects = allProjects.filter((project) => {
    const matchesSearch =
      project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      project.type.toLowerCase().includes(searchQuery.toLowerCase()) ||
      project.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      project.owner.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesStatus =
      statusFilter === 'All Statuses' || project.status === statusFilter;

    const matchesType =
      typeFilter === 'All Types' || project.type === typeFilter;

    return matchesSearch && matchesStatus && matchesType;
  });

  // Quick Actions Data
  const quickActions = [
    {
      id: 'new-project',
      title: 'New Project',
      subtitle: 'Start from template',
      icon: FolderPlus,
    },
    {
      id: 'browse-advisors',
      title: 'Browse Advisors',
      subtitle: 'Find an expert',
      icon: Users,
    },
    {
      id: 'regulatory-library',
      title: 'Regulatory Library',
      subtitle: 'Rules & guidance',
      icon: BookOpen,
    },
    {
      id: 'generate-report',
      title: 'Generate Report',
      subtitle: 'Export compliance docs',
      icon: FileText,
    },
  ];

  // Activity Feed Data
  const activityFeed = [
    {
      id: 1,
      badge: 'YO',
      user: 'You',
      action: 'updated',
      target: 'AML Compliance Framework',
      time: '2h ago',
    },
    {
      id: 2,
      badge: 'SO',
      user: 'S. Okonkwo',
      action: 'submitted',
      target: 'KYC Onboarding Workflow',
      time: '5h ago',
    },
    {
      id: 3,
      badge: 'MC',
      user: 'M. Chen',
      action: 'completed',
      target: 'GDPR Data Audit Trail',
      time: 'Yesterday',
    },
    {
      id: 4,
      badge: 'AP',
      user: 'A. Petrov',
      action: 'created draft',
      target: 'Regulatory Reporting Q3',
      time: '3 days ago',
    },
  ];

  // Notifications Data (Advisor 1, Advisor 2 & System alerts)
  const notificationsList = [
    {
      id: 1,
      sender: 'Advisor 1 (S. Okonkwo)',
      avatar: 'SO',
      avatarBg: 'bg-[#7c4a27] text-white',
      title: 'Review Feedback Submitted',
      message: 'Advisor 1 (S. Okonkwo) submitted feedback for KYC Onboarding Workflow: "CDD verification steps approved, pending final compliance sign-off."',
      time: '10 minutes ago',
      unread: true,
      projectId: 'PRJ-002',
    },
    {
      id: 2,
      sender: 'Advisor 2 (A. Petrov)',
      avatar: 'AP',
      avatarBg: 'bg-[#96562c] text-white',
      title: 'Draft Pack Approved',
      message: 'Advisor 2 (A. Petrov) approved draft submission for Regulatory Reporting Q3 pack.',
      time: '1 hour ago',
      unread: true,
      projectId: 'PRJ-003',
    },
    {
      id: 3,
      sender: 'System Alert',
      avatar: 'FRT',
      avatarBg: 'bg-slate-800 text-amber-400 border border-amber-500/30',
      title: 'Regulatory Guidance Updated',
      message: 'FCA published new Anti-Money Laundering & CTF compliance standards for Q4 2026.',
      time: '3 hours ago',
      unread: false,
    },
  ];

  // Metric Cards Config
  const metricsData = [
    { id: 'total', label: 'TOTAL PROJECTS', val: `${allProjects.length}`, sub: '2 owned by me' },
    { id: 'progress', label: 'IN PROGRESS', val: '2', sub: 'Active workflows' },
    { id: 'review', label: 'UNDER REVIEW', val: '1', sub: 'Awaiting approval' },
    { id: 'completed', label: 'COMPLETED', val: '1', sub: 'All time' },
  ];

  // Default active project fallback if null
  const currentProject = selectedProject || allProjects[0];

  return (
    <div className={`min-h-screen w-full flex flex-col font-sans transition-colors duration-300 ${
      isDarkMode ? 'bg-[#121214] text-slate-100' : 'bg-[#e2e8f0] text-slate-800'
    }`}>
      {/* Toast Notification Banner */}
      {toastMessage && (
        <div className="fixed top-16 right-6 z-50 bg-emerald-600 text-white px-4 py-3 rounded-xl shadow-2xl flex items-center gap-2.5 animate-fadeIn font-semibold text-xs sm:text-sm">
          <CheckCircle2 className="w-5 h-5 text-white shrink-0" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Top Header Navbar */}
      <header className={`w-full border-b px-4 sm:px-6 py-3 flex items-center justify-between sticky top-0 z-40 transition-colors duration-300 ${
        isDarkMode ? 'bg-[#1a1a1e] border-slate-800' : 'bg-white border-slate-200'
      }`}>
        {/* Left Section: Sidebar Toggle + FRT Logo + Title */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className={`p-1.5 rounded-lg transition-colors cursor-pointer ${
              isDarkMode ? 'text-slate-300 hover:bg-slate-800' : 'text-slate-600 hover:bg-stone-100'
            }`}
          >
            <Menu className="w-5 h-5" />
          </button>

          {/* FRT Square Badge Logo */}
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-[#7c4a27] dark:bg-[#96562c] text-white font-black text-xs flex items-center justify-center tracking-tighter shadow-sm">
              FRT
            </div>
            <span className="font-extrabold tracking-wider text-sm sm:text-base select-none hidden sm:inline-block">
              FINREGTECH SHIPYARD
            </span>
          </div>
        </div>

        {/* Center Title Badge */}
        <div className="hidden md:flex items-center justify-center">
          <span className="font-extrabold tracking-wider text-sm sm:text-base select-none uppercase">
            BUILDER DASHBOARD
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
                setIsUserMenuOpen(false);
                setHasUnreadNotifications(false);
              }}
              title="Click to view notifications from Advisor 1 & Advisor 2"
              className={`relative p-2 rounded-xl border transition-all cursor-pointer ${
                isDarkMode
                  ? 'border-slate-800 hover:border-slate-700 bg-slate-900/60 text-slate-200'
                  : 'border-stone-200 hover:border-stone-300 bg-stone-50 text-slate-700'
              }`}
            >
              <Bell className="w-5 h-5 text-amber-400" />
              {hasUnreadNotifications && (
                <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-rose-500 rounded-full ring-2 ring-[#121214] animate-pulse" />
              )}
            </button>

            {/* Notifications Dropdown Panel */}
            {isNotificationMenuOpen && (
              <div className={`absolute right-0 mt-2 w-80 sm:w-96 rounded-2xl shadow-2xl border overflow-hidden z-50 animate-fadeIn ${
                isDarkMode ? 'bg-[#1a1a1e] border-slate-800 text-slate-100' : 'bg-white border-stone-200 text-slate-900'
              }`}>
                {/* Panel Header */}
                <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <h3 className="font-bold text-sm sm:text-base text-slate-100">Notifications</h3>
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

                {/* Notifications List */}
                <div className="max-h-96 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-800/80 text-left">
                  {notificationsList.map((notif) => (
                    <div
                      key={notif.id}
                      onClick={() => {
                        if (notif.projectId) {
                          const proj = allProjects.find((p) => p.id === notif.projectId);
                          if (proj) handleOpenProject(proj);
                        }
                        setIsNotificationMenuOpen(false);
                      }}
                      className={`p-4 transition-colors cursor-pointer ${
                        isDarkMode
                          ? 'hover:bg-slate-800/60'
                          : 'hover:bg-stone-50'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <div className={`w-8 h-8 rounded-lg font-bold text-xs flex items-center justify-center shrink-0 mt-0.5 ${notif.avatarBg}`}>
                          {notif.avatar}
                        </div>
                        <div className="flex-1 space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-xs text-amber-400">{notif.sender}</span>
                            <span className="text-[11px] text-slate-400 font-medium">{notif.time}</span>
                          </div>
                          <p className="font-semibold text-xs text-slate-200">{notif.title}</p>
                          <p className="text-xs text-slate-300 leading-relaxed font-normal">{notif.message}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* User Profile Dropdown */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
              className={`flex items-center gap-2.5 p-1.5 rounded-xl border transition-all cursor-pointer ${
                isDarkMode
                  ? 'border-slate-800 hover:border-slate-700 bg-slate-900/60'
                  : 'border-stone-200 hover:border-stone-300 bg-stone-50'
              }`}
            >
              <div className="w-8 h-8 rounded-lg bg-[#7c4a27]/15 dark:bg-amber-500/20 text-[#7c4a27] dark:text-amber-300 font-bold text-xs flex items-center justify-center border border-[#7c4a27]/20">
                JN
              </div>
              <span className="text-sm font-semibold hidden md:inline-block">J. Nakamura</span>
              <ChevronDown className="w-4 h-4 text-slate-400" />
            </button>

            {/* User Menu Overlay Matching Uploaded Image */}
            {isUserMenuOpen && (
              <div className={`absolute right-0 mt-2 w-60 rounded-xl shadow-2xl border overflow-hidden z-50 animate-fadeIn ${
                isDarkMode ? 'bg-[#1a1a1e] border-slate-800 text-slate-200' : 'bg-white border-stone-200 text-slate-800'
              }`}>
                <div className="p-4 border-b border-slate-200 dark:border-slate-800 text-left">
                  <p className="font-bold text-sm text-slate-900 dark:text-slate-100">Jun Nakamura</p>
                  <p className="text-slate-400 text-xs mt-0.5 font-normal">jun@finregtech.io</p>
                  <div className="mt-2.5">
                    <span className="inline-block px-2.5 py-0.5 border border-slate-200 dark:border-slate-700 bg-stone-50 dark:bg-slate-800 text-slate-600 dark:text-slate-300 text-[11px] font-mono rounded">
                      Builder
                    </span>
                  </div>
                </div>

                <div className="py-1 border-b border-slate-200 dark:border-slate-800 text-left text-xs sm:text-sm font-medium">
                  <button
                    type="button"
                    onClick={() => {
                      setIsUserMenuOpen(false);
                      alert('Opening Profile & Settings...');
                    }}
                    className="w-full text-left px-4 py-2.5 hover:bg-stone-100 dark:hover:bg-slate-800/70 text-slate-700 dark:text-slate-200 transition-colors cursor-pointer"
                  >
                    Profile & Settings
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setIsUserMenuOpen(false);
                      alert('Opening Billing...');
                    }}
                    className="w-full text-left px-4 py-2.5 hover:bg-stone-100 dark:hover:bg-slate-800/70 text-slate-700 dark:text-slate-200 transition-colors cursor-pointer"
                  >
                    Billing
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setIsUserMenuOpen(false);
                      alert('Opening Help & Documentation...');
                    }}
                    className="w-full text-left px-4 py-2.5 hover:bg-stone-100 dark:hover:bg-slate-800/70 text-slate-700 dark:text-slate-200 transition-colors cursor-pointer"
                  >
                    Help & Documentation
                  </button>
                </div>

                <div className="py-1 text-left">
                  <button
                    type="button"
                    onClick={() => {
                      logoutUser();
                      if (onSignOut) onSignOut();
                    }}
                    className="w-full text-left px-4 py-2.5 text-xs sm:text-sm font-semibold text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors cursor-pointer"
                  >
                    Sign out
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
          } transition-all duration-300 border-r flex flex-col justify-between p-3 z-30 shrink-0 ${
            isDarkMode ? 'bg-[#161619] border-slate-800' : 'bg-white border-slate-200'
          }`}
        >
          {/* Navigation Links List */}
          <nav className="space-y-1">
            {[
              { name: 'Dashboard', icon: LayoutDashboard },
              { name: 'My Projects', icon: FolderKanban, badge: allProjects.length },
              { name: 'Create Project', icon: PlusCircle },
              { name: 'Advisors / Experts', icon: Users },
              { name: 'Regulatory Support', icon: ShieldCheck },
              { name: 'Tools', icon: Wrench },
              { name: 'Settings', icon: Settings },
            ].map((item) => {
              const Icon = item.icon;
              const isActive =
                activeTab === item.name ||
                (item.name === 'My Projects' && activeTab === 'Project Details');

              return (
                <button
                  key={item.name}
                  type="button"
                  onClick={() => setActiveTab(item.name)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer ${
                    isActive
                      ? isDarkMode
                        ? 'bg-[#96562c]/20 text-amber-400 border border-[#96562c]/30'
                        : 'bg-amber-50 text-[#7c4a27] border border-amber-200/80 shadow-xs'
                      : isDarkMode
                      ? 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                      : 'text-slate-600 hover:bg-stone-100 hover:text-slate-900'
                  }`}
                >
                  <Icon className={`w-4 h-4 shrink-0 ${
                    isActive ? (isDarkMode ? 'text-amber-400' : 'text-[#7c4a27]') : 'text-slate-400'
                  }`} />
                  {isSidebarOpen && (
                    <span className="flex-1 text-left truncate">{item.name}</span>
                  )}
                  {isSidebarOpen && item.badge && (
                    <span className={`text-[11px] px-2 py-0.5 rounded-md font-bold ${
                      isActive
                        ? 'bg-[#7c4a27] text-white'
                        : isDarkMode
                        ? 'bg-slate-800 text-slate-400'
                        : 'bg-stone-100 text-stone-600'
                    }`}>
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </aside>

        {/* Dashboard Content Container */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6 overflow-x-hidden">
          {/* TAB 1: DASHBOARD HOME VIEW */}
          {activeTab === 'Dashboard' && (
            <div className="space-y-6 animate-fadeIn">
              {/* Welcome Header Banner */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h1 className={`text-2xl sm:text-3xl font-bold tracking-tight ${
                    isDarkMode ? 'text-slate-100' : 'text-slate-900'
                  }`}>
                    Welcome back, J. Nakamura
                  </h1>
                  <p className={`text-xs sm:text-sm mt-1 font-medium ${
                    isDarkMode ? 'text-slate-300' : 'text-slate-500'
                  }`}>
                    Monday, 22 September 2026 <span className="mx-1">·</span> Builder workspace
                  </p>
                </div>

                {/* + Create New Project Button */}
                <button
                  type="button"
                  onClick={() => {
                    setIsCreateProjectTouched(!isCreateProjectTouched);
                    setActiveTab('Create Project');
                  }}
                  title="Touch to toggle grey border, cream color lighting glow & zoom-in"
                  className={`px-5 py-3 rounded-xl font-bold text-sm flex items-center justify-center gap-2 transition-all duration-300 cursor-pointer border-2 ${
                    isCreateProjectTouched
                      ? isDarkMode
                        ? 'bg-[#96562c] text-white border-slate-300 scale-[1.04] shadow-[0_0_35px_rgba(251,191,36,0.35),0_12px_36px_rgba(150,86,44,0.4)] ring-4 ring-amber-500/30'
                        : 'bg-[#7c4a27] text-white border-slate-500 scale-[1.04] shadow-[0_0_40px_rgba(254,243,199,0.95),0_14px_40px_rgba(124,74,39,0.3)] ring-4 ring-amber-100/90'
                      : isDarkMode
                      ? 'bg-[#96562c] hover:bg-[#7c4a27] border-slate-700 hover:border-slate-300 text-white hover:scale-[1.04] hover:shadow-[0_0_35px_rgba(251,191,36,0.25)]'
                      : 'bg-[#7c4a27] hover:bg-[#633a1e] border-stone-300 hover:border-slate-500 text-white hover:scale-[1.04] hover:shadow-[0_0_40px_rgba(254,243,199,0.95)]'
                  }`}
                >
                  <Plus className="w-4 h-4 stroke-[3]" />
                  <span>Create New Project</span>
                </button>
              </div>

              {/* 4 METRIC STAT CARDS GRID */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {metricsData.map((m) => {
                  const isActive = activeMetricId === m.id;
                  return (
                    <div
                      key={m.id}
                      onClick={() => setActiveMetricId(isActive ? null : m.id)}
                      title="Click box to toggle brown border, cream edge lighting glow & zoom-in"
                      className={`p-5 rounded-2xl border transition-all duration-300 cursor-pointer ${
                        isActive
                          ? isDarkMode
                            ? 'bg-[#1e1e24] border-[#96562c] scale-[1.03] shadow-[0_0_35px_rgba(251,191,36,0.25),0_12px_36px_rgba(150,86,44,0.35)] ring-2 ring-[#96562c]/40'
                            : 'bg-[#fdfdf9] border-[#7c4a27] scale-[1.03] shadow-[0_0_40px_rgba(254,243,199,0.95),0_14px_40px_rgba(124,74,39,0.22)] ring-4 ring-amber-100/90'
                          : isDarkMode
                          ? 'bg-[#1a1a1e] border-slate-800 shadow-sm hover:border-[#96562c] hover:scale-[1.02] hover:shadow-[0_0_30px_rgba(251,191,36,0.2),0_10px_28px_rgba(150,86,44,0.28)]'
                          : 'bg-white border-stone-200/90 shadow-xs hover:border-[#7c4a27] hover:scale-[1.02] hover:shadow-[0_0_35px_rgba(254,243,199,0.85),0_12px_32px_rgba(124,74,39,0.18)] hover:bg-[#fdfdfc]'
                      }`}
                    >
                      <p className={`text-xs font-bold tracking-wider uppercase ${
                        isDarkMode ? 'text-amber-300/90' : 'text-slate-500'
                      }`}>{m.label}</p>
                      <p className={`text-3xl sm:text-4xl font-black mt-2 tracking-tight ${
                        isDarkMode ? 'text-slate-100' : 'text-slate-900'
                      }`}>{m.val}</p>
                      <p className={`text-xs mt-1 font-semibold ${
                        isDarkMode ? 'text-slate-300' : 'text-slate-500'
                      }`}>{m.sub}</p>
                    </div>
                  );
                })}
              </div>

              {/* RECENT PROJECTS CONTAINER BOX */}
              <div
                onClick={() => setIsRecentProjectsActive(!isRecentProjectsActive)}
                title="Click to toggle cream edge lighting glow & zoom-in"
                className={`rounded-2xl border transition-all duration-300 overflow-hidden cursor-pointer ${
                  isRecentProjectsActive
                    ? isDarkMode
                      ? 'bg-[#1e1e24] border-[#96562c] scale-[1.015] shadow-[0_0_35px_rgba(251,191,36,0.25),0_12px_36px_rgba(150,86,44,0.35)] ring-2 ring-[#96562c]/40'
                      : 'bg-[#fdfdf9] border-[#7c4a27] scale-[1.015] shadow-[0_0_40px_rgba(254,243,199,0.95),0_14px_40px_rgba(124,74,39,0.22)] ring-4 ring-amber-100/90'
                    : isDarkMode
                    ? 'bg-[#1a1a1e] border-slate-800 shadow-sm hover:border-[#96562c] hover:scale-[1.01] hover:shadow-[0_0_30px_rgba(251,191,36,0.2),0_10px_28px_rgba(150,86,44,0.28)]'
                    : 'bg-white border-stone-200/90 shadow-xs hover:border-[#7c4a27] hover:scale-[1.01] hover:shadow-[0_0_35px_rgba(254,243,199,0.85),0_12px_32px_rgba(124,74,39,0.18)] hover:bg-[#fdfdfc]'
                }`}
              >
                <div className="p-5 border-b flex items-center justify-between border-slate-200 dark:border-slate-800">
                  <div className="flex items-center gap-2">
                    <h2 className={`text-base sm:text-lg font-bold tracking-tight ${
                      isDarkMode ? 'text-slate-100' : 'text-slate-900'
                    }`}>
                      Recent Projects
                    </h2>
                    {isRecentProjectsActive && (
                      <span className="flex items-center gap-1 text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-amber-100 text-[#7c4a27] dark:bg-amber-950/60 dark:text-amber-300 animate-fadeIn">
                        <Sparkles className="w-3 h-3 text-[#7c4a27] dark:text-amber-400" />
                        <span>Cream Glow & Zoom Active</span>
                      </span>
                    )}
                  </div>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      setActiveTab('My Projects');
                    }}
                    className="text-xs font-bold text-[#7c4a27] dark:text-amber-400 hover:underline flex items-center gap-1 cursor-pointer"
                  >
                    <span>View all</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs sm:text-sm border-collapse">
                    <thead>
                      <tr className={`border-b text-[11px] font-extrabold uppercase tracking-wider ${
                        isDarkMode
                          ? 'border-slate-800 bg-slate-900/80 text-slate-200'
                          : 'border-stone-100 bg-stone-50/80 text-stone-500'
                      }`}>
                        <th className="py-3.5 px-5">PROJECT NAME</th>
                        <th className="py-3.5 px-5">TYPE</th>
                        <th className="py-3.5 px-5">STATUS</th>
                        <th className="py-3.5 px-5">LAST UPDATED</th>
                        <th className="py-3.5 px-5 text-right">ACTION</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-medium">
                      {allProjects.slice(0, 4).map((project) => (
                        <tr
                          key={project.id}
                          className={`transition-colors ${
                            isDarkMode ? 'hover:bg-slate-800/40' : 'hover:bg-stone-50/90'
                          }`}
                        >
                          <td className={`py-4 px-5 font-bold text-sm ${
                            isDarkMode ? 'text-slate-100' : 'text-slate-900'
                          }`}>
                            {project.name}
                          </td>
                          <td className={`py-4 px-5 font-medium ${
                            isDarkMode ? 'text-slate-200' : 'text-slate-600'
                          }`}>
                            {project.type}
                          </td>
                          <td className="py-4 px-5">
                            <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-bold border ${project.statusColor}`}>
                              <span className={`w-1.5 h-1.5 rounded-full ${project.dotColor}`} />
                              {project.status}
                            </span>
                          </td>
                          <td className={`py-4 px-5 font-medium ${
                            isDarkMode ? 'text-slate-200' : 'text-slate-600'
                          }`}>
                            {project.lastUpdated}
                          </td>
                          <td className="py-4 px-5 text-right">
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleOpenProject(project);
                              }}
                              className={`text-xs font-bold hover:underline inline-flex items-center gap-1 cursor-pointer ${
                                isDarkMode ? 'text-amber-400' : 'text-[#7c4a27]'
                              }`}
                            >
                              <span>Open</span>
                              <ArrowRight className="w-3.5 h-3.5" />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* QUICK ACTIONS & ACTIVITY FEED ROW */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-2">
                <div
                  onClick={() => setIsQuickActionsActive(!isQuickActionsActive)}
                  title="Click box to toggle brown border, cream edge lighting glow & zoom-in"
                  className={`rounded-2xl border transition-all duration-300 overflow-hidden cursor-pointer ${
                    isQuickActionsActive
                      ? isDarkMode
                        ? 'bg-[#1e1e24] border-[#96562c] scale-[1.015] shadow-[0_0_35px_rgba(251,191,36,0.25),0_12px_36px_rgba(150,86,44,0.35)] ring-2 ring-[#96562c]/40'
                        : 'bg-[#fdfdf9] border-[#7c4a27] scale-[1.015] shadow-[0_0_40px_rgba(254,243,199,0.95),0_14px_40px_rgba(124,74,39,0.22)] ring-4 ring-amber-100/90'
                      : isDarkMode
                      ? 'bg-[#1a1a1e] border-slate-800 shadow-sm hover:border-[#96562c] hover:scale-[1.01]'
                      : 'bg-white border-stone-200/90 shadow-xs hover:border-[#7c4a27] hover:scale-[1.01] hover:bg-[#fdfdfc]'
                  }`}
                >
                  <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
                    <h2 className={`text-base sm:text-lg font-bold tracking-tight ${
                      isDarkMode ? 'text-slate-100' : 'text-slate-900'
                    }`}>
                      Quick Actions
                    </h2>
                    {isQuickActionsActive && <Sparkles className="w-4 h-4 text-[#7c4a27] dark:text-amber-400" />}
                  </div>

                  <div className="p-5 grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {quickActions.map((action) => {
                      const IconComponent = action.icon;
                      const isActionActive = activeQuickActionId === action.id;

                      return (
                        <button
                          key={action.id}
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            if (action.id === 'new-project') {
                              setActiveTab('Create Project');
                            } else if (action.id === 'browse-advisors') {
                              setActiveTab('Advisors / Experts');
                            } else {
                              setActiveQuickActionId(isActionActive ? null : action.id);
                            }
                          }}
                          className={`p-4 rounded-xl border text-left transition-all duration-300 cursor-pointer group ${
                            isActionActive
                              ? isDarkMode
                                ? 'bg-slate-800/90 border-[#96562c] scale-[1.03] shadow-[0_0_25px_rgba(251,191,36,0.3)]'
                                : 'bg-[#fdfdf9] border-[#7c4a27] scale-[1.03] shadow-[0_0_30px_rgba(254,243,199,0.95),0_10px_28px_rgba(124,74,39,0.2)] ring-4 ring-amber-100/90'
                              : isDarkMode
                              ? 'bg-slate-900/60 border-slate-800 hover:border-[#96562c] hover:scale-[1.02] hover:bg-slate-800/60'
                              : 'bg-stone-50/70 border-stone-200/80 hover:border-[#7c4a27] hover:scale-[1.02] hover:bg-stone-100/80 shadow-xs'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-2">
                            <div className={`w-9 h-9 rounded-lg flex items-center justify-center transition-colors ${
                              isActionActive || isDarkMode
                                ? 'bg-[#96562c] text-white'
                                : 'bg-amber-100/60 text-[#7c4a27] group-hover:bg-[#7c4a27] group-hover:text-white'
                            }`}>
                              <IconComponent className="w-5 h-5 stroke-[2.2]" />
                            </div>
                            <ArrowRight className="w-4 h-4 text-slate-300 dark:text-slate-600 group-hover:text-[#7c4a27] dark:group-hover:text-amber-400 transition-colors" />
                          </div>
                          <p className={`font-bold text-sm tracking-tight ${
                            isDarkMode ? 'text-slate-100' : 'text-slate-900'
                          }`}>
                            {action.title}
                          </p>
                          <p className={`text-xs mt-0.5 font-semibold ${
                            isDarkMode ? 'text-slate-300' : 'text-slate-500'
                          }`}>
                            {action.subtitle}
                          </p>
                        </button>
                      );
                    })}
                  </div>
                </div>

                <div
                  onClick={() => setIsActivityFeedActive(!isActivityFeedActive)}
                  title="Click box to toggle brown border, cream edge lighting glow & zoom-in"
                  className={`rounded-2xl border transition-all duration-300 overflow-hidden cursor-pointer ${
                    isActivityFeedActive
                      ? isDarkMode
                        ? 'bg-[#1e1e24] border-[#96562c] scale-[1.015] shadow-[0_0_35px_rgba(251,191,36,0.25),0_12px_36px_rgba(150,86,44,0.35)] ring-2 ring-[#96562c]/40'
                        : 'bg-[#fdfdf9] border-[#7c4a27] scale-[1.015] shadow-[0_0_40px_rgba(254,243,199,0.95),0_14px_40px_rgba(124,74,39,0.22)] ring-4 ring-amber-100/90'
                      : isDarkMode
                      ? 'bg-[#1a1a1e] border-slate-800 shadow-sm hover:border-[#96562c] hover:scale-[1.01]'
                      : 'bg-white border-stone-200/90 shadow-xs hover:border-[#7c4a27] hover:scale-[1.01] hover:bg-[#fdfdfc]'
                  }`}
                >
                  <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
                    <h2 className={`text-base sm:text-lg font-bold tracking-tight ${
                      isDarkMode ? 'text-slate-100' : 'text-slate-900'
                    }`}>
                      Activity Feed
                    </h2>
                    {isActivityFeedActive && <Sparkles className="w-4 h-4 text-[#7c4a27] dark:text-amber-400" />}
                  </div>

                  <div className="divide-y divide-slate-100 dark:divide-slate-800/70">
                    {activityFeed.map((item) => (
                      <div
                        key={item.id}
                        className={`p-4 flex items-start gap-3.5 transition-all duration-300 ${
                          isDarkMode ? 'hover:bg-slate-800/40' : 'hover:bg-stone-50/80'
                        }`}
                      >
                        <div className={`w-9 h-9 rounded-lg font-bold text-xs flex items-center justify-center shrink-0 border mt-0.5 ${
                          isDarkMode
                            ? 'bg-slate-800 border-slate-700 text-amber-400'
                            : 'bg-stone-100 border-stone-200 text-[#7c4a27]'
                        }`}>
                          {item.badge}
                        </div>

                        <div className="flex-1 text-xs sm:text-sm">
                          <p className={isDarkMode ? 'text-slate-100 font-medium' : 'text-slate-800'}>
                            <span className="font-bold">{item.user}</span>{' '}
                            <span className="text-slate-600 dark:text-slate-300">{item.action}</span>{' '}
                            <span className="font-bold text-[#7c4a27] dark:text-amber-400">{item.target}</span>
                          </p>

                          <p className={`text-xs mt-1 font-semibold flex items-center gap-1 ${
                            isDarkMode ? 'text-slate-400' : 'text-slate-500'
                          }`}>
                            <Clock className="w-3 h-3 text-slate-400" />
                            <span>{item.time}</span>
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: MY PROJECTS VIEW */}
          {activeTab === 'My Projects' && (
            <div className="space-y-6 animate-fadeIn">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h1 className={`text-2xl sm:text-3xl font-bold tracking-tight ${
                    isDarkMode ? 'text-slate-100' : 'text-slate-900'
                  }`}>
                    My Projects
                  </h1>
                  <p className={`text-xs sm:text-sm mt-1 font-medium ${
                    isDarkMode ? 'text-slate-300' : 'text-slate-500'
                  }`}>
                    {allProjects.length} projects <span className="mx-1">·</span> {filteredProjects.length} shown
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() => {
                    setIsCreateProjectTouched(!isCreateProjectTouched);
                    setActiveTab('Create Project');
                  }}
                  title="Touch to toggle grey border, cream color lighting glow & zoom-in"
                  className={`px-5 py-3 rounded-xl font-bold text-sm flex items-center justify-center gap-2 transition-all duration-300 cursor-pointer border-2 ${
                    isCreateProjectTouched
                      ? isDarkMode
                        ? 'bg-[#96562c] text-white border-slate-300 scale-[1.04] shadow-[0_0_35px_rgba(251,191,36,0.35),0_12px_36px_rgba(150,86,44,0.4)] ring-4 ring-amber-500/30'
                        : 'bg-[#7c4a27] text-white border-slate-500 scale-[1.04] shadow-[0_0_40px_rgba(254,243,199,0.95),0_14px_40px_rgba(124,74,39,0.3)] ring-4 ring-amber-100/90'
                      : isDarkMode
                      ? 'bg-[#96562c] hover:bg-[#7c4a27] border-slate-700 hover:border-slate-300 text-white hover:scale-[1.04] hover:shadow-[0_0_35px_rgba(251,191,36,0.25)]'
                      : 'bg-[#7c4a27] hover:bg-[#633a1e] border-stone-300 hover:border-slate-500 text-white hover:scale-[1.04] hover:shadow-[0_0_40px_rgba(254,243,199,0.95)]'
                  }`}
                >
                  <Plus className="w-4 h-4 stroke-[3]" />
                  <span>Create New Project</span>
                </button>
              </div>

              <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3.5">
                <div className="relative flex-1 max-w-md">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                    <Search className="w-4 h-4" />
                  </div>
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search projects..."
                    className={`w-full pl-10 pr-4 py-2.5 text-sm rounded-xl border focus:outline-none transition-all ${
                      isDarkMode
                        ? 'bg-[#1a1a1e] border-slate-800 text-slate-100 placeholder-slate-500 hover:border-[#96562c] focus:border-[#96562c] focus:ring-4 focus:ring-[#96562c]/20'
                        : 'bg-white border-stone-200 text-slate-900 placeholder-slate-400 hover:border-[#7c4a27] focus:border-[#7c4a27] focus:ring-4 focus:ring-[#7c4a27]/15'
                    }`}
                  />
                </div>

                <div className="flex flex-wrap items-center gap-2.5">
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className={`px-3 py-2.5 rounded-xl border text-xs sm:text-sm font-semibold focus:outline-none cursor-pointer transition-all ${
                      isDarkMode
                        ? 'bg-[#1a1a1e] border-slate-800 text-slate-200 hover:border-[#96562c]'
                        : 'bg-white border-stone-200 text-slate-700 hover:border-[#7c4a27]'
                    }`}
                  >
                    <option value="All Statuses">All Statuses</option>
                    <option value="In Progress">In Progress</option>
                    <option value="Under Review">Under Review</option>
                    <option value="Draft">Draft</option>
                    <option value="Completed">Completed</option>
                  </select>

                  <select
                    value={typeFilter}
                    onChange={(e) => setTypeFilter(e.target.value)}
                    className={`px-3 py-2.5 rounded-xl border text-xs sm:text-sm font-semibold focus:outline-none cursor-pointer transition-all ${
                      isDarkMode
                        ? 'bg-[#1a1a1e] border-slate-800 text-slate-200 hover:border-[#96562c]'
                        : 'bg-white border-stone-200 text-slate-700 hover:border-[#7c4a27]'
                    }`}
                  >
                    <option value="All Types">All Types</option>
                    <option value="AML/CTF">AML/CTF</option>
                    <option value="KYC/CDD">KYC/CDD</option>
                    <option value="Regulatory Reporting">Regulatory Reporting</option>
                    <option value="Data Governance">Data Governance</option>
                  </select>

                  <div className={`flex items-center p-1 rounded-xl border ${
                    isDarkMode ? 'bg-[#1a1a1e] border-slate-800' : 'bg-white border-stone-200'
                  }`}>
                    <button
                      type="button"
                      onClick={() => setViewMode('list')}
                      title="List View"
                      className={`p-1.5 rounded-lg transition-all cursor-pointer ${
                        viewMode === 'list'
                          ? isDarkMode
                            ? 'bg-[#96562c] text-white'
                            : 'bg-[#7c4a27] text-white'
                          : 'text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
                      }`}
                    >
                      <List className="w-4 h-4" />
                    </button>
                    <button
                      type="button"
                      onClick={() => setViewMode('grid')}
                      title="Grid View"
                      className={`p-1.5 rounded-lg transition-all cursor-pointer ${
                        viewMode === 'grid'
                          ? isDarkMode
                            ? 'bg-[#96562c] text-white'
                            : 'bg-[#7c4a27] text-white'
                          : 'text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
                      }`}
                    >
                      <LayoutGrid className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>

              <div
                onClick={() => setIsMyProjectsBoxActive(!isMyProjectsBoxActive)}
                title="Click box to toggle brown border, cream edge lighting glow & zoom-in"
                className={`rounded-2xl border transition-all duration-300 overflow-hidden cursor-pointer ${
                  isMyProjectsBoxActive
                    ? isDarkMode
                      ? 'bg-[#1e1e24] border-[#96562c] scale-[1.015] shadow-[0_0_35px_rgba(251,191,36,0.25),0_12px_36px_rgba(150,86,44,0.35)] ring-2 ring-[#96562c]/40'
                      : 'bg-[#fdfdf9] border-[#7c4a27] scale-[1.015] shadow-[0_0_40px_rgba(254,243,199,0.95),0_14px_40px_rgba(124,74,39,0.22)] ring-4 ring-amber-100/90'
                    : isDarkMode
                    ? 'bg-[#1a1a1e] border-slate-800 shadow-sm hover:border-[#96562c] hover:scale-[1.01]'
                    : 'bg-white border-stone-200/90 shadow-xs hover:border-[#7c4a27] hover:scale-[1.01] hover:bg-[#fdfdfc]'
                }`}
              >
                {viewMode === 'list' ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs sm:text-sm border-collapse">
                      <thead>
                        <tr className={`border-b text-[11px] font-extrabold uppercase tracking-wider ${
                          isDarkMode
                            ? 'border-slate-800 bg-slate-900/80 text-slate-200'
                            : 'border-stone-100 bg-stone-50/80 text-stone-500'
                        }`}>
                          <th className="py-3.5 px-5">ID</th>
                          <th className="py-3.5 px-5">PROJECT NAME</th>
                          <th className="py-3.5 px-5">TYPE</th>
                          <th className="py-3.5 px-5">STATUS</th>
                          <th className="py-3.5 px-5">LAST UPDATED</th>
                          <th className="py-3.5 px-5">OWNER</th>
                          <th className="py-3.5 px-5 text-right">ACTION</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-medium">
                        {filteredProjects.map((project) => (
                          <tr
                            key={project.id}
                            className={`transition-colors ${
                              isDarkMode ? 'hover:bg-slate-800/40' : 'hover:bg-stone-50/90'
                            }`}
                          >
                            <td className="py-4 px-5 font-mono text-xs font-semibold text-slate-500 dark:text-slate-300">
                              {project.id}
                            </td>
                            <td className="py-4 px-5 font-bold text-slate-900 dark:text-slate-100">
                              {project.name}
                            </td>
                            <td className="py-4 px-5 text-slate-600 dark:text-slate-300">
                              {project.type}
                            </td>
                            <td className="py-4 px-5">
                              <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-bold border ${project.statusColor}`}>
                                <span className={`w-1.5 h-1.5 rounded-full ${project.dotColor}`} />
                                {project.status}
                              </span>
                            </td>
                            <td className="py-4 px-5 text-slate-600 dark:text-slate-300">
                              {project.lastUpdated}
                            </td>
                            <td className="py-4 px-5 font-medium text-slate-700 dark:text-slate-200">
                              {project.owner}
                            </td>
                            <td className="py-4 px-5 text-right">
                              <button
                                type="button"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleOpenProject(project);
                                }}
                                className="text-xs font-bold text-[#7c4a27] dark:text-amber-400 hover:underline inline-flex items-center gap-1 cursor-pointer"
                              >
                                <span>Open</span>
                                <ArrowRight className="w-3.5 h-3.5" />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="p-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {filteredProjects.map((project) => (
                      <div
                        key={project.id}
                        className={`p-5 rounded-xl border text-left transition-all duration-300 cursor-pointer ${
                          isDarkMode
                            ? 'bg-slate-900/60 border-slate-800 hover:border-[#96562c]'
                            : 'bg-stone-50/70 border-stone-200/80 hover:border-[#7c4a27]'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-3">
                          <span className="font-mono text-xs font-bold text-slate-500 dark:text-slate-300">{project.id}</span>
                          <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[11px] font-bold border ${project.statusColor}`}>
                            <span className={`w-1.5 h-1.5 rounded-full ${project.dotColor}`} />
                            {project.status}
                          </span>
                        </div>
                        <h3 className="font-bold text-base text-slate-900 dark:text-slate-100 mb-1">{project.name}</h3>
                        <p className="text-xs text-slate-500 dark:text-slate-300 mb-4">{project.type}</p>
                        <div className="flex items-center justify-between pt-3 border-t border-slate-200 dark:border-slate-800 text-xs">
                          <span className="text-slate-500 dark:text-slate-300 font-medium">{project.owner}</span>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleOpenProject(project);
                            }}
                            className="font-bold text-[#7c4a27] dark:text-amber-400 hover:underline flex items-center gap-1"
                          >
                            <span>Open</span>
                            <ArrowRight className="w-3 h-3" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 3: CREATE NEW PROJECT VIEW */}
          {activeTab === 'Create Project' && (
            <div className="space-y-6 animate-fadeIn max-w-4xl">
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 dark:text-slate-300">
                <button
                  type="button"
                  onClick={() => setActiveTab('Dashboard')}
                  className="hover:text-[#7c4a27] dark:hover:text-amber-400 cursor-pointer transition-colors"
                >
                  Dashboard
                </button>
                <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                <span className="text-slate-800 dark:text-slate-200 font-bold">Create Project</span>
              </div>

              <div className="text-left">
                <h1 className={`text-2xl sm:text-3xl font-bold tracking-tight ${
                  isDarkMode ? 'text-slate-100' : 'text-slate-900'
                }`}>
                  Create New Project
                </h1>
                <p className={`text-xs sm:text-sm mt-1.5 font-medium ${
                  isDarkMode ? 'text-slate-300' : 'text-slate-500'
                }`}>
                  Define your compliance or regulatory project. You can edit all details later.
                </p>
              </div>

              <div
                onClick={() => setIsFormCardActive(!isFormCardActive)}
                title="Click box to toggle brown border, cream edge lighting glow & zoom-in"
                className={`rounded-2xl border p-6 sm:p-8 transition-all duration-300 text-left cursor-pointer ${
                  isFormCardActive
                    ? isDarkMode
                      ? 'bg-[#1a1a1e] border-[#96562c] scale-[1.01] shadow-[0_0_35px_rgba(251,191,36,0.25),0_12px_36px_rgba(150,86,44,0.35)] ring-2 ring-[#96562c]/40'
                      : 'bg-[#fdfdf9] border-[#7c4a27] scale-[1.01] shadow-[0_0_40px_rgba(254,243,199,0.95),0_14px_40px_rgba(124,74,39,0.22)] ring-4 ring-amber-100/90'
                    : isDarkMode
                    ? 'bg-[#1a1a1e] border-slate-800 shadow-sm hover:border-[#96562c] hover:scale-[1.005]'
                    : 'bg-white border-stone-200/90 shadow-xs hover:border-[#7c4a27] hover:scale-[1.005] hover:bg-[#fdfdfc]'
                }`}
              >
                <form onSubmit={handleCreateProjectSubmit} className="space-y-8">
                  <div className="space-y-5">
                    <h2 className="text-xs font-bold tracking-wider uppercase text-slate-400 border-b border-slate-100 dark:border-slate-800 pb-2">
                      PROJECT BASICS
                    </h2>

                    <div className="space-y-1.5">
                      <label className={`block text-xs sm:text-sm font-semibold ${
                        isDarkMode ? 'text-slate-200' : 'text-slate-700'
                      }`}>
                        PROJECT NAME <span className="text-[#7c4a27] dark:text-amber-400 font-bold">*</span>
                      </label>
                      <input
                        type="text"
                        required
                        value={newProjectName}
                        onChange={(e) => setNewProjectName(e.target.value)}
                        placeholder="e.g. SMCR Compliance Review 2026"
                        className={`w-full px-4 py-3 text-sm rounded-xl border focus:outline-none transition-all ${
                          isDarkMode
                            ? 'bg-slate-800/80 border-slate-700 text-slate-100 placeholder-slate-500 hover:border-[#96562c] focus:border-[#96562c] focus:ring-4 focus:ring-[#96562c]/20'
                            : 'bg-white border-stone-200 text-slate-900 placeholder-slate-400 hover:border-[#7c4a27] focus:border-[#7c4a27] focus:ring-4 focus:ring-[#7c4a27]/15'
                        }`}
                      />
                    </div>

                    <div className="space-y-1.5">
                      <label className={`block text-xs sm:text-sm font-semibold ${
                        isDarkMode ? 'text-slate-200' : 'text-slate-700'
                      }`}>
                        PROJECT TYPE <span className="text-[#7c4a27] dark:text-amber-400 font-bold">*</span>
                      </label>
                      <select
                        required
                        value={newProjectType}
                        onChange={(e) => setNewProjectType(e.target.value)}
                        className={`w-full px-4 py-3 text-sm rounded-xl border focus:outline-none cursor-pointer transition-all ${
                          isDarkMode
                            ? 'bg-slate-800/80 border-slate-700 text-slate-100 hover:border-[#96562c] focus:border-[#96562c]'
                            : 'bg-white border-stone-200 text-slate-900 hover:border-[#7c4a27] focus:border-[#7c4a27]'
                        }`}
                      >
                        <option value="">Select type...</option>
                        <option value="AML/CTF">AML/CTF (Anti-Money Laundering)</option>
                        <option value="KYC/CDD">KYC/CDD (Know Your Customer)</option>
                        <option value="Regulatory Reporting">Regulatory Reporting</option>
                        <option value="Data Governance">Data Governance</option>
                        <option value="Consumer Duty / Conduct">Consumer Duty / Conduct</option>
                      </select>
                    </div>

                    <div className="space-y-1.5">
                      <label className={`block text-xs sm:text-sm font-semibold ${
                        isDarkMode ? 'text-slate-200' : 'text-slate-700'
                      }`}>
                        DESCRIPTION
                      </label>
                      <textarea
                        rows={4}
                        value={newProjectDescription}
                        onChange={(e) => setNewProjectDescription(e.target.value)}
                        placeholder="Brief description of the project scope and objectives..."
                        className={`w-full px-4 py-3 text-sm rounded-xl border focus:outline-none transition-all ${
                          isDarkMode
                            ? 'bg-slate-800/80 border-slate-700 text-slate-100 placeholder-slate-500 hover:border-[#96562c] focus:border-[#96562c] focus:ring-4 focus:ring-[#96562c]/20'
                            : 'bg-white border-stone-200 text-slate-900 placeholder-slate-400 hover:border-[#7c4a27] focus:border-[#7c4a27] focus:ring-4 focus:ring-[#7c4a27]/15'
                        }`}
                      />
                    </div>
                  </div>

                  <div className="space-y-5 pt-2">
                    <h2 className="text-xs font-bold tracking-wider uppercase text-slate-400 border-b border-slate-100 dark:border-slate-800 pb-2">
                      REGULATORY CONTEXT
                    </h2>

                    <div className="space-y-1.5">
                      <label className={`block text-xs sm:text-sm font-semibold ${
                        isDarkMode ? 'text-slate-200' : 'text-slate-700'
                      }`}>
                        JURISDICTION
                      </label>
                      <select
                        value={newProjectJurisdiction}
                        onChange={(e) => setNewProjectJurisdiction(e.target.value)}
                        className={`w-full px-4 py-3 text-sm rounded-xl border focus:outline-none cursor-pointer transition-all ${
                          isDarkMode
                            ? 'bg-slate-800/80 border-slate-700 text-slate-100 hover:border-[#96562c] focus:border-[#96562c]'
                            : 'bg-white border-stone-200 text-slate-900 hover:border-[#7c4a27] focus:border-[#7c4a27]'
                        }`}
                      >
                        <option value="">Select jurisdiction...</option>
                        <option value="UK (FCA / PRA)">UK (FCA / PRA)</option>
                        <option value="EU (EBA / ESMA)">EU (EBA / ESMA)</option>
                        <option value="US (SEC / FINRA)">US (SEC / FINRA)</option>
                        <option value="Global / Cross-border">Global / Cross-border</option>
                      </select>
                    </div>

                    <div className="space-y-1.5">
                      <label className={`block text-xs sm:text-sm font-semibold ${
                        isDarkMode ? 'text-slate-200' : 'text-slate-700'
                      }`}>
                        REGULATORY DOMAIN / FRAMEWORK
                      </label>
                      <input
                        type="text"
                        value={newProjectDomain}
                        onChange={(e) => setNewProjectDomain(e.target.value)}
                        placeholder="e.g. Anti-Bribery & Corruption, SMCR, MiFID II..."
                        className={`w-full px-4 py-3 text-sm rounded-xl border focus:outline-none transition-all ${
                          isDarkMode
                            ? 'bg-slate-800/80 border-slate-700 text-slate-100 placeholder-slate-500 hover:border-[#96562c] focus:border-[#96562c] focus:ring-4 focus:ring-[#96562c]/20'
                            : 'bg-white border-stone-200 text-slate-900 placeholder-slate-400 hover:border-[#7c4a27] focus:border-[#7c4a27] focus:ring-4 focus:ring-[#7c4a27]/15'
                        }`}
                      />
                    </div>
                  </div>

                  <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-200 dark:border-slate-800">
                    <button
                      type="button"
                      onClick={() => setActiveTab('Dashboard')}
                      className={`px-5 py-3 rounded-xl font-bold text-sm transition-all cursor-pointer ${
                        isDarkMode
                          ? 'bg-slate-800 hover:bg-slate-700 text-slate-300'
                          : 'bg-stone-100 hover:bg-stone-200 text-slate-700'
                      }`}
                    >
                      Cancel
                    </button>

                    <button
                      type="submit"
                      onClick={(e) => e.stopPropagation()}
                      className="px-6 py-3 rounded-xl bg-[#7c4a27] hover:bg-[#633a1e] dark:bg-[#96562c] dark:hover:bg-[#7c4a27] text-white font-bold text-sm shadow-md shadow-amber-950/20 flex items-center justify-center gap-2 transition-all cursor-pointer border-2 border-stone-300 hover:border-slate-500 hover:scale-[1.03] hover:shadow-[0_0_35px_rgba(254,243,199,0.95)]"
                    >
                      <Plus className="w-4 h-4 stroke-[3]" />
                      <span>Create Project</span>
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

          {/* TAB 4: PROJECT DETAILS / OVERVIEW VIEW (Exact match with uploaded screenshot in Grey & Brown Theme!) */}
          {activeTab === 'Project Details' && (
            <div className="space-y-6 animate-fadeIn text-left">
              {/* Breadcrumb Navigation */}
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 dark:text-slate-400">
                <button
                  type="button"
                  onClick={() => setActiveTab('My Projects')}
                  className="hover:text-[#7c4a27] dark:hover:text-amber-400 cursor-pointer transition-colors"
                >
                  My Projects
                </button>
                <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                <span className="text-slate-800 dark:text-slate-200 font-bold">{currentProject.name}</span>
              </div>

              {/* Project Header Overview Card */}
              <div
                onClick={() => setIsProjectDetailsCardActive(!isProjectDetailsCardActive)}
                title="Click box to toggle brown border, cream edge lighting glow & zoom-in"
                className={`rounded-2xl border p-6 sm:p-8 transition-all duration-300 cursor-pointer ${
                  isProjectDetailsCardActive
                    ? isDarkMode
                      ? 'bg-[#1e1e24] border-[#96562c] scale-[1.01] shadow-[0_0_35px_rgba(251,191,36,0.25),0_12px_36px_rgba(150,86,44,0.35)] ring-2 ring-[#96562c]/40'
                      : 'bg-[#fdfdf9] border-[#7c4a27] scale-[1.01] shadow-[0_0_40px_rgba(254,243,199,0.95),0_14px_40px_rgba(124,74,39,0.22)] ring-4 ring-amber-100/90'
                    : isDarkMode
                    ? 'bg-[#1a1a1e] border-slate-800 shadow-sm hover:border-[#96562c] hover:scale-[1.005]'
                    : 'bg-white border-stone-200/90 shadow-xs hover:border-[#7c4a27] hover:scale-[1.005] hover:bg-[#fdfdfc]'
                }`}
              >
                <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                  <div>
                    {/* ID & Status Badges */}
                    <div className="flex items-center gap-2.5 mb-2.5">
                      <span className="font-mono text-xs font-bold text-slate-400 bg-stone-100 dark:bg-slate-800 px-2.5 py-1 rounded">
                        {currentProject.id}
                      </span>
                      <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-bold border ${currentProject.statusColor}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${currentProject.dotColor}`} />
                        {currentProject.status}
                      </span>
                    </div>

                    {/* Title & Description */}
                    <h1 className={`text-2xl sm:text-3xl font-bold tracking-tight ${
                      isDarkMode ? 'text-slate-100' : 'text-slate-900'
                    }`}>
                      {currentProject.name}
                    </h1>
                    <p className={`text-xs sm:text-sm mt-1.5 font-normal max-w-2xl ${
                      isDarkMode ? 'text-slate-400' : 'text-slate-600'
                    }`}>
                      {currentProject.description || 'End-to-end compliance workflow for retail operations.'}
                    </p>

                    {/* Metadata line */}
                    <p className="text-xs text-slate-400 mt-3 font-medium">
                      Type: <span className="font-bold text-slate-700 dark:text-slate-300">{currentProject.type}</span> · Owner: <span className="font-bold text-slate-700 dark:text-slate-300">{currentProject.owner}</span> · Updated: <span className="font-bold text-slate-700 dark:text-slate-300">{currentProject.lastUpdated}</span>
                    </p>
                  </div>

                  {/* Top Right Action Buttons: Edit & Open Workflow */}
                  <div className="flex items-center gap-2.5 shrink-0 pt-2 md:pt-0">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        alert(`Editing settings for ${currentProject.name}...`);
                      }}
                      className={`px-4 py-2.5 rounded-xl font-bold text-xs sm:text-sm border transition-all cursor-pointer ${
                        isDarkMode
                          ? 'bg-slate-800 border-slate-700 hover:border-slate-500 text-slate-200'
                          : 'bg-stone-50 border-stone-200 hover:border-stone-400 text-slate-700'
                      }`}
                    >
                      Edit
                    </button>

                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        alert(`Opening active workflow for ${currentProject.name}...`);
                      }}
                      className="px-5 py-2.5 rounded-xl bg-[#7c4a27] hover:bg-[#633a1e] dark:bg-[#96562c] dark:hover:bg-[#7c4a27] text-white font-bold text-xs sm:text-sm shadow-md shadow-amber-950/20 flex items-center justify-center gap-2 transition-all cursor-pointer border-2 border-stone-300 hover:border-slate-500 hover:scale-[1.03]"
                    >
                      <span>Open Workflow</span>
                      <ArrowRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>

              {/* Sub-Navigation Tabs Bar */}
              <div className={`flex items-center gap-6 border-b text-xs sm:text-sm font-bold ${
                isDarkMode ? 'border-slate-800' : 'border-slate-200'
              }`}>
                {['Overview', 'Workflow', 'Documents', 'Audit Trail'].map((tab) => (
                  <button
                    key={tab}
                    type="button"
                    onClick={() => setProjectSubTab(tab)}
                    className={`py-3 transition-colors cursor-pointer border-b-2 -mb-px ${
                      projectSubTab === tab
                        ? 'border-[#7c4a27] text-[#7c4a27] dark:border-amber-400 dark:text-amber-400'
                        : 'border-transparent text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
                    }`}
                  >
                    {tab}
                  </button>
                ))}
              </div>

              {/* Sub-Tab 1: OVERVIEW TAB CONTENT */}
              {projectSubTab === 'Overview' && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-2">
                  {/* LEFT COLUMN: PROJECT DETAILS CARD (2 cols) */}
                  <div
                    onClick={() => setIsProjectDetailsCardActive(!isProjectDetailsCardActive)}
                    title="Click box to toggle brown border, cream edge lighting glow & zoom-in"
                    className={`lg:col-span-2 rounded-2xl border p-6 transition-all duration-300 cursor-pointer ${
                      isProjectDetailsCardActive
                        ? isDarkMode
                          ? 'bg-[#1e1e24] border-[#96562c] scale-[1.01] shadow-[0_0_35px_rgba(251,191,36,0.25),0_12px_36px_rgba(150,86,44,0.35)] ring-2 ring-[#96562c]/40'
                          : 'bg-[#fdfdf9] border-[#7c4a27] scale-[1.01] shadow-[0_0_40px_rgba(254,243,199,0.95),0_14px_40px_rgba(124,74,39,0.22)] ring-4 ring-amber-100/90'
                        : isDarkMode
                        ? 'bg-[#1a1a1e] border-slate-800 shadow-sm hover:border-[#96562c] hover:scale-[1.005]'
                        : 'bg-white border-stone-200/90 shadow-xs hover:border-[#7c4a27] hover:scale-[1.005] hover:bg-[#fdfdfc]'
                    }`}
                  >
                    <h2 className={`text-xs font-bold tracking-wider uppercase border-b border-slate-100 dark:border-slate-800 pb-3 mb-4 ${
                      isDarkMode ? 'text-amber-300/90' : 'text-slate-500'
                    }`}>
                      PROJECT DETAILS
                    </h2>

                    <div className="divide-y divide-slate-100 dark:divide-slate-800/60 text-xs sm:text-sm">
                      <div className="py-3 flex items-center justify-between">
                        <span className="text-slate-500 dark:text-slate-300 font-medium">Project ID</span>
                        <span className="font-mono font-bold text-slate-800 dark:text-slate-100">{currentProject.id}</span>
                      </div>
                      <div className="py-3 flex items-center justify-between">
                        <span className="text-slate-500 dark:text-slate-300 font-medium">Project Name</span>
                        <span className="font-bold text-slate-900 dark:text-slate-100">{currentProject.name}</span>
                      </div>
                      <div className="py-3 flex items-center justify-between">
                        <span className="text-slate-500 dark:text-slate-300 font-medium">Type</span>
                        <span className="font-semibold text-slate-700 dark:text-slate-200">{currentProject.type}</span>
                      </div>
                      <div className="py-3 flex items-center justify-between">
                        <span className="text-slate-500 dark:text-slate-300 font-medium">Status</span>
                        <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-bold border ${currentProject.statusColor}`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${currentProject.dotColor || 'bg-blue-600'}`} />
                          {currentProject.status}
                        </span>
                      </div>
                      <div className="py-3 flex items-center justify-between">
                        <span className="text-slate-500 dark:text-slate-300 font-medium">Owner</span>
                        <span className="font-semibold text-slate-800 dark:text-slate-100">{currentProject.owner}</span>
                      </div>
                      <div className="py-3 flex items-center justify-between">
                        <span className="text-slate-500 dark:text-slate-300 font-medium">Last Updated</span>
                        <span className="font-medium text-slate-700 dark:text-slate-200">{currentProject.lastUpdated}</span>
                      </div>
                      <div className="py-3 flex items-center justify-between">
                        <span className="text-slate-500 dark:text-slate-300 font-medium">Created</span>
                        <span className="font-medium text-slate-700 dark:text-slate-200">{currentProject.created || '01 Sep 2026'}</span>
                      </div>
                      <div className="py-3 flex items-center justify-between">
                        <span className="text-slate-500 dark:text-slate-300 font-medium">Jurisdiction</span>
                        <span className="font-semibold text-[#7c4a27] dark:text-amber-400">{currentProject.jurisdiction || 'United Kingdom - FCA'}</span>
                      </div>
                    </div>
                  </div>

                  {/* RIGHT COLUMN: STACKED COMPLETION & TEAM CARDS (1 col) */}
                  <div className="space-y-6">
                    {/* COMPLETION CARD */}
                    <div
                      onClick={() => setIsCompletionCardActive(!isCompletionCardActive)}
                      title="Click box to toggle brown border, cream edge lighting glow & zoom-in"
                      className={`rounded-2xl border p-5 transition-all duration-300 cursor-pointer ${
                        isCompletionCardActive
                          ? isDarkMode
                            ? 'bg-[#1e1e24] border-[#96562c] scale-[1.015] shadow-[0_0_35px_rgba(251,191,36,0.25),0_12px_36px_rgba(150,86,44,0.35)] ring-2 ring-[#96562c]/40'
                            : 'bg-[#fdfdf9] border-[#7c4a27] scale-[1.015] shadow-[0_0_40px_rgba(254,243,199,0.95),0_14px_40px_rgba(124,74,39,0.22)] ring-4 ring-amber-100/90'
                          : isDarkMode
                          ? 'bg-[#1a1a1e] border-slate-800 shadow-sm hover:border-[#96562c] hover:scale-[1.01]'
                          : 'bg-white border-stone-200/90 shadow-xs hover:border-[#7c4a27] hover:scale-[1.01] hover:bg-[#fdfdfc]'
                      }`}
                    >
                      <h2 className={`text-xs font-bold tracking-wider uppercase border-b border-slate-100 dark:border-slate-800 pb-3 mb-4 ${
                        isDarkMode ? 'text-amber-300/90' : 'text-slate-500'
                      }`}>
                        COMPLETION
                      </h2>

                      {/* Progress bar */}
                      <div className="space-y-2 mb-5">
                        <div className="flex items-center justify-between text-xs font-bold">
                          <span className="text-slate-600 dark:text-slate-300">Overall progress</span>
                          <span className="text-[#7c4a27] dark:text-amber-400 text-sm">60%</span>
                        </div>
                        <div className="w-full h-2 bg-stone-100 dark:bg-slate-800 rounded-full overflow-hidden">
                          <div className="h-full bg-[#7c4a27] dark:bg-amber-500 rounded-full w-[60%]" />
                        </div>
                      </div>

                      {/* Checklist */}
                      <div className="space-y-2.5 text-xs sm:text-sm font-medium">
                        <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 line-through">
                          <CheckSquare className="w-4 h-4 shrink-0 text-emerald-600 stroke-[2.5]" />
                          <span>Requirements defined</span>
                        </div>
                        <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 line-through">
                          <CheckSquare className="w-4 h-4 shrink-0 text-emerald-600 stroke-[2.5]" />
                          <span>Workflow configured</span>
                        </div>
                        <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 line-through">
                          <CheckSquare className="w-4 h-4 shrink-0 text-emerald-600 stroke-[2.5]" />
                          <span>Advisor review</span>
                        </div>
                        <div className="flex items-center gap-2 text-slate-500 dark:text-slate-300">
                          <Square className="w-4 h-4 shrink-0 stroke-[2]" />
                          <span>Compliance sign-off</span>
                        </div>
                        <div className="flex items-center gap-2 text-slate-500 dark:text-slate-300">
                          <Square className="w-4 h-4 shrink-0 stroke-[2]" />
                          <span>Final submission</span>
                        </div>
                      </div>
                    </div>

                    {/* TEAM CARD */}
                    <div
                      onClick={() => setIsTeamCardActive(!isTeamCardActive)}
                      title="Click box to toggle brown border, cream edge lighting glow & zoom-in"
                      className={`rounded-2xl border p-5 transition-all duration-300 cursor-pointer ${
                        isTeamCardActive
                          ? isDarkMode
                            ? 'bg-[#1e1e24] border-[#96562c] scale-[1.015] shadow-[0_0_35px_rgba(251,191,36,0.25),0_12px_36px_rgba(150,86,44,0.35)] ring-2 ring-[#96562c]/40'
                            : 'bg-[#fdfdf9] border-[#7c4a27] scale-[1.015] shadow-[0_0_40px_rgba(254,243,199,0.95),0_14px_40px_rgba(124,74,39,0.22)] ring-4 ring-amber-100/90'
                          : isDarkMode
                          ? 'bg-[#1a1a1e] border-slate-800 shadow-sm hover:border-[#96562c] hover:scale-[1.01]'
                          : 'bg-white border-stone-200/90 shadow-xs hover:border-[#7c4a27] hover:scale-[1.01] hover:bg-[#fdfdfc]'
                      }`}
                    >
                      <h2 className={`text-xs font-bold tracking-wider uppercase border-b border-slate-100 dark:border-slate-800 pb-3 mb-4 ${
                        isDarkMode ? 'text-amber-300/90' : 'text-slate-500'
                      }`}>
                        TEAM
                      </h2>

                      <div className="space-y-3 divide-y divide-slate-100 dark:divide-slate-800/60">
                        <div className="pt-2 flex items-center justify-between">
                          <div className="flex items-center gap-2.5">
                            <div className="w-7 h-7 rounded-lg bg-[#7c4a27] text-white font-bold text-xs flex items-center justify-center">
                              JN
                            </div>
                            <span className="font-bold text-xs sm:text-sm text-slate-900 dark:text-slate-100">J. Nakamura</span>
                          </div>
                          <span className="text-[11px] font-mono font-semibold px-2 py-0.5 rounded bg-amber-50 text-[#7c4a27] border border-amber-200/60 dark:bg-amber-950/40 dark:text-amber-300">
                            Owner
                          </span>
                        </div>

                        <div className="pt-3 flex items-center justify-between">
                          <div className="flex items-center gap-2.5">
                            <div className="w-7 h-7 rounded-lg bg-[#96562c] text-white font-bold text-xs flex items-center justify-center">
                              SO
                            </div>
                            <span className="font-bold text-xs sm:text-sm text-slate-900 dark:text-slate-100">S. Okonkwo</span>
                          </div>
                          <span className="text-[11px] font-mono text-slate-500 dark:text-slate-300 font-medium">
                            Advisor 1
                          </span>
                        </div>

                        <div className="pt-3 flex items-center justify-between">
                          <div className="flex items-center gap-2.5">
                            <div className="w-7 h-7 rounded-lg bg-slate-700 text-white font-bold text-xs flex items-center justify-center">
                              AP
                            </div>
                            <span className="font-bold text-xs sm:text-sm text-slate-900 dark:text-slate-100">A. Petrov</span>
                          </div>
                          <span className="text-[11px] font-mono text-slate-500 dark:text-slate-300 font-medium">
                            Advisor 2
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Sub-Tabs Placeholders for Workflow, Documents, Audit Trail */}
              {projectSubTab !== 'Overview' && (
                <div className={`p-8 rounded-2xl border text-center animate-fadeIn ${
                  isDarkMode ? 'bg-[#1a1a1e] border-slate-800' : 'bg-white border-stone-200'
                }`}>
                  <h2 className="text-xl font-bold mb-2">{projectSubTab} Module</h2>
                  <p className="text-slate-400 text-sm mb-6">Detailed {projectSubTab.toLowerCase()} data for {currentProject.name}.</p>
                  <button
                    type="button"
                    onClick={() => setProjectSubTab('Overview')}
                    className="px-4 py-2 bg-[#7c4a27] text-white font-semibold rounded-xl text-xs cursor-pointer"
                  >
                    ← Return to Overview
                  </button>
                </div>
              )}
            </div>
          )}

          {/* TAB: ADVISORS / EXPERTS VIEW */}
          {activeTab === 'Advisors / Experts' && (
            <AdvisorsExpertsView isDarkMode={isDarkMode} />
          )}

          {/* TAB: REGULATORY SUPPORT VIEW */}
          {activeTab === 'Regulatory Support' && (
            <RegulatorySupportView isDarkMode={isDarkMode} />
          )}

          {/* OTHER TABS PLACEHOLDER (Tools, Settings) */}
          {activeTab !== 'Dashboard' && activeTab !== 'My Projects' && activeTab !== 'Create Project' && activeTab !== 'Project Details' && activeTab !== 'Advisors / Experts' && activeTab !== 'Regulatory Support' && (
            <div className={`p-8 rounded-2xl border text-center animate-fadeIn ${
              isDarkMode ? 'bg-[#1a1a1e] border-slate-800' : 'bg-white border-stone-200'
            }`}>
              <h2 className="text-xl font-bold mb-2">{activeTab} Workspace</h2>
              <p className="text-slate-400 text-sm mb-6">This module is part of the FinRegTech Shipyard build.</p>
              <button
                type="button"
                onClick={() => setActiveTab('Dashboard')}
                className="px-4 py-2 bg-[#7c4a27] text-white font-semibold rounded-xl text-xs cursor-pointer"
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
