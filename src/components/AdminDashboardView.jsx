import React, { useState } from 'react';
import {
  Menu,
  Bell,
  ChevronDown,
  LayoutGrid,
  Users,
  Shield,
  Folder,
  Mail,
  FileText,
  Activity,
  Settings,
  ArrowRight,
  LogOut,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Search,
  ExternalLink,
  ShieldAlert,
  ShieldCheck,
  Check,
  Sliders,
  Filter,
  UserCheck,
  Lock,
  Database,
  Calendar,
  Plus,
  X
} from 'lucide-react';
import { logoutUser, getRegisteredUsers } from '../services/authService';
import { getLocalProjects } from '../services/projectService';

export default function AdminDashboardView({
  isDarkMode = true,
  onSignOut,
  currentUser,
}) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [activeTab, setActiveTab] = useState('Dashboard');
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [isNotificationOpen, setIsNotificationOpen] = useState(false);
  const [toastMsg, setToastMsg] = useState(null);

  // Dynamic Admin Profile (DEF-03)
  const adminName = currentUser?.name || 'Avery Patel';
  const adminEmail = currentUser?.email || 'admin@gmail.com';
  const adminInitials = adminName
    .split(' ')
    .filter(Boolean)
    .map((n) => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase() || 'AP';

  const showToast = (msg) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(null), 3000);
  };

  // Seed / Baseline Admin Users matching Images 1 & 2
  const DEFAULT_ADMIN_USERS = [
    {
      id: 'USR-001',
      name: 'Jun Nakamura',
      email: 'jun@northbank.com',
      role: 'Builder',
      status: 'Active',
      registered: '04 Aug 2026',
      lastLogin: '8 min ago',
    },
    {
      id: 'USR-002',
      name: 'Dr. Maya Chen',
      email: 'maya@regadvisory.com',
      role: 'Advisor',
      status: 'Active',
      registered: '11 Aug 2026',
      lastLogin: '24 min ago',
    },
    {
      id: 'USR-003',
      name: 'Daniel Okafor',
      email: 'daniel@independent.demo',
      role: 'Advisor',
      status: 'Active',
      registered: '18 Aug 2026',
      lastLogin: 'Yesterday',
    },
    {
      id: 'USR-004',
      name: 'Avery Patel',
      email: 'avery@shipyard.demo',
      role: 'Admin',
      status: 'Active',
      registered: '01 Aug 2026',
      lastLogin: 'Just now',
    },
    {
      id: 'USR-005',
      name: 'Sofia Alvarez',
      email: 'sofia@trustworks.demo',
      role: 'Advisor',
      status: 'Inactive',
      registered: '21 Aug 2026',
      lastLogin: '12 Sep 2026',
    },
  ];

  // Helper to load live registered users (DEF-03)
  const loadInitialUsers = () => {
    try {
      const reg = getRegisteredUsers();
      if (!Array.isArray(reg) || reg.length === 0) return DEFAULT_ADMIN_USERS;

      const formattedReg = reg.map((u, idx) => {
        let displayRole = 'Builder';
        const rawRole = (u.role || u.platform_role || '').toUpperCase();
        if (rawRole.includes('ADVISOR')) displayRole = 'Advisor';
        else if (rawRole.includes('ADMIN')) displayRole = 'Admin';
        else displayRole = 'Builder';

        return {
          id: u.id && u.id.startsWith('USR-') ? u.id : `USR-${String(idx + 1).padStart(3, '0')}`,
          name: u.name || 'User',
          email: u.email || '',
          role: displayRole,
          status: u.status || 'Active',
          registered: u.created_at
            ? new Date(u.created_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
            : '01 Aug 2026',
          lastLogin: u.last_login_at || 'Recently',
        };
      });

      const emailMap = new Map();
      formattedReg.forEach((u) => emailMap.set(u.email.toLowerCase(), u));
      DEFAULT_ADMIN_USERS.forEach((def) => {
        if (!emailMap.has(def.email.toLowerCase())) {
          emailMap.set(def.email.toLowerCase(), def);
        }
      });
      return Array.from(emailMap.values());
    } catch (e) {
      return DEFAULT_ADMIN_USERS;
    }
  };

  const [users, setUsers] = useState(loadInitialUsers);

  // Projects Oversight list dynamic loader (DEF-03)
  const DEFAULT_ADMIN_PROJECTS = [
    {
      id: 'PRJ-001',
      name: 'ABC Shield',
      owner: 'J. Nakamura',
      status: 'In Progress',
      statusColor: 'bg-[#281d11] text-amber-400 border-amber-800/50',
      dotColor: 'bg-amber-400',
      assignedAdvisors: '1 / 2',
      creationDate: '22 Sep 2026',
      lastActivity: '22 Sep 2026',
      readiness: '70% · Progressing',
      accessBoundary: 'Metadata visibility only; restricted content requires explicit authorization.',
    },
    {
      id: 'PRJ-002',
      name: 'KYC Onboarding Controls',
      owner: 'S. Okonkwo',
      status: 'Under Review',
      statusColor: 'bg-slate-800/80 text-amber-300 border-amber-800/40',
      dotColor: 'bg-amber-400',
      assignedAdvisors: '0 / 2',
      creationDate: '18 Sep 2026',
      lastActivity: '21 Sep 2026',
      readiness: 'Review required',
      accessBoundary: 'Metadata visibility only; restricted content requires explicit authorization.',
    },
    {
      id: 'PRJ-003',
      name: 'Regulatory Reporting Q3',
      owner: 'A. Petrov',
      status: 'Draft',
      statusColor: 'bg-slate-800/60 text-slate-300 border-slate-700/60',
      dotColor: 'bg-slate-500',
      assignedAdvisors: '0 / 2',
      creationDate: '18 Sep 2026',
      lastActivity: '19 Sep 2026',
      readiness: 'Review required',
      accessBoundary: 'Metadata visibility only; restricted content requires explicit authorization.',
    },
  ];

  const loadInitialProjects = () => {
    try {
      const local = getLocalProjects();
      if (!Array.isArray(local) || local.length === 0) return DEFAULT_ADMIN_PROJECTS;
      const formattedLocal = local.map((p) => ({
        id: p.id,
        name: p.name,
        owner: p.owner || 'Project Owner',
        status: p.status || 'In Progress',
        statusColor: p.statusColor || 'bg-[#281d11] text-amber-400 border-amber-800/50',
        dotColor: p.dotColor || 'bg-amber-400',
        assignedAdvisors: '0 / 2',
        creationDate: p.created || 'Recently',
        lastActivity: p.lastUpdated || 'Recently',
        readiness: 'Initial Review',
        accessBoundary: 'Metadata visibility only; restricted content requires explicit authorization.',
      }));
      return [...formattedLocal, ...DEFAULT_ADMIN_PROJECTS];
    } catch (e) {
      return DEFAULT_ADMIN_PROJECTS;
    }
  };

  const [projectsList, setProjectsList] = useState(loadInitialProjects);

  // Advisor Invitations list dynamic loader (DEF-03)
  const DEFAULT_ADMIN_INVITATIONS = [
    {
      id: 'INV-001',
      project: 'ABC Shield',
      invitingBuilder: 'Jun Nakamura',
      invitedAdvisor: 'Dr. Maya Chen',
      expertise: 'Regulatory Compliance',
      invitationDate: '20 Sep 2026',
      status: 'Accepted',
      statusBadgeClass: 'bg-[#0e2316] text-emerald-400 border-emerald-800/50',
      statusDotClass: 'bg-emerald-400',
      accessStatus: 'Active',
    },
    {
      id: 'INV-002',
      project: 'ABC Shield',
      invitingBuilder: 'Jun Nakamura',
      invitedAdvisor: 'Daniel Okafor',
      expertise: 'Tech Expert',
      invitationDate: '29 Sep 2026',
      status: 'Pending',
      statusBadgeClass: 'bg-[#281d11] text-amber-400 border-amber-800/50',
      statusDotClass: 'bg-amber-400',
      accessStatus: 'Not granted',
    },
    {
      id: 'INV-003',
      project: 'KYC Onboarding Controls',
      invitingBuilder: 'Sam Okonkwo',
      invitedAdvisor: 'Sofia Alvarez',
      expertise: 'Legal Partner',
      invitationDate: '18 Sep 2026',
      status: 'Revoked',
      statusBadgeClass: 'bg-[#2a1414] text-rose-400 border-rose-800/50',
      statusDotClass: 'bg-rose-500',
      accessStatus: 'Revoked',
    },
    {
      id: 'INV-004',
      project: 'Regulatory Reporting Q3',
      invitingBuilder: 'Ana Petrov',
      invitedAdvisor: 'Dr. Maya Chen',
      expertise: 'Funding / Business Support',
      invitationDate: '16 Sep 2026',
      status: 'Declined',
      statusBadgeClass: 'bg-[#281d11] text-amber-400 border-amber-800/50',
      statusDotClass: 'bg-amber-500',
      accessStatus: 'Not granted',
    },
  ];

  const loadInitialInvitations = () => {
    try {
      const raw = localStorage.getItem('finreg_advisor_assignments');
      const assignments = raw ? JSON.parse(raw) : [];
      if (!Array.isArray(assignments) || assignments.length === 0) return DEFAULT_ADMIN_INVITATIONS;
      const formatted = assignments.map((a, idx) => ({
        id: a.id || `INV-${String(idx + 10).padStart(3, '0')}`,
        project: a.projectName || 'Project',
        invitingBuilder: 'Builder',
        invitedAdvisor: a.advisorName || 'Advisor',
        expertise: a.advisorRole || 'Advisor Expert',
        invitationDate: a.assignedDate || 'Recently',
        status: a.status === 'In Review' ? 'Active' : (a.status || 'Active'),
        statusBadgeClass: 'bg-[#0e2316] text-emerald-400 border-emerald-800/50',
        statusDotClass: 'bg-emerald-400',
        accessStatus: 'Active',
      }));
      return [...formatted, ...DEFAULT_ADMIN_INVITATIONS];
    } catch (e) {
      return DEFAULT_ADMIN_INVITATIONS;
    }
  };

  const [advisorInvitationsList, setAdvisorInvitationsList] = useState(loadInitialInvitations);

  // 6 Metric Cards computed dynamically from live platform data (DEF-03)
  const metricCards = [
    {
      title: 'Total Users',
      val: String(users.length).padStart(2, '0'),
      subtitle: `${users.filter((u) => u.status === 'Active').length} active platform accounts`,
    },
    {
      title: 'Active Users',
      val: String(users.filter((u) => u.status === 'Active').length).padStart(2, '0'),
      subtitle: `${Math.round((users.filter((u) => u.status === 'Active').length / (users.length || 1)) * 100)}% of platform accounts`,
    },
    {
      title: 'Total Projects',
      val: String(projectsList.length).padStart(2, '0'),
      subtitle: `${projectsList.filter((p) => p.status !== 'Draft').length} active · ${projectsList.filter((p) => p.status === 'Draft').length} draft`,
    },
    {
      title: 'Active Advisor Invitations',
      val: String(advisorInvitationsList.length).padStart(2, '0'),
      subtitle: `${advisorInvitationsList.filter((i) => i.status === 'Accepted' || i.status === 'Active').length} accepted · ${advisorInvitationsList.filter((i) => i.status === 'Pending').length} pending`,
    },
    {
      title: 'Pending Source Validation',
      val: '01',
      subtitle: 'Regulatory review required',
    },
    {
      title: 'Recent Security Events',
      val: '05',
      subtitle: '2 require attention',
    },
  ];

  // Middle Section 4 Cards data matching Image 2 (media_1791981200685_5461ca8a.png)
  const recentPlatformActivity = [
    { time: '15:14', text: 'Account status changed for Sofia Alvarez' },
    { time: '14:42', text: 'Blocked Admin authentication attempt' },
    { time: '13:06', text: 'Advisor role metadata reviewed' },
  ];

  const recentUserRegistrations = users.slice(0, 3).map((u) => ({
    date: u.registered ? u.registered.slice(0, 6).toUpperCase() : 'TODAY',
    text: `${u.name} · ${u.role}`,
  }));

  const projectStatusOverview = [
    { count: String(projectsList.filter((p) => p.status === 'In Progress').length).padStart(2, '0'), label: 'Active projects' },
    { count: String(projectsList.filter((p) => p.status === 'Under Review').length).padStart(2, '0'), label: 'Under review' },
    { count: String(projectsList.filter((p) => p.status === 'Draft' || p.status === 'Completed').length).padStart(2, '0'), label: 'Draft / Completed' },
  ];

  const recentAccessChanges = [
    { tag: 'USER', text: 'Sofia Alvarez deactivated' },
    { tag: 'ROLE', text: 'Daniel Okafor permissions reviewed' },
    { tag: 'ACCESS', text: 'ABC Shield invitation pending' },
  ];

  // Bottom Section Security Alerts matching Image 3 (media_1791981206848_d73db92a.png)
  const securityAlerts = [
    {
      tag: 'BLOCKED',
      description: 'Repeated Admin authentication failures',
    },
    {
      tag: 'SESSION',
      description: 'Expired privileged session',
    },
  ];

  const [searchUserQuery, setSearchUserQuery] = useState('');
  const [selectedRoleFilter, setSelectedRoleFilter] = useState('All roles');
  const [selectedStatusFilter, setSelectedStatusFilter] = useState('All statuses');
  const [deactivatingUser, setDeactivatingUser] = useState(null);
  const [showStatusRecordedBanner, setShowStatusRecordedBanner] = useState(true);

  const persistUserStatus = (userId, newStatus) => {
    try {
      const raw = localStorage.getItem('finreg_registered_users');
      if (raw) {
        const parsed = JSON.parse(raw);
        const updated = parsed.map((u) => (u.id === userId || u.email === userId ? { ...u, status: newStatus } : u));
        localStorage.setItem('finreg_registered_users', JSON.stringify(updated));
      }
    } catch (e) {
      // ignore
    }
  };

  const handleConfirmDeactivate = (userId) => {
    setUsers((prev) =>
      prev.map((u) => (u.id === userId ? { ...u, status: 'Inactive' } : u))
    );
    persistUserStatus(userId, 'Inactive');
    setShowStatusRecordedBanner(true);
    showToast(`Account status updated for ${deactivatingUser?.name || 'User'} and recorded in audit log.`);
    setDeactivatingUser(null);
  };

  const handleToggleStatus = (userId) => {
    setUsers((prev) =>
      prev.map((u) => {
        if (u.id === userId) {
          const nextStatus = u.status === 'Active' ? 'Inactive' : 'Active';
          persistUserStatus(userId, nextStatus);
          return { ...u, status: nextStatus };
        }
        return u;
      })
    );
    setShowStatusRecordedBanner(true);
  };

  const filteredUsers = users.filter((u) => {
    const matchesSearch =
      searchUserQuery.trim() === '' ||
      u.name.toLowerCase().includes(searchUserQuery.toLowerCase()) ||
      u.email.toLowerCase().includes(searchUserQuery.toLowerCase());

    const matchesRole =
      selectedRoleFilter === 'All roles' || u.role.toLowerCase() === selectedRoleFilter.toLowerCase();

    const matchesStatus =
      selectedStatusFilter === 'All statuses' || u.status.toLowerCase() === selectedStatusFilter.toLowerCase();

    return matchesSearch && matchesRole && matchesStatus;
  });

  // Project Oversight states matching Images 2 & 3
  const [selectedProjectOverview, setSelectedProjectOverview] = useState(null);
  const [projectSearchQuery, setProjectSearchQuery] = useState('');
  const [projectStatusFilter, setProjectStatusFilter] = useState('All statuses');

  const filteredProjects = projectsList.filter((proj) => {
    const matchesSearch =
      projectSearchQuery.trim() === '' ||
      proj.name.toLowerCase().includes(projectSearchQuery.toLowerCase()) ||
      proj.id.toLowerCase().includes(projectSearchQuery.toLowerCase()) ||
      proj.owner.toLowerCase().includes(projectSearchQuery.toLowerCase());

    const matchesStatus =
      projectStatusFilter === 'All statuses' ||
      proj.status.toLowerCase() === projectStatusFilter.toLowerCase();

    return matchesSearch && matchesStatus;
  });

  // Advisor Invitations states matching media_1791998978622_11428009.png
  const [advisorInvitationStatusFilter, setAdvisorInvitationStatusFilter] = useState('All statuses');

  const filteredAdvisorInvitations = advisorInvitationsList.filter((inv) => {
    if (advisorInvitationStatusFilter === 'All statuses') return true;
    return inv.status.toLowerCase() === advisorInvitationStatusFilter.toLowerCase();
  });

  // Regulatory Data Management state matching Images 1, 2, & 3
  const [isAddSourceModalOpen, setIsAddSourceModalOpen] = useState(false);
  const [newSourceForm, setNewSourceForm] = useState({
    title: '',
    authority: '',
    jurisdiction: '',
    publicationDate: '',
    version: '',
    topic: '',
    applicability: '',
  });

  const [regulatorySources, setRegulatorySources] = useState([
    {
      id: 'SRC-001',
      title: 'FCA Handbook',
      applicability: 'Applicable to all UK-authorised firms conducting customer onboarding',
      authority: 'FCA',
      jurisdiction: 'United Kingdom',
      publication: '01 Sep 2026',
      version: 'Release 126 · Sep 2026',
      topic: 'Risk-sensitive customer due diligence',
      status: 'Validated',
      statusBadgeClass: 'bg-[#0e2316] text-emerald-400 border-emerald-800/50',
      statusDotClass: 'bg-emerald-400',
      lastUpdated: '29 Sep 2026',
    },
    {
      id: 'SRC-002',
      title: 'JMLSG Guidance',
      applicability: 'Applicable to UK financial services firms with payment or deposit-taking activities',
      authority: 'JMLSG',
      jurisdiction: 'United Kingdom',
      publication: '18 Jul 2024',
      version: 'Jul 2024 revision',
      topic: 'Ongoing transaction monitoring',
      status: 'Pending Validation',
      statusBadgeClass: 'bg-[#281d11] text-amber-400 border-amber-800/50',
      statusDotClass: 'bg-amber-400',
      lastUpdated: '29 Sep 2026',
    },
    {
      id: 'SRC-003',
      title: 'SAR Guidance',
      applicability: 'Applicable to all UK-based firms subject to POCA 2002 Part 7',
      authority: 'NCA',
      jurisdiction: 'United Kingdom',
      publication: '15 Jan 2025',
      version: 'Version 3.1 · Jan 2025',
      topic: 'Suspicious activity escalation',
      status: 'Validated',
      statusBadgeClass: 'bg-[#0e2316] text-emerald-400 border-emerald-800/50',
      statusDotClass: 'bg-emerald-400',
      lastUpdated: '29 Sep 2026',
    },
  ]);

  const handleAddSource = (e) => {
    e?.preventDefault();
    if (!newSourceForm.title.trim()) {
      showToast('Please enter a source or document title');
      return;
    }

    const newSource = {
      id: `SRC-${Date.now()}`,
      title: newSourceForm.title.trim(),
      applicability: newSourceForm.applicability.trim() || 'Human-reviewed applicability notes',
      authority: newSourceForm.authority.trim() || 'FCA',
      jurisdiction: newSourceForm.jurisdiction.trim() || 'United Kingdom',
      publication: newSourceForm.publicationDate.trim() || '29 Sep 2026',
      version: newSourceForm.version.trim() || 'Version 1.0',
      topic: newSourceForm.topic.trim() || 'General Compliance',
      status: 'Pending Validation',
      statusBadgeClass: 'bg-[#281d11] text-amber-400 border-amber-800/50',
      statusDotClass: 'bg-amber-400',
      lastUpdated: '29 Sep 2026',
    };

    setRegulatorySources((prev) => [newSource, ...prev]);
    setIsAddSourceModalOpen(false);
    setNewSourceForm({
      title: '',
      authority: '',
      jurisdiction: '',
      publicationDate: '',
      version: '',
      topic: '',
      applicability: '',
    });
    showToast('Regulatory source added as Pending Validation');
  };

  // Audit Logs state matching Image 4 (media_1791999494451_b654a5f6.png)
  const [auditLogSearchQuery, setAuditLogSearchQuery] = useState('');
  const [auditLogDateFilter, setAuditLogDateFilter] = useState('');
  const [auditLogActionTypeFilter, setAuditLogActionTypeFilter] = useState('All action types');
  const [auditLogResultFilter, setAuditLogResultFilter] = useState('All results');

  const [auditLogsList] = useState([
    {
      id: 'AUD-001',
      timestamp: '29 Sep 2026 · 15:14',
      user: 'Avery Patel',
      action: 'Account deactivated',
      affectedResource: 'Sofia Alvarez',
      eventCategory: 'User Access',
      result: 'Success',
      resultBadgeClass: 'bg-[#0e2316] text-emerald-400 border-emerald-800/50',
      resultDotClass: 'bg-emerald-400',
      relevantDetails: 'Administrative confirmation recorded',
    },
    {
      id: 'AUD-002',
      timestamp: '29 Sep 2026 · 14:42',
      user: 'Unknown account',
      action: 'Login failure',
      affectedResource: 'Admin authentication',
      eventCategory: 'Security',
      result: 'Blocked',
      resultBadgeClass: 'bg-[#2a1414] text-rose-400 border-rose-800/50',
      resultDotClass: 'bg-rose-500',
      relevantDetails: 'Generic authentication failure returned',
    },
    {
      id: 'AUD-003',
      timestamp: '29 Sep 2026 · 13:05',
      user: 'Avery Patel',
      action: 'Role changed',
      affectedResource: 'Daniel Okafor',
      eventCategory: 'Permissions',
      result: 'Success',
      resultBadgeClass: 'bg-[#0e2316] text-emerald-400 border-emerald-800/50',
      resultDotClass: 'bg-emerald-400',
      relevantDetails: 'Advisor role retained; expertise updated',
    },
    {
      id: 'AUD-004',
      timestamp: '29 Sep 2026 · 11:30',
      user: 'Jun Nakamura',
      action: 'Invitation created',
      affectedResource: 'ABC Shield',
      eventCategory: 'Invitation',
      result: 'Success',
      resultBadgeClass: 'bg-[#0e2316] text-emerald-400 border-emerald-800/50',
      resultDotClass: 'bg-emerald-400',
      relevantDetails: 'Advisor limit remains 2',
    },
    {
      id: 'AUD-005',
      timestamp: '28 Sep 2026 · 16:41',
      user: 'Avery Patel',
      action: 'Source metadata updated',
      affectedResource: 'FCA Handbook',
      eventCategory: 'Regulatory Data',
      result: 'Success',
      resultBadgeClass: 'bg-[#0e2316] text-emerald-400 border-emerald-800/50',
      resultDotClass: 'bg-emerald-400',
      relevantDetails: 'Validation state unchanged',
    },
  ]);

  const filteredAuditLogs = auditLogsList.filter((log) => {
    const matchesSearch =
      auditLogSearchQuery.trim() === '' ||
      log.user.toLowerCase().includes(auditLogSearchQuery.toLowerCase()) ||
      log.action.toLowerCase().includes(auditLogSearchQuery.toLowerCase()) ||
      log.affectedResource.toLowerCase().includes(auditLogSearchQuery.toLowerCase()) ||
      log.relevantDetails.toLowerCase().includes(auditLogSearchQuery.toLowerCase());

    const matchesAction =
      auditLogActionTypeFilter === 'All action types' ||
      log.action.toLowerCase() === auditLogActionTypeFilter.toLowerCase();

    const matchesResult =
      auditLogResultFilter === 'All results' ||
      log.result.toLowerCase() === auditLogResultFilter.toLowerCase();

    const matchesDate =
      auditLogDateFilter.trim() === '' ||
      log.timestamp.toLowerCase().includes(auditLogDateFilter.toLowerCase());

    return matchesSearch && matchesAction && matchesResult && matchesDate;
  });

  // Selected audit event for viewing details modal matching Image 1
  const [selectedAuditEvent, setSelectedAuditEvent] = useState(null);

  // Admin settings notification preference matching uploaded image
  const [adminNotificationPref, setAdminNotificationPref] = useState('Essential Admin alerts');

  return (
    <div className="min-h-screen bg-[#0f1012] text-slate-100 flex flex-col font-sans select-none antialiased">
      {/* Toast Notification Alert */}
      {toastMsg && (
        <div className="fixed bottom-6 right-6 z-50 bg-[#1e2025] border border-amber-500/80 text-amber-300 px-4 py-3 rounded-md shadow-2xl flex items-center gap-3 text-xs sm:text-sm font-semibold animate-fadeIn">
          <CheckCircle2 className="w-4 h-4 text-amber-400 shrink-0" />
          <span>{toastMsg}</span>
        </div>
      )}

      {/* TOP NAVBAR matching images */}
      <header className="h-16 border-b border-slate-800 bg-[#121316] flex items-center justify-between px-4 sm:px-6 sticky top-0 z-40">
        {/* Left: Brand & Sidebar toggle */}
        <div className="flex items-center gap-3 sm:gap-4">
          <button
            type="button"
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="p-1.5 rounded-md text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors cursor-pointer"
            title="Toggle Sidebar"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-md bg-[#1a1712] border border-amber-500/50 flex items-center justify-center text-amber-400 font-bold font-serif text-sm shadow-sm">
              F
            </div>
            <div className="leading-tight text-left">
              <span className="font-extrabold text-white tracking-tight text-sm sm:text-base block">
                FinRegTech
              </span>
              <span className="text-[9px] font-mono tracking-[0.22em] text-amber-500 font-bold block uppercase -mt-0.5">
                SHIPYARD
              </span>
            </div>
          </div>
        </div>

        {/* Center: Admin Workspace Label & Current View */}
        <div className="hidden sm:flex flex-col items-center justify-center text-center">
          <span className="text-[10px] font-mono tracking-widest text-slate-500 uppercase font-bold">
            ADMIN WORKSPACE
          </span>
          <span className="text-xs sm:text-sm font-bold text-white -mt-0.5">
            {activeTab}
          </span>
        </div>

        {/* Right: Notifications & Avery Patel Profile */}
        <div className="flex items-center gap-3">
          {/* Notification Bell */}
          <div className="relative">
            <button
              type="button"
              onClick={() => {
                setIsNotificationOpen(!isNotificationOpen);
                setIsUserMenuOpen(false);
              }}
              className="p-2 rounded-md text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors relative cursor-pointer"
              title="Notifications"
            >
              <Bell className="w-4 h-4" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-amber-500 ring-2 ring-[#121316]" />
            </button>

            {/* Notification Dropdown */}
            {isNotificationOpen && (
              <div className="absolute right-0 mt-2 w-80 rounded-xl bg-[#16181d] border border-slate-800 shadow-2xl p-4 z-50 animate-fadeIn text-left">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
                  <span className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                    Security Alerts
                  </span>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-400 font-mono font-bold">
                    2 New
                  </span>
                </div>
                <div className="space-y-2.5 text-xs">
                  <div className="p-2.5 rounded-md bg-slate-900/80 border border-slate-800">
                    <p className="font-bold text-amber-400">Repeated Admin authentication failures</p>
                    <p className="text-[11px] text-slate-400 mt-0.5">Blocked attempt from 192.168.1.104</p>
                  </div>
                  <div className="p-2.5 rounded-md bg-slate-900/80 border border-slate-800">
                    <p className="font-bold text-amber-400">Expired privileged session</p>
                    <p className="text-[11px] text-slate-400 mt-0.5">Session timeout reached for audit administrator</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* User Profile Badge (AP · Avery Patel) */}
          <div className="relative">
            <button
              type="button"
              onClick={() => {
                setIsUserMenuOpen(!isUserMenuOpen);
                setIsNotificationOpen(false);
              }}
              className="flex items-center gap-2.5 p-1 rounded-md hover:bg-slate-800/80 transition-colors cursor-pointer"
            >
              <div className="w-8 h-8 rounded bg-[#1e222a] border border-slate-700/80 flex items-center justify-center text-xs font-bold text-slate-200">
                {adminInitials}
              </div>
              <span className="hidden md:inline text-xs sm:text-sm font-semibold text-slate-200">
                {adminName}
              </span>
            </button>

            {/* User Dropdown */}
            {isUserMenuOpen && (
              <div className="absolute right-0 mt-2 w-64 rounded-xl bg-[#16181d] border border-slate-800 shadow-2xl p-2 z-50 animate-fadeIn text-left">
                <div className="p-3 border-b border-slate-800">
                  <p className="text-sm font-bold text-white">{adminName}</p>
                  <p className="text-xs text-slate-400">{adminEmail}</p>
                  <div className="mt-2 flex items-center gap-1.5">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">
                      Global Administrator
                    </span>
                  </div>
                </div>
                <div className="py-1">
                  <button
                    type="button"
                    onClick={() => {
                      setIsUserMenuOpen(false);
                      setActiveTab('Settings');
                    }}
                    className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-medium text-slate-300 hover:bg-slate-800 rounded-md cursor-pointer transition-colors"
                  >
                    <Settings className="w-3.5 h-3.5 text-slate-400" />
                    <span>Admin Settings</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      logoutUser();
                      if (onSignOut) onSignOut();
                    }}
                    className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-semibold text-rose-400 hover:bg-rose-950/30 rounded-md cursor-pointer transition-colors"
                  >
                    <LogOut className="w-3.5 h-3.5 text-rose-400" />
                    <span>Log out</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* WORKSPACE BODY: SIDEBAR + CONTENT */}
      <div className="flex-1 flex w-full">
        {/* LEFT SIDEBAR NAVIGATION matching screenshots */}
        <aside
          className={`${
            isSidebarOpen ? 'w-64' : 'w-16'
          } transition-all duration-300 border-r border-slate-800 bg-[#121316] flex flex-col justify-between p-3 z-30 shrink-0`}
        >
          <div className="space-y-4">
            {isSidebarOpen && (
              <div className="px-3 pt-3 text-left">
                <span className="text-[10px] font-mono font-extrabold tracking-widest text-slate-500 uppercase">
                  ADMIN NAVIGATION
                </span>
              </div>
            )}

            <nav className="space-y-1 text-left">
              {[
                { name: 'Dashboard', icon: LayoutGrid },
                { name: 'User Management', icon: Users },
                { name: 'Roles & Permissions', icon: ShieldCheck },
                { name: 'Project Oversight', icon: Folder },
                { name: 'Advisor Invitations', icon: FileText },
                {
                  name: 'Regulatory Data Management',
                  displayName: 'Regulatory Data\nManagement',
                  icon: Shield,
                },
                { name: 'Audit Logs', icon: FileText },
                { name: 'Platform Health', icon: Bell },
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
                    title={item.name}
                  >
                    <Icon
                      className={`w-4 h-4 shrink-0 ${
                        isActive ? 'text-amber-400' : 'text-slate-400'
                      }`}
                    />
                    {isSidebarOpen && (
                      <span className="truncate whitespace-pre-line text-left leading-tight">
                        {item.displayName || item.name}
                      </span>
                    )}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Sidebar Footer */}
          {isSidebarOpen && (
            <div className="pt-4 border-t border-slate-800/80 px-2 space-y-3 text-left">
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <span>All systems operational</span>
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-400">
                  FinRegTech ShipYard
                </p>
                <p className="text-[11px] font-mono text-slate-500">
                  Prototype · September 2026
                </p>
              </div>
              <button
                type="button"
                onClick={() => {
                  logoutUser();
                  if (onSignOut) onSignOut();
                }}
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-amber-400 cursor-pointer transition-colors pt-1"
              >
                <span>←</span>
                <span>Logout</span>
              </button>
            </div>
          )}
        </aside>

        {/* MAIN CONTENT AREA */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto max-w-7xl mx-auto w-full">
          {/* TAB 1: DASHBOARD VIEW matching uploaded Images 1, 2, 3 */}
          {activeTab === 'Dashboard' && (
            <div className="space-y-6 sm:space-y-8 animate-fadeIn text-left">
              {/* Header Titles matching Image 1 */}
              <div>
                <span className="text-[11px] font-mono font-bold tracking-widest text-slate-500 uppercase block mb-1">
                  GLOBAL ADMIN · PROTOTYPE DATA
                </span>
                <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
                  Welcome, Administrator
                </h1>
                <p className="text-xs sm:text-sm text-slate-400 mt-2 font-normal leading-relaxed max-w-4xl">
                  Platform Overview for the single application-wide Admin role. Project ownership and confidential project content remain separately permissioned.
                </p>
              </div>

              {/* 6 Metric Stat Cards (2 rows of 3) matching Image 1 */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                {metricCards.map((metric, idx) => (
                  <div
                    key={idx}
                    className="rounded-2xl border border-slate-800/90 bg-[#16181d] p-5 sm:p-6 shadow-lg flex flex-col justify-between"
                  >
                    <span className="text-xs text-slate-400 font-medium">
                      {metric.title}
                    </span>
                    <div className="my-2.5">
                      <span className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
                        {metric.val}
                      </span>
                    </div>
                    <span className="text-xs text-slate-500 font-normal">
                      {metric.subtitle}
                    </span>
                  </div>
                ))}
              </div>

              {/* Middle Section (2x2 Grid) matching Image 2 */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* 1. Recent Platform Activity */}
                <div className="rounded-2xl border border-slate-800/90 bg-[#16181d] p-6 shadow-lg">
                  <h2 className="text-base sm:text-lg font-bold tracking-tight text-white pb-4 border-b border-slate-800/80 mb-4">
                    Recent Platform Activity
                  </h2>
                  <div className="divide-y divide-slate-800/60">
                    {recentPlatformActivity.map((act, idx) => (
                      <div key={idx} className="flex items-center gap-4 py-3 first:pt-0 last:pb-0">
                        <span className="font-mono text-xs font-semibold text-amber-400 w-12 shrink-0">
                          {act.time}
                        </span>
                        <span className="text-xs sm:text-sm text-slate-200 font-medium">
                          {act.text}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 2. Recent User Registrations */}
                <div className="rounded-2xl border border-slate-800/90 bg-[#16181d] p-6 shadow-lg">
                  <h2 className="text-base sm:text-lg font-bold tracking-tight text-white pb-4 border-b border-slate-800/80 mb-4">
                    Recent User Registrations
                  </h2>
                  <div className="divide-y divide-slate-800/60">
                    {recentUserRegistrations.map((reg, idx) => (
                      <div key={idx} className="flex items-center gap-4 py-3 first:pt-0 last:pb-0">
                        <span className="font-mono text-xs font-semibold text-amber-400 w-16 shrink-0 uppercase">
                          {reg.date}
                        </span>
                        <span className="text-xs sm:text-sm text-slate-200 font-medium">
                          {reg.text}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 3. Project Status Overview */}
                <div className="rounded-2xl border border-slate-800/90 bg-[#16181d] p-6 shadow-lg">
                  <h2 className="text-base sm:text-lg font-bold tracking-tight text-white pb-4 border-b border-slate-800/80 mb-4">
                    Project Status Overview
                  </h2>
                  <div className="divide-y divide-slate-800/60">
                    {projectStatusOverview.map((item, idx) => (
                      <div key={idx} className="flex items-center gap-4 py-3 first:pt-0 last:pb-0">
                        <span className="font-mono text-xs font-bold text-amber-400 w-10 shrink-0">
                          {item.count}
                        </span>
                        <span className="text-xs sm:text-sm text-slate-200 font-medium">
                          {item.label}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 4. Recent Access Changes */}
                <div className="rounded-2xl border border-slate-800/90 bg-[#16181d] p-6 shadow-lg">
                  <h2 className="text-base sm:text-lg font-bold tracking-tight text-white pb-4 border-b border-slate-800/80 mb-4">
                    Recent Access Changes
                  </h2>
                  <div className="divide-y divide-slate-800/60">
                    {recentAccessChanges.map((change, idx) => (
                      <div key={idx} className="flex items-center gap-4 py-3 first:pt-0 last:pb-0">
                        <span className="font-mono text-[10px] font-bold text-amber-400 tracking-wider uppercase w-14 shrink-0">
                          {change.tag}
                        </span>
                        <span className="text-xs sm:text-sm text-slate-200 font-medium">
                          {change.text}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Bottom Section (Security Alerts & Quick Actions) matching Image 3 */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Left Card: Security Alerts */}
                <div className="rounded-2xl border border-slate-800/90 bg-[#16181d] p-6 shadow-lg flex flex-col justify-between">
                  <div>
                    <span className="text-[10px] font-mono font-bold tracking-widest text-slate-500 uppercase block mb-1">
                      SECURITY ALERTS · SAMPLE MONITORING
                    </span>
                    <h2 className="text-base sm:text-lg font-bold tracking-tight text-white mb-6">
                      2 alerts require attention
                    </h2>

                    <div className="divide-y divide-slate-800/60">
                      {securityAlerts.map((alert, idx) => (
                        <div
                          key={idx}
                          className="flex items-center justify-between gap-4 py-4 first:pt-0 last:pb-0"
                        >
                          <div className="flex items-center gap-3 min-w-0">
                            <span className="font-mono text-[10px] font-bold text-amber-400 tracking-wider uppercase shrink-0">
                              {alert.tag}
                            </span>
                            <span className="text-xs sm:text-sm font-semibold text-white truncate">
                              {alert.description}
                            </span>
                          </div>
                          <button
                            type="button"
                            onClick={() => {
                              showToast(`Reviewing alert: ${alert.description}`);
                              setActiveTab('Audit Logs');
                            }}
                            className="px-3.5 py-1.5 rounded-md border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-200 text-xs font-semibold cursor-pointer transition-colors shrink-0"
                          >
                            Review
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Right Card: Quick Actions */}
                <div className="rounded-2xl border border-slate-800/90 bg-[#16181d] p-6 shadow-lg">
                  <span className="text-[10px] font-mono font-bold tracking-widest text-slate-500 uppercase block mb-1">
                    QUICK ACTIONS
                  </span>
                  <h2 className="text-base sm:text-lg font-bold tracking-tight text-white mb-6">
                    Platform administration
                  </h2>

                  {/* 5 Quick Action Buttons with slight curvature (rounded-md) */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                    <button
                      type="button"
                      onClick={() => setActiveTab('User Management')}
                      className="px-4 py-3 rounded-md border border-slate-800 bg-[#111216] hover:bg-slate-800/60 hover:border-slate-700 text-left transition-colors flex items-center justify-between cursor-pointer group"
                    >
                      <span className="text-xs sm:text-sm font-semibold text-slate-200 group-hover:text-white">
                        View Users
                      </span>
                      <span className="text-slate-400 group-hover:text-amber-400 transition-colors">
                        →
                      </span>
                    </button>

                    <button
                      type="button"
                      onClick={() => setActiveTab('Roles & Permissions')}
                      className="px-4 py-3 rounded-md border border-slate-800 bg-[#111216] hover:bg-slate-800/60 hover:border-slate-700 text-left transition-colors flex items-center justify-between cursor-pointer group"
                    >
                      <span className="text-xs sm:text-sm font-semibold text-slate-200 group-hover:text-white leading-tight">
                        Review Roles &amp;<br className="hidden sm:inline" /> Permissions
                      </span>
                      <span className="text-slate-400 group-hover:text-amber-400 transition-colors">
                        →
                      </span>
                    </button>

                    <button
                      type="button"
                      onClick={() => setActiveTab('Project Oversight')}
                      className="px-4 py-3 rounded-md border border-slate-800 bg-[#111216] hover:bg-slate-800/60 hover:border-slate-700 text-left transition-colors flex items-center justify-between cursor-pointer group"
                    >
                      <span className="text-xs sm:text-sm font-semibold text-slate-200 group-hover:text-white">
                        Monitor Projects
                      </span>
                      <span className="text-slate-400 group-hover:text-amber-400 transition-colors">
                        →
                      </span>
                    </button>

                    <button
                      type="button"
                      onClick={() => setActiveTab('Audit Logs')}
                      className="px-4 py-3 rounded-md border border-slate-800 bg-[#111216] hover:bg-slate-800/60 hover:border-slate-700 text-left transition-colors flex items-center justify-between cursor-pointer group"
                    >
                      <span className="text-xs sm:text-sm font-semibold text-slate-200 group-hover:text-white">
                        Review Audit Logs
                      </span>
                      <span className="text-slate-400 group-hover:text-amber-400 transition-colors">
                        →
                      </span>
                    </button>

                    <button
                      type="button"
                      onClick={() => setActiveTab('Regulatory Data Management')}
                      className="px-4 py-3 rounded-md border border-slate-800 bg-[#111216] hover:bg-slate-800/60 hover:border-slate-700 text-left transition-colors flex items-center justify-between cursor-pointer group sm:col-span-1"
                    >
                      <span className="text-xs sm:text-sm font-semibold text-slate-200 group-hover:text-white">
                        Manage Regulatory<br className="hidden sm:inline" /> Sources
                      </span>
                      <span className="text-slate-400 group-hover:text-amber-400 transition-colors">
                        →
                      </span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: USER MANAGEMENT matching media_1791982823780_dc3deb23.png & media_1791982833596_f62fc301.png */}
          {activeTab === 'User Management' && (
            <div className="space-y-6 animate-fadeIn text-left">
              {/* Header Titles matching Image 1 */}
              <div>
                <span className="text-[11px] font-mono font-bold tracking-widest text-slate-500 uppercase block mb-1">
                  GLOBAL ADMIN
                </span>
                <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
                  User Management
                </h1>
                <p className="text-xs sm:text-sm text-slate-400 mt-2 font-normal leading-relaxed max-w-4xl">
                  Search and manage authorized platform accounts. The first Admin is company-provisioned; there is no public Admin registration.
                </p>
              </div>

              {/* Search & Filter Bar matching Image 1 */}
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
                <div className="relative flex-1">
                  <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                  <input
                    type="text"
                    value={searchUserQuery}
                    onChange={(e) => setSearchUserQuery(e.target.value)}
                    placeholder="Search users by name or email"
                    className="w-full pl-10 pr-4 py-2.5 rounded-md bg-[#121316] border border-slate-800 text-xs sm:text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500/80 transition-colors"
                  />
                </div>

                <div className="relative">
                  <select
                    value={selectedRoleFilter}
                    onChange={(e) => setSelectedRoleFilter(e.target.value)}
                    className="w-full sm:w-auto px-4 py-2.5 rounded-md bg-[#121316] border border-slate-800 text-xs sm:text-sm text-slate-200 focus:outline-none focus:border-amber-500/80 appearance-none pr-9 cursor-pointer transition-colors"
                  >
                    <option value="All roles">All roles</option>
                    <option value="Builder">Builder</option>
                    <option value="Advisor">Advisor</option>
                    <option value="Admin">Admin</option>
                  </select>
                  <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                </div>

                <div className="relative">
                  <select
                    value={selectedStatusFilter}
                    onChange={(e) => setSelectedStatusFilter(e.target.value)}
                    className="w-full sm:w-auto px-4 py-2.5 rounded-md bg-[#121316] border border-slate-800 text-xs sm:text-sm text-slate-200 focus:outline-none focus:border-amber-500/80 appearance-none pr-9 cursor-pointer transition-colors"
                  >
                    <option value="All statuses">All statuses</option>
                    <option value="Active">Active</option>
                    <option value="Inactive">Inactive</option>
                  </select>
                  <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                </div>
              </div>

              {/* Status Banner matching Image 1 */}
              {showStatusRecordedBanner && (
                <div className="bg-[#0c2417] border border-emerald-800/60 rounded-xl p-3 sm:p-3.5 flex items-center gap-3 shadow-md">
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-950/80 text-emerald-400 border border-emerald-700/50 shrink-0">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                    <span>Recorded</span>
                  </span>
                  <span className="text-xs sm:text-sm font-medium text-emerald-300/90">
                    Account status updated and recorded in the audit log.
                  </span>
                </div>
              )}

              {/* Users Table matching Images 1 & 2 */}
              <div className="rounded-2xl border border-slate-800/90 bg-[#131519] shadow-lg overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs sm:text-sm border-collapse min-w-[780px]">
                    <thead>
                      <tr className="border-b border-slate-800/80 text-[10px] font-mono font-bold uppercase tracking-wider text-slate-500">
                        <th className="py-3 px-4">USER</th>
                        <th className="py-3 px-4">EMAIL</th>
                        <th className="py-3 px-4">ASSIGNED ROLE</th>
                        <th className="py-3 px-4">ACCOUNT STATUS</th>
                        <th className="py-3 px-4">REGISTRATION DATE</th>
                        <th className="py-3 px-4">LAST LOGIN</th>
                        <th className="py-3 px-4 text-right">ACTIONS</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-medium">
                      {filteredUsers.map((user) => (
                        <tr key={user.id} className="hover:bg-slate-800/20 transition-colors">
                          <td className="py-4 px-4 font-bold text-white text-sm">
                            {user.name}
                          </td>
                          <td className="py-4 px-4 text-slate-400 font-medium text-xs sm:text-sm">
                            {user.email}
                          </td>
                          <td className="py-4 px-4 text-slate-300 font-medium text-xs sm:text-sm">
                            {user.role}
                          </td>
                          <td className="py-4 px-4">
                            {user.status === 'Active' ? (
                              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#12281b] border border-emerald-800/50 text-emerald-400">
                                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                                <span>Active</span>
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#2a1414] border border-rose-800/50 text-rose-400">
                                <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
                                <span>Inactive</span>
                              </span>
                            )}
                          </td>
                          <td className="py-4 px-4 text-slate-400 font-mono text-xs">
                            {user.registered}
                          </td>
                          <td className="py-4 px-4 text-slate-300 text-xs sm:text-sm">
                            {user.lastLogin}
                          </td>
                          <td className="py-4 px-4 text-right">
                            <div className="flex items-center justify-end gap-3">
                              <button
                                type="button"
                                onClick={() => showToast(`Viewing profile details for ${user.name}`)}
                                className="text-xs sm:text-sm font-semibold text-slate-300 hover:text-white transition-colors cursor-pointer"
                              >
                                View Details
                              </button>
                              {user.status === 'Active' ? (
                                <button
                                  type="button"
                                  onClick={() => setDeactivatingUser(user)}
                                  className="px-3.5 py-1.5 rounded-md border border-rose-800/80 bg-rose-950/30 hover:bg-rose-900/40 text-rose-300 text-xs font-semibold cursor-pointer transition-colors"
                                >
                                  Deactivate
                                </button>
                              ) : (
                                <button
                                  type="button"
                                  onClick={() => {
                                    handleToggleStatus(user.id);
                                    showToast(`Account activated for ${user.name}`);
                                  }}
                                  className="px-3.5 py-1.5 rounded-md border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-200 text-xs font-semibold cursor-pointer transition-colors"
                                >
                                  Activate
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: ROLES & PERMISSIONS matching media_1791983409533_20735f7a.png */}
          {activeTab === 'Roles & Permissions' && (
            <div className="space-y-6 animate-fadeIn text-left">
              {/* Header Titles matching Image 1 */}
              <div>
                <span className="text-[11px] font-mono font-bold tracking-widest text-slate-500 uppercase block mb-1">
                  LEAST-PRIVILEGE ACCESS
                </span>
                <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
                  Roles &amp; Permissions
                </h1>
                <p className="text-xs sm:text-sm text-slate-400 mt-2 font-normal leading-relaxed max-w-4xl">
                  Platform roles are centrally assigned and administrative changes are audited.
                </p>
              </div>

              {/* Roles Table Card matching Image 1 */}
              <div className="rounded-2xl border border-slate-800/90 bg-[#131519] shadow-lg overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs sm:text-sm border-collapse min-w-[780px]">
                    <thead>
                      <tr className="border-b border-slate-800/80 text-[10px] font-mono font-bold uppercase tracking-wider text-slate-500">
                        <th className="py-3 px-4">ROLE</th>
                        <th className="py-3 px-4">PERMITTED ACTIONS</th>
                        <th className="py-3 px-4">ACCESS BOUNDARY</th>
                        <th className="py-3 px-4">STATUS</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-medium">
                      {/* Builder */}
                      <tr className="hover:bg-slate-800/20 transition-colors">
                        <td className="py-4 px-4 font-bold text-white text-sm">
                          Builder
                        </td>
                        <td className="py-4 px-4 text-slate-300 font-medium text-xs sm:text-sm">
                          Owned projects; invite max 2 advisors;
                        </td>
                        <td className="py-4 px-4 text-slate-300 font-medium text-xs sm:text-sm">
                          No platform administration
                        </td>
                        <td className="py-4 px-4">
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#12281b] border border-emerald-800/50 text-emerald-400">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                            <span>Active definition</span>
                          </span>
                        </td>
                      </tr>

                      {/* Advisor */}
                      <tr className="hover:bg-slate-800/20 transition-colors">
                        <td className="py-4 px-4 font-bold text-white text-sm">
                          Advisor
                        </td>
                        <td className="py-4 px-4 text-slate-300 font-medium text-xs sm:text-sm">
                          Assigned projects; permitted requirem
                        </td>
                        <td className="py-4 px-4 text-slate-300 font-medium text-xs sm:text-sm">
                          No ownership or Builder decisions
                        </td>
                        <td className="py-4 px-4">
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#12281b] border border-emerald-800/50 text-emerald-400">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                            <span>Active definition</span>
                          </span>
                        </td>
                      </tr>

                      {/* Admin */}
                      <tr className="hover:bg-slate-800/20 transition-colors">
                        <td className="py-4 px-4 font-bold text-white text-sm">
                          Admin
                        </td>
                        <td className="py-4 px-4 text-slate-300 font-medium text-xs sm:text-sm">
                          Users and roles; project metadata; invit
                        </td>
                        <td className="py-4 px-4 text-slate-300 font-medium text-xs sm:text-sm">
                          No automatic confidential document access
                        </td>
                        <td className="py-4 px-4">
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#12281b] border border-emerald-800/50 text-emerald-400">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                            <span>Active definition</span>
                          </span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                {/* Bottom Box: ADMIN ACCESS BOUNDARY matching Image 1 */}
                <div className="bg-[#241a10] border-t border-amber-800/50 p-4 sm:p-5 text-left">
                  <span className="text-[10px] font-mono font-bold tracking-widest text-[#d59336] uppercase block mb-1">
                    ADMIN ACCESS BOUNDARY
                  </span>
                  <p className="text-xs sm:text-sm text-[#dec29c] font-normal leading-relaxed">
                    Global administration does not automatically grant unrestricted access to confidential project documents, Builder decisions, or advisor submissions.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: PROJECT OVERSIGHT matching media_1791983426855_311d8b4d.png */}
          {activeTab === 'Project Oversight' && (
            <div className="space-y-6 animate-fadeIn text-left">
              {/* Header Titles matching Image 2 */}
              <div>
                <span className="text-[11px] font-mono font-bold tracking-widest text-slate-500 uppercase block mb-1">
                  PLATFORM METADATA
                </span>
                <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
                  Project Oversight
                </h1>
                <p className="text-xs sm:text-sm text-slate-400 mt-2 font-normal leading-relaxed max-w-4xl">
                  Monitor project status and access metadata without changing Builder decisions or advisor advice.
                </p>
              </div>

              {/* Search & Filter Bar matching Image 2 */}
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
                <div className="relative flex-1">
                  <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                  <input
                    type="text"
                    value={projectSearchQuery}
                    onChange={(e) => setProjectSearchQuery(e.target.value)}
                    placeholder="Search projects"
                    className="w-full pl-10 pr-4 py-2.5 rounded-md bg-[#121316] border border-slate-800 text-xs sm:text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500/80 transition-colors"
                  />
                </div>

                <div className="relative">
                  <select
                    value={projectStatusFilter}
                    onChange={(e) => setProjectStatusFilter(e.target.value)}
                    className="w-full sm:w-auto px-4 py-2.5 rounded-md bg-[#121316] border border-slate-800 text-xs sm:text-sm text-slate-200 focus:outline-none focus:border-amber-500/80 appearance-none pr-9 cursor-pointer transition-colors"
                  >
                    <option value="All statuses">All statuses</option>
                    <option value="In Progress">In Progress</option>
                    <option value="Under Review">Under Review</option>
                    <option value="Draft">Draft</option>
                  </select>
                  <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                </div>
              </div>

              {/* Projects Table matching Image 2 */}
              <div className="rounded-2xl border border-slate-800/90 bg-[#131519] shadow-lg overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs sm:text-sm border-collapse min-w-[850px]">
                    <thead>
                      <tr className="border-b border-slate-800/80 text-[10px] font-mono font-bold uppercase tracking-wider text-slate-500">
                        <th className="py-3 px-4">PROJECT</th>
                        <th className="py-3 px-4">OWNER</th>
                        <th className="py-3 px-4">STATUS</th>
                        <th className="py-3 px-4">ASSIGNED ADVISORS</th>
                        <th className="py-3 px-4">CREATION DATE</th>
                        <th className="py-3 px-4">LAST ACTIVITY</th>
                        <th className="py-3 px-4">READINESS</th>
                        <th className="py-3 px-4 text-right"></th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-medium">
                      {filteredProjects.map((proj) => (
                        <tr key={proj.id} className="hover:bg-slate-800/20 transition-colors">
                          <td className="py-4 px-4">
                            <div className="font-bold text-white text-sm">
                              {proj.name}
                            </div>
                            <div className="text-xs font-mono text-slate-500 mt-0.5">
                              {proj.id}
                            </div>
                          </td>
                          <td className="py-4 px-4 text-slate-300 font-medium text-xs sm:text-sm">
                            {proj.owner}
                          </td>
                          <td className="py-4 px-4">
                            <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${proj.statusColor}`}>
                              <span className={`w-1.5 h-1.5 rounded-full ${proj.dotColor}`} />
                              <span>{proj.status}</span>
                            </span>
                          </td>
                          <td className="py-4 px-4 text-slate-300 text-xs sm:text-sm">
                            {proj.assignedAdvisors}
                          </td>
                          <td className="py-4 px-4 text-slate-400 font-mono text-xs">
                            {proj.creationDate}
                          </td>
                          <td className="py-4 px-4 text-slate-400 font-mono text-xs">
                            {proj.lastActivity}
                          </td>
                          <td className="py-4 px-4 text-slate-300 text-xs sm:text-sm">
                            {proj.readiness}
                          </td>
                          <td className="py-4 px-4 text-right">
                            <button
                              type="button"
                              onClick={() => setSelectedProjectOverview(proj)}
                              className="text-xs sm:text-sm font-semibold text-slate-300 hover:text-white transition-colors cursor-pointer"
                            >
                              View overview
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

          {/* TAB 5: ADVISOR INVITATIONS matching media_1791998978622_11428009.png */}
          {activeTab === 'Advisor Invitations' && (
            <div className="space-y-6 animate-fadeIn text-left">
              <div>
                <span className="text-[11px] font-mono font-medium tracking-widest text-slate-500 uppercase block mb-1">
                  ADMIN MONITORING
                </span>
                <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
                  Advisor Invitations
                </h1>
                <p className="text-xs sm:text-sm text-slate-400 mt-2 font-normal max-w-3xl leading-relaxed">
                  Builders remain responsible for invitations and the two-advisor limit. Admin monitoring cannot silently accept or bypass access controls.
                </p>
              </div>

              {/* Status Filter Dropdown matching screenshot */}
              <div>
                <div className="relative inline-block w-44 sm:w-48">
                  <select
                    value={advisorInvitationStatusFilter}
                    onChange={(e) => setAdvisorInvitationStatusFilter(e.target.value)}
                    className="w-full appearance-none bg-[#111317] border border-slate-700/80 rounded-md px-3.5 py-2 pr-9 text-xs sm:text-sm text-slate-200 focus:outline-none focus:border-amber-500/80 cursor-pointer shadow-sm"
                  >
                    <option value="All statuses">All statuses</option>
                    <option value="Accepted">Accepted</option>
                    <option value="Pending">Pending</option>
                    <option value="Revoked">Revoked</option>
                    <option value="Declined">Declined</option>
                  </select>
                  <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                </div>
              </div>

              {/* Advisor Invitations Table matching screenshot */}
              <div className="rounded-xl border border-slate-800/80 bg-[#111317] overflow-hidden shadow-lg">
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="border-b border-slate-800/80 bg-transparent text-[10px] sm:text-[11px] font-mono font-medium tracking-wider text-slate-500 uppercase">
                        <th className="py-3.5 px-6 font-semibold">PROJECT</th>
                        <th className="py-3.5 px-6 font-semibold">INVITING BUILDER</th>
                        <th className="py-3.5 px-6 font-semibold">INVITED ADVISOR</th>
                        <th className="py-3.5 px-6 font-semibold">EXPERTISE</th>
                        <th className="py-3.5 px-6 font-semibold">INVITATION DATE</th>
                        <th className="py-3.5 px-6 font-semibold">STATUS</th>
                        <th className="py-3.5 px-6 font-semibold">ACCESS STATUS</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 text-xs sm:text-sm">
                      {filteredAdvisorInvitations.map((inv) => (
                        <tr key={inv.id} className="hover:bg-slate-800/20 transition-colors">
                          <td className="py-4 px-6 font-bold text-white whitespace-nowrap">
                            {inv.project}
                          </td>
                          <td className="py-4 px-6 text-slate-300 whitespace-nowrap">
                            {inv.invitingBuilder}
                          </td>
                          <td className="py-4 px-6 text-slate-300 whitespace-nowrap">
                            {inv.invitedAdvisor}
                          </td>
                          <td className="py-4 px-6 text-slate-400 whitespace-nowrap">
                            {inv.expertise}
                          </td>
                          <td className="py-4 px-6 text-slate-400 whitespace-nowrap">
                            {inv.invitationDate}
                          </td>
                          <td className="py-4 px-6 whitespace-nowrap">
                            <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border ${inv.statusBadgeClass}`}>
                              <span className={`w-1.5 h-1.5 rounded-full ${inv.statusDotClass}`} />
                              {inv.status}
                            </span>
                          </td>
                          <td className={`py-4 px-6 whitespace-nowrap ${inv.accessStatus === 'Active' ? 'text-slate-300' : 'text-slate-400'}`}>
                            {inv.accessStatus}
                          </td>
                        </tr>
                      ))}
                      {filteredAdvisorInvitations.length === 0 && (
                        <tr>
                          <td colSpan="7" className="py-8 px-6 text-center text-slate-500 font-mono text-xs">
                            No advisor invitations match the selected status filter.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* TAB 6: REGULATORY DATA MANAGEMENT matching Images 1, 2, & 3 */}
          {activeTab === 'Regulatory Data Management' && (
            <div className="space-y-6 animate-fadeIn text-left">
              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                <div>
                  <span className="text-[11px] font-mono font-medium tracking-widest text-slate-500 uppercase block mb-1">
                    SOURCE PROVENANCE
                  </span>
                  <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
                    Regulatory Data Management
                  </h1>
                  <p className="text-xs sm:text-sm text-slate-400 mt-2 font-normal max-w-3xl leading-relaxed">
                    Manage source metadata and validation workflows without representing unverified information as officially validated.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setIsAddSourceModalOpen(true)}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-md bg-[#f59e0b] hover:bg-amber-400 text-black font-semibold text-xs sm:text-sm transition-colors cursor-pointer shadow-sm self-start sm:self-auto shrink-0"
                >
                  <Plus className="w-4 h-4 stroke-[2.5]" />
                  <span>Add Source</span>
                </button>
              </div>

              {/* Horizontally scrollable sources table matching Image 1 & 2 */}
              <div className="rounded-xl border border-slate-800/80 bg-[#111317] overflow-hidden shadow-lg">
                <div className="overflow-x-auto admin-table-scrollbar">
                  <table className="w-full text-left border-collapse min-w-[1300px]">
                    <thead>
                      <tr className="border-b border-slate-800/80 bg-transparent text-[10px] sm:text-[11px] font-mono font-medium tracking-wider text-slate-500 uppercase">
                        <th className="py-3.5 px-6 font-semibold min-w-[280px]">SOURCE / DOCUMENT</th>
                        <th className="py-3.5 px-6 font-semibold min-w-[110px]">AUTHORITY</th>
                        <th className="py-3.5 px-6 font-semibold min-w-[140px]">JURISDICTION</th>
                        <th className="py-3.5 px-6 font-semibold min-w-[120px]">PUBLICATION</th>
                        <th className="py-3.5 px-6 font-semibold min-w-[160px]">VERSION</th>
                        <th className="py-3.5 px-6 font-semibold min-w-[260px]">TOPIC</th>
                        <th className="py-3.5 px-6 font-semibold min-w-[160px]">VALIDATION</th>
                        <th className="py-3.5 px-6 font-semibold min-w-[120px]">LAST UPDATED</th>
                        <th className="py-3.5 px-6 font-semibold min-w-[110px]"></th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 text-xs sm:text-sm">
                      {regulatorySources.map((src) => (
                        <tr key={src.id} className="hover:bg-slate-800/20 transition-colors">
                          <td className="py-4 px-6">
                            <p className="font-bold text-white whitespace-nowrap">{src.title}</p>
                            <p className="text-[11px] text-slate-400 font-mono mt-0.5 whitespace-nowrap">
                              {src.applicability}
                            </p>
                          </td>
                          <td className="py-4 px-6 text-slate-300 whitespace-nowrap">
                            {src.authority}
                          </td>
                          <td className="py-4 px-6 text-slate-300 whitespace-nowrap">
                            {src.jurisdiction}
                          </td>
                          <td className="py-4 px-6 text-slate-300 whitespace-nowrap font-sans">
                            {src.publication}
                          </td>
                          <td className="py-4 px-6 text-slate-300 whitespace-nowrap">
                            {src.version}
                          </td>
                          <td className="py-4 px-6 text-slate-300 whitespace-nowrap">
                            {src.topic}
                          </td>
                          <td className="py-4 px-6 whitespace-nowrap">
                            <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border ${src.statusBadgeClass}`}>
                              <span className={`w-1.5 h-1.5 rounded-full ${src.statusDotClass}`} />
                              {src.status}
                            </span>
                          </td>
                          <td className="py-4 px-6 text-slate-300 whitespace-nowrap font-sans">
                            {src.lastUpdated}
                          </td>
                          <td className="py-4 px-6 text-right whitespace-nowrap">
                            <button
                              type="button"
                              onClick={() => showToast(`Viewing source: ${src.title}`)}
                              className="text-slate-300 hover:text-white font-medium text-xs sm:text-sm transition-colors cursor-pointer"
                            >
                              View Source
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

          {/* TAB 7: AUDIT LOGS matching Image 4 (media_1791999494451_b654a5f6.png) */}
          {activeTab === 'Audit Logs' && (
            <div className="space-y-6 animate-fadeIn text-left">
              <div>
                <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
                  Audit Logs
                </h1>
                <p className="text-xs sm:text-sm text-slate-400 mt-2 font-normal max-w-3xl leading-relaxed">
                  Authorized platform audit events cannot be edited or deleted through the Admin interface.
                </p>
              </div>

              {/* Filter controls row matching Image 4 */}
              <div className="flex flex-wrap items-center gap-3">
                {/* Search Input */}
                <div className="relative flex-1 min-w-[220px] max-w-sm">
                  <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                  <input
                    type="text"
                    value={auditLogSearchQuery}
                    onChange={(e) => setAuditLogSearchQuery(e.target.value)}
                    placeholder="Filter by user or action"
                    className="w-full bg-[#111317] border border-slate-700/80 rounded-md pl-9 pr-4 py-2 text-xs sm:text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500/80 shadow-sm"
                  />
                </div>

                {/* Date Input */}
                <div className="relative w-36 sm:w-44">
                  <input
                    type="text"
                    value={auditLogDateFilter}
                    onChange={(e) => setAuditLogDateFilter(e.target.value)}
                    placeholder="dd-mm-yyyy"
                    className="w-full bg-[#111317] border border-slate-700/80 rounded-md px-3.5 py-2 pr-9 text-xs sm:text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500/80 shadow-sm"
                  />
                  <Calendar className="w-4 h-4 text-slate-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                </div>

                {/* Action Type Dropdown */}
                <div className="relative w-44 sm:w-48">
                  <select
                    value={auditLogActionTypeFilter}
                    onChange={(e) => setAuditLogActionTypeFilter(e.target.value)}
                    className="w-full appearance-none bg-[#111317] border border-slate-700/80 rounded-md px-3.5 py-2 pr-9 text-xs sm:text-sm text-slate-200 focus:outline-none focus:border-amber-500/80 cursor-pointer shadow-sm"
                  >
                    <option value="All action types">All action types</option>
                    <option value="Account deactivated">Account deactivated</option>
                    <option value="Login failure">Login failure</option>
                    <option value="Role changed">Role changed</option>
                    <option value="Invitation created">Invitation created</option>
                    <option value="Source metadata updated">Source metadata updated</option>
                  </select>
                  <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                </div>

                {/* Result Dropdown */}
                <div className="relative w-36 sm:w-40">
                  <select
                    value={auditLogResultFilter}
                    onChange={(e) => setAuditLogResultFilter(e.target.value)}
                    className="w-full appearance-none bg-[#111317] border border-slate-700/80 rounded-md px-3.5 py-2 pr-9 text-xs sm:text-sm text-slate-200 focus:outline-none focus:border-amber-500/80 cursor-pointer shadow-sm"
                  >
                    <option value="All results">All results</option>
                    <option value="Success">Success</option>
                    <option value="Blocked">Blocked</option>
                  </select>
                  <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                </div>
              </div>

              {/* Audit Logs Table matching Image 4 */}
              <div className="rounded-xl border border-slate-800/80 bg-[#111317] overflow-hidden shadow-lg">
                <div className="overflow-x-auto admin-table-scrollbar">
                  <table className="w-full text-left border-collapse min-w-[1100px]">
                    <thead>
                      <tr className="border-b border-slate-800/80 bg-transparent text-[10px] sm:text-[11px] font-mono font-medium tracking-wider text-slate-500 uppercase">
                        <th className="py-3.5 px-6 font-semibold whitespace-nowrap min-w-[160px]">TIMESTAMP</th>
                        <th className="py-3.5 px-6 font-semibold whitespace-nowrap min-w-[140px]">USER</th>
                        <th className="py-3.5 px-6 font-semibold whitespace-nowrap min-w-[180px]">ACTION</th>
                        <th className="py-3.5 px-6 font-semibold whitespace-nowrap min-w-[180px]">AFFECTED RESOURCE</th>
                        <th className="py-3.5 px-6 font-semibold whitespace-nowrap min-w-[140px]">EVENT CATEGORY</th>
                        <th className="py-3.5 px-6 font-semibold whitespace-nowrap min-w-[120px]">RESULT</th>
                        <th className="py-3.5 px-6 font-semibold whitespace-nowrap min-w-[280px]">RELEVANT DETAILS</th>
                        <th className="py-3.5 px-6 font-semibold whitespace-nowrap min-w-[100px]"></th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 text-xs sm:text-sm">
                      {filteredAuditLogs.map((log) => (
                        <tr key={log.id} className="hover:bg-slate-800/20 transition-colors">
                          <td className="py-4 px-6 text-slate-400 whitespace-nowrap font-mono text-xs">
                            {log.timestamp}
                          </td>
                          <td className="py-4 px-6 font-bold text-white whitespace-nowrap">
                            {log.user}
                          </td>
                          <td className="py-4 px-6 text-slate-300 whitespace-nowrap">
                            {log.action}
                          </td>
                          <td className="py-4 px-6 text-slate-300 whitespace-nowrap">
                            {log.affectedResource}
                          </td>
                          <td className="py-4 px-6 text-slate-400 whitespace-nowrap">
                            {log.eventCategory}
                          </td>
                          <td className="py-4 px-6 whitespace-nowrap">
                            <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border ${log.resultBadgeClass}`}>
                              <span className={`w-1.5 h-1.5 rounded-full ${log.resultDotClass}`} />
                              {log.result}
                            </span>
                          </td>
                          <td className="py-4 px-6 text-slate-300 whitespace-nowrap max-w-xs truncate">
                            {log.relevantDetails}
                          </td>
                          <td className="py-4 px-6 text-right whitespace-nowrap">
                            <button
                              type="button"
                              onClick={() => setSelectedAuditEvent(log)}
                              className="text-slate-300 hover:text-white font-medium text-xs sm:text-sm transition-colors cursor-pointer"
                            >
                              View Event
                            </button>
                          </td>
                        </tr>
                      ))}
                      {filteredAuditLogs.length === 0 && (
                        <tr>
                          <td colSpan="8" className="py-8 px-6 text-center text-slate-500 font-mono text-xs">
                            No audit log entries match the selected filters.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* TAB 8: PLATFORM HEALTH matching Images 2 & 3 (media_1792000007744_803651b7.png & media_1792000017200_afe0267c.png) */}
          {activeTab === 'Platform Health' && (
            <div className="space-y-6 animate-fadeIn text-left">
              {/* Header */}
              <div>
                <span className="text-[11px] font-mono font-medium tracking-widest text-slate-500 uppercase block mb-1">
                  PROTOTYPE MONITORING DATA
                </span>
                <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
                  Platform Health &amp; Security
                </h1>
                <p className="text-xs sm:text-sm text-slate-400 mt-2 font-normal max-w-3xl leading-relaxed">
                  Demonstration states only. This wireframe is not connected to live infrastructure or security telemetry.
                </p>
              </div>

              {/* 6 Metric Cards matching Image 2 */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                {/* 1. Platform Services */}
                <div className="rounded-xl border border-slate-800/80 bg-[#16181d] p-5 shadow-lg">
                  <span className="text-xs font-medium text-slate-400 block">
                    Platform Services
                  </span>
                  <p className="text-2xl sm:text-3xl font-mono text-white mt-3 mb-1">
                    Operational
                  </p>
                  <span className="text-xs text-slate-500 block">
                    Sample status
                  </span>
                </div>

                {/* 2. Authentication Failures */}
                <div className="rounded-xl border border-slate-800/80 bg-[#16181d] p-5 shadow-lg">
                  <span className="text-xs font-medium text-slate-400 block">
                    Authentication Failures
                  </span>
                  <p className="text-2xl sm:text-3xl font-mono font-bold text-white mt-3 mb-1">
                    07
                  </p>
                  <span className="text-xs text-slate-500 block">
                    Last 24 hours
                  </span>
                </div>

                {/* 3. Suspicious Alerts */}
                <div className="rounded-xl border border-slate-800/80 bg-[#16181d] p-5 shadow-lg">
                  <span className="text-xs font-medium text-slate-400 block">
                    Suspicious Alerts
                  </span>
                  <p className="text-2xl sm:text-3xl font-mono font-bold text-white mt-3 mb-1">
                    02
                  </p>
                  <span className="text-xs text-slate-500 block">
                    Human review required
                  </span>
                </div>

                {/* 4. Active Sessions */}
                <div className="rounded-xl border border-slate-800/80 bg-[#16181d] p-5 shadow-lg">
                  <span className="text-xs font-medium text-slate-400 block">
                    Active Sessions
                  </span>
                  <p className="text-2xl sm:text-3xl font-mono font-bold text-white mt-3 mb-1">
                    34
                  </p>
                  <span className="text-xs text-slate-500 block">
                    3 privileged sessions
                  </span>
                </div>

                {/* 5. System Errors */}
                <div className="rounded-xl border border-slate-800/80 bg-[#16181d] p-5 shadow-lg">
                  <span className="text-xs font-medium text-slate-400 block">
                    System Errors
                  </span>
                  <p className="text-2xl sm:text-3xl font-mono font-bold text-white mt-3 mb-1">
                    03
                  </p>
                  <span className="text-xs text-slate-500 block">
                    No critical outage
                  </span>
                </div>

                {/* 6. Security Events */}
                <div className="rounded-xl border border-slate-800/80 bg-[#16181d] p-5 shadow-lg">
                  <span className="text-xs font-medium text-slate-400 block">
                    Security Events
                  </span>
                  <p className="text-2xl sm:text-3xl font-mono font-bold text-white mt-3 mb-1">
                    05
                  </p>
                  <span className="text-xs text-slate-500 block">
                    Recent recorded events
                  </span>
                </div>
              </div>

              {/* 4 Bottom Cards matching Images 2 & 3 */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-2">
                {/* 1. Service Status */}
                <div className="rounded-2xl border border-slate-800/90 bg-[#16181d] p-6 shadow-lg">
                  <h2 className="text-base sm:text-lg font-bold tracking-tight text-white pb-4 border-b border-slate-800/80 mb-4">
                    Service Status
                  </h2>
                  <div className="divide-y divide-slate-800/60">
                    {[
                      { tag: 'CORE', status: 'Operational' },
                      { tag: 'AUTH', status: 'Operational' },
                      { tag: 'DATA', status: 'Operational' },
                      { tag: 'AUDIT', status: 'Operational' },
                    ].map((svc, idx) => (
                      <div key={idx} className="flex items-center gap-6 py-3.5 first:pt-0 last:pb-0">
                        <span className="font-mono text-xs font-bold text-amber-400 w-16 uppercase tracking-wider shrink-0">
                          {svc.tag}
                        </span>
                        <span className="text-xs sm:text-sm text-slate-200 font-medium">
                          {svc.status}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 2. Recent Authentication Failures */}
                <div className="rounded-2xl border border-slate-800/90 bg-[#16181d] p-6 shadow-lg">
                  <h2 className="text-base sm:text-lg font-bold tracking-tight text-white pb-4 border-b border-slate-800/80 mb-4">
                    Recent Authentication Failures
                  </h2>
                  <div className="divide-y divide-slate-800/60">
                    {[
                      { time: '15:42', text: 'Repeated invalid credentials attempt' },
                      { time: '14:38', text: 'Unknown account · generic failure' },
                      { time: '11:16', text: 'Expired session rejected' },
                    ].map((fail, idx) => (
                      <div key={idx} className="flex items-center gap-6 py-3.5 first:pt-0 last:pb-0">
                        <span className="font-mono text-xs font-bold text-amber-400 w-16 shrink-0">
                          {fail.time}
                        </span>
                        <span className="text-xs sm:text-sm text-slate-200 font-medium">
                          {fail.text}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 3. Session & Access Events */}
                <div className="rounded-2xl border border-slate-800/90 bg-[#16181d] p-6 shadow-lg">
                  <h2 className="text-base sm:text-lg font-bold tracking-tight text-white pb-4 border-b border-slate-800/80 mb-4">
                    Session &amp; Access Events
                  </h2>
                  <div className="divide-y divide-slate-800/60">
                    {[
                      { tag: 'SESSION', text: 'Privileged session expired normally' },
                      { tag: 'ACCESS', text: 'Revoked advisor access confirmed' },
                      { tag: 'ROLE', text: 'Role change required confirmation' },
                    ].map((evt, idx) => (
                      <div key={idx} className="flex items-center gap-6 py-3.5 first:pt-0 last:pb-0">
                        <span className="font-mono text-[10px] font-bold text-amber-400 tracking-wider uppercase w-16 shrink-0">
                          {evt.tag}
                        </span>
                        <span className="text-xs sm:text-sm text-slate-200 font-medium">
                          {evt.text}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 4. Security Event History */}
                <div className="rounded-2xl border border-slate-800/90 bg-[#16181d] p-6 shadow-lg">
                  <h2 className="text-base sm:text-lg font-bold tracking-tight text-white pb-4 border-b border-slate-800/80 mb-4">
                    Security Event History
                  </h2>
                  <div className="divide-y divide-slate-800/60">
                    {[
                      { tag: 'ALERT', text: 'Repeated failed Admin attempts' },
                      { tag: 'INFO', text: 'Access key rotation review due' },
                      { tag: 'ERROR', text: '3 non-critical background errors' },
                    ].map((sec, idx) => (
                      <div key={idx} className="flex items-center gap-6 py-3.5 first:pt-0 last:pb-0">
                        <span className="font-mono text-[10px] font-bold text-amber-400 tracking-wider uppercase w-16 shrink-0">
                          {sec.tag}
                        </span>
                        <span className="text-xs sm:text-sm text-slate-200 font-medium">
                          {sec.text}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 9: SETTINGS matching uploaded image (media_1792000441142_4822c8ce.png) */}
          {activeTab === 'Settings' && (
            <div className="space-y-6 animate-fadeIn text-left">
              <div>
                <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
                  Admin Settings
                </h1>
                <p className="text-xs sm:text-sm text-slate-400 mt-2 font-normal max-w-3xl leading-relaxed">
                  Account and security information for the global Admin session. Secrets are never displayed after entry.
                </p>
              </div>

              {/* Settings Card */}
              <div className="rounded-xl border border-slate-800/80 bg-[#111317] p-6 sm:p-7 shadow-lg space-y-6">
                {/* 4 Metadata Items in 2x2 grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pb-2">
                  {/* 1. Admin Profile */}
                  <div>
                    <span className="text-[10px] font-mono font-medium tracking-widest text-slate-500 uppercase block mb-1">
                      ADMIN PROFILE
                    </span>
                    <p className="text-sm font-semibold text-white">
                      Avery Patel · Global Administrator
                    </p>
                  </div>

                  {/* 2. Account Security */}
                  <div>
                    <span className="text-[10px] font-mono font-medium tracking-widest text-slate-500 uppercase block mb-1">
                      ACCOUNT SECURITY
                    </span>
                    <p className="text-sm text-slate-300">
                      Company-provisioned Admin role · Additional key verified by backend
                    </p>
                  </div>

                  {/* 3. Session Information */}
                  <div>
                    <span className="text-[10px] font-mono font-medium tracking-widest text-slate-500 uppercase block mb-1">
                      SESSION INFORMATION
                    </span>
                    <p className="text-sm text-slate-300">
                      Privileged session · Expires after inactivity
                    </p>
                  </div>

                  {/* 4. Admin Access Key */}
                  <div>
                    <span className="text-[10px] font-mono font-medium tracking-widest text-slate-500 uppercase block mb-1">
                      ADMIN ACCESS KEY
                    </span>
                    <p className="text-sm text-slate-300">
                      Not displayed or stored in this interface
                    </p>
                  </div>
                </div>

                {/* Notification preferences dropdown */}
                <div>
                  <label className="block text-xs sm:text-sm text-slate-300 font-medium mb-2">
                    Notification preferences
                  </label>
                  <div className="relative">
                    <select
                      value={adminNotificationPref}
                      onChange={(e) => {
                        setAdminNotificationPref(e.target.value);
                        showToast(`Notification preference set to: ${e.target.value}`);
                      }}
                      className="w-full appearance-none bg-[#111317] border border-slate-700/80 rounded-md px-4 py-2.5 pr-10 text-xs sm:text-sm text-slate-200 focus:outline-none focus:border-amber-500/80 cursor-pointer shadow-sm"
                    >
                      <option value="Essential Admin alerts">Essential Admin alerts</option>
                      <option value="All platform events">All platform events</option>
                      <option value="Security & authentication alerts only">Security &amp; authentication alerts only</option>
                      <option value="Mute non-critical notifications">Mute non-critical notifications</option>
                    </select>
                    <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                  </div>
                </div>

                {/* Key Rotation / Revocation box */}
                <div className="rounded-md bg-[#251b0f] border border-amber-900/60 p-5 text-left">
                  <span className="text-[10px] font-mono font-bold tracking-widest text-amber-500/90 uppercase block mb-2">
                    KEY ROTATION / REVOCATION
                  </span>
                  <p className="text-xs sm:text-sm text-amber-200/90 leading-relaxed mb-4">
                    Conceptual workflow only: key rotation or revocation must be performed by authorized company-controlled administration and recorded in the audit log.
                  </p>
                  <button
                    type="button"
                    onClick={() => showToast('Key rotation request submitted for authorization.')}
                    className="px-4 py-2 rounded-md bg-[#16181f] border border-slate-700 hover:border-amber-500/80 text-white text-xs sm:text-sm font-semibold cursor-pointer transition-colors shadow-sm"
                  >
                    Request key rotation
                  </button>
                </div>
              </div>

              {/* Bottom-right Logout button */}
              <div className="flex justify-end pt-2">
                <button
                  type="button"
                  onClick={() => {
                    logoutUser();
                    if (onSignOut) onSignOut();
                  }}
                  className="px-5 py-2 rounded-md bg-[#231416] border border-rose-800/80 text-rose-300 hover:bg-rose-950/60 hover:text-rose-200 text-xs sm:text-sm font-semibold transition-colors cursor-pointer shadow-sm"
                >
                  Logout
                </button>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* DEACTIVATE CONFIRMATION MODAL matching Image 3 (media_1791982900934_5d51a9c2.png) */}
      {deactivatingUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fadeIn">
          <div className="rounded-2xl border border-slate-700/80 bg-[#16181f] max-w-lg w-full p-6 sm:p-7 shadow-2xl animate-scaleIn text-left">
            {/* Header: Title & Close Button */}
            <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
              <h3 className="text-base sm:text-lg font-bold text-white tracking-tight">
                Confirm Administrative Change
              </h3>
              <button
                type="button"
                onClick={() => setDeactivatingUser(null)}
                className="text-xs font-semibold text-slate-400 hover:text-slate-200 cursor-pointer transition-colors"
              >
                Close
              </button>
            </div>

            {/* Body */}
            <div className="py-6">
              <p className="text-xs sm:text-sm text-slate-300 font-normal leading-relaxed">
                Confirm the account status change for {deactivatingUser.name}. This action will be recorded in the platform audit log.
              </p>
            </div>

            {/* Actions: Cancel & Confirm change */}
            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setDeactivatingUser(null)}
                className="px-4 py-2 rounded-md border border-slate-700 bg-[#1e222a] hover:bg-slate-700 text-slate-200 text-xs sm:text-sm font-semibold cursor-pointer transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => handleConfirmDeactivate(deactivatingUser.id)}
                className="px-4 py-2 rounded-md border border-rose-800/80 bg-[#351a1a] hover:bg-rose-900/60 text-rose-300 text-xs sm:text-sm font-semibold cursor-pointer transition-colors shadow-md"
              >
                Confirm change
              </button>
            </div>
          </div>
        </div>
      )}

      {/* PROJECT OVERVIEW MODAL matching Image 3 (media_1791983439586_56d2549b.png) */}
      {selectedProjectOverview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fadeIn">
          <div className="rounded-2xl border border-slate-700/80 bg-[#16181f] max-w-lg w-full p-6 sm:p-7 shadow-2xl animate-scaleIn text-left">
            {/* Header: Title & Close Button */}
            <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
              <h3 className="text-base sm:text-lg font-bold text-white tracking-tight">
                Project Overview
              </h3>
              <button
                type="button"
                onClick={() => setSelectedProjectOverview(null)}
                className="text-xs font-semibold text-slate-400 hover:text-slate-200 cursor-pointer transition-colors"
              >
                Close
              </button>
            </div>

            {/* Content matching Image 3 */}
            <div className="py-6 space-y-5">
              <h2 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight">
                {selectedProjectOverview.name}
              </h2>

              <div>
                <span className="text-[10px] font-mono font-bold tracking-widest text-slate-500 uppercase block mb-1">
                  OWNER
                </span>
                <p className="text-sm font-semibold text-white">
                  {selectedProjectOverview.owner}
                </p>
              </div>

              <div>
                <span className="text-[10px] font-mono font-bold tracking-widest text-slate-500 uppercase block mb-1">
                  PROJECT STATUS
                </span>
                <p className="text-sm font-semibold text-white">
                  {selectedProjectOverview.status}
                </p>
              </div>

              <div>
                <span className="text-[10px] font-mono font-bold tracking-widest text-slate-500 uppercase block mb-1">
                  ACCESS BOUNDARY
                </span>
                <p className="text-xs sm:text-sm text-slate-300 font-normal leading-relaxed">
                  {selectedProjectOverview.accessBoundary ||
                    'Metadata visibility only; restricted content requires explicit authorization.'}
                </p>
              </div>

              {/* Big Gold Close Button with slight curve (rounded-md) */}
              <button
                type="button"
                onClick={() => setSelectedProjectOverview(null)}
                className="w-full py-3 px-4 rounded-md bg-[#e59b38] hover:bg-[#d68a27] text-slate-950 font-bold text-xs sm:text-sm transition-all cursor-pointer shadow-md mt-6 active:scale-[0.99]"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ADD REGULATORY SOURCE MODAL matching Image 3 (media_1791999368286_8da461eb.png) */}
      {isAddSourceModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fadeIn">
          <div className="bg-[#16181d] border border-slate-700/80 rounded-xl w-full max-w-xl shadow-2xl p-6 relative animate-fadeIn text-left">
            {/* Header */}
            <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-5">
              <h3 className="text-base sm:text-lg font-bold text-white tracking-tight">
                Add Regulatory Source
              </h3>
              <button
                type="button"
                onClick={() => setIsAddSourceModalOpen(false)}
                className="text-xs text-slate-400 hover:text-white transition-colors cursor-pointer font-medium"
              >
                Close
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleAddSource} className="space-y-4">
              {/* Source or document title */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Source or document title
                </label>
                <input
                  type="text"
                  value={newSourceForm.title}
                  onChange={(e) =>
                    setNewSourceForm({ ...newSourceForm, title: e.target.value })
                  }
                  placeholder="Document title"
                  className="w-full bg-[#111216] border border-slate-700/80 rounded-md px-3.5 py-2.5 text-xs sm:text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500/80"
                  required
                />
              </div>

              {/* Issuing authority */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Issuing authority
                </label>
                <input
                  type="text"
                  value={newSourceForm.authority}
                  onChange={(e) =>
                    setNewSourceForm({ ...newSourceForm, authority: e.target.value })
                  }
                  placeholder="Authority"
                  className="w-full bg-[#111216] border border-slate-700/80 rounded-md px-3.5 py-2.5 text-xs sm:text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500/80"
                />
              </div>

              {/* Row: Jurisdiction & Publication date */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">
                    Jurisdiction
                  </label>
                  <input
                    type="text"
                    value={newSourceForm.jurisdiction}
                    onChange={(e) =>
                      setNewSourceForm({ ...newSourceForm, jurisdiction: e.target.value })
                    }
                    placeholder="Jurisdiction"
                    className="w-full bg-[#111216] border border-slate-700/80 rounded-md px-3.5 py-2.5 text-xs sm:text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500/80"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">
                    Publication date
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      value={newSourceForm.publicationDate}
                      onChange={(e) =>
                        setNewSourceForm({ ...newSourceForm, publicationDate: e.target.value })
                      }
                      placeholder="dd-mm-yyyy"
                      className="w-full bg-[#111216] border border-slate-700/80 rounded-md px-3.5 py-2.5 pr-9 text-xs sm:text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500/80"
                    />
                    <Calendar className="w-4 h-4 text-slate-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                  </div>
                </div>
              </div>

              {/* Row: Version & Topic */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">
                    Version
                  </label>
                  <input
                    type="text"
                    value={newSourceForm.version}
                    onChange={(e) =>
                      setNewSourceForm({ ...newSourceForm, version: e.target.value })
                    }
                    placeholder="Version"
                    className="w-full bg-[#111216] border border-slate-700/80 rounded-md px-3.5 py-2.5 text-xs sm:text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500/80"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">
                    Topic
                  </label>
                  <input
                    type="text"
                    value={newSourceForm.topic}
                    onChange={(e) =>
                      setNewSourceForm({ ...newSourceForm, topic: e.target.value })
                    }
                    placeholder="Topic"
                    className="w-full bg-[#111216] border border-slate-700/80 rounded-md px-3.5 py-2.5 text-xs sm:text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500/80"
                  />
                </div>
              </div>

              {/* Applicability */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Applicability
                </label>
                <textarea
                  rows={3}
                  value={newSourceForm.applicability}
                  onChange={(e) =>
                    setNewSourceForm({ ...newSourceForm, applicability: e.target.value })
                  }
                  placeholder="Human-reviewed applicability notes"
                  className="w-full bg-[#111216] border border-slate-700/80 rounded-md p-3 text-xs sm:text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500/80 resize-none"
                />
              </div>

              {/* Modal Actions */}
              <div className="flex items-center justify-end gap-3 pt-3">
                <button
                  type="button"
                  onClick={() => setIsAddSourceModalOpen(false)}
                  className="px-4 py-2 rounded-md text-xs sm:text-sm font-medium text-slate-300 hover:text-white hover:bg-slate-800 transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-md text-xs sm:text-sm font-semibold text-black bg-[#f59e0b] hover:bg-amber-400 transition-colors cursor-pointer shadow-sm"
                >
                  Add as Pending Validation
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* AUDIT EVENT DETAILS MODAL matching Image 1 (media_1791999970886_8eac6b2b.png) */}
      {selectedAuditEvent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fadeIn">
          <div className="bg-[#16181f] border border-slate-700/80 rounded-xl w-full max-w-lg shadow-2xl p-6 sm:p-7 relative animate-fadeIn text-left space-y-4">
            <div className="border-b border-slate-800/80 pb-3">
              <span className="text-[10px] font-mono font-bold tracking-widest text-slate-500 uppercase block mb-1">
                USER
              </span>
              <p className="text-sm font-semibold text-white">
                {selectedAuditEvent.user}
              </p>
            </div>

            <div className="border-b border-slate-800/80 pb-3">
              <span className="text-[10px] font-mono font-bold tracking-widest text-slate-500 uppercase block mb-1">
                ACTION
              </span>
              <p className="text-sm font-semibold text-white">
                {selectedAuditEvent.action}
              </p>
            </div>

            <div className="border-b border-slate-800/80 pb-3">
              <span className="text-[10px] font-mono font-bold tracking-widest text-slate-500 uppercase block mb-1">
                AFFECTED RESOURCE
              </span>
              <p className="text-sm font-semibold text-white">
                {selectedAuditEvent.affectedResource}
              </p>
            </div>

            <div className="border-b border-slate-800/80 pb-3">
              <span className="text-[10px] font-mono font-bold tracking-widest text-slate-500 uppercase block mb-1">
                CATEGORY
              </span>
              <p className="text-sm font-semibold text-white">
                {selectedAuditEvent.eventCategory}
              </p>
            </div>

            <div className="border-b border-slate-800/80 pb-3">
              <span className="text-[10px] font-mono font-bold tracking-widest text-slate-500 uppercase block mb-1">
                RESULT
              </span>
              <p className="text-sm font-semibold text-white">
                {selectedAuditEvent.result}
              </p>
            </div>

            <div className="border-b border-slate-800/80 pb-3">
              <span className="text-[10px] font-mono font-bold tracking-widest text-slate-500 uppercase block mb-1">
                DETAILS
              </span>
              <p className="text-sm font-semibold text-white">
                {selectedAuditEvent.relevantDetails}
              </p>
            </div>

            <p className="text-xs text-slate-400 pt-1 font-normal">
              This audit event is read-only.
            </p>

            {/* Big Yellow/Gold Close Button matching Image 1 */}
            <button
              type="button"
              onClick={() => setSelectedAuditEvent(null)}
              className="w-full py-3 px-4 rounded-md bg-[#e59b38] hover:bg-[#d68a27] text-slate-950 font-bold text-xs sm:text-sm transition-all cursor-pointer shadow-md mt-4 active:scale-[0.99]"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
