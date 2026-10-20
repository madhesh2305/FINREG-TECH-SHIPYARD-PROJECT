import React, { useState, useEffect } from 'react';
import { getProjects, getProjectDetails, createProject } from '../services/projectService';
import { getCurrentUser, logoutUser } from '../services/authService';
import { getAdvisors } from '../services/advisorService';
import AdvisorsExpertsView from './AdvisorsExpertsView';
import RegulatorySupportView from './RegulatorySupportView';
import ToolsView from './ToolsView';
import SettingsView from './SettingsView';
import AdvisorAdviceView from './AdvisorAdviceView';
import AdviceDecisionsView from './AdviceDecisionsView';
import AiRagFindingsView from './AiRagFindingsView';
import ReadinessView from './ReadinessView';
import AuditTrailView from './AuditTrailView';




import {
  Menu,
  Sun,
  Moon,
  Bell,
  ChevronDown,
  LayoutDashboard,
  Folder,
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

export default function DashboardView({ isDarkMode, onToggleTheme, onSignOut, currentUser }) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [activeTab, setActiveTab] = useState('Dashboard'); // 'Dashboard' | 'My Projects' | 'Create Project' | 'Project Details'
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [isNotificationMenuOpen, setIsNotificationMenuOpen] = useState(false);

  // Authenticated user profile state (DEF-03)
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

  const userName = userProfile?.name || 'Project Builder';
  const userEmail = userProfile?.email || 'builder@example.com';
  const userRoleTitle = userProfile?.role || 'Builder';
  const userInitials = userName
    .split(' ')
    .filter(Boolean)
    .map((n) => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase() || 'PB';

  // Interactive Notifications State
  const [notificationsList, setNotificationsList] = useState([]);

  const unreadCount = notificationsList.filter((n) => !n.read).length;

  const handleNotificationClick = (item) => {
    setNotificationsList((prev) =>
      prev.map((n) => (n.id === item.id ? { ...n, read: true } : n))
    );
    setIsNotificationMenuOpen(false);
    if (item.tab) {
      setActiveTab(item.tab);
    }
  };

  const handleMarkAllRead = () => {
    setNotificationsList((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  // Selected Project State for Project Details View
  const [selectedProject, setSelectedProject] = useState(null);
  const [projectSubTab, setProjectSubTab] = useState('Overview');
  const [targetRequirementId, setTargetRequirementId] = useState(null);

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
  const [createProjectStep, setCreateProjectStep] = useState(1);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectType, setNewProjectType] = useState('');
  const [newProjectDescription, setNewProjectDescription] = useState('');
  const [newProjectJurisdiction, setNewProjectJurisdiction] = useState('');
  const [newProjectDomain, setNewProjectDomain] = useState('');
  const [toastMessage, setToastMessage] = useState(null);

  // Projects list initialized to empty array (ready for live backend API data)
  const SEEDED_BUILDER_PROJECTS = [];

  // Helper to load projects scoped to authenticated user
  const loadScopedProjects = () => {
    try {
      const email = (currentUser?.email || '').toLowerCase().trim();
      const name = (currentUser?.name || '').toLowerCase().trim();
      const raw = localStorage.getItem('finreg_projects');
      const local = raw ? JSON.parse(raw) : [];

      if (!email && !name) return local;

      // Scoping: match if project ownerEmail matches currentUser email OR owner name matches
      const userProjects = local.filter((p) => {
        const pEmail = (p.ownerEmail || '').toLowerCase().trim();
        const pOwner = (p.owner || '').toLowerCase().trim();
        const matchesEmail = email && pEmail && pEmail === email;
        const matchesName = name && pOwner && pOwner === name;
        return matchesEmail || matchesName;
      });

      return userProjects.length > 0 ? userProjects : local;
    } catch (e) {
      return [];
    }
  };

  const [allProjects, setAllProjects] = useState(loadScopedProjects);

  // Load user & live projects from backend API on mount
  useEffect(() => {
    let isMounted = true;
    async function loadBackendData() {
      try {
        const liveProjects = await getProjects();
        if (isMounted && Array.isArray(liveProjects) && liveProjects.length > 0) {
          const email = (currentUser?.email || '').toLowerCase().trim();
          const name = (currentUser?.name || '').toLowerCase().trim();
          const scoped = liveProjects.filter(
            (p) =>
              (p.ownerEmail && p.ownerEmail.toLowerCase() === email) ||
              (p.owner && p.owner.toLowerCase() === name)
          );
          if (scoped.length > 0) setAllProjects(scoped);
        }
      } catch (err) {
        console.warn('[DashboardView] API load warning, using local scoped projects:', err);
      }
    }
    loadBackendData();
    return () => {
      isMounted = false;
    };
  }, [currentUser]);

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

  // Handle New Project Creation via POST /projects (DEF-08: Bind creator name to authenticated user)
  const handleCreateProjectSubmit = async (e) => {
    e.preventDefault();
    if (!newProjectName || !newProjectType) return;

    const creatorName = currentUser?.name || 'Project Owner';
    const creatorEmail = (currentUser?.email || '').toLowerCase();

    const payload = {
      name: newProjectName,
      type: newProjectType,
      description: newProjectDescription || 'Newly created regulatory project.',
      jurisdiction: newProjectJurisdiction || 'United Kingdom - FCA',
      owner: creatorName,
      ownerEmail: creatorEmail,
    };

    let createdProject;
    try {
      createdProject = await createProject(payload);
    } catch (err) {
      console.warn('[DashboardView] POST /projects failed, fallback to local state:', err);
      createdProject = {
        id: `PRJ-00${Math.floor(Math.random() * 900) + 100}`,
        ...payload,
        status: 'Draft',
        statusColor: 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700',
        dotColor: 'bg-slate-400',
        lastUpdated: 'Just now',
        owner: creatorName,
        ownerEmail: creatorEmail,
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
      owner: createdProject.owner || creatorName,
      ownerEmail: creatorEmail,
      progress: 0,
      isNew: true,
      description: createdProject.description || payload.description,
      created: createdProject.created || 'Today',
      jurisdiction: createdProject.jurisdiction || payload.jurisdiction,
    };

    setAllProjects([newEntry, ...allProjects]);
    setToastMessage(`Project "${newProjectName}" created successfully!`);

    // Reset Form
    setCreateProjectStep(1);
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

  // Activity Feed Data initialized to empty array (ready for live backend audit stream)
  const activityFeed = [];

  const loadDynamicAdvice = () => {
    try {
      const raw = localStorage.getItem('finreg_advisor_reviews');
      const list = raw ? JSON.parse(raw) : [];
      return Array.isArray(list)
        ? list.filter(
            (r) =>
              r &&
              !r.id?.includes('MOCK') &&
              r.project !== 'ABC Shield' &&
              !r.advisor?.includes('Maya Chen') &&
              !r.requirement?.includes('CDD evidence controls')
          )
        : [];
    } catch (e) {
      return [];
    }
  };
  const dynamicAdviceList = loadDynamicAdvice();
  const pendingReviewsCount = dynamicAdviceList.filter((a) => a.status === 'Pending Review' || a.status === 'Submitted').length;
  const acceptedReviewsCount = dynamicAdviceList.filter((a) => a.status === 'Accepted').length;
  const clarificationReviewsCount = dynamicAdviceList.filter((a) => a.status === 'Needs Clarification').length;

  // Metric Cards Config computed dynamically from live user projects
  const activeCount = allProjects.filter((p) => p.status === 'In Progress').length;
  const metricsData = [
    { id: 'active', label: 'Active projects', val: String(activeCount).padStart(2, '0'), sub: `${allProjects.length} total projects` },
    { id: 'requirements', label: 'Open requirements', val: '00', sub: 'From project rulebooks' },
    { id: 'reviews', label: 'Advisor reviews', val: '00', sub: 'Pending expert sign-off' },
    { id: 'readiness', label: 'Audit readiness', val: '00%', sub: 'Across active projects' },
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

          {/* Notification Bell with Interactive Dropdown (DEF-05) */}
          <div className="relative">
            <button
              type="button"
              onClick={() => {
                setIsNotificationMenuOpen(!isNotificationMenuOpen);
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

            {/* Notifications Dropdown Panel (DEF-05) */}
            {isNotificationMenuOpen && (
              <div className="absolute right-0 mt-3 w-80 sm:w-[350px] rounded-2xl bg-[#16181d] border border-slate-700/80 shadow-2xl overflow-hidden z-50 text-left animate-fadeIn">
                {/* Panel Header */}
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

                {/* Notifications List */}
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
              onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
              className={`flex items-center gap-2.5 p-1.5 rounded-xl border transition-all cursor-pointer ${
                isDarkMode
                  ? 'border-slate-800 hover:border-slate-700 bg-slate-900/60'
                  : 'border-stone-200 hover:border-stone-300 bg-stone-50'
              }`}
            >
              <div className="w-8 h-8 rounded-lg bg-[#7c4a27]/15 dark:bg-amber-500/20 text-[#7c4a27] dark:text-amber-300 font-bold text-xs flex items-center justify-center border border-[#7c4a27]/20">
                {userInitials}
              </div>
              <span className="text-sm font-semibold hidden md:inline-block">{userName}</span>
              <ChevronDown className="w-4 h-4 text-slate-400" />
            </button>

            {/* User Menu Overlay showing Name, Logged-in Email, and Log out option */}
            {isUserMenuOpen && (
              <div className={`absolute right-0 mt-2 w-60 rounded-xl shadow-2xl border overflow-hidden z-50 animate-fadeIn ${
                isDarkMode ? 'bg-[#1a1a1e] border-slate-800 text-slate-200' : 'bg-white border-stone-200 text-slate-800'
              }`}>
                {/* User Info Header: Name & Logged-in Email */}
                <div className="p-4 border-b border-slate-200 dark:border-slate-800 text-left">
                  <p className="font-bold text-sm text-slate-900 dark:text-slate-100">{userName}</p>
                  <p className="text-slate-400 text-xs mt-0.5 font-normal">{userEmail}</p>
                  <div className="mt-2">
                    <span className="inline-block px-2.5 py-0.5 border border-slate-200 dark:border-slate-700 bg-stone-50 dark:bg-slate-800 text-slate-600 dark:text-slate-300 text-[11px] font-mono rounded">
                      {userRoleTitle}
                    </span>
                  </div>
                </div>

                {/* Log out Option */}
                <div className="py-1 text-left">
                  <button
                    type="button"
                    onClick={() => {
                      logoutUser();
                      if (onSignOut) onSignOut();
                    }}
                    className="w-full flex items-center gap-2 px-4 py-2.5 text-xs sm:text-sm font-semibold text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors cursor-pointer"
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
              { name: 'Regulatory Requirements', icon: ShieldCheck },
              { name: 'Advisors / Experts', icon: Users },
              { name: 'Advisor Advice', icon: FileText },
              { name: 'Advice & Decisions', icon: FileText },
              { name: 'AI / RAG Findings', icon: Search },
              { name: 'Readiness', icon: LayoutGrid },
              { name: 'Audit Trail', icon: List },
              { name: 'Tools', icon: Wrench },
              { name: 'Settings', icon: Settings },
            ].map((item) => {
              const Icon = item.icon;
              const isActive =
                activeTab === item.name ||
                (item.name === 'My Projects' && activeTab === 'Project Details') ||
                (item.name === 'Regulatory Requirements' && activeTab === 'Regulatory Support');

              return (
                <button
                  key={item.name}
                  type="button"
                  onClick={() => {
                    setActiveTab(item.name);
                    if (item.name === 'Regulatory Requirements') {
                      setTargetRequirementId(null);
                    }
                  }}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-xs sm:text-sm font-semibold transition-all cursor-pointer ${
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
                  <span className="text-[11px] font-mono font-extrabold tracking-widest text-slate-400 dark:text-slate-500 uppercase block mb-1">
                    {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' }).toUpperCase()}
                  </span>
                  <h1 className={`text-2xl sm:text-3xl font-bold tracking-tight ${
                    isDarkMode ? 'text-slate-100' : 'text-slate-900'
                  }`}>
                    Welcome back, {currentUser?.name ? currentUser.name.split(' ')[0] : 'Builder'}
                  </h1>
                  <p className={`text-xs sm:text-sm mt-1 font-medium ${
                    isDarkMode ? 'text-slate-300' : 'text-slate-500'
                  }`}>
                    Your regulatory delivery workspace is up to date.
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

              {/* ADVISOR ADVICE & LIVE WORKFLOW OVERVIEW SECTION MATCHING media_1791775936383_c278f0e5.png */}
              <div className="space-y-4">
                {/* TOP CARD: ADVISOR ADVICE */}
                <div className="rounded-2xl border border-slate-200 dark:border-slate-800/90 bg-white dark:bg-[#161619] p-6 shadow-sm">
                  <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
                    {/* Left: Eyebrow + Title */}
                    <div className="min-w-[260px]">
                      <div className="text-[11px] font-mono tracking-widest text-slate-400 uppercase font-semibold mb-1">
                        ADVISOR ADVICE
                      </div>
                      <h2 className="text-lg sm:text-xl font-bold text-slate-900 dark:text-white">
                        {currentProject?.name ? `Expert reviews for ${currentProject.name}` : 'Advisor reviews overview'}
                      </h2>
                    </div>

                    {/* Center: 3 Metrics with vertical divider lines */}
                    <div className="grid grid-cols-3 gap-6 sm:gap-8 flex-1 max-w-xl">
                      <div className="lg:border-l lg:border-slate-800/80 lg:pl-6">
                        <div className="text-[10px] font-mono tracking-wider text-slate-400 uppercase font-semibold mb-1">
                          PENDING REVIEWS
                        </div>
                        <div className="text-xl sm:text-2xl font-bold text-[#e6a13d] dark:text-[#f59e0b]">
                          {pendingReviewsCount}
                        </div>
                      </div>

                      <div className="border-l border-slate-200 dark:border-slate-800/80 pl-6">
                        <div className="text-[10px] font-mono tracking-wider text-slate-400 uppercase font-semibold mb-1">
                          ACCEPTED
                        </div>
                        <div className="text-xl sm:text-2xl font-bold text-[#e6a13d] dark:text-[#f59e0b]">
                          {acceptedReviewsCount}
                        </div>
                      </div>

                      <div className="border-l border-slate-200 dark:border-slate-800/80 pl-6">
                        <div className="text-[10px] font-mono tracking-wider text-slate-400 uppercase font-semibold mb-1">
                          NEEDS CLARIFICATION
                        </div>
                        <div className="text-xl sm:text-2xl font-bold text-[#e6a13d] dark:text-[#f59e0b]">
                          {clarificationReviewsCount}
                        </div>
                      </div>
                    </div>

                    {/* Right: Action Button */}
                    <div className="shrink-0">
                      <button
                        type="button"
                        onClick={() => setActiveTab('Advisor Advice')}
                        className="px-4 py-2.5 rounded-md border border-slate-700/80 bg-[#1e2025] hover:bg-slate-800 text-slate-200 hover:text-white text-xs sm:text-sm font-semibold transition-colors cursor-pointer inline-flex items-center gap-1.5 shadow-sm"
                      >
                        <span>View advisor advice</span>
                        <span>→</span>
                      </button>
                    </div>
                  </div>
                </div>

                {/* BOTTOM 2 CARDS: AI / RAG FINDINGS and READINESS SUMMARY */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {/* Card 1: AI / RAG Findings */}
                  <div className="rounded-2xl border border-slate-200 dark:border-slate-800/90 bg-white dark:bg-[#161619] p-6 shadow-sm flex flex-col justify-between">
                    <div>
                      <div className="text-[11px] font-mono tracking-widest text-slate-400 uppercase font-semibold mb-1.5">
                        AI / RAG FINDINGS
                      </div>
                      <h3 className="text-lg sm:text-xl font-bold text-slate-900 dark:text-white mb-2">
                        {currentProject ? 'No open evidence conflicts' : 'No findings requiring human review'}
                      </h3>
                      <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 font-normal leading-relaxed mb-6">
                        {currentProject ? `AI retrieval-augmented findings for ${currentProject.name} will appear once documents are linked.` : 'Connect project requirements to generate RAG findings.'}
                      </p>
                    </div>
                    <div>
                      <button
                        type="button"
                        onClick={() => setActiveTab('AI / RAG Findings')}
                        className="px-4 py-2.5 rounded-md border border-slate-700/80 bg-[#1e2025] hover:bg-slate-800 text-slate-200 hover:text-white text-xs sm:text-sm font-semibold transition-colors cursor-pointer inline-flex items-center gap-1.5 shadow-sm"
                      >
                        <span>Review AI findings</span>
                        <span>→</span>
                      </button>
                    </div>
                  </div>

                  {/* Card 2: Readiness Summary */}
                  <div className="rounded-2xl border border-slate-200 dark:border-slate-800/90 bg-white dark:bg-[#161619] p-6 shadow-sm flex flex-col justify-between">
                    <div>
                      <div className="text-[11px] font-mono tracking-widest text-slate-400 uppercase font-semibold mb-1.5">
                        READINESS SUMMARY
                      </div>
                      <h3 className="text-lg sm:text-xl font-bold text-slate-900 dark:text-white mb-2">
                        {currentProject ? `${currentProject.progress || 0}% progressing` : '0% progressing'}
                      </h3>
                      <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 font-normal leading-relaxed mb-6">
                        {currentProject ? 'Readiness updates as shared advice statuses change.' : 'No readiness items recorded. Connect requirements to begin tracking.'}
                      </p>
                    </div>
                    <div>
                      <button
                        type="button"
                        onClick={() => setActiveTab('Readiness')}
                        className="px-4 py-2.5 rounded-md border border-slate-700/80 bg-[#1e2025] hover:bg-slate-800 text-slate-200 hover:text-white text-xs sm:text-sm font-semibold transition-colors cursor-pointer inline-flex items-center gap-1.5 shadow-sm"
                      >
                        <span>Open readiness</span>
                        <span>→</span>
                      </button>
                    </div>
                  </div>
                </div>
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
                  <div>
                    <h2 className={`text-base sm:text-lg font-bold tracking-tight ${
                      isDarkMode ? 'text-slate-100' : 'text-slate-900'
                    }`}>
                      My Projects
                    </h2>
                    <p className="text-xs text-slate-400 font-normal mt-0.5">
                      Recently updated regulatory initiatives
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      setActiveTab('My Projects');
                    }}
                    className="px-4 py-2 rounded-xl border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-200 text-xs font-bold transition-colors cursor-pointer"
                  >
                    View all projects
                  </button>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs sm:text-sm border-collapse">
                    <thead>
                      <tr className={`border-b text-[11px] font-extrabold uppercase tracking-wider ${
                        isDarkMode
                          ? 'border-slate-800 bg-slate-900/80 text-slate-400'
                          : 'border-stone-100 bg-stone-50/80 text-stone-500'
                      }`}>
                        <th className="py-3.5 px-5">PROJECT</th>
                        <th className="py-3.5 px-5">TYPE</th>
                        <th className="py-3.5 px-5">STATUS</th>
                        <th className="py-3.5 px-5">OWNER</th>
                        <th className="py-3.5 px-5">LAST UPDATED</th>
                        <th className="py-3.5 px-5 text-right"></th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-medium">
                      {allProjects.length === 0 ? (
                        <tr>
                          <td colSpan={6} className="py-12 px-5 text-center">
                            <Folder className="w-10 h-10 text-slate-500 mx-auto mb-2.5 stroke-[1.5]" />
                            <p className="text-sm font-bold text-slate-200">No projects created yet</p>
                            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                              Launch your first regulatory compliance project by clicking "Create Project" in Quick Actions below.
                            </p>
                          </td>
                        </tr>
                      ) : (
                        allProjects.slice(0, 4).map((project) => (
                          <tr
                            key={project.id}
                            className={`transition-colors ${
                              isDarkMode ? 'hover:bg-slate-800/40' : 'hover:bg-stone-50/90'
                            }`}
                          >
                            <td className="py-4 px-5">
                              <div className={`font-bold text-sm ${isDarkMode ? 'text-slate-100' : 'text-slate-900'}`}>
                                {project.name}
                              </div>
                              <div className="text-[11px] font-mono text-slate-500 mt-0.5">
                                {project.id}
                              </div>
                            </td>
                            <td className={`py-4 px-5 font-medium text-xs sm:text-sm ${
                              isDarkMode ? 'text-slate-300' : 'text-slate-600'
                            }`}>
                              {project.type}
                            </td>
                            <td className="py-4 px-5">
                              <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border ${project.statusColor}`}>
                                <span className={`w-1.5 h-1.5 rounded-full ${project.dotColor}`} />
                                {project.status}
                              </span>
                            </td>
                            <td className={`py-4 px-5 font-medium text-xs sm:text-sm ${
                              isDarkMode ? 'text-slate-300' : 'text-slate-600'
                            }`}>
                              {project.owner || currentUser?.name || 'Project Owner'}
                            </td>
                            <td className={`py-4 px-5 font-medium text-xs sm:text-sm ${
                              isDarkMode ? 'text-slate-300' : 'text-slate-600'
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
                                isDarkMode ? 'text-slate-300 hover:text-white' : 'text-[#7c4a27]'
                              }`}
                            >
                              <span>Open</span>
                              <ArrowRight className="w-3.5 h-3.5" />
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
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
                    {activityFeed.length === 0 ? (
                      <div className="p-8 text-center text-xs text-slate-500 dark:text-slate-400">
                        No recent activity recorded yet. Live audit stream events will appear here once projects or requirements are updated.
                      </div>
                    ) : (
                      activityFeed.map((item) => (
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
                      ))
                    )}
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
                        {filteredProjects.length === 0 ? (
                          <tr>
                            <td colSpan={7} className="py-12 px-5 text-center">
                              <FolderKanban className="w-10 h-10 text-slate-500 mx-auto mb-3 stroke-[1.5]" />
                              <p className="text-sm font-bold text-slate-200">No projects found</p>
                              <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                                {searchQuery || statusFilter !== 'All Statuses' || typeFilter !== 'All Types'
                                  ? 'No projects match your current filter criteria.'
                                  : 'No projects created yet. Launch your first compliance project to get started.'}
                              </p>
                              {(!searchQuery && statusFilter === 'All Statuses' && typeFilter === 'All Types') && (
                                <button
                                  type="button"
                                  onClick={() => setActiveTab('Create Project')}
                                  className="mt-4 px-4 py-2 rounded-xl bg-[#7c4a27] hover:bg-[#96562c] text-white text-xs font-bold transition-colors cursor-pointer"
                                >
                                  Create Project
                                </button>
                              )}
                            </td>
                          </tr>
                        ) : (
                          filteredProjects.map((project) => (
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
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                ) : filteredProjects.length === 0 ? (
                  <div className="py-16 px-5 text-center">
                    <FolderKanban className="w-10 h-10 text-slate-500 mx-auto mb-3 stroke-[1.5]" />
                    <p className="text-sm font-bold text-slate-200">No projects found</p>
                    <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                      {searchQuery || statusFilter !== 'All Statuses' || typeFilter !== 'All Types'
                        ? 'No projects match your current filter criteria.'
                        : 'No projects created yet. Launch your first compliance project to get started.'}
                    </p>
                    {(!searchQuery && statusFilter === 'All Statuses' && typeFilter === 'All Types') && (
                      <button
                        type="button"
                        onClick={() => setActiveTab('Create Project')}
                        className="mt-4 px-4 py-2 rounded-xl bg-[#7c4a27] hover:bg-[#96562c] text-white text-xs font-bold transition-colors cursor-pointer"
                      >
                        Create Project
                      </button>
                    )}
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

          {/* TAB 3: CREATE PROJECT VIEW (Matching uploaded image media_1791737402091_0e2c6bea.png) */}
          {activeTab === 'Create Project' && (
            <div className="space-y-6 animate-fadeIn max-w-5xl text-left">
              {/* Header Title & Subtitle */}
              <div className="space-y-1.5">
                <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-100">
                  Create Project
                </h1>
                <p className="text-xs sm:text-sm text-slate-400 font-normal">
                  Add the essentials now. Optional profile information and documents can be completed later.
                </p>
              </div>

              {/* 3-Step Wizard Navigation Bar matching media_1791737402091_0e2c6bea.png */}
              <div className="rounded-xl border border-slate-800 bg-[#161619] grid grid-cols-1 sm:grid-cols-3 divide-y sm:divide-y-0 sm:divide-x divide-slate-800 overflow-hidden shadow-sm">
                {/* Step 1: Project Information */}
                <button
                  type="button"
                  onClick={() => setCreateProjectStep(1)}
                  className={`p-3.5 sm:px-6 flex items-center justify-center sm:justify-start gap-3 transition-colors cursor-pointer ${
                    createProjectStep === 1 ? 'bg-amber-500/5' : 'hover:bg-slate-800/30'
                  }`}
                >
                  <div className={`w-6 h-6 rounded-full border flex items-center justify-center text-xs font-bold shrink-0 ${
                    createProjectStep === 1
                      ? 'border-amber-500/90 text-amber-400 bg-amber-500/10'
                      : 'border-slate-700 text-slate-400'
                  }`}>
                    1
                  </div>
                  <span className={`text-xs sm:text-sm font-bold ${
                    createProjectStep === 1 ? 'text-slate-100' : 'text-slate-400'
                  }`}>
                    Project Information
                  </span>
                </button>

                {/* Step 2: Project Profile */}
                <button
                  type="button"
                  onClick={() => setCreateProjectStep(2)}
                  className={`p-3.5 sm:px-6 flex items-center justify-center sm:justify-start gap-3 transition-colors cursor-pointer ${
                    createProjectStep === 2 ? 'bg-amber-500/5' : 'hover:bg-slate-800/30'
                  }`}
                >
                  <div className={`w-6 h-6 rounded-full border flex items-center justify-center text-xs font-bold shrink-0 ${
                    createProjectStep === 2
                      ? 'border-amber-500/90 text-amber-400 bg-amber-500/10'
                      : 'border-slate-700 text-slate-400'
                  }`}>
                    2
                  </div>
                  <span className={`text-xs sm:text-sm font-semibold ${
                    createProjectStep === 2 ? 'text-slate-100' : 'text-slate-400'
                  }`}>
                    Project Profile
                  </span>
                </button>

                {/* Step 3: Review */}
                <button
                  type="button"
                  onClick={() => setCreateProjectStep(3)}
                  className={`p-3.5 sm:px-6 flex items-center justify-center sm:justify-start gap-3 transition-colors cursor-pointer ${
                    createProjectStep === 3 ? 'bg-amber-500/5' : 'hover:bg-slate-800/30'
                  }`}
                >
                  <div className={`w-6 h-6 rounded-full border flex items-center justify-center text-xs font-bold shrink-0 ${
                    createProjectStep === 3
                      ? 'border-amber-500/90 text-amber-400 bg-amber-500/10'
                      : 'border-slate-700 text-slate-400'
                  }`}>
                    3
                  </div>
                  <span className={`text-xs sm:text-sm font-semibold ${
                    createProjectStep === 3 ? 'text-slate-100' : 'text-slate-400'
                  }`}>
                    Review
                  </span>
                </button>
              </div>

              {/* STEP 1: PROJECT INFORMATION FORM (Direct match with media_1791737402091_0e2c6bea.png) */}
              {createProjectStep === 1 && (
                <div className="rounded-2xl border border-slate-800/90 bg-[#161619] p-6 sm:p-8 space-y-6 text-left shadow-xl animate-fadeIn">
                  <h2 className="text-lg sm:text-xl font-bold text-slate-100">
                    Project Information
                  </h2>

                  <form onSubmit={(e) => { e.preventDefault(); setCreateProjectStep(2); }} className="space-y-6">
                    {/* Row 1: Project Name & Project Type */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-2">
                        <label className="block text-xs font-semibold text-slate-200">
                          Project Name <span className="text-amber-400">*</span>
                        </label>
                        <input
                          type="text"
                          required
                          value={newProjectName}
                          onChange={(e) => setNewProjectName(e.target.value)}
                          placeholder="e.g. ABC Shield"
                          className="w-full px-4 py-3 text-sm rounded-xl border border-slate-800 bg-[#121214] text-slate-100 placeholder-slate-500 focus:outline-none focus:border-[#96562c] focus:ring-2 focus:ring-[#96562c]/20 transition-all"
                        />
                      </div>

                      <div className="space-y-2">
                        <label className="block text-xs font-semibold text-slate-200">
                          Project Type <span className="text-amber-400">*</span>
                        </label>
                        <select
                          required
                          value={newProjectType}
                          onChange={(e) => setNewProjectType(e.target.value)}
                          className="w-full px-4 py-3 text-sm rounded-xl border border-slate-800 bg-[#121214] text-slate-200 focus:outline-none focus:border-[#96562c] cursor-pointer transition-all"
                        >
                          <option value="">Select project type</option>
                          <option value="AML/CTF">AML/CTF (Anti-Money Laundering)</option>
                          <option value="KYC/CDD">KYC/CDD (Know Your Customer)</option>
                          <option value="Regulatory Reporting">Regulatory Reporting</option>
                          <option value="Data Governance">Data Governance</option>
                          <option value="Consumer Duty / Conduct">Consumer Duty / Conduct</option>
                        </select>
                      </div>
                    </div>

                    {/* Row 2: Jurisdiction */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-2">
                        <label className="block text-xs font-semibold text-slate-200">
                          Jurisdiction <span className="text-amber-400">*</span>
                        </label>
                        <select
                          required
                          value={newProjectJurisdiction}
                          onChange={(e) => setNewProjectJurisdiction(e.target.value)}
                          className="w-full px-4 py-3 text-sm rounded-xl border border-slate-800 bg-[#121214] text-slate-200 focus:outline-none focus:border-[#96562c] cursor-pointer transition-all"
                        >
                          <option value="">Select jurisdiction</option>
                          <option value="United Kingdom">United Kingdom</option>
                          <option value="European Union">European Union</option>
                          <option value="United States">United States</option>
                          <option value="Global / International">Global / International</option>
                        </select>
                      </div>
                    </div>

                    {/* Row 3: Description */}
                    <div className="space-y-2">
                      <label className="block text-xs font-semibold text-slate-200">
                        Description <span className="text-amber-400">*</span>
                      </label>
                      <textarea
                        rows={5}
                        required
                        value={newProjectDescription}
                        onChange={(e) => setNewProjectDescription(e.target.value)}
                        placeholder="Briefly describe the project objective"
                        className="w-full px-4 py-3 text-sm rounded-xl border border-slate-800 bg-[#121214] text-slate-100 placeholder-slate-500 focus:outline-none focus:border-[#96562c] focus:ring-2 focus:ring-[#96562c]/20 transition-all leading-relaxed"
                      />
                    </div>

                    {/* Actions */}
                    <div className="flex items-center justify-between pt-4 border-t border-slate-800/80">
                      <button
                        type="button"
                        onClick={() => setActiveTab('Dashboard')}
                        className="px-5 py-2.5 rounded-xl border border-slate-800 hover:border-slate-700 bg-slate-900/60 text-slate-400 hover:text-slate-200 font-medium text-xs sm:text-sm cursor-pointer transition-colors"
                      >
                        Cancel
                      </button>

                      <div className="flex items-center gap-3">
                        <button
                          type="button"
                          onClick={() => {
                            if (!newProjectName.trim()) {
                              setToastMessage('Please enter a Project Name');
                              setTimeout(() => setToastMessage(null), 2500);
                              return;
                            }
                            if (!newProjectType) {
                              setToastMessage('Please select a Project Type');
                              setTimeout(() => setToastMessage(null), 2500);
                              return;
                            }
                            setCreateProjectStep(2);
                          }}
                          className="px-6 py-2.5 rounded-xl bg-[#e6a13d] hover:bg-[#d8932f] text-slate-950 font-bold text-xs sm:text-sm shadow-md flex items-center gap-2 cursor-pointer transition-colors"
                        >
                          <span>Next: Project Profile</span>
                          <ArrowRight className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </form>
                </div>
              )}

              {/* STEP 2: PROJECT PROFILE */}
              {createProjectStep === 2 && (
                <div className="rounded-2xl border border-slate-800/90 bg-[#161619] p-6 sm:p-8 space-y-6 text-left shadow-xl animate-fadeIn">
                  <h2 className="text-lg sm:text-xl font-bold text-slate-100">
                    Project Profile
                  </h2>
                  <p className="text-xs text-slate-400">
                    Optional governance and scope parameters to align your compliance workflow.
                  </p>

                  <div className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-2">
                        <label className="block text-xs font-semibold text-slate-200">
                          Regulatory Framework / Standard
                        </label>
                        <input
                          type="text"
                          value={newProjectDomain}
                          onChange={(e) => setNewProjectDomain(e.target.value)}
                          placeholder="e.g. FCA SYSC 6.3, UK MLR 2017"
                          className="w-full px-4 py-3 text-sm rounded-xl border border-slate-800 bg-[#121214] text-slate-100 placeholder-slate-500 focus:outline-none focus:border-[#96562c] transition-all"
                        />
                      </div>

                      <div className="space-y-2">
                        <label className="block text-xs font-semibold text-slate-200">
                          Target Delivery Date
                        </label>
                        <input
                          type="date"
                          defaultValue="2026-11-30"
                          className="w-full px-4 py-3 text-sm rounded-xl border border-slate-800 bg-[#121214] text-slate-100 focus:outline-none focus:border-[#96562c] transition-all"
                        />
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-4 border-t border-slate-800/80">
                      <button
                        type="button"
                        onClick={() => setCreateProjectStep(1)}
                        className="px-5 py-2.5 rounded-xl border border-slate-800 hover:border-slate-700 bg-slate-900/60 text-slate-400 hover:text-slate-200 font-medium text-xs sm:text-sm cursor-pointer transition-colors"
                      >
                        ← Back
                      </button>

                      <button
                        type="button"
                        onClick={() => setCreateProjectStep(3)}
                        className="px-6 py-2.5 rounded-xl bg-[#e6a13d] hover:bg-[#d8932f] text-slate-950 font-bold text-xs sm:text-sm shadow-md flex items-center gap-2 cursor-pointer transition-colors"
                      >
                        <span>Next: Review</span>
                        <ArrowRight className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* STEP 3: REVIEW & SUBMIT */}
              {createProjectStep === 3 && (
                <div className="rounded-2xl border border-slate-800/90 bg-[#161619] p-6 sm:p-8 space-y-6 text-left shadow-xl animate-fadeIn">
                  <h2 className="text-lg sm:text-xl font-bold text-slate-100">
                    Review Project Information
                  </h2>
                  <p className="text-xs text-slate-400">
                    Verify project parameters before adding to your delivery workspace.
                  </p>

                  <div className="divide-y divide-slate-800/80 rounded-xl border border-slate-800/80 bg-[#121214] p-5 text-sm space-y-3.5">
                    <div className="flex items-center justify-between pt-1">
                      <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Project Name</span>
                      <span className="font-bold text-slate-100">{newProjectName || 'Untitled Project'}</span>
                    </div>
                    <div className="flex items-center justify-between pt-3.5">
                      <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Project Type</span>
                      <span className="font-semibold text-amber-400">{newProjectType || 'AML/CTF'}</span>
                    </div>
                    <div className="flex items-center justify-between pt-3.5">
                      <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Jurisdiction</span>
                      <span className="font-semibold text-slate-200">{newProjectJurisdiction || 'United Kingdom'}</span>
                    </div>
                    {newProjectDomain && (
                      <div className="flex items-center justify-between pt-3.5">
                        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Regulatory Framework</span>
                        <span className="font-semibold text-slate-200">{newProjectDomain}</span>
                      </div>
                    )}
                    <div className="pt-3.5">
                      <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Description</span>
                      <p className="text-slate-300 text-xs sm:text-sm leading-relaxed">{newProjectDescription || 'None provided.'}</p>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-4 border-t border-slate-800/80">
                    <button
                      type="button"
                      onClick={() => setCreateProjectStep(2)}
                      className="px-5 py-2.5 rounded-xl border border-slate-800 hover:border-slate-700 bg-slate-900/60 text-slate-400 hover:text-slate-200 font-medium text-xs sm:text-sm cursor-pointer transition-colors"
                    >
                      ← Back to Profile
                    </button>

                    <button
                      type="button"
                      onClick={handleCreateProjectSubmit}
                      className="px-7 py-3 rounded-xl bg-[#e6a13d] hover:bg-[#d8932f] text-slate-950 font-bold text-xs sm:text-sm shadow-md flex items-center gap-2 cursor-pointer transition-colors"
                    >
                      <Plus className="w-4 h-4 stroke-[3]" />
                      <span>Create Project</span>
                    </button>
                  </div>
                </div>
              )}
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
                        setProjectSubTab('Workflow');
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

                      {(() => {
                        // Dynamic progress calculation based on project state (DEF-10)
                        const isDraft = !currentProject || currentProject.status === 'Draft' || currentProject.isNew;
                        const isCompleted = currentProject?.status === 'Completed';
                        const isReview = currentProject?.status === 'Under Review';

                        let checklistItems = [];
                        if (isCompleted) {
                          checklistItems = [
                            { label: 'Requirements defined', done: true },
                            { label: 'Workflow configured', done: true },
                            { label: 'Advisor review', done: true },
                            { label: 'Compliance sign-off', done: true },
                            { label: 'Final submission', done: true },
                          ];
                        } else if (isDraft) {
                          checklistItems = [
                            { label: 'Requirements defined', done: false },
                            { label: 'Workflow configured', done: false },
                            { label: 'Advisor review', done: false },
                            { label: 'Compliance sign-off', done: false },
                            { label: 'Final submission', done: false },
                          ];
                        } else if (isReview) {
                          checklistItems = [
                            { label: 'Requirements defined', done: true },
                            { label: 'Workflow configured', done: true },
                            { label: 'Advisor review', done: false },
                            { label: 'Compliance sign-off', done: false },
                            { label: 'Final submission', done: false },
                          ];
                        } else {
                          // Default for PRJ-001 In Progress fixture
                          checklistItems = [
                            { label: 'Requirements defined', done: true },
                            { label: 'Workflow configured', done: true },
                            { label: 'Advisor review', done: true },
                            { label: 'Compliance sign-off', done: false },
                            { label: 'Final submission', done: false },
                          ];
                        }

                        const doneCount = checklistItems.filter((item) => item.done).length;
                        const progressPct = currentProject?.progress !== undefined
                          ? currentProject.progress
                          : Math.round((doneCount / checklistItems.length) * 100);

                        return (
                          <>
                            {/* Progress bar */}
                            <div className="space-y-2 mb-5">
                              <div className="flex items-center justify-between text-xs font-bold">
                                <span className="text-slate-600 dark:text-slate-300">Overall progress</span>
                                <span className="text-[#7c4a27] dark:text-amber-400 text-sm">{progressPct}%</span>
                              </div>
                              <div className="w-full h-2 bg-stone-100 dark:bg-slate-800 rounded-full overflow-hidden">
                                <div
                                  className="h-full bg-[#7c4a27] dark:bg-amber-500 rounded-full transition-all duration-500"
                                  style={{ width: `${progressPct}%` }}
                                />
                              </div>
                            </div>

                            {/* Checklist */}
                            <div className="space-y-2.5 text-xs sm:text-sm font-medium">
                              {checklistItems.map((item, idx) => (
                                <div
                                  key={idx}
                                  className={`flex items-center gap-2 ${
                                    item.done
                                      ? 'text-emerald-600 dark:text-emerald-400 line-through'
                                      : 'text-slate-500 dark:text-slate-300'
                                  }`}
                                >
                                  {item.done ? (
                                    <CheckSquare className="w-4 h-4 shrink-0 text-emerald-600 stroke-[2.5]" />
                                  ) : (
                                    <Square className="w-4 h-4 shrink-0 stroke-[2]" />
                                  )}
                                  <span>{item.label}</span>
                                </div>
                              ))}
                            </div>
                          </>
                        );
                      })()}
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
                        {/* Dynamic Project Owner */}
                        <div className="pt-2 flex items-center justify-between">
                          <div className="flex items-center gap-2.5">
                            <div className="w-7 h-7 rounded-lg bg-[#7c4a27] text-white font-bold text-xs flex items-center justify-center">
                              {(selectedProject?.owner || currentUser?.name || 'Owner')
                                .split(' ')
                                .filter(Boolean)
                                .map((n) => n[0])
                                .join('')
                                .slice(0, 2)
                                .toUpperCase()}
                            </div>
                            <span className="font-bold text-xs sm:text-sm text-slate-900 dark:text-slate-100">
                              {selectedProject?.owner || currentUser?.name || 'Project Owner'}
                            </span>
                          </div>
                          <span className="text-[11px] font-mono font-semibold px-2 py-0.5 rounded bg-amber-50 text-[#7c4a27] border border-amber-200/60 dark:bg-amber-950/40 dark:text-amber-300">
                            Owner
                          </span>
                        </div>

                        {/* Dynamic Assigned Advisors */}
                        {(() => {
                          let advisors = [];
                          try {
                            const raw = localStorage.getItem('finreg_advisor_assignments');
                            const assignments = raw ? JSON.parse(raw) : [];
                            advisors = assignments.filter(
                              (a) =>
                                a.projectId === selectedProject?.id ||
                                (selectedProject?.name && a.projectName === selectedProject?.name)
                            );
                          } catch (e) {
                            advisors = [];
                          }

                          if (advisors.length === 0) {
                            return (
                              <div className="pt-3 text-xs text-slate-400 dark:text-slate-400 italic">
                                No advisors assigned yet. Invite advisors from the Advisors &amp; Experts tab.
                              </div>
                            );
                          }

                          return advisors.map((adv, idx) => {
                            const advName = adv.advisorName || adv.name || `Advisor ${idx + 1}`;
                            const advInitials = advName
                              .split(' ')
                              .filter(Boolean)
                              .map((n) => n[0])
                              .join('')
                              .slice(0, 2)
                              .toUpperCase();
                            const colorBg = idx % 2 === 0 ? 'bg-[#96562c]' : 'bg-slate-700';

                            return (
                              <div key={adv.id || idx} className="pt-3 flex items-center justify-between">
                                <div className="flex items-center gap-2.5">
                                  <div className={`w-7 h-7 rounded-lg ${colorBg} text-white font-bold text-xs flex items-center justify-center`}>
                                    {advInitials}
                                  </div>
                                  <span className="font-bold text-xs sm:text-sm text-slate-900 dark:text-slate-100">
                                    {advName}
                                  </span>
                                </div>
                                <span className="text-[11px] font-mono text-slate-500 dark:text-slate-300 font-medium">
                                  {adv.roleTag || adv.advisorRole || `Advisor ${idx + 1}`}
                                </span>
                              </div>
                            );
                          });
                        })()}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Sub-Tab 2: WORKFLOW TAB CONTENT (Matching media_1791212953490.png) */}
              {projectSubTab === 'Workflow' && (
                <div className="rounded-2xl border border-slate-800 bg-[#161619] p-6 sm:p-8 space-y-6 shadow-lg animate-fadeIn text-left pt-4">
                  <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-100 mb-6">
                    Workflow
                  </h2>

                  <div className="divide-y divide-slate-800/80">
                    {/* Step 01 */}
                    <div className="py-4 sm:py-5 flex items-center justify-between gap-4">
                      <div className="flex items-center gap-4 sm:gap-6">
                        <span className="text-amber-400 font-mono font-bold text-sm sm:text-base w-8 shrink-0">
                          01
                        </span>
                        <span className="font-bold text-slate-100 text-sm sm:text-base">
                          Scope &amp; risk assessment
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => setToastMessage('Opening Scope & risk assessment workflow step...')}
                        className="text-slate-400 hover:text-slate-200 text-xs sm:text-sm font-semibold flex items-center gap-1.5 cursor-pointer transition-colors"
                      >
                        <span>View</span>
                        <ArrowRight className="w-4 h-4" />
                      </button>
                    </div>

                    {/* Step 02 */}
                    <div className="py-4 sm:py-5 flex items-center justify-between gap-4">
                      <div className="flex items-center gap-4 sm:gap-6">
                        <span className="text-amber-400 font-mono font-bold text-sm sm:text-base w-8 shrink-0">
                          02
                        </span>
                        <span className="font-bold text-slate-100 text-sm sm:text-base">
                          Control design
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => setToastMessage('Opening Control design workflow step...')}
                        className="text-slate-400 hover:text-slate-200 text-xs sm:text-sm font-semibold flex items-center gap-1.5 cursor-pointer transition-colors"
                      >
                        <span>View</span>
                        <ArrowRight className="w-4 h-4" />
                      </button>
                    </div>

                    {/* Step 03 */}
                    <div className="py-4 sm:py-5 flex items-center justify-between gap-4">
                      <div className="flex items-center gap-4 sm:gap-6">
                        <span className="text-amber-400 font-mono font-bold text-sm sm:text-base w-8 shrink-0">
                          03
                        </span>
                        <span className="font-bold text-slate-100 text-sm sm:text-base">
                          Advisor validation
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => setToastMessage('Opening Advisor validation workflow step...')}
                        className="text-slate-400 hover:text-slate-200 text-xs sm:text-sm font-semibold flex items-center gap-1.5 cursor-pointer transition-colors"
                      >
                        <span>View</span>
                        <ArrowRight className="w-4 h-4" />
                      </button>
                    </div>

                    {/* Step 04 */}
                    <div className="py-4 sm:py-5 flex items-center justify-between gap-4">
                      <div className="flex items-center gap-4 sm:gap-6">
                        <span className="text-amber-400 font-mono font-bold text-sm sm:text-base w-8 shrink-0">
                          04
                        </span>
                        <span className="font-bold text-slate-100 text-sm sm:text-base">
                          Approval &amp; implementation
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => setToastMessage('Opening Approval & implementation workflow step...')}
                        className="text-slate-400 hover:text-slate-200 text-xs sm:text-sm font-semibold flex items-center gap-1.5 cursor-pointer transition-colors"
                      >
                        <span>View</span>
                        <ArrowRight className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Sub-Tab 3: DOCUMENTS TAB CONTENT (Matching media_1791213224180.png) */}
              {projectSubTab === 'Documents' && (
                <div className="rounded-2xl border border-slate-800 bg-[#161619] p-6 sm:p-8 space-y-6 shadow-lg animate-fadeIn text-left pt-4">
                  <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-100 mb-6">
                    Documents
                  </h2>

                  <div className="divide-y divide-slate-800/80">
                    {Array.isArray(currentProject?.documents) && currentProject.documents.length > 0 ? (
                      currentProject.documents.map((doc, idx) => (
                        <div key={idx} className="py-4 sm:py-5 flex items-center justify-between gap-4">
                          <div className="flex items-center gap-4 sm:gap-6">
                            <span className="text-amber-400 font-mono font-extrabold text-[11px] sm:text-xs uppercase tracking-wider w-20 sm:w-24 shrink-0">
                              {doc.type || 'DOCUMENT'}
                            </span>
                            <span className="font-bold text-slate-100 text-sm sm:text-base">
                              {doc.name || doc.title}
                            </span>
                          </div>
                          <button
                            type="button"
                            onClick={() => setToastMessage(`Opening ${doc.name || doc.title}...`)}
                            className="text-slate-400 hover:text-slate-200 text-xs sm:text-sm font-semibold flex items-center gap-1.5 cursor-pointer transition-colors"
                          >
                            <span>View</span>
                            <ArrowRight className="w-4 h-4" />
                          </button>
                        </div>
                      ))
                    ) : (
                      <div className="py-8 text-center text-slate-500 text-sm">
                        No documents uploaded for this project yet. Uploaded policies, evidence matrices, and source files will appear here.
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Sub-Tab 4: AUDIT TRAIL TAB CONTENT (Matching media_1791213504450.png) */}
              {projectSubTab === 'Audit Trail' && (
                <div className="rounded-2xl border border-slate-800 bg-[#161619] p-6 sm:p-8 space-y-6 shadow-lg animate-fadeIn text-left pt-4">
                  <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-100 mb-6">
                    Audit Trail
                  </h2>

                  <div className="divide-y divide-slate-800/80">
                    {Array.isArray(currentProject?.auditEvents) && currentProject.auditEvents.length > 0 ? (
                      currentProject.auditEvents.map((evt, idx) => (
                        <div key={idx} className="py-4 sm:py-5 flex items-center justify-between gap-4">
                          <div className="flex items-center gap-4 sm:gap-6">
                            <span className="text-amber-400 font-mono font-extrabold text-[11px] sm:text-xs uppercase tracking-wider w-20 sm:w-24 shrink-0">
                              {evt.date || 'LOG'}
                            </span>
                            <span className="font-bold text-slate-100 text-sm sm:text-base">
                              {evt.action || evt.text}
                            </span>
                          </div>
                          <button
                            type="button"
                            onClick={() => setToastMessage('Viewing audit event details...')}
                            className="text-slate-400 hover:text-slate-200 text-xs sm:text-sm font-semibold flex items-center gap-1.5 cursor-pointer transition-colors"
                          >
                            <span>View</span>
                            <ArrowRight className="w-4 h-4" />
                          </button>
                        </div>
                      ))
                    ) : (
                      <div className="py-8 text-center text-slate-500 text-sm">
                        No audit trail events recorded for this project yet. Actions and validations will be recorded here automatically.
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB: ADVISORS / EXPERTS VIEW */}
          {activeTab === 'Advisors / Experts' && (
            <AdvisorsExpertsView isDarkMode={isDarkMode} availableProjects={allProjects} />
          )}

          {/* TAB: ADVISOR ADVICE VIEW (Matching uploaded image media_1791737929366_a3b12230.png) */}
          {activeTab === 'Advisor Advice' && (
            <AdvisorAdviceView isDarkMode={isDarkMode} />
          )}

          {/* TAB: REGULATORY REQUIREMENTS / REGULATORY SUPPORT VIEW */}
          {(activeTab === 'Regulatory Requirements' || activeTab === 'Regulatory Support') && (
            <RegulatorySupportView isDarkMode={isDarkMode} initialRequirementId={targetRequirementId} />
          )}

          {/* TAB: ADVICE & DECISIONS VIEW (Matching media_1791738876275_cf9f871c.png) */}
          {activeTab === 'Advice & Decisions' && (
            <AdviceDecisionsView isDarkMode={isDarkMode} />
          )}

          {/* TAB: AI / RAG FINDINGS VIEW (Matching uploaded images) */}
          {activeTab === 'AI / RAG Findings' && (
            <AiRagFindingsView isDarkMode={isDarkMode} />
          )}

          {/* TAB: READINESS VIEW (Matching uploaded images media_1791739750674_a1d6ca4d.png and media_1791739798112_b0256e69.png) */}
          {activeTab === 'Readiness' && (
            <ReadinessView
              isDarkMode={isDarkMode}
              onOpenRelatedItem={(item) => {
                const reqId = (item && item.reqId) || (item && item.code && item.code.startsWith('REQ-') ? item.code : 'REQ-142');
                setTargetRequirementId(reqId);
                setActiveTab('Regulatory Requirements');
              }}
            />
          )}

          {/* TAB: AUDIT TRAIL VIEW (Matching uploaded images media_1791740746094_bb421bec.png and media_1791740799469_3c3a4c41.png) */}
          {activeTab === 'Audit Trail' && (
            <AuditTrailView isDarkMode={isDarkMode} />
          )}

          {/* TAB: TOOLS VIEW */}
          {activeTab === 'Tools' && (
            <ToolsView isDarkMode={isDarkMode} />
          )}

          {/* TAB: SETTINGS VIEW */}
          {activeTab === 'Settings' && (
            <SettingsView isDarkMode={isDarkMode} onSignOut={onSignOut} currentUser={userProfile} />
          )}

          {/* OTHER TABS PLACEHOLDER */}
          {activeTab !== 'Dashboard' && activeTab !== 'My Projects' && activeTab !== 'Create Project' && activeTab !== 'Project Details' && activeTab !== 'Advisors / Experts' && activeTab !== 'Advisor Advice' && activeTab !== 'Advice & Decisions' && activeTab !== 'AI / RAG Findings' && activeTab !== 'Readiness' && activeTab !== 'Audit Trail' && activeTab !== 'Regulatory Requirements' && activeTab !== 'Regulatory Support' && activeTab !== 'Tools' && activeTab !== 'Settings' && (
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
