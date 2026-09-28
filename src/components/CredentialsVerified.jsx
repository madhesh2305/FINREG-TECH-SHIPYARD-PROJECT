import React from 'react';
import { BarChart3, Check } from 'lucide-react';

export default function CredentialsVerified({ isDarkMode }) {
  return (
    <div className="text-center py-2 animate-fadeIn">
      {/* Top Icon Box (Rich Brown Badge) */}
      <div className="flex justify-center mb-5">
        <div className="w-13 h-13 bg-[#7c4a27] dark:bg-[#96562c] rounded-2xl flex items-center justify-center shadow-md shadow-amber-950/20">
          <BarChart3 className="w-7 h-7 text-white stroke-[2.5]" />
        </div>
      </div>

      {/* Header Titles */}
      <div className="text-center mb-8">
        <h1 className={`text-2xl sm:text-[26px] font-bold tracking-tight ${
          isDarkMode ? 'text-slate-100' : 'text-slate-900'
        }`}>
          Welcome to FinRegTech ShipYard
        </h1>
        <p className={`text-sm mt-1.5 font-normal ${
          isDarkMode ? 'text-slate-400' : 'text-slate-500'
        }`}>
          Sign in to continue to your projects
        </p>
      </div>

      {/* Verified Badge & Messages (Brown Theme) */}
      <div className="my-8 flex flex-col items-center justify-center">
        <div className={`w-14 h-14 rounded-full flex items-center justify-center mb-4 ring-8 ${
          isDarkMode
            ? 'bg-amber-950/50 text-amber-400 ring-amber-900/30'
            : 'bg-amber-50 text-[#7c4a27] ring-amber-100/80'
        }`}>
          <Check className="w-7 h-7 stroke-[3]" />
        </div>

        <h2 className={`text-lg font-bold tracking-tight ${
          isDarkMode ? 'text-slate-100' : 'text-slate-900'
        }`}>
          Credentials verified
        </h2>
        <p className={`text-sm mt-1 ${
          isDarkMode ? 'text-slate-400' : 'text-slate-500'
        }`}>
          Proceeding to Builder Dashboard...
        </p>

        {/* Animated 3 Loading Dots (Warm Brown) */}
        <div className="flex items-center gap-2 mt-6">
          <span className="w-2.5 h-2.5 bg-[#7c4a27] dark:bg-amber-500 rounded-full animate-bounce [animation-delay:-0.3s]" />
          <span className="w-2.5 h-2.5 bg-[#7c4a27] dark:bg-amber-500 rounded-full animate-bounce [animation-delay:-0.15s]" />
          <span className="w-2.5 h-2.5 bg-[#7c4a27] dark:bg-amber-500 rounded-full animate-bounce" />
        </div>
      </div>
    </div>
  );
}
