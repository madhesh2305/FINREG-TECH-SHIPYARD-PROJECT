import React from 'react';
import { logoutUser } from '../services/authService';

export default function SettingsView({ isDarkMode, onSignOut, currentUser }) {
  const handleLogout = () => {
    logoutUser();
    if (onSignOut) {
      onSignOut();
    }
  };

  const displayName = currentUser?.name || 'Jun Nakamura';
  const displayEmail = currentUser?.email || 'jun@northbank.com';
  const displayRole = currentUser?.role || 'Builder / Project Owner';

  return (
    <div className="space-y-6 animate-fadeIn text-left relative max-w-5xl">
      {/* HEADER SECTION MATCHING media_1791742757844_ca0f028c.png */}
      <div>
        <div className="text-[11px] font-mono tracking-widest text-slate-500 uppercase font-semibold mb-1">
          ACCOUNT
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-white">
          Settings
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1.5 font-normal max-w-3xl">
          Your account and access summary. Role and permission changes are managed by authorized administrators.
        </p>
      </div>

      {/* ACCOUNT INFORMATION CARD MATCHING media_1791742757844_ca0f028c.png */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800/90 bg-white dark:bg-[#161619] shadow-xl overflow-hidden mt-6">
        {/* Card Header */}
        <div className="p-6 sm:p-8 pb-5 border-b border-slate-100 dark:border-slate-800/80">
          <h2 className="text-lg sm:text-xl font-bold text-slate-900 dark:text-white">
            Account information
          </h2>
        </div>

        {/* Card Body */}
        <div className="p-6 sm:p-8 space-y-8">
          {/* Row 1: NAME and EMAIL (DEF-03) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 sm:gap-8">
            <div>
              <div className="text-[10px] font-mono tracking-wider text-slate-400 uppercase font-semibold mb-1.5">
                NAME
              </div>
              <div className="text-sm sm:text-base font-semibold text-slate-900 dark:text-slate-100">
                {displayName}
              </div>
            </div>

            <div>
              <div className="text-[10px] font-mono tracking-wider text-slate-400 uppercase font-semibold mb-1.5">
                EMAIL
              </div>
              <div className="text-sm sm:text-base font-semibold text-slate-900 dark:text-slate-100">
                {displayEmail}
              </div>
            </div>
          </div>

          {/* Row 2: ASSIGNED ROLE and PROJECT ACCESS SUMMARY (DEF-04) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 sm:gap-8">
            <div>
              <div className="text-[10px] font-mono tracking-wider text-slate-400 uppercase font-semibold mb-1.5">
                ASSIGNED ROLE
              </div>
              <div className="text-sm sm:text-base font-semibold text-slate-900 dark:text-slate-100">
                {displayRole}
              </div>
            </div>

            <div>
              <div className="text-[10px] font-mono tracking-wider text-slate-400 uppercase font-semibold mb-1.5">
                PROJECT ACCESS SUMMARY
              </div>
              <div className="text-sm sm:text-base font-semibold text-slate-900 dark:text-slate-100">
                3 owned projects · 1 active advisor
              </div>
            </div>
          </div>

          {/* Row 3: NOTIFICATIONS */}
          <div>
            <div className="text-[10px] font-mono tracking-wider text-slate-400 uppercase font-semibold mb-1.5">
              NOTIFICATIONS
            </div>
            <div className="text-sm sm:text-base font-semibold text-slate-900 dark:text-slate-100">
              Essential workflow notifications enabled
            </div>
          </div>
        </div>

        {/* Card Footer with Log out Button */}
        <div className="p-6 sm:p-8 pt-6 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-end">
          <button
            type="button"
            onClick={handleLogout}
            className="px-6 py-2.5 rounded-md border border-rose-900/60 bg-[#251316] hover:bg-[#32171c] text-rose-300 hover:text-rose-200 text-xs sm:text-sm font-semibold transition-colors cursor-pointer shadow-sm"
          >
            Log out
          </button>
        </div>
      </div>
    </div>
  );
}
