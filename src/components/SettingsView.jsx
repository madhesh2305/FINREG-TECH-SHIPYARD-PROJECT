import React, { useState } from 'react';
import { Check, Shield, Bell, User, Lock, Key, Laptop } from 'lucide-react';
import { updateUserProfile, updateNotificationPreferences } from '../services/userService';

export default function SettingsView({ isDarkMode }) {
  const [activeSettingsTab, setActiveSettingsTab] = useState('Profile'); // 'Profile' | 'Security' | 'Notifications' | 'Access / Permissions'
  const [toastMsg, setToastMsg] = useState(null);

  // Profile Form States
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [profileData, setProfileData] = useState({
    name: 'Jun Nakamura',
    email: 'jun@northbank.com',
    organization: 'Northbank Financial',
    role: 'Builder / Compliance Lead',
  });

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
        await updateUserProfile(profileData);
      } catch (err) {
        console.warn('[SettingsView] updateUserProfile warning:', err);
      }
      showToast('Profile settings saved successfully!');
      setIsEditingProfile(false);
    } else {
      setIsEditingProfile(true);
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

                {/* Role */}
                <div className="space-y-2">
                  <label className="block text-xs font-semibold text-slate-400">
                    Role
                  </label>
                  <input
                    type="text"
                    name="role"
                    disabled={!isEditingProfile}
                    value={profileData.role}
                    onChange={handleProfileChange}
                    className="w-full px-4 py-3 rounded-xl border border-slate-800 bg-[#121214] text-slate-200 text-xs sm:text-sm font-medium focus:outline-none focus:border-[#96562c] disabled:opacity-90 disabled:cursor-not-allowed transition-all"
                  />
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
                    onClick={() => showToast('Password change link sent to your email!')}
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
    </div>
  );
}
