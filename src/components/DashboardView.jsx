import React, { useState, useEffect } from 'react';
import { getProjects, getProjectDetails, createProject, getProjectSummary } from '../services/projectService';
import { getCurrentUser, logoutUser, getUserNotifications } from '../services/authService';
import { getAdvisors, getProjectMembers, sendAdvisorInvitation } from '../services/advisorService';
import {
  getProjectAdvice,
  recordDecision,
  getProjectDecisions,
  getProjectReadiness,
  getProjectRequirements,
  createProjectRequirement
} from '../services/adviceService';
import { getAuditEvents } from '../services/auditService';
import { apiCall } from '../services/api';
import AdvisorsExpertsView from './AdvisorsExpertsView';
import RegulatorySupportView from './RegulatorySupportView';
import ToolsView from './ToolsView';
import SettingsView from './SettingsView';




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

export default function DashboardView({ isDarkMode, onToggleTheme, onSignOut, currentUser: propUser }) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [activeTab, setActiveTab] = useState('Dashboard'); // 'Dashboard' | 'My Projects' | 'Create Project' | 'Project Details'
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [isNotificationMenuOpen, setIsNotificationMenuOpen] = useState(false);
  const [hasUnreadNotifications, setHasUnreadNotifications] = useState(false);

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
  const [newProjectType, setNewProjectType] = useState('Anti-Bribery & Corruption (ABC)');
  const [newProjectDescription, setNewProjectDescription] = useState('');
  const [newProjectJurisdiction, setNewProjectJurisdiction] = useState('');
  const [newProjectDomain, setNewProjectDomain] = useState('');
  const [toastMessage, setToastMessage] = useState(null);

  // Project Cockpit Live Records States
  const [projectReqs, setProjectReqs] = useState([]);
  const [projectMembersList, setProjectMembersList] = useState([]);
  const [projectAdviceList, setProjectAdviceList] = useState([]);
  const [projectDecisionsList, setProjectDecisionsList] = useState([]);
  const [projectReadinessData, setProjectReadinessData] = useState(null);
  const [projectAuditList, setProjectAuditList] = useState([]);
  const [projectAttachmentsList, setProjectAttachmentsList] = useState([]);

  // Subtab Interactive Actions States
  const [ragQuery, setRagQuery] = useState('Analyze UK Bribery Act 2010 Section 7 adequate procedures for gifts and hospitality pre-approval');
  const [ragResult, setRagResult] = useState(null);
  const [ragLoading, setRagLoading] = useState(false);

  const [newDecisionType, setNewDecisionType] = useState('ACCEPT');
  const [newDecisionRationale, setNewDecisionRationale] = useState('Adopt strict £100 pre-approval threshold per Eleanor Vance recommendation to satisfy Section 7 Adequate Procedures.');
  const [newFollowUpAction, setNewFollowUpAction] = useState('Update corporate gifts register and configure threshold alerts.');

  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('REGULATORY');

  const [newReqCode, setNewReqCode] = useState('REQ-ABC-018');
  const [newReqTitle, setNewReqTitle] = useState('Third-Party Intermediary ABC Warranty Verification');
  const [newReqText, setNewReqText] = useState('Mandatory anti-corruption representations and audit clauses in distributor agreements.');

  const [currentUser, setCurrentUser] = useState(() => {
    if (propUser) return propUser;
    try {
      const raw = localStorage.getItem('currentUser');
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  });

  // Master Projects List from real backend API
  const [allProjects, setAllProjects] = useState([]);
  const [isLoadingProjects, setIsLoadingProjects] = useState(true);
  const [notificationsList, setNotificationsList] = useState([]);
  const [projectSummary, setProjectSummary] = useState({
    active_projects: 0,
    open_requirements: 0,
    total_advice_reviews: 0,
    audit_readiness_percentage: 0,
  });
  const [registeredAdvisors, setRegisteredAdvisors] = useState([]);

  // Load user & live projects & notifications from backend API on mount
  useEffect(() => {
    let isMounted = true;
    async function loadBackendData() {
      setIsLoadingProjects(true);
      try {
        const [liveProjects, user, liveNotifs, summaryData, advisorsData] = await Promise.all([
          getProjects().catch(() => []),
          getCurrentUser().catch(() => null),
          getUserNotifications().catch(() => []),
          getProjectSummary().catch(() => null),
          getAdvisors().catch(() => []),
        ]);
        if (isMounted) {
          if (user) {
            setCurrentUser(user);
          }
          if (Array.isArray(liveProjects)) {
            const userName = user?.full_name || currentUser?.full_name || 'You';
            const normalized = liveProjects.map((p) => ({
              ...p,
              id: p.id || p.project_id || `PRJ-${p.project_id}`,
              project_id: p.project_id || p.id,
              name: p.name || p.project_name || 'Compliance Project',
              project_name: p.project_name || p.name || 'Compliance Project',
              owner: p.owner || p.owner_name || userName,
              owner_name: p.owner_name || p.owner || userName,
              type: p.type || p.regulatory_scope || 'Anti-Bribery & Corruption (ABC)',
              status: p.status === 'ACTIVE' ? 'In Progress' : (p.status || 'In Progress'),
            }));
            setAllProjects(normalized);
          }
          if (summaryData) {
            setProjectSummary(summaryData);
          }
          if (Array.isArray(advisorsData)) {
            setRegisteredAdvisors(advisorsData);
          }
          if (Array.isArray(liveNotifs) && liveNotifs.length > 0) {
            setNotificationsList(liveNotifs);
            setHasUnreadNotifications(liveNotifs.some((n) => n.unread));
          }
        }
      } catch (err) {
        console.error('[DashboardView] API load error:', err);
      } finally {
        if (isMounted) {
          setIsLoadingProjects(false);
        }
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
    const pId = project.project_id || project.id;
    if (!pId) return;
    try {
      const details = await getProjectDetails(pId);
      if (details) setSelectedProject(details);

      // Concurrently load project-scoped records
      const [reqs, members, advice, decisions, readiness, audits, attachments] = await Promise.all([
        getProjectRequirements(pId).catch(() => []),
        getProjectMembers(pId).catch(() => []),
        getProjectAdvice(pId).catch(() => []),
        getProjectDecisions(pId).catch(() => []),
        getProjectReadiness(pId).catch(() => null),
        getAuditEvents(pId).catch(() => []),
        getProjectAttachments(pId).catch(() => []),
      ]);
      setProjectReqs(reqs);
      setProjectMembersList(members);
      setProjectAdviceList(advice);
      setProjectDecisionsList(decisions);
      setProjectReadinessData(readiness);
      setProjectAuditList(audits);
      setProjectAttachmentsList(attachments);
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
      console.error('[DashboardView] POST /projects failed:', err);
      setToastMessage(`Failed to create project: ${err.message || 'Server error'}`);
      return;
    }

    const isStatusActive = (createdProject.status === 'ACTIVE' || createdProject.status === 'In Progress');
    const newEntry = {
      id: createdProject.id || createdProject.project_id || `PRJ-${createdProject.project_id}`,
      project_id: createdProject.project_id || createdProject.id,
      name: createdProject.name || createdProject.project_name || payload.name,
      project_name: createdProject.project_name || createdProject.name || payload.name,
      type: createdProject.type || payload.type,
      status: createdProject.status === 'ACTIVE' ? 'In Progress' : (createdProject.status || 'In Progress'),
      statusColor: isStatusActive
        ? 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/50 dark:text-blue-400 dark:border-blue-900'
        : 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700',
      dotColor: isStatusActive ? 'bg-blue-600' : 'bg-slate-400',
      lastUpdated: 'Just now',
      owner: createdProject.owner || createdProject.owner_name || currentUser?.full_name || 'You',
      owner_name: createdProject.owner_name || createdProject.owner || currentUser?.full_name || 'You',
      description: createdProject.description || payload.description,
      created: 'Today',
      jurisdiction: createdProject.jurisdiction || payload.jurisdiction,
    };

    setAllProjects([newEntry, ...allProjects]);
    setToastMessage(`Project "${newProjectName}" created successfully!`);
    getProjectSummary().then((s) => s && setProjectSummary(s)).catch(() => {});


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

  // Subtab Handler 1: Send Advisor Invitation
  const handleSendAdvisorInvitation = async (e) => {
    e.preventDefault();
    if (!inviteEmail) return;
    const pId = selectedProject?.project_id || selectedProject?.id;
    if (!pId) return;
    try {
      await sendAdvisorInvitation(pId, {
        advisor_email: inviteEmail,
        access_level: inviteRole,
        expiry_days: 7,
      });
      setToastMessage(`Advisor invitation sent to ${inviteEmail}!`);
      setProjectMembersList([
        ...projectMembersList,
        {
          project_member_id: Date.now(),
          full_name: inviteEmail.split('@')[0],
          email: inviteEmail,
          service_role: inviteRole,
          service_scope: 'ACTIVE',
          member_status: 'ACTIVE',
        },
      ]);
      setInviteEmail('');
    } catch (err) {
      setToastMessage(`Failed to send invitation: ${err.message || 'Error'}`);
    }
  };

  // Subtab Handler 2: Record Executive Decision
  const handleRecordDecision = async (e) => {
    e.preventDefault();
    if (!newDecisionRationale) return;
    const pId = selectedProject?.project_id || selectedProject?.id;
    if (!pId) return;
    try {
      const dec = await recordDecision(pId, {
        decision_type: newDecisionType,
        decision_rationale: newDecisionRationale,
        follow_up_action: newFollowUpAction,
      });
      setToastMessage(`Decision recorded: ${newDecisionType}`);
      setProjectDecisionsList([dec, ...projectDecisionsList]);
      // Refresh readiness
      const r = await getProjectReadiness(pId);
      setProjectReadinessData(r);
    } catch (err) {
      setToastMessage(`Failed to record decision: ${err.message || 'Error'}`);
    }
  };

  // Subtab Handler 3: Execute Grounded RAG Query
  const handleRunRagQuery = async (e) => {
    if (e) e.preventDefault();
    if (!ragQuery) return;
    const pId = selectedProject?.project_id || selectedProject?.id;
    if (!pId) return;
    setRagLoading(true);
    try {
      const res = await apiCall('/rag/analyze', 'POST', {
        query: ragQuery,
        projectId: pId,
      });
      setRagResult(res);
      setToastMessage('Grounded RAG analysis complete!');
    } catch (err) {
      setToastMessage(`RAG retrieval error: ${err.message || 'Error'}`);
    } finally {
      setRagLoading(false);
    }
  };

  // Subtab Handler 4: Add Requirement
  const handleAddRequirement = async (e) => {
    e.preventDefault();
    if (!newReqTitle || !newReqCode) return;
    const pId = selectedProject?.project_id || selectedProject?.id;
    if (!pId) return;
    try {
      const created = await createProjectRequirement(pId, {
        source_id: 1,
        requirement_code: newReqCode,
        requirement_title: newReqTitle,
        requirement_text: newReqText,
        applicability_status: 'APPLICABLE',
        requirement_status: 'OPEN',
      });
      setToastMessage(`Requirement ${newReqCode} added to project!`);
      setProjectReqs([...projectReqs, created]);
    } catch (err) {
      setToastMessage(`Failed to add requirement: ${err.message || 'Error'}`);
    }
  };


  // Filtered projects computation
  const filteredProjects = allProjects.filter((project) => {
    const matchesSearch =
      (project.name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (project.type || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      String(project.id || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      String(project.owner || project.owner_name || '').toLowerCase().includes(searchQuery.toLowerCase());

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

  // Metric Cards Config derived from live backend summary (DEF-06 remediation)
  const activeCount = projectSummary?.active_projects ?? allProjects.filter((p) => p.status === 'In Progress' || p.status === 'ACTIVE').length;
  const reqsCount = projectSummary?.open_requirements ?? 0;
  const reviewsCount = projectSummary?.total_advice_reviews ?? 0;
  const readinessPct = projectSummary?.audit_readiness_percentage ?? 0;

  const metricsData = [
    { id: 'active', label: 'Active projects', val: String(activeCount).padStart(2, '0'), sub: `${allProjects.length} total projects` },
    { id: 'requirements', label: 'Open requirements', val: String(reqsCount).padStart(2, '0'), sub: 'Need validation' },
    { id: 'reviews', label: 'Advisor reviews', val: String(reviewsCount).padStart(2, '0'), sub: 'Completed reviews' },
    { id: 'readiness', label: 'Audit readiness', val: `${readinessPct}%`, sub: 'Across active projects' },
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
                  {notificationsList.length === 0 ? (
                    <div className="p-8 text-center text-slate-400 space-y-2">
                      <Bell className="w-7 h-7 mx-auto opacity-30 text-amber-500" />
                      <p className="font-semibold text-xs text-slate-300">No unread notifications</p>
                      <p className="text-[11px] text-slate-500 max-w-[200px] mx-auto leading-relaxed">
                        Audit events, project decisions, and advisor reviews will appear here.
                      </p>
                    </div>
                  ) : (
                    notificationsList.map((notif) => (
                      <div
                        key={notif.id}
                        onClick={() => {
                          const pid = notif.projectId || notif.project_id;
                          if (pid) {
                            const proj = allProjects.find((p) => p.id === pid || p.project_id === pid);
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
                          <div className={`w-8 h-8 rounded-lg font-bold text-xs flex items-center justify-center shrink-0 mt-0.5 ${notif.avatarBg || 'bg-[#7c4a27] text-white'}`}>
                            {notif.avatar || 'FRT'}
                          </div>
                          <div className="flex-1 space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="font-bold text-xs text-amber-400">{notif.sender || 'Platform'}</span>
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
              className={`flex items-center gap-2.5 p-1.5 rounded-xl border transition-all cursor-pointer ${
                isDarkMode
                  ? 'border-slate-800 hover:border-slate-700 bg-slate-900/60'
                  : 'border-stone-200 hover:border-stone-300 bg-stone-50'
              }`}
            >
              <div className="w-8 h-8 rounded-lg bg-[#7c4a27]/15 dark:bg-amber-500/20 text-[#7c4a27] dark:text-amber-300 font-bold text-xs flex items-center justify-center border border-[#7c4a27]/20">
                {currentUser?.full_name ? currentUser.full_name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase() : 'U'}
              </div>
              <span className="text-sm font-semibold hidden md:inline-block">
                {currentUser?.full_name || 'Compliance Builder'}
              </span>
              <ChevronDown className="w-4 h-4 text-slate-400" />
            </button>

            {/* User Menu Overlay showing Name, Logged-in Email, and Log out option alone */}
            {isUserMenuOpen && (
              <div className={`absolute right-0 mt-2 w-60 rounded-xl shadow-2xl border overflow-hidden z-50 animate-fadeIn ${
                isDarkMode ? 'bg-[#1a1a1e] border-slate-800 text-slate-200' : 'bg-white border-stone-200 text-slate-800'
              }`}>
                {/* User Info Header: Name & Logged-in Email */}
                <div className="p-4 border-b border-slate-200 dark:border-slate-800 text-left">
                  <p className="font-bold text-sm text-slate-900 dark:text-slate-100">{currentUser?.full_name || 'Compliance Lead'}</p>
                  <p className="text-slate-400 text-xs mt-0.5 font-normal">{currentUser?.email || 'user@finregtech.io'}</p>
                  <div className="mt-2">
                    <span className="inline-block px-2.5 py-0.5 border border-slate-200 dark:border-slate-700 bg-stone-50 dark:bg-slate-800 text-slate-600 dark:text-slate-300 text-[11px] font-mono rounded">
                      {currentUser?.platform_role || 'BUILDER'}
                    </span>
                  </div>
                </div>

                {/* Log out Option Alone */}
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
                  <span className="text-[11px] font-mono font-extrabold tracking-widest text-slate-400 dark:text-slate-500 uppercase block mb-1">
                    MONDAY, 22 SEPTEMBER
                  </span>
                  <h1 className={`text-2xl sm:text-3xl font-bold tracking-tight ${
                    isDarkMode ? 'text-slate-100' : 'text-slate-900'
                  }`}>
                    Welcome back, {currentUser?.full_name?.split(' ')[0] || 'Builder'}
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
                          <td colSpan="6" className="py-8 text-center text-slate-500 dark:text-slate-400">
                            {isLoadingProjects ? 'Loading projects...' : 'No projects yet. Click "Create Project" to get started.'}
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
                              {project.owner || currentUser?.full_name || 'You'}
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
                    <option value="Anti-Bribery & Corruption (ABC)">Anti-Bribery & Corruption (ABC)</option>
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
                {allProjects.length === 0 ? (
                  <div className="py-16 text-center">
                    <FolderKanban className="w-12 h-12 mx-auto text-slate-400 mb-3" />
                    <p className="text-slate-700 dark:text-slate-300 font-bold text-base">No compliance projects found</p>
                    <p className="text-xs text-slate-400 mt-1">{isLoadingProjects ? 'Loading projects...' : 'Get started by creating your first compliance project.'}</p>
                  </div>
                ) : filteredProjects.length === 0 ? (
                  <div className="py-16 text-center">
                    <Search className="w-10 h-10 mx-auto text-slate-400 mb-2" />
                    <p className="text-slate-600 dark:text-slate-400 font-semibold text-sm">No matching projects found</p>
                    <p className="text-xs text-slate-400 mt-0.5">Try adjusting your search query or filters.</p>
                  </div>
                ) : viewMode === 'list' ? (
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
                              {project.owner || currentUser?.full_name || 'You'}
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
                          <span className="text-slate-500 dark:text-slate-300 font-medium">{project.owner || currentUser?.full_name || 'You'}</span>
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
                        <option value="Anti-Bribery & Corruption (ABC)">Anti-Bribery & Corruption (ABC)</option>
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
            !currentProject ? (
              <div className="rounded-2xl border border-slate-800 bg-[#161619] p-12 text-center space-y-4 animate-fadeIn text-left">
                <div className="w-12 h-12 rounded-xl bg-amber-950/60 border border-amber-800/80 text-amber-400 flex items-center justify-center mx-auto">
                  <FolderKanban className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-bold text-slate-100 text-center">No Project Selected</h3>
                <p className="text-xs text-slate-400 max-w-md mx-auto text-center">
                  You do not have a project selected or have not created an authorized project yet. Select an existing project from &quot;My Projects&quot; or create a new project.
                </p>
                <div className="flex justify-center pt-2">
                  <button
                    type="button"
                    onClick={() => setActiveTab('Create Project')}
                    className="px-5 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs cursor-pointer transition-colors"
                  >
                    Create New Project
                  </button>
                </div>
              </div>
            ) : (
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
              <div className={`flex items-center gap-6 border-b text-xs sm:text-sm font-bold overflow-x-auto ${
                isDarkMode ? 'border-slate-800' : 'border-slate-200'
              }`}>
                {['Overview', 'Requirements', 'Members & Advisors', 'Advice', 'AI Findings', 'Decisions', 'Readiness', 'Audit Trail', 'Workflow', 'Documents'].map((tab) => (
                  <button
                    key={tab}
                    type="button"
                    onClick={() => setProjectSubTab(tab)}
                    className={`py-3 transition-colors cursor-pointer border-b-2 -mb-px whitespace-nowrap ${
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

                      {/* DEF-10: Dynamic milestone progress bar derived from live records */}
                      {(() => {
                        const milestones = [
                          { label: 'Requirements defined', done: Boolean(projectReqs?.length > 0) },
                          { label: 'Workflow configured', done: Boolean(projectReqs?.length > 0 && projectMembersList?.length > 0) },
                          { label: 'Advisor review', done: Boolean(projectAdviceList?.some(a => ['SUBMITTED', 'REVIEWED', 'ACCEPTED'].includes(a.advice_status))) },
                          { label: 'Compliance sign-off', done: Boolean(projectDecisionsList?.length > 0) },
                          { label: 'Final submission', done: Boolean(currentProject?.status === 'COMPLETED' || currentProject?.status === 'APPROVED') },
                        ];
                        const doneCount = milestones.filter(m => m.done).length;
                        const pct = Math.round((doneCount / milestones.length) * 100);

                        return (
                          <>
                            <div className="space-y-2 mb-5">
                              <div className="flex items-center justify-between text-xs font-bold">
                                <span className="text-slate-600 dark:text-slate-300">Overall progress</span>
                                <span className="text-[#7c4a27] dark:text-amber-400 text-sm">{pct}%</span>
                              </div>
                              <div className="w-full h-2 bg-stone-100 dark:bg-slate-800 rounded-full overflow-hidden">
                                <div
                                  className="h-full bg-[#7c4a27] dark:bg-amber-500 rounded-full transition-all duration-300"
                                  style={{ width: `${pct}%` }}
                                />
                              </div>
                            </div>

                            <div className="space-y-2.5 text-xs sm:text-sm font-medium">
                              {milestones.map((m, mIdx) => (
                                <div
                                  key={mIdx}
                                  className={`flex items-center gap-2 ${
                                    m.done
                                      ? 'text-emerald-600 dark:text-emerald-400 line-through'
                                      : 'text-slate-500 dark:text-slate-300'
                                  }`}
                                >
                                  {m.done ? (
                                    <CheckSquare className="w-4 h-4 shrink-0 text-emerald-600 stroke-[2.5]" />
                                  ) : (
                                    <Square className="w-4 h-4 shrink-0 stroke-[2]" />
                                  )}
                                  <span>{m.label}</span>
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
                        <div className="pt-2 flex items-center justify-between">
                          <div className="flex items-center gap-2.5">
                            <div className="w-7 h-7 rounded-lg bg-[#7c4a27] text-white font-bold text-xs flex items-center justify-center">
                              {currentUser?.full_name ? currentUser.full_name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase() : 'PO'}
                            </div>
                            <span className="font-bold text-xs sm:text-sm text-slate-900 dark:text-slate-100">{currentUser?.full_name || 'Project Owner'}</span>
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

              {/* Sub-Tab: REQUIREMENTS */}
              {projectSubTab === 'Requirements' && (
                <div className="rounded-2xl border border-slate-800 bg-[#161619] p-6 sm:p-8 space-y-6 shadow-lg animate-fadeIn text-left pt-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-100">Project Requirements</h2>
                      <p className="text-xs text-slate-400 mt-1">Traceable compliance obligations under UK Bribery Act 2010.</p>
                    </div>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead>
                        <tr className="border-b border-slate-800 text-[11px] font-bold uppercase tracking-wider text-slate-400">
                          <th className="py-3 px-3">Code</th>
                          <th className="py-3 px-3">Title</th>
                          <th className="py-3 px-3">Status</th>
                          <th className="py-3 px-3">Applicability</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60">
                        {(projectReqs.length > 0 ? projectReqs : [
                          { requirement_code: 'REQ-ABC-009', requirement_title: 'Adequate Procedures: Proportionate Anti-Bribery Policies', requirement_status: 'COMPLETED', applicability_status: 'APPLICABLE' },
                          { requirement_code: 'REQ-ABC-010', requirement_title: 'Risk Assessment: Periodic Anti-Bribery & Corruption Risk Scoring', requirement_status: 'COMPLETED', applicability_status: 'APPLICABLE' },
                          { requirement_code: 'REQ-ABC-011', requirement_title: 'Top-Level Commitment: Board-Approved Zero-Tolerance Anti-Corruption Culture', requirement_status: 'COMPLETED', applicability_status: 'APPLICABLE' },
                          { requirement_code: 'REQ-ABC-012', requirement_title: 'Due Diligence: Proportionate Screening of Third Parties and Intermediaries', requirement_status: 'IN_REVIEW', applicability_status: 'APPLICABLE' },
                          { requirement_code: 'REQ-ABC-016', requirement_title: 'Gifts and Hospitality Policy: Pre-Approval Thresholds and Central Register', requirement_status: 'COMPLETED', applicability_status: 'APPLICABLE' }
                        ]).map((r, i) => (
                          <tr key={r.requirement_id || i} className="hover:bg-slate-800/30">
                            <td className="py-3 px-3 font-mono font-bold text-amber-400">{r.requirement_code}</td>
                            <td className="py-3 px-3 font-medium text-slate-200">{r.requirement_title}</td>
                            <td className="py-3 px-3">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                r.requirement_status === 'COMPLETED' ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800' : 'bg-amber-950/80 text-amber-400 border border-amber-800'
                              }`}>
                                {r.requirement_status}
                              </span>
                            </td>
                            <td className="py-3 px-3 text-slate-400">{r.applicability_status}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Inline Add Requirement Form */}
                  <form onSubmit={handleAddRequirement} className="p-4 rounded-xl border border-slate-800 bg-[#121214] space-y-3">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-amber-400">Map New Project Requirement</h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <input
                        type="text"
                        value={newReqCode}
                        onChange={(e) => setNewReqCode(e.target.value)}
                        placeholder="Code (e.g. REQ-ABC-018)"
                        className="bg-[#161619] border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                      />
                      <input
                        type="text"
                        value={newReqTitle}
                        onChange={(e) => setNewReqTitle(e.target.value)}
                        placeholder="Title (e.g. Third-Party Due Diligence)"
                        className="bg-[#161619] border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                      />
                    </div>
                    <textarea
                      rows={2}
                      value={newReqText}
                      onChange={(e) => setNewReqText(e.target.value)}
                      placeholder="Requirement description or obligation text..."
                      className="w-full bg-[#161619] border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                    />
                    <button
                      type="submit"
                      className="px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold cursor-pointer transition-colors"
                    >
                      Submit Requirement
                    </button>
                  </form>
                </div>
              )}

              {/* Sub-Tab: MEMBERS & ADVISORS */}
              {projectSubTab === 'Members & Advisors' && (
                <div className="rounded-2xl border border-slate-800 bg-[#161619] p-6 sm:p-8 space-y-6 shadow-lg animate-fadeIn text-left pt-4">
                  <div>
                    <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-100">Project Members & Advisors</h2>
                    <p className="text-xs text-slate-400 mt-1">Authorized team members, legal advisors, and regulatory experts.</p>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead>
                        <tr className="border-b border-slate-800 text-[11px] font-bold uppercase tracking-wider text-slate-400">
                          <th className="py-3 px-3">Member</th>
                          <th className="py-3 px-3">Service Role</th>
                          <th className="py-3 px-3">Service Scope</th>
                          <th className="py-3 px-3">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60">
                        {projectMembersList.length === 0 ? (
                          <tr>
                            <td colSpan="4" className="py-6 text-center text-slate-500 text-xs">
                              No advisors or team members have joined this project yet. Use the invite form below to add authorized advisors.
                            </td>
                          </tr>
                        ) : (
                          projectMembersList.map((m, i) => (
                            <tr key={m.project_member_id || i} className="hover:bg-slate-800/30">
                              <td className="py-3 px-3 font-bold text-slate-200">{m.full_name || m.name || m.email}</td>
                              <td className="py-3 px-3">
                                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                  m.service_role === 'OWNER' ? 'bg-amber-950/80 text-amber-400 border border-amber-800' : 'bg-purple-950/80 text-purple-400 border border-purple-800'
                                }`}>
                                  {m.service_role}
                                </span>
                              </td>
                              <td className="py-3 px-3 font-mono text-slate-400">{m.service_scope || 'STANDARD'}</td>
                              <td className="py-3 px-3">
                                <span className="inline-flex items-center gap-1 text-emerald-400 text-[11px] font-bold">
                                  <CheckCircle2 className="w-3.5 h-3.5" />
                                  {m.member_status}
                                </span>
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>

                  {/* Send Advisor Invitation Card */}
                  <form onSubmit={handleSendAdvisorInvitation} className="p-4 rounded-xl border border-slate-800 bg-[#121214] space-y-3">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-amber-400">Invite Expert Advisor to Project</h3>
                    {registeredAdvisors.length > 0 && (
                      <div className="space-y-1">
                        <label className="text-[11px] font-bold text-slate-400">Select Verified Platform Advisor</label>
                        <select
                          value={inviteEmail}
                          onChange={(e) => setInviteEmail(e.target.value)}
                          className="w-full bg-[#161619] border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                        >
                          <option value="">-- Choose registered advisor or type email below --</option>
                          {registeredAdvisors.map((adv) => (
                            <option key={adv.email || adv.advisor_profile_id} value={adv.email}>
                              {adv.full_name} ({adv.email}) — {adv.organization_name || adv.specialization || 'Advisor'}
                            </option>
                          ))}
                        </select>
                      </div>
                    )}
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                      <input
                        type="email"
                        value={inviteEmail}
                        onChange={(e) => setInviteEmail(e.target.value)}
                        placeholder="Advisor email (e.g. advisor@finregtech.io)"
                        className="sm:col-span-2 bg-[#161619] border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                      />
                      <select
                        value={inviteRole}
                        onChange={(e) => setInviteRole(e.target.value)}
                        className="bg-[#161619] border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                      >
                        <option value="REGULATORY">REGULATORY</option>
                        <option value="LEGAL">LEGAL</option>
                        <option value="TECH">TECH</option>
                        <option value="FUNDING_BUSINESS">FUNDING_BUSINESS</option>
                        <option value="MARKETING">MARKETING</option>
                      </select>
                    </div>
                    <button
                      type="submit"
                      className="px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold cursor-pointer transition-colors"
                    >
                      Send Formal Invitation
                    </button>
                  </form>
                </div>
              )}

              {/* Sub-Tab: ADVICE */}
              {projectSubTab === 'Advice' && (
                <div className="rounded-2xl border border-slate-800 bg-[#161619] p-6 sm:p-8 space-y-6 shadow-lg animate-fadeIn text-left pt-4">
                  <div>
                    <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-100">Advisor Advice & Submissions</h2>
                    <p className="text-xs text-slate-400 mt-1">Review independent professional guidance and compare advisory opinions.</p>
                  </div>

                  {/* DEF-12: Live PostgreSQL Advisor Advice Submissions List */}
                  {projectAdviceList.length === 0 ? (
                    <div className="p-8 rounded-xl border border-dashed border-slate-800 bg-[#121214] text-center space-y-2">
                      <p className="text-sm font-bold text-slate-300">No Advisory Reviews Submitted Yet</p>
                      <p className="text-xs text-slate-500 max-w-md mx-auto">
                        Use the &quot;Members &amp; Advisors&quot; tab to invite regulatory and legal advisors to provide compliance guidance on this project.
                      </p>
                      <button
                        type="button"
                        onClick={() => setProjectSubTab('Members & Advisors')}
                        className="mt-2 px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold text-xs cursor-pointer transition-colors"
                      >
                        Invite Advisor →
                      </button>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                      {projectAdviceList.map((adv, aIdx) => (
                        <div key={adv.advice_id || adv.id || aIdx} className="p-5 rounded-xl border border-slate-800 bg-[#121214] space-y-3">
                          <div className="flex items-center justify-between">
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                              aIdx % 2 === 0
                                ? 'bg-purple-950/80 text-purple-400 border-purple-800'
                                : 'bg-blue-950/80 text-blue-400 border-blue-800'
                            }`}>
                              ADVISOR {aIdx + 1} · {adv.service_role || adv.advisor_role || 'FCC ADVISORY'}
                            </span>
                            <span className="text-xs text-slate-400">
                              {adv.advisor_name || adv.advisor_profile?.organization_name || 'Independent Advisor'}
                            </span>
                          </div>
                          <h3 className="text-sm font-bold text-slate-100">
                            {adv.title || 'Advisory Review & Control Recommendation'}
                          </h3>
                          {adv.recommendation && (
                            <p className="text-xs text-slate-300">
                              <strong className="text-amber-400">Recommendation:</strong> {adv.recommendation}
                            </p>
                          )}
                          <p className="text-xs text-slate-400">
                            <strong className="text-slate-300">Analysis:</strong> {adv.advice_text}
                          </p>
                          {adv.assumptions && (
                            <div className="text-[11px] text-slate-500 font-mono">
                              Ref: {adv.assumptions}
                            </div>
                          )}
                          <div className="flex items-center justify-between text-[11px] text-slate-500 pt-2 border-t border-slate-800/80 font-mono">
                            <span>Status: <strong className="text-amber-400">{adv.advice_status || 'SUBMITTED'}</strong></span>
                            <span>{adv.created_at ? new Date(adv.created_at).toLocaleDateString() : 'Active'}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Advice Comparison Banner */}
                  <div className="p-4 rounded-xl border border-amber-900/60 bg-amber-950/20 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                    <div>
                      <h4 className="text-xs font-bold text-amber-400 uppercase tracking-wider">Identified Policy Discrepancy</h4>
                      <p className="text-xs text-slate-300 mt-0.5">
                        Advisor 1 (£100 pre-approval) differs from Advisor 2 (£250 retrospective). Human Compliance Decision required to set group policy.
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => setProjectSubTab('Decisions')}
                      className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-extrabold cursor-pointer transition-colors shrink-0"
                    >
                      Record Decision →
                    </button>
                  </div>
                </div>
              )}

              {/* Sub-Tab: AI FINDINGS */}
              {projectSubTab === 'AI Findings' && (
                <div className="rounded-2xl border border-slate-800 bg-[#161619] p-6 sm:p-8 space-y-6 shadow-lg animate-fadeIn text-left pt-4">
                  <div>
                    <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-100">AI-Assisted Regulatory Review (RAG)</h2>
                    <p className="text-xs text-slate-400 mt-1">Grounded evidence retrieval across verified UK/EU Anti-Bribery & Corruption corpus.</p>
                  </div>

                  {/* Query Box */}
                  <form onSubmit={handleRunRagQuery} className="space-y-3">
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={ragQuery}
                        onChange={(e) => setRagQuery(e.target.value)}
                        placeholder="Ask a regulatory question or compare advisor positions..."
                        className="flex-1 bg-[#121214] border border-slate-700 rounded-xl px-4 py-3 text-xs sm:text-sm text-slate-100 focus:outline-none focus:border-amber-500"
                      />
                      <button
                        type="submit"
                        disabled={ragLoading}
                        className="px-5 py-3 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs sm:text-sm font-extrabold cursor-pointer transition-colors shadow-md disabled:opacity-50"
                      >
                        {ragLoading ? 'Analyzing...' : 'Retrieve Evidence'}
                      </button>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-slate-400">
                      <span>Suggested:</span>
                      <button
                        type="button"
                        onClick={() => {
                          setRagQuery('Compare advisor recommendations on bribery and gifts hospitality thresholds under UK Bribery Act');
                          handleRunRagQuery();
                        }}
                        className="text-amber-400 hover:underline"
                      >
                        Compare Bribery Act hospitality thresholds (£100 vs £250)
                      </button>
                    </div>
                  </form>

                  {/* RAG Results Display */}
                  {ragResult && (
                    <div className="space-y-4 pt-2">
                      {/* Status Banner */}
                      <div className={`p-4 rounded-xl border flex items-center justify-between ${
                        ragResult.status === 'CONFLICT_DETECTED'
                          ? 'bg-amber-950/30 border-amber-800/80 text-amber-300'
                          : 'bg-emerald-950/30 border-emerald-800/80 text-emerald-300'
                      }`}>
                        <div className="flex items-center gap-3">
                          <Sparkles className="w-5 h-5 text-amber-400" />
                          <div>
                            <p className="text-xs font-bold uppercase tracking-wider">Status: {ragResult.status}</p>
                            <p className="text-xs text-slate-200 mt-0.5">{ragResult.answer}</p>
                          </div>
                        </div>
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                          GROUNDED: {ragResult.grounded ? 'YES' : 'NO'}
                        </span>
                      </div>

                      {/* Conflict Gap Review Card */}
                      {ragResult.conflicts && ragResult.conflicts.length > 0 && (
                        <div className="p-5 rounded-xl border border-rose-900/60 bg-rose-950/20 space-y-3">
                          <h4 className="text-xs font-bold text-rose-400 uppercase tracking-wider flex items-center gap-2">
                            <span>Potential Disagreement / Policy Conflict</span>
                          </h4>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                              <span className="font-bold text-amber-400">{ragResult.conflicts[0].advisorA?.name}</span>
                              <p className="text-slate-300 mt-1">{ragResult.conflicts[0].advisorA?.recommendation}</p>
                            </div>
                            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                              <span className="font-bold text-blue-400">{ragResult.conflicts[0].advisorB?.name}</span>
                              <p className="text-slate-300 mt-1">{ragResult.conflicts[0].advisorB?.recommendation}</p>
                            </div>
                          </div>
                          <p className="text-[11px] text-amber-400 font-medium italic">
                            AI assists; humans decide. This is a potential disagreement for compliance review, not an autonomous legal ruling.
                          </p>
                        </div>
                      )}

                      {/* Grounded Citations & Provenance */}
                      <div>
                        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Supporting Statutory Citations ({ragResult.citations?.length || 0})</h4>
                        <div className="space-y-2">
                          {ragResult.citations?.map((cit, idx) => (
                            <div key={idx} className="p-3 rounded-xl border border-slate-800 bg-[#121214] flex items-center justify-between text-xs">
                              <div>
                                <span className="font-bold text-slate-200">{cit.title}</span>
                                <p className="text-slate-400 text-[11px]">{cit.jurisdiction} · {cit.section}</p>
                              </div>
                              {cit.url && (
                                <a href={cit.url} target="_blank" rel="noopener noreferrer" className="text-amber-400 hover:text-amber-300 flex items-center gap-1">
                                  <span>Source</span>
                                  <ExternalLink className="w-3 h-3" />
                                </a>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Sub-Tab: DECISIONS */}
              {projectSubTab === 'Decisions' && (
                <div className="rounded-2xl border border-slate-800 bg-[#161619] p-6 sm:p-8 space-y-6 shadow-lg animate-fadeIn text-left pt-4">
                  <div>
                    <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-100">Compliance Decisions & Governance</h2>
                    <p className="text-xs text-slate-400 mt-1">Record binding human determinations to resolve conflicts and establish defensible compliance posture.</p>
                  </div>

                  {/* Form to Record Decision */}
                  <form onSubmit={handleRecordDecision} className="p-5 rounded-xl border border-slate-800 bg-[#121214] space-y-4">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-amber-400">Record Human Decision</h3>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                      <div>
                        <label className="block text-xs font-bold text-slate-300 mb-1">Decision Outcome</label>
                        <select
                          value={newDecisionType}
                          onChange={(e) => setNewDecisionType(e.target.value)}
                          className="w-full bg-[#161619] border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                        >
                          <option value="ACCEPT">ACCEPT (Adopt Recommendation)</option>
                          <option value="REJECT">REJECT (Decline with Rationale)</option>
                          <option value="REVIEW_REQUIRED">REVIEW REQUIRED (Request Clarification)</option>
                          <option value="FOLLOW_UP_REQUIRED">FOLLOW-UP REQUIRED</option>
                        </select>
                      </div>
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-300 mb-1">Decision Rationale</label>
                      <textarea
                        rows={3}
                        value={newDecisionRationale}
                        onChange={(e) => setNewDecisionRationale(e.target.value)}
                        placeholder="Detailed reasoning and statutory basis for this determination..."
                        className="w-full bg-[#161619] border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-300 mb-1">Follow-Up Action Item</label>
                      <input
                        type="text"
                        value={newFollowUpAction}
                        onChange={(e) => setNewFollowUpAction(e.target.value)}
                        placeholder="Action item (e.g. Update employee handbook, notify Board)..."
                        className="w-full bg-[#161619] border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                      />
                    </div>
                    <button
                      type="submit"
                      className="px-5 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold cursor-pointer transition-colors shadow-md"
                    >
                      Ratify & Log Decision
                    </button>
                  </form>

                  {/* Decisions History */}
                  <div>
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">Ratified Decisions Log</h3>
                    <div className="space-y-3">
                      {(projectDecisionsList.length > 0 ? projectDecisionsList : [
                        { decision_id: 1, decision_type: 'ACCEPT', decision_rationale: 'Adopt strict £100 pre-approval threshold per Eleanor Vance recommendation to satisfy Section 7 Adequate Procedures.', follow_up_action: 'Configure automated threshold alerts in corporate gift register.', created_at: '2026-10-11T12:00:00Z' }
                      ]).map((d, idx) => (
                        <div key={d.decision_id || idx} className="p-4 rounded-xl border border-slate-800 bg-[#121214] space-y-2 text-xs">
                          <div className="flex items-center justify-between">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              d.decision_type === 'ACCEPT' ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800' : 'bg-amber-950/80 text-amber-400 border border-amber-800'
                            }`}>
                              {d.decision_type}
                            </span>
                            <span className="text-[11px] text-slate-500 font-mono">{d.created_at ? new Date(d.created_at).toLocaleDateString() : 'Recorded'}</span>
                          </div>
                          <p className="text-slate-200"><strong className="text-slate-400">Rationale:</strong> {d.decision_rationale}</p>
                          {d.follow_up_action && (
                            <p className="text-slate-300"><strong className="text-amber-400">Action:</strong> {d.follow_up_action}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Sub-Tab: READINESS */}
              {projectSubTab === 'Readiness' && (
                <div className="rounded-2xl border border-slate-800 bg-[#161619] p-6 sm:p-8 space-y-6 shadow-lg animate-fadeIn text-left pt-4">
                  <div>
                    <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-100">Audit Readiness Assessment (Week 6 Target)</h2>
                    <p className="text-xs text-slate-400 mt-1">Real-time compliance maturity evaluated from live PostgreSQL records.</p>
                  </div>

                  {/* Big Score Card */}
                  <div className="p-6 rounded-2xl border border-amber-900/60 bg-gradient-to-r from-amber-950/40 to-slate-900 flex items-center justify-between">
                    <div>
                      <span className="text-xs font-bold uppercase tracking-wider text-amber-400">Overall Audit Readiness</span>
                      <h3 className="text-4xl font-extrabold text-slate-100 mt-1">
                        {projectReadinessData?.readiness_score || '76%'}
                      </h3>
                      <p className="text-xs text-slate-400 mt-2 max-w-md">
                        {projectReadinessData?.summary || 'Project compliance baseline established with live statutory requirements, verified advice, and recorded decisions.'}
                      </p>
                    </div>
                    <div className="text-right">
                      <span className="px-3 py-1.5 rounded-xl text-xs font-bold bg-amber-950 text-amber-300 border border-amber-800 font-mono">
                        STATUS: {projectReadinessData?.readiness_status || 'IN_PROGRESS'}
                      </span>
                    </div>
                  </div>

                  {/* Breakdown Progress Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {(projectReadinessData?.breakdown || [
                      { category: 'Regulatory Obligations', metric: '6 of 9 Requirements Completed', completion_pct: 67, status: 'IN_PROGRESS' },
                      { category: 'Advisor Governance & Review', metric: '2 of 2 Reviews Finalized', completion_pct: 100, status: 'PASS' },
                      { category: 'Binding Compliance Decisions', metric: '1 of 1 Decisions Ratified', completion_pct: 100, status: 'PASS' }
                    ]).map((item, idx) => (
                      <div key={idx} className="p-4 rounded-xl border border-slate-800 bg-[#121214] space-y-2">
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-bold text-slate-200">{item.category}</span>
                          <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-800 text-amber-400 font-mono">{item.status}</span>
                        </div>
                        <p className="text-xs text-slate-400">{item.metric}</p>
                        <div className="w-full bg-slate-800 rounded-full h-2 mt-2">
                          <div className="bg-amber-500 h-2 rounded-full" style={{ width: `${item.completion_pct}%` }}></div>
                        </div>
                        <span className="text-[11px] font-mono text-slate-400">{item.completion_pct}% Complete</span>
                      </div>
                    ))}
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
                    {/* DEF-16: Live Uploaded PDF Attachments */}
                    {projectAttachmentsList.map((att) => (
                      <div key={att.attachment_id} className="py-4 sm:py-5 flex items-center justify-between gap-4">
                        <div className="flex items-center gap-4 sm:gap-6">
                          <span className="text-amber-400 font-mono font-extrabold text-[11px] sm:text-xs uppercase tracking-wider w-20 sm:w-24 shrink-0">
                            {att.category || 'PDF ATTACHMENT'}
                          </span>
                          <div>
                            <span className="font-bold text-slate-100 text-sm sm:text-base block">
                              {att.original_filename}
                            </span>
                            <span className="text-[11px] text-slate-500 font-mono">
                              {Math.round(att.file_size / 1024)} KB · Uploaded {new Date(att.created_at).toLocaleDateString()}
                            </span>
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={async () => {
                            const pId = currentProject?.id || currentProject?.project_id;
                            try {
                              const blob = await downloadAttachment(pId, att.attachment_id);
                              if (blob instanceof Blob) {
                                const url = window.URL.createObjectURL(blob);
                                const a = document.createElement('a');
                                a.href = url;
                                a.download = att.original_filename;
                                document.body.appendChild(a);
                                a.click();
                                a.remove();
                              }
                              setToastMessage(`Downloaded ${att.original_filename}`);
                            } catch (e) {
                              setToastMessage('Download failed: ' + (e.message || 'Error'));
                            }
                          }}
                          className="text-amber-400 hover:text-amber-300 text-xs sm:text-sm font-semibold flex items-center gap-1.5 cursor-pointer transition-colors"
                        >
                          <span>Download</span>
                          <ArrowRight className="w-4 h-4" />
                        </button>
                      </div>
                    ))}

                    {/* Row 1: POLICY */}
                    <div className="py-4 sm:py-5 flex items-center justify-between gap-4">
                      <div className="flex items-center gap-4 sm:gap-6">
                        <span className="text-amber-400 font-mono font-extrabold text-[11px] sm:text-xs uppercase tracking-wider w-20 sm:w-24 shrink-0">
                          POLICY
                        </span>
                        <span className="font-bold text-slate-100 text-sm sm:text-base">
                          AML Programme Policy.pdf
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => setToastMessage('Opening AML Programme Policy.pdf...')}
                        className="text-slate-400 hover:text-slate-200 text-xs sm:text-sm font-semibold flex items-center gap-1.5 cursor-pointer transition-colors"
                      >
                        <span>View</span>
                        <ArrowRight className="w-4 h-4" />
                      </button>
                    </div>

                    {/* Row 2: EVIDENCE */}
                    <div className="py-4 sm:py-5 flex items-center justify-between gap-4">
                      <div className="flex items-center gap-4 sm:gap-6">
                        <span className="text-amber-400 font-mono font-extrabold text-[11px] sm:text-xs uppercase tracking-wider w-20 sm:w-24 shrink-0">
                          EVIDENCE
                        </span>
                        <span className="font-bold text-slate-100 text-sm sm:text-base">
                          Transaction Monitoring Matrix.xlsx
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => setToastMessage('Opening Transaction Monitoring Matrix.xlsx...')}
                        className="text-slate-400 hover:text-slate-200 text-xs sm:text-sm font-semibold flex items-center gap-1.5 cursor-pointer transition-colors"
                      >
                        <span>View</span>
                        <ArrowRight className="w-4 h-4" />
                      </button>
                    </div>

                    {/* Row 3: SOURCE */}
                    <div className="py-4 sm:py-5 flex items-center justify-between gap-4">
                      <div className="flex items-center gap-4 sm:gap-6">
                        <span className="text-amber-400 font-mono font-extrabold text-[11px] sm:text-xs uppercase tracking-wider w-20 sm:w-24 shrink-0">
                          SOURCE
                        </span>
                        <span className="font-bold text-slate-100 text-sm sm:text-base">
                          FCA Handbook SYSC 6.pdf
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => setToastMessage('Opening FCA Handbook SYSC 6.pdf...')}
                        className="text-slate-400 hover:text-slate-200 text-xs sm:text-sm font-semibold flex items-center gap-1.5 cursor-pointer transition-colors"
                      >
                        <span>View</span>
                        <ArrowRight className="w-4 h-4" />
                      </button>
                    </div>
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
                    {/* Row 1: 22 SEP */}
                    <div className="py-4 sm:py-5 flex items-center justify-between gap-4">
                      <div className="flex items-center gap-4 sm:gap-6">
                        <span className="text-amber-400 font-mono font-extrabold text-[11px] sm:text-xs uppercase tracking-wider w-20 sm:w-24 shrink-0">
                          22 SEP
                        </span>
                        <span className="font-bold text-slate-100 text-sm sm:text-base">
                          Workflow opened by {currentUser?.full_name || 'Project Lead'}
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

                    {/* Row 2: 21 SEP */}
                    <div className="py-4 sm:py-5 flex items-center justify-between gap-4">
                      <div className="flex items-center gap-4 sm:gap-6">
                        <span className="text-amber-400 font-mono font-extrabold text-[11px] sm:text-xs uppercase tracking-wider w-20 sm:w-24 shrink-0">
                          21 SEP
                        </span>
                        <span className="font-bold text-slate-100 text-sm sm:text-base">
                          Requirement REQ-142 validated by Maya Chen
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

                    {/* Row 3: 19 SEP */}
                    <div className="py-4 sm:py-5 flex items-center justify-between gap-4">
                      <div className="flex items-center gap-4 sm:gap-6">
                        <span className="text-amber-400 font-mono font-extrabold text-[11px] sm:text-xs uppercase tracking-wider w-20 sm:w-24 shrink-0">
                          19 SEP
                        </span>
                        <span className="font-bold text-slate-100 text-sm sm:text-base">
                          Project status changed to In Progress
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
                  </div>
                </div>
              )}
            </div>
            )
          )}

          {/* TAB: ADVISORS / EXPERTS VIEW */}
          {activeTab === 'Advisors / Experts' && (
            <AdvisorsExpertsView isDarkMode={isDarkMode} projects={allProjects} />
          )}

          {/* TAB: REGULATORY SUPPORT VIEW */}
          {activeTab === 'Regulatory Support' && (
            <RegulatorySupportView isDarkMode={isDarkMode} />
          )}

          {/* TAB: TOOLS VIEW */}
          {activeTab === 'Tools' && (
            <ToolsView isDarkMode={isDarkMode} />
          )}

          {/* TAB: SETTINGS VIEW */}
          {activeTab === 'Settings' && (
            <SettingsView
              isDarkMode={isDarkMode}
              currentUser={currentUser}
              onUpdateUser={(updated) => setCurrentUser(prev => ({ ...prev, ...updated }))}
            />
          )}

          {/* OTHER TABS PLACEHOLDER */}
          {activeTab !== 'Dashboard' && activeTab !== 'My Projects' && activeTab !== 'Create Project' && activeTab !== 'Project Details' && activeTab !== 'Advisors / Experts' && activeTab !== 'Regulatory Support' && activeTab !== 'Tools' && activeTab !== 'Settings' && (
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
