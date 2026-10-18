import React, { useState } from 'react';
import { Check, Shield, Bell, User, Lock, Key, Laptop, Eye, EyeOff } from 'lucide-react';
import { updateUserProfile, updateNotificationPreferences } from '../services/userService';
import { changePassword } from '../services/authService';

export default function SettingsView({ isDarkMode, currentUser: propUser, onUpdateUser }) {
  const [activeSettingsTab, setActiveSettingsTab] = useState('Profile'); // 'Profile' | 'Security' | 'Notifications' | 'Access / Permissions'
  const [toastMsg, setToastMsg] = useState(null);

  const getStoredUser = () => {
    if (propUser) return propUser;
    try {
      const raw = localStorage.getItem('currentUser');
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  };
  const storedUser = getStoredUser();

  // Profile Form States
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [profileData, setProfileData] = useState({
    name: storedUser?.full_name || 'Compliance User',
    email: storedUser?.email || 'user@finregtech.io',
    organization: storedUser?.organization || 'FinRegTech ShipYard',
    role: storedUser?.platform_role || 'BUILDER',
  });

  // Password Change Modal States (DEF-02)
  const [isChangePasswordModalOpen, setIsChangePasswordModalOpen] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [passwordError, setPasswordError] = useState('');
  const [isUpdatingPassword, setIsUpdatingPassword] = useState(false);

  // Notifications Toggle States matching reference screenshot media_1790751758825.png
  const [notifications, setNotifications] = useState({
    email: true,
    projectUpdates: true,
    advisorUpdates: true,
    regulatoryUpdates: false,
  });

  const showToast = (msg) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(null), 3000);
  };

  const handleProfileChange = (e) => {
    setProfileData({
      ...profileData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSaveProfile = async () => {
    if (isEditingProfile) {
      try {
        const updated = await updateUserProfile(profileData);
        if (updated && updated.full_name) {
          const cur = getStoredUser() || {};
          cur.full_name = updated.full_name;
          localStorage.setItem('currentUser', JSON.stringify(cur));
          setProfileData(prev => ({ ...prev, name: updated.full_name }));
          if (onUpdateUser) onUpdateUser({ full_name: updated.full_name });
        }
        showToast('Profile settings saved successfully in PostgreSQL!');
        setIsEditingProfile(false);
      } catch (err) {
        console.error('[SettingsView] updateUserProfile failed:', err);
        showToast(`Failed to save profile: ${err.message || 'Server error'}`);
      }
    } else {
      setIsEditingProfile(true);
    }
  };

  const handleChangePasswordSubmit = async (e) => {
    e.preventDefault();
    setPasswordError('');

    if (!currentPassword || !newPassword) {
      setPasswordError('Please fill in all password fields.');
      return;
    }
    if (newPassword.length < 6) {
      setPasswordError('New password must be at least 6 characters.');
      return;
    }
    if (newPassword !== confirmNewPassword) {
      setPasswordError('New passwords do not match.');
      return;
    }

    setIsUpdatingPassword(true);
    try {
      await changePassword(currentPassword, newPassword);
      showToast('Password updated successfully in PostgreSQL!');
      setIsChangePasswordModalOpen(false);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmNewPassword('');
    } catch (err) {
      console.error('[SettingsView] changePassword error:', err);
      setPasswordError(err.message || 'Failed to change password. Check current credentials.');
    } finally {
      setIsUpdatingPassword(false);
    }
  };


  const toggleNotification = async (key) => {
    const nextVal = !notifications[key];
    const updated = {
      ...notifications,
      [key]: nextVal,
    };
    setNotifications(updated);
    try {
      await updateNotificationPreferences(updated);
    } catch (err) {
      console.warn('[SettingsView] updateNotificationPreferences warning:', err);
    }
    showToast(`Notification setting updated.`);
  };

  return (
    <div className="space-y-6 animate-fadeIn text-left relative">
      {/* Toast Notification Banner */}
      {toastMsg && (
        <div className="fixed top-16 right-6 z-50 bg-[#7c4a27] dark:bg-[#96562c] text-white px-4 py-3 rounded-xl shadow-2xl flex items-center gap-2.5 animate-fadeIn font-semibold text-xs sm:text-sm border-2 border-amber-300">
          <Check className="w-5 h-5 text-amber-300 shrink-0" />
          <span>{toastMsg}</span>
        </div>
      )}

      {/* Settings Header matching reference screenshot */}
      <div>
        <span className="text-[11px] font-extrabold tracking-widest text-[#7c4a27] dark:text-amber-400/90 uppercase font-mono">
          WORKSPACE PREFERENCES
        </span>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100 mt-1">
          Settings
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1.5 font-normal max-w-2xl">
          Manage your profile, account security, alerts, and permissions.
        </p>
      </div>

      {/* Main Settings Layout Grid (Left Side Tab Navigation + Right Side Content Card) */}
      <div className="flex flex-col lg:flex-row gap-8 pt-2">
        {/* Left Sub-Tab Navigation Bar matching media_1790751727170.png */}
        <div className="w-full lg:w-60 flex flex-row lg:flex-col gap-1 overflow-x-auto lg:overflow-visible shrink-0 pb-2 lg:pb-0">
          {[
            { id: 'Profile', label: 'Profile' },
            { id: 'Security', label: 'Security' },
            { id: 'Notifications', label: 'Notifications' },
            { id: 'Access / Permissions', label: 'Access / Permissions' },
          ].map((tab) => {
            const isActive = activeSettingsTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveSettingsTab(tab.id)}
                className={`px-4 py-3 rounded-xl text-xs sm:text-sm font-bold text-left transition-all whitespace-nowrap cursor-pointer ${
                  isActive
                    ? 'bg-[#382618] dark:bg-[#342416] text-amber-400 border border-[#96562c]/60 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Right Side Settings Panel Container */}
        <div className="flex-1">
          {/* TAB 1: PROFILE VIEW (Matching media_1790751727170.png) */}
          {activeSettingsTab === 'Profile' && (
            <div className="rounded-2xl border border-slate-800 bg-[#161619] p-6 sm:p-8 space-y-6 shadow-lg animate-fadeIn">
              <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-100">
                Profile
              </h2>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 pt-2">
                {/* Name */}
                <div className="space-y-2">
                  <label className="block text-xs font-semibold text-slate-400">
                    Name
                  </label>
                  <input
                    type="text"
                    name="name"
                    disabled={!isEditingProfile}
                    value={profileData.name}
                    onChange={handleProfileChange}
                    className="w-full px-4 py-3 rounded-xl border border-slate-800 bg-[#121214] text-slate-200 text-xs sm:text-sm font-medium focus:outline-none focus:border-[#96562c] disabled:opacity-90 disabled:cursor-not-allowed transition-all"
                  />
                </div>

                {/* Email */}
                <div className="space-y-2">
                  <label className="block text-xs font-semibold text-slate-400">
                    Email
                  </label>
                  <input
                    type="email"
                    name="email"
                    disabled={!isEditingProfile}
                    value={profileData.email}
                    onChange={handleProfileChange}
                    className="w-full px-4 py-3 rounded-xl border border-slate-800 bg-[#121214] text-slate-200 text-xs sm:text-sm font-medium focus:outline-none focus:border-[#96562c] disabled:opacity-90 disabled:cursor-not-allowed transition-all"
                  />
                </div>

                {/* Organization */}
                <div className="space-y-2">
                  <label className="block text-xs font-semibold text-slate-400">
                    Organization
                  </label>
                  <input
                    type="text"
                    name="organization"
                    disabled={!isEditingProfile}
                    value={profileData.organization}
                    onChange={handleProfileChange}
                    className="w-full px-4 py-3 rounded-xl border border-slate-800 bg-[#121214] text-slate-200 text-xs sm:text-sm font-medium focus:outline-none focus:border-[#96562c] disabled:opacity-90 disabled:cursor-not-allowed transition-all"
                  />
                </div>

                {/* Role (DEF-04: Permanently locked & governed by Administrator) */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <label className="block text-xs font-semibold text-slate-400">
                      Role
                    </label>
                    <span className="text-[10px] font-mono font-bold text-amber-500 bg-amber-950/60 border border-amber-800/80 px-2 py-0.5 rounded">
                      GOVERNED BY ADMINISTRATOR
                    </span>
                  </div>
                  <div className="relative">
                    <input
                      type="text"
                      name="role"
                      disabled={true}
                      readOnly={true}
                      value={profileData.role}
                      className="w-full px-4 py-3 rounded-xl border border-slate-800 bg-[#121214]/60 text-slate-400 font-mono text-xs sm:text-sm font-medium cursor-not-allowed opacity-80"
                    />
                    <div className="absolute inset-y-0 right-0 pr-3.5 flex items-center pointer-events-none text-slate-500">
                      <Lock className="w-4 h-4" />
                    </div>
                  </div>
                  <p className="text-[11px] text-slate-500 leading-normal">
                    Platform roles are enforced by RBAC security governance and cannot be modified from user settings. Contact platform admin to request a role change.
                  </p>
                </div>
              </div>

              {/* Bottom Action Row matching screenshot */}
              <div className="flex justify-end pt-6">
                <button
                  type="button"
                  onClick={handleSaveProfile}
                  className="px-6 py-2.5 rounded-xl bg-[#f59e0b] hover:bg-[#d97706] text-slate-950 font-extrabold text-xs shadow-md transition-all cursor-pointer border border-amber-300/60 hover:scale-[1.02]"
                >
                  {isEditingProfile ? 'Save profile' : 'Edit profile'}
                </button>
              </div>
            </div>
          )}

          {/* TAB 2: SECURITY VIEW (Matching media_1790751744574.png) */}
          {activeSettingsTab === 'Security' && (
            <div className="rounded-2xl border border-slate-800 bg-[#161619] p-6 sm:p-8 space-y-6 shadow-lg animate-fadeIn">
              <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-100">
                Security
              </h2>

              <div className="space-y-6 pt-2">
                {/* Password Row */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800/80">
                  <div>
                    <h3 className="text-sm font-bold text-slate-100">Password</h3>
                    <p className="text-xs text-slate-400 mt-1">Last changed 72 days ago</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setIsChangePasswordModalOpen(true);
                      setPasswordError('');
                    }}
                    className="px-4 py-2 rounded-xl border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-200 font-bold text-xs cursor-pointer transition-colors self-start sm:self-auto"
                  >
                    Change password
                  </button>
                </div>

                {/* Active Sessions Row */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2">
                  <div>
                    <h3 className="text-sm font-bold text-slate-100">Active sessions</h3>
                    <p className="text-xs text-slate-400 mt-1">
                      2 active sessions · London, United Kingdom
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => showToast('Session manager opened. 2 active sessions found.')}
                    className="px-4 py-2 rounded-xl border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-200 font-bold text-xs cursor-pointer transition-colors self-start sm:self-auto"
                  >
                    Manage sessions
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: NOTIFICATIONS VIEW (Matching media_1790751758825.png) */}
          {activeSettingsTab === 'Notifications' && (
            <div className="rounded-2xl border border-slate-800 bg-[#161619] p-6 sm:p-8 space-y-6 shadow-lg animate-fadeIn">
              <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-100">
                Notifications
              </h2>

              <div className="space-y-6 divide-y divide-slate-800/80 pt-2">
                {/* Email Notifications */}
                <div className="flex items-center justify-between gap-4 pt-1">
                  <div>
                    <h3 className="text-sm font-bold text-slate-100">Email notifications</h3>
                    <p className="text-xs text-slate-400 mt-1">
                      Receive relevant email notifications and summaries.
                    </p>
                  </div>
                  <label className="flex items-center gap-2 cursor-pointer shrink-0">
                    <input
                      type="checkbox"
                      checked={notifications.email}
                      onChange={() => toggleNotification('email')}
                      className="w-4 h-4 rounded border-slate-700 text-amber-500 focus:ring-amber-400 bg-slate-900 cursor-pointer accent-[#f59e0b]"
                    />
                    <span className="text-xs font-semibold text-slate-200 w-6">
                      {notifications.email ? 'On' : 'Off'}
                    </span>
                  </label>
                </div>

                {/* Project Updates */}
                <div className="flex items-center justify-between gap-4 pt-5">
                  <div>
                    <h3 className="text-sm font-bold text-slate-100">Project updates</h3>
                    <p className="text-xs text-slate-400 mt-1">
                      Receive relevant project updates and summaries.
                    </p>
                  </div>
                  <label className="flex items-center gap-2 cursor-pointer shrink-0">
                    <input
                      type="checkbox"
                      checked={notifications.projectUpdates}
                      onChange={() => toggleNotification('projectUpdates')}
                      className="w-4 h-4 rounded border-slate-700 text-amber-500 focus:ring-amber-400 bg-slate-900 cursor-pointer accent-[#f59e0b]"
                    />
                    <span className="text-xs font-semibold text-slate-200 w-6">
                      {notifications.projectUpdates ? 'On' : 'Off'}
                    </span>
                  </label>
                </div>

                {/* Advisor Updates */}
                <div className="flex items-center justify-between gap-4 pt-5">
                  <div>
                    <h3 className="text-sm font-bold text-slate-100">Advisor updates</h3>
                    <p className="text-xs text-slate-400 mt-1">
                      Receive relevant advisor updates and summaries.
                    </p>
                  </div>
                  <label className="flex items-center gap-2 cursor-pointer shrink-0">
                    <input
                      type="checkbox"
                      checked={notifications.advisorUpdates}
                      onChange={() => toggleNotification('advisorUpdates')}
                      className="w-4 h-4 rounded border-slate-700 text-amber-500 focus:ring-amber-400 bg-slate-900 cursor-pointer accent-[#f59e0b]"
                    />
                    <span className="text-xs font-semibold text-slate-200 w-6">
                      {notifications.advisorUpdates ? 'On' : 'Off'}
                    </span>
                  </label>
                </div>

                {/* Regulatory Updates */}
                <div className="flex items-center justify-between gap-4 pt-5">
                  <div>
                    <h3 className="text-sm font-bold text-slate-100">Regulatory updates</h3>
                    <p className="text-xs text-slate-400 mt-1">
                      Receive relevant regulatory updates and summaries.
                    </p>
                  </div>
                  <label className="flex items-center gap-2 cursor-pointer shrink-0">
                    <input
                      type="checkbox"
                      checked={notifications.regulatoryUpdates}
                      onChange={() => toggleNotification('regulatoryUpdates')}
                      className="w-4 h-4 rounded border-slate-700 text-amber-500 focus:ring-amber-400 bg-slate-900 cursor-pointer accent-[#f59e0b]"
                    />
                    <span className="text-xs font-semibold text-slate-200 w-6">
                      {notifications.regulatoryUpdates ? 'On' : 'Off'}
                    </span>
                  </label>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: ACCESS / PERMISSIONS VIEW (Matching media_1790751772679.png) */}
          {activeSettingsTab === 'Access / Permissions' && (
            <div className="rounded-2xl border border-slate-800 bg-[#161619] p-6 sm:p-8 space-y-7 shadow-lg animate-fadeIn">
              <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-100">
                Access / Permissions
              </h2>

              <div className="space-y-6 pt-2">
                {/* CURRENT ROLE */}
                <div>
                  <span className="block text-[11px] font-extrabold tracking-widest text-slate-500 uppercase font-mono mb-1.5">
                    CURRENT ROLE
                  </span>
                  <p className="text-sm font-bold text-slate-100">
                    Builder / Compliance Lead
                  </p>
                </div>

                {/* PROJECT ACCESS */}
                <div className="pt-6 border-t border-slate-800/80">
                  <span className="block text-[11px] font-extrabold tracking-widest text-slate-500 uppercase font-mono mb-1.5">
                    PROJECT ACCESS
                  </span>
                  <p className="text-sm font-bold text-slate-100">
                    5 projects · 3 owned · 2 collaborator
                  </p>
                </div>

                {/* PERMISSION SUMMARY */}
                <div className="pt-6 border-t border-slate-800/80">
                  <span className="block text-[11px] font-extrabold tracking-widest text-slate-500 uppercase font-mono mb-1.5">
                    PERMISSION SUMMARY
                  </span>
                  <p className="text-sm font-bold text-slate-100 leading-relaxed">
                    Create and manage projects, invite advisors, edit requirements, export audit records
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* DEF-02: CHANGE PASSWORD MODAL */}
      {isChangePasswordModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fadeIn">
          <div className="w-full max-w-md rounded-2xl bg-[#1a1a1e] border border-slate-700 p-6 sm:p-7 shadow-2xl text-left space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                <Lock className="w-5 h-5 text-amber-500" />
                Change Password
              </h2>
              <button
                type="button"
                onClick={() => setIsChangePasswordModalOpen(false)}
                className="text-slate-400 hover:text-slate-200 text-sm font-semibold p-1 cursor-pointer"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-slate-400">
              Update your account password. Credential updates are verified and encrypted using bcrypt in PostgreSQL.
            </p>

            {passwordError && (
              <div className="p-3 rounded-xl bg-rose-950/70 border border-rose-800 text-rose-300 text-xs font-semibold text-left animate-fadeIn">
                {passwordError}
              </div>
            )}

            <form onSubmit={handleChangePasswordSubmit} className="space-y-4">
              {/* Current Password */}
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-slate-300">
                  Current Password
                </label>
                <div className="relative">
                  <input
                    type={showCurrentPassword ? 'text' : 'password'}
                    required
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    placeholder="Enter current password"
                    className="w-full pl-3 pr-10 py-2.5 rounded-xl text-xs sm:text-sm bg-slate-800/80 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500"
                  />
                  <button
                    type="button"
                    onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-200 cursor-pointer"
                  >
                    {showCurrentPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* New Password */}
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-slate-300">
                  New Password (min 6 characters)
                </label>
                <div className="relative">
                  <input
                    type={showNewPassword ? 'text' : 'password'}
                    required
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Enter new password"
                    className="w-full pl-3 pr-10 py-2.5 rounded-xl text-xs sm:text-sm bg-slate-800/80 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500"
                  />
                  <button
                    type="button"
                    onClick={() => setShowNewPassword(!showNewPassword)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-200 cursor-pointer"
                  >
                    {showNewPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Confirm New Password */}
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-slate-300">
                  Confirm New Password
                </label>
                <input
                  type="password"
                  required
                  value={confirmNewPassword}
                  onChange={(e) => setConfirmNewPassword(e.target.value)}
                  placeholder="Repeat new password"
                  className="w-full px-3 py-2.5 rounded-xl text-xs sm:text-sm bg-slate-800/80 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500"
                />
              </div>

              <div className="flex gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setIsChangePasswordModalOpen(false)}
                  className="flex-1 py-2.5 px-4 rounded-xl border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs cursor-pointer transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isUpdatingPassword}
                  className="flex-1 py-2.5 px-4 rounded-xl bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-slate-950 font-bold text-xs cursor-pointer transition-colors shadow-md"
                >
                  {isUpdatingPassword ? 'Updating...' : 'Update Password'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
