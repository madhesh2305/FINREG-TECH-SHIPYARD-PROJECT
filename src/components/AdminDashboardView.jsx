import React, { useState, useEffect } from 'react';
import {
  Users,
  ShieldAlert,
  FolderKanban,
  FileCheck2,
  Activity,
  LogOut,
  CheckCircle2,
  XCircle,
  Search,
  ExternalLink,
  Shield,
  UserCheck,
  UserX,
  RefreshCw,
  AlertTriangle
} from 'lucide-react';
import { logoutUser } from '../services/authService';
import { getAdminStats, getAdminUsers, updateUserStatus, getAdminAuditEvents } from '../services/adminService';
import { getRegulatorySources } from '../services/regulatoryService';

export default function AdminDashboardView({ isDarkMode = true, onSignOut }) {
  const [currentUser] = useState(() => {
    try {
      const raw = localStorage.getItem('currentUser');
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  });

  const [activeTab, setActiveTab] = useState('users'); // 'users' | 'regulatory' | 'audit'

  // Independent state tracking for each live dashboard data source (DEF-03 & DEF-17)
  const [statsState, setStatsState] = useState({ data: null, loading: true, error: null });
  const [usersState, setUsersState] = useState({ data: [], loading: true, error: null });
  const [sourcesState, setSourcesState] = useState({ data: [], loading: true, error: null });
  const [auditState, setAuditState] = useState({ data: [], loading: true, error: null });

  const [searchQuery, setSearchQuery] = useState('');
  const [toastMessage, setToastMessage] = useState(null);

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const fetchStats = async () => {
    setStatsState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await getAdminStats();
      setStatsState({ data, loading: false, error: null });
    } catch (err) {
      setStatsState({ data: null, loading: false, error: err.message || 'Failed to load platform metrics' });
    }
  };

  const fetchUsers = async () => {
    setUsersState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await getAdminUsers();
      setUsersState({ data: Array.isArray(data) ? data : [], loading: false, error: null });
    } catch (err) {
      setUsersState({ data: [], loading: false, error: err.message || 'Failed to load registered users' });
    }
  };

  const fetchSources = async () => {
    setSourcesState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await getRegulatorySources();
      setSourcesState({ data: Array.isArray(data) ? data : [], loading: false, error: null });
    } catch (err) {
      setSourcesState({ data: [], loading: false, error: err.message || 'Failed to load regulatory sources' });
    }
  };

  const fetchAudit = async () => {
    setAuditState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await getAdminAuditEvents();
      setAuditState({ data: Array.isArray(data) ? data : [], loading: false, error: null });
    } catch (err) {
      setAuditState({ data: [], loading: false, error: err.message || 'Failed to load audit events' });
    }
  };

  const loadAllData = () => {
    fetchStats();
    fetchUsers();
    fetchSources();
    fetchAudit();
  };

  useEffect(() => {
    loadAllData();
  }, []);

  const handleToggleStatus = async (user) => {
    try {
      const uid = user.user_id || user.id;
      const updated = await updateUserStatus(uid, !user.is_active);
      setUsersState((prev) => ({
        ...prev,
        data: prev.data.map((u) => ((u.user_id === user.user_id || u.id === user.id) ? { ...u, is_active: updated.is_active } : u)),
      }));
      showToast(`User ${user.email} status updated to ${updated.is_active ? 'ACTIVE' : 'DEACTIVATED'}`);
    } catch (err) {
      showToast(err.message || 'Failed to update user status');
    }
  };

  const filteredUsers = usersState.data.filter(
    (u) =>
      u.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      u.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (u.platform_role && u.platform_role.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const isAnyLoading = statsState.loading || usersState.loading || sourcesState.loading || auditState.loading;

  return (
    <div className={`min-h-screen flex flex-col font-sans ${isDarkMode ? 'bg-[#121214] text-slate-100' : 'bg-[#faf8f5] text-slate-900'}`}>
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-5 right-5 z-50 flex items-center gap-2 px-4 py-3 rounded-xl bg-amber-500 text-slate-950 font-semibold shadow-2xl animate-bounce">
          <CheckCircle2 className="w-5 h-5" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Header */}
      <header className={`border-b px-6 py-4 flex items-center justify-between ${isDarkMode ? 'bg-[#161619] border-slate-800' : 'bg-white border-slate-200'}`}>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-600 to-amber-400 flex items-center justify-center font-bold text-slate-950 shadow-md">
            <Shield className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight">FinRegTech ShipYard</h1>
            <p className="text-xs text-amber-500 font-semibold tracking-wider uppercase">Platform Administration Cockpit</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-right hidden sm:block">
            <p className="text-xs font-bold text-slate-200">{currentUser?.full_name || 'FinRegTech Admin'}</p>
            <p className="text-[10px] text-slate-400">{currentUser?.email || 'admin@finregtech.io'}</p>
            <span className="inline-block mt-0.5 px-2 py-0.5 rounded text-[10px] font-extrabold bg-amber-950/80 text-amber-400 border border-amber-800/80">
              ADMINISTRATOR
            </span>
          </div>

          <button
            type="button"
            onClick={onSignOut || logoutUser}
            className="flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold bg-rose-950/40 hover:bg-rose-900/60 text-rose-300 border border-rose-800/50 transition-colors cursor-pointer"
          >
            <LogOut className="w-4 h-4" />
            <span className="hidden sm:inline">Sign Out</span>
          </button>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">
        {/* Metric Cards Grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {/* Card 1: Total Users */}
          <div className={`p-4 rounded-2xl border ${isDarkMode ? 'bg-[#161619] border-slate-800' : 'bg-white border-slate-200'}`}>
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider">Total Users</span>
              <Users className="w-4 h-4 text-amber-400" />
            </div>
            {statsState.loading ? (
              <p className="text-2xl font-extrabold text-slate-500 animate-pulse">...</p>
            ) : statsState.error ? (
              <div>
                <p className="text-xs text-rose-400 font-semibold">Load Error</p>
                <button type="button" onClick={fetchStats} className="text-[10px] text-amber-400 underline cursor-pointer">
                  Retry
                </button>
              </div>
            ) : (
              <p className="text-2xl font-extrabold text-slate-100">{statsState.data?.total_users ?? 0}</p>
            )}
            <span className="text-[11px] text-slate-400 font-medium">Registered platform users</span>
          </div>

          {/* Card 2: Active Users */}
          <div className={`p-4 rounded-2xl border ${isDarkMode ? 'bg-[#161619] border-slate-800' : 'bg-white border-slate-200'}`}>
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider">Active Users</span>
              <UserCheck className="w-4 h-4 text-emerald-400" />
            </div>
            {statsState.loading ? (
              <p className="text-2xl font-extrabold text-slate-500 animate-pulse">...</p>
            ) : statsState.error ? (
              <div>
                <p className="text-xs text-rose-400 font-semibold">Load Error</p>
                <button type="button" onClick={fetchStats} className="text-[10px] text-amber-400 underline cursor-pointer">
                  Retry
                </button>
              </div>
            ) : (
              <p className="text-2xl font-extrabold text-amber-400">{statsState.data?.active_users ?? 0}</p>
            )}
            <span className="text-[11px] text-emerald-400 font-medium">Active accounts</span>
          </div>

          {/* Card 3: Projects */}
          <div className={`p-4 rounded-2xl border ${isDarkMode ? 'bg-[#161619] border-slate-800' : 'bg-white border-slate-200'}`}>
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider">Workspaces</span>
              <FolderKanban className="w-4 h-4 text-blue-400" />
            </div>
            {statsState.loading ? (
              <p className="text-2xl font-extrabold text-slate-500 animate-pulse">...</p>
            ) : statsState.error ? (
              <div>
                <p className="text-xs text-rose-400 font-semibold">Load Error</p>
                <button type="button" onClick={fetchStats} className="text-[10px] text-amber-400 underline cursor-pointer">
                  Retry
                </button>
              </div>
            ) : (
              <p className="text-2xl font-extrabold text-slate-100">{statsState.data?.total_projects ?? 0}</p>
            )}
            <span className="text-[11px] text-slate-400 font-medium">Compliance workspaces</span>
          </div>

          {/* Card 4: Regulatory Corpus */}
          <div className={`p-4 rounded-2xl border ${isDarkMode ? 'bg-[#161619] border-slate-800' : 'bg-white border-slate-200'}`}>
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider">Regulatory Corpus</span>
              <FileCheck2 className="w-4 h-4 text-emerald-400" />
            </div>
            {statsState.loading ? (
              <p className="text-2xl font-extrabold text-slate-500 animate-pulse">...</p>
            ) : statsState.error ? (
              <div>
                <p className="text-xs text-rose-400 font-semibold">Load Error</p>
                <button type="button" onClick={fetchStats} className="text-[10px] text-amber-400 underline cursor-pointer">
                  Retry
                </button>
              </div>
            ) : (
              <p className="text-2xl font-extrabold text-slate-100">{statsState.data?.regulatory_sources_count ?? 0}</p>
            )}
            <span className="text-[11px] text-emerald-400 font-medium">Verified rule sources</span>
          </div>

          {/* Card 5: Audit Events */}
          <div className={`p-4 rounded-2xl border ${isDarkMode ? 'bg-[#161619] border-slate-800' : 'bg-white border-slate-200'}`}>
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider">Audit Trail</span>
              <Activity className="w-4 h-4 text-purple-400" />
            </div>
            {statsState.loading ? (
              <p className="text-2xl font-extrabold text-slate-500 animate-pulse">...</p>
            ) : statsState.error ? (
              <div>
                <p className="text-xs text-rose-400 font-semibold">Load Error</p>
                <button type="button" onClick={fetchStats} className="text-[10px] text-amber-400 underline cursor-pointer">
                  Retry
                </button>
              </div>
            ) : (
              <p className="text-2xl font-extrabold text-slate-100">{statsState.data?.total_audit_events ?? 0}</p>
            )}
            <span className="text-[11px] text-purple-400 font-medium">PostgreSQL Audit Log</span>
          </div>

          {/* Card 6: Security State */}
          <div className={`p-4 rounded-2xl border ${isDarkMode ? 'bg-[#161619] border-slate-800' : 'bg-white border-slate-200'}`}>
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider">Security State</span>
              <ShieldAlert className="w-4 h-4 text-emerald-400" />
            </div>
            <p className="text-xl font-bold text-slate-100">Active</p>
            <span className="text-[11px] text-slate-400 font-medium">Role & ownership policy checks</span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className={`flex items-center justify-between border-b ${isDarkMode ? 'border-slate-800' : 'border-slate-200'}`}>
          <div className="flex items-center gap-6">
            <button
              type="button"
              onClick={() => setActiveTab('users')}
              className={`py-3 text-sm font-bold border-b-2 -mb-px transition-colors cursor-pointer ${
                activeTab === 'users' ? 'border-amber-400 text-amber-400' : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              User & Role Management ({usersState.data.length})
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('regulatory')}
              className={`py-3 text-sm font-bold border-b-2 -mb-px transition-colors cursor-pointer ${
                activeTab === 'regulatory' ? 'border-amber-400 text-amber-400' : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Regulatory Corpus ({sourcesState.data.length})
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('audit')}
              className={`py-3 text-sm font-bold border-b-2 -mb-px transition-colors cursor-pointer ${
                activeTab === 'audit' ? 'border-amber-400 text-amber-400' : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Platform Audit Stream ({auditState.data.length})
            </button>
          </div>

          <button
            type="button"
            onClick={loadAllData}
            title="Refresh All Data"
            className="p-2 text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
          >
            <RefreshCw className={`w-4 h-4 ${isAnyLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* TAB 1: USER MANAGEMENT */}
        {activeTab === 'users' && (
          <div className={`rounded-2xl border p-6 space-y-4 ${isDarkMode ? 'bg-[#161619] border-slate-800' : 'bg-white border-slate-200'}`}>
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-base font-bold text-slate-100">Platform Accounts</h2>
                <p className="text-xs text-slate-400">View, audit, and manage user accounts and access permissions.</p>
              </div>

              <div className="relative w-full sm:w-64">
                <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
                <input
                  type="text"
                  placeholder="Search user, email, role..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className={`w-full pl-9 pr-3 py-2 rounded-xl text-xs font-medium border focus:outline-none ${
                    isDarkMode ? 'bg-[#1a1a1e] border-slate-700 text-slate-200 focus:border-amber-500' : 'bg-slate-50 border-slate-300'
                  }`}
                />
              </div>
            </div>

            {usersState.error && (
              <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-300 flex items-center justify-between">
                <div>
                  <p className="font-semibold text-xs flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4 text-rose-400" />
                    Failed to retrieve registered users
                  </p>
                  <p className="text-[11px] opacity-80 mt-0.5">{usersState.error}</p>
                </div>
                <button
                  type="button"
                  onClick={fetchUsers}
                  className="px-3 py-1.5 rounded-lg bg-rose-800 hover:bg-rose-700 text-white font-bold text-xs cursor-pointer"
                >
                  Retry Users
                </button>
              </div>
            )}

            {usersState.loading ? (
              <div className="py-12 text-center text-slate-400 text-xs flex items-center justify-center gap-2">
                <RefreshCw className="w-4 h-4 animate-spin text-amber-400" />
                <span>Loading platform accounts from database...</span>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className={`border-b text-[11px] font-bold uppercase tracking-wider text-slate-400 ${isDarkMode ? 'border-slate-800' : 'border-slate-200'}`}>
                      <th className="py-3 px-4">User</th>
                      <th className="py-3 px-4">Email</th>
                      <th className="py-3 px-4">Platform Role</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4">Created Date</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {filteredUsers.length === 0 ? (
                      <tr>
                        <td colSpan="6" className="py-6 text-center text-slate-500 text-xs">
                          {usersState.data.length === 0 ? 'No registered platform users found in database.' : 'No matching platform accounts found.'}
                        </td>
                      </tr>
                    ) : (
                      filteredUsers.map((user) => (
                        <tr key={user.user_id} className="hover:bg-slate-800/30 transition-colors">
                          <td className="py-3 px-4 font-bold text-slate-200">
                            {user.full_name}
                          </td>
                          <td className="py-3 px-4 text-slate-400 font-mono">{user.email}</td>
                          <td className="py-3 px-4">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                user.platform_role === 'ADMIN'
                                  ? 'bg-amber-950/80 text-amber-400 border border-amber-800/80'
                                  : user.platform_role === 'ADVISOR'
                                  ? 'bg-purple-950/80 text-purple-400 border border-purple-800/80'
                                  : 'bg-blue-950/80 text-blue-400 border border-blue-800/80'
                              }`}
                            >
                              {user.platform_role}
                            </span>
                          </td>
                          <td className="py-3 px-4">
                            <span
                              className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold ${
                                user.is_active
                                  ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800/60'
                                  : 'bg-rose-950/60 text-rose-400 border border-rose-800/60'
                              }`}
                            >
                              <span className={`w-1.5 h-1.5 rounded-full ${user.is_active ? 'bg-emerald-400' : 'bg-rose-400'}`} />
                              {user.is_active ? 'Active' : 'Deactivated'}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-slate-400">
                            {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                          </td>
                          <td className="py-3 px-4 text-right">
                            <button
                              type="button"
                              onClick={() => handleToggleStatus(user)}
                              className={`px-2.5 py-1 rounded-lg text-[11px] font-bold transition-colors cursor-pointer ${
                                user.is_active
                                  ? 'bg-rose-950/60 hover:bg-rose-900/80 text-rose-300 border border-rose-800/60'
                                  : 'bg-emerald-950/60 hover:bg-emerald-900/80 text-emerald-300 border border-emerald-800/60'
                              }`}
                            >
                              {user.is_active ? 'Deactivate' : 'Activate'}
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: REGULATORY SOURCES */}
        {activeTab === 'regulatory' && (
          <div className={`rounded-2xl border p-6 space-y-4 ${isDarkMode ? 'bg-[#161619] border-slate-800' : 'bg-white border-slate-200'}`}>
            <div>
              <h2 className="text-base font-bold text-slate-100">Regulatory Corpus Sources</h2>
              <p className="text-xs text-slate-400">Approved statutory frameworks and reference documents for project analysis.</p>
            </div>

            {sourcesState.error && (
              <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-300 flex items-center justify-between">
                <div>
                  <p className="font-semibold text-xs flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4 text-rose-400" />
                    Failed to retrieve regulatory sources
                  </p>
                  <p className="text-[11px] opacity-80 mt-0.5">{sourcesState.error}</p>
                </div>
                <button
                  type="button"
                  onClick={fetchSources}
                  className="px-3 py-1.5 rounded-lg bg-rose-800 hover:bg-rose-700 text-white font-bold text-xs cursor-pointer"
                >
                  Retry Sources
                </button>
              </div>
            )}

            {sourcesState.loading ? (
              <div className="py-12 text-center text-slate-400 text-xs flex items-center justify-center gap-2">
                <RefreshCw className="w-4 h-4 animate-spin text-amber-400" />
                <span>Loading regulatory corpus from database...</span>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {sourcesState.data.length === 0 ? (
                  <p className="col-span-2 py-8 text-center text-slate-500 text-xs">No regulatory sources registered in the database.</p>
                ) : (
                  sourcesState.data.map((src) => (
                    <div
                      key={src.source_id || src.id}
                      className={`p-4 rounded-xl border flex flex-col justify-between ${
                        isDarkMode ? 'bg-[#1a1a1e] border-slate-800' : 'bg-slate-50 border-slate-200'
                      }`}
                    >
                      <div className="space-y-1.5">
                        <div className="flex items-center justify-between">
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-950/80 text-amber-400 border border-amber-800/80">
                            {src.jurisdiction || 'SG/MAS'}
                          </span>
                          <span className="text-[10px] font-mono text-slate-400">{src.source_type || 'STATUTORY'}</span>
                        </div>
                        <h3 className="text-sm font-bold text-slate-200">{src.source_name || src.title}</h3>
                        <p className="text-xs text-slate-400 leading-relaxed line-clamp-2">
                          {src.description || 'Verified regulatory source text for AI analysis and project compliance scoring.'}
                        </p>
                      </div>

                      <div className="pt-3 mt-3 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-400">
                        <span>Version: {src.version || '1.0'}</span>
                        {src.url ? (
                          <a
                            href={src.url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-amber-400 hover:underline flex items-center gap-1 font-semibold"
                          >
                            <span>Read Source</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        ) : (
                          <span className="text-slate-500">Official Document</span>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        )}

        {/* TAB 3: SYSTEM AUDIT STREAM */}
        {activeTab === 'audit' && (
          <div className={`rounded-2xl border p-6 space-y-4 ${isDarkMode ? 'bg-[#161619] border-slate-800' : 'bg-white border-slate-200'}`}>
            <div>
              <h2 className="text-base font-bold text-slate-100">Platform Security & Administrative Audit Trail</h2>
              <p className="text-xs text-slate-400">Database-persisted event log recording security, authentication, and administrative actions.</p>
            </div>

            {auditState.error && (
              <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-300 flex items-center justify-between">
                <div>
                  <p className="font-semibold text-xs flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4 text-rose-400" />
                    Failed to retrieve audit trail
                  </p>
                  <p className="text-[11px] opacity-80 mt-0.5">{auditState.error}</p>
                </div>
                <button
                  type="button"
                  onClick={fetchAudit}
                  className="px-3 py-1.5 rounded-lg bg-rose-800 hover:bg-rose-700 text-white font-bold text-xs cursor-pointer"
                >
                  Retry Audit Log
                </button>
              </div>
            )}

            {auditState.loading ? (
              <div className="py-12 text-center text-slate-400 text-xs flex items-center justify-center gap-2">
                <RefreshCw className="w-4 h-4 animate-spin text-amber-400" />
                <span>Loading platform audit log from database...</span>
              </div>
            ) : (
              <div className="divide-y divide-slate-800/60">
                {auditState.data.length === 0 ? (
                  <p className="py-6 text-center text-slate-500 text-xs">No audit events recorded yet in the database.</p>
                ) : (
                  auditState.data.map((evt, idx) => (
                    <div key={evt.id || evt.event_id || idx} className="py-3 flex items-center justify-between gap-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-amber-950/80 text-amber-400 border border-amber-800/80 flex items-center justify-center font-bold text-xs">
                          {evt.badge || 'EV'}
                        </div>
                        <div>
                          <p className="text-xs font-bold text-slate-200">
                            <span className="text-amber-400">{evt.actor_email || evt.user || 'System'}</span> {evt.action}{' '}
                            <span className="text-slate-300 font-medium">"{evt.target || evt.entity_type || 'Platform'}"</span>
                          </p>
                          <p className="text-[10px] text-slate-400 font-mono mt-0.5">
                            {evt.description || evt.event_description || 'Security audit log entry'}
                          </p>
                        </div>
                      </div>

                      <span className="text-[10px] text-slate-400 font-mono whitespace-nowrap">
                        {evt.created_at || evt.timestamp || 'Recorded'}
                      </span>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
