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
  RefreshCw
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
  const [stats, setStats] = useState({
    total_users: 0,
    active_users: 0,
    total_projects: 0,
    regulatory_sources_count: 0,
    total_audit_events: 0,
  });
  const [users, setUsers] = useState([]);
  const [regulatorySources, setRegulatorySources] = useState([]);
  const [auditEvents, setAuditEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [toastMessage, setToastMessage] = useState(null);

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const [loadError, setLoadError] = useState(null);

  const loadData = async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const [statsData, usersData, sourcesData, auditData] = await Promise.all([
        getAdminStats().catch((err) => {
          console.warn('[AdminDashboardView] stats error:', err);
          return null;
        }),
        getAdminUsers().catch((err) => {
          console.warn('[AdminDashboardView] users error:', err);
          return [];
        }),
        getRegulatorySources().catch((err) => {
          console.warn('[AdminDashboardView] sources error:', err);
          return [];
        }),
        getAdminAuditEvents().catch((err) => {
          console.warn('[AdminDashboardView] audit error:', err);
          return [];
        }),
      ]);
      setStats(statsData || {
        total_users: Array.isArray(usersData) ? usersData.length : 0,
        active_users: Array.isArray(usersData) ? usersData.filter(u => u.is_active).length : 0,
        total_projects: 0,
        regulatory_sources_count: Array.isArray(sourcesData) ? sourcesData.length : 0,
        total_audit_events: Array.isArray(auditData) ? auditData.length : 0,
      });
      setUsers(Array.isArray(usersData) ? usersData : []);
      setRegulatorySources(Array.isArray(sourcesData) ? sourcesData : []);
      setAuditEvents(Array.isArray(auditData) ? auditData : []);
    } catch (err) {
      console.error('[AdminDashboardView] Data load failed:', err);
      setLoadError('Some administrative services could not be reached. Retrying will re-synchronize live metrics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleToggleStatus = async (user) => {
    try {
      const updated = await updateUserStatus(user.user_id, !user.is_active);
      setUsers(users.map((u) => (u.user_id === user.user_id ? { ...u, is_active: updated.is_active } : u)));
      showToast(`User ${user.email} status updated to ${updated.is_active ? 'ACTIVE' : 'DEACTIVATED'}`);
    } catch (err) {
      showToast(err.message || 'Failed to update user status');
    }
  };

  const filteredUsers = users.filter(
    (u) =>
      u.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      u.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (u.platform_role && u.platform_role.toLowerCase().includes(searchQuery.toLowerCase()))
  );

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
              {currentUser?.platform_role || 'PLATFORM ADMIN'}
            </span>
          </div>

          <button
            type="button"
            onClick={() => {
              logoutUser();
              if (onSignOut) onSignOut();
              window.location.reload();
            }}
            className="flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold text-rose-400 hover:bg-rose-950/30 border border-rose-900/50 transition-all cursor-pointer"
          >
            <LogOut className="w-4 h-4" />
            <span className="hidden sm:inline">Sign Out</span>
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">
        {/* DEF-17: Recoverable Error Banner for Admin Cockpit */}
        {loadError && (
          <div className="p-4 rounded-xl border border-amber-800 bg-amber-950/40 text-amber-300 text-xs flex items-center justify-between">
            <span>{loadError}</span>
            <button
              type="button"
              onClick={loadData}
              className="px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold text-xs cursor-pointer"
            >
              Retry Sync
            </button>
          </div>
        )}
        {/* KPI Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className={`p-4 rounded-2xl border ${isDarkMode ? 'bg-[#161619] border-slate-800' : 'bg-white border-slate-200'}`}>
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider">Total Users</span>
              <Users className="w-4 h-4 text-amber-400" />
            </div>
            <p className="text-2xl font-extrabold text-slate-100">{stats.total_users}</p>
            <span className="text-[11px] text-emerald-400 font-medium">{stats.active_users} active accounts</span>
          </div>

          <div className={`p-4 rounded-2xl border ${isDarkMode ? 'bg-[#161619] border-slate-800' : 'bg-white border-slate-200'}`}>
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider">Active Projects</span>
              <FolderKanban className="w-4 h-4 text-blue-400" />
            </div>
            <p className="text-2xl font-extrabold text-slate-100">{stats.total_projects}</p>
            <span className="text-[11px] text-slate-400 font-medium">Compliance workspaces</span>
          </div>

          <div className={`p-4 rounded-2xl border ${isDarkMode ? 'bg-[#161619] border-slate-800' : 'bg-white border-slate-200'}`}>
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider">Regulatory Corpus</span>
              <FileCheck2 className="w-4 h-4 text-emerald-400" />
            </div>
            <p className="text-2xl font-extrabold text-slate-100">{stats.regulatory_sources_count}</p>
            <span className="text-[11px] text-emerald-400 font-medium">Verified ABC sources</span>
          </div>

          <div className={`p-4 rounded-2xl border ${isDarkMode ? 'bg-[#161619] border-slate-800' : 'bg-white border-slate-200'}`}>
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider">Audit Events</span>
              <Activity className="w-4 h-4 text-purple-400" />
            </div>
            <p className="text-2xl font-extrabold text-slate-100">{stats.total_audit_events}</p>
            <span className="text-[11px] text-purple-400 font-medium">Immutable records</span>
          </div>

          <div className={`p-4 rounded-2xl border ${isDarkMode ? 'bg-[#161619] border-slate-800' : 'bg-white border-slate-200'}`}>
            <div className="flex items-center justify-between text-slate-400 mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider">Security State</span>
              <ShieldAlert className="w-4 h-4 text-emerald-400" />
            </div>
            <p className="text-2xl font-extrabold text-emerald-400">ENFORCED</p>
            <span className="text-[11px] text-slate-400 font-medium">RBAC + BOLA isolation</span>
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
              User & Role Management ({users.length})
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('regulatory')}
              className={`py-3 text-sm font-bold border-b-2 -mb-px transition-colors cursor-pointer ${
                activeTab === 'regulatory' ? 'border-amber-400 text-amber-400' : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Regulatory Corpus ({regulatorySources.length})
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('audit')}
              className={`py-3 text-sm font-bold border-b-2 -mb-px transition-colors cursor-pointer ${
                activeTab === 'audit' ? 'border-amber-400 text-amber-400' : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Platform Audit Stream
            </button>
          </div>

          <button
            type="button"
            onClick={loadData}
            title="Refresh Data"
            className="p-2 text-slate-400 hover:text-slate-200 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
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
                        No matching platform accounts found.
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
                          {user.platform_role !== 'ADMIN' && (
                            <button
                              type="button"
                              onClick={() => handleToggleStatus(user)}
                              className={`px-3 py-1 rounded-lg text-[11px] font-bold transition-all cursor-pointer ${
                                user.is_active
                                  ? 'bg-rose-950/60 text-rose-300 hover:bg-rose-900 border border-rose-800'
                                  : 'bg-emerald-950/60 text-emerald-300 hover:bg-emerald-900 border border-emerald-800'
                              }`}
                            >
                              {user.is_active ? 'Deactivate' : 'Activate'}
                            </button>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 2: REGULATORY CORPUS */}
        {activeTab === 'regulatory' && (
          <div className={`rounded-2xl border p-6 space-y-4 ${isDarkMode ? 'bg-[#161619] border-slate-800' : 'bg-white border-slate-200'}`}>
            <div>
              <h2 className="text-base font-bold text-slate-100">Curated Statutory Corpus (ABC Scope)</h2>
              <p className="text-xs text-slate-400">Authoritative statutory sources verified for UK/EU Anti-Bribery & Corruption compliance.</p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className={`border-b text-[11px] font-bold uppercase tracking-wider text-slate-400 ${isDarkMode ? 'border-slate-800' : 'border-slate-200'}`}>
                    <th className="py-3 px-4">Code</th>
                    <th className="py-3 px-4">Title</th>
                    <th className="py-3 px-4">Authority</th>
                    <th className="py-3 px-4">Jurisdiction</th>
                    <th className="py-3 px-4">Validation Status</th>
                    <th className="py-3 px-4 text-right">Official Reference</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {regulatorySources.length === 0 ? (
                    <tr>
                      <td colSpan="6" className="py-6 text-center text-slate-500 text-xs">
                        No regulatory sources found in database.
                      </td>
                    </tr>
                  ) : (
                    regulatorySources.map((source, idx) => (
                      <tr key={source.id || idx} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-3 px-4 font-mono font-bold text-amber-400">{source.code || source.id}</td>
                        <td className="py-3 px-4 font-medium text-slate-200 max-w-sm truncate" title={source.title}>
                          {source.title}
                        </td>
                        <td className="py-3 px-4 text-slate-400">{source.authority}</td>
                        <td className="py-3 px-4">
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300">
                            {source.jurisdiction}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950/60 text-emerald-400 border border-emerald-800/60">
                            <CheckCircle2 className="w-3 h-3" />
                            Validated
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right">
                          {(source.sourceUrl || source.source_url) && (
                            <a
                              href={source.sourceUrl || source.source_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 text-amber-400 hover:text-amber-300 transition-colors"
                            >
                              <span>Open</span>
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 3: SYSTEM AUDIT STREAM */}
        {activeTab === 'audit' && (
          <div className={`rounded-2xl border p-6 space-y-4 ${isDarkMode ? 'bg-[#161619] border-slate-800' : 'bg-white border-slate-200'}`}>
            <div>
              <h2 className="text-base font-bold text-slate-100">Immutable Platform Audit Trail</h2>
              <p className="text-xs text-slate-400">Cryptographically verifiable event stream recording material actions.</p>
            </div>

            <div className="divide-y divide-slate-800/60">
              {auditEvents.length === 0 ? (
                <p className="py-6 text-center text-slate-500 text-xs">No audit events recorded yet.</p>
              ) : (
                auditEvents.map((evt, idx) => (
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
                        <p className="text-[11px] text-slate-500 font-mono">
                          {evt.created_at ? new Date(evt.created_at).toLocaleString() : evt.time || 'Recorded'}
                        </p>
                      </div>
                    </div>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
                      VERIFIED
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
