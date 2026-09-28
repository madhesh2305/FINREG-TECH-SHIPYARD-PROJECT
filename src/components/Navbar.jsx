import React from 'react';
import { Menu } from 'lucide-react';

export default function Navbar({ onGetStarted }) {
  return (
    <header className="w-full border-b border-slate-800 bg-[#1a1a1e] text-slate-100 px-4 sm:px-6 py-3 flex items-center justify-between sticky top-0 z-50 transition-colors duration-300">
      {/* Left Branding */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          aria-label="Toggle navigation menu"
          className="p-1.5 rounded-lg text-slate-300 hover:bg-slate-800 hover:text-white transition-colors cursor-pointer"
        >
          <Menu className="w-5 h-5" />
        </button>
        <span className="font-extrabold tracking-wider text-sm sm:text-base select-none">
          FINREGTECH SHIPYARD
        </span>
      </div>

      {/* Right Top Corner Controls: Get Started & Version */}
      <div className="flex items-center gap-3 sm:gap-4">
        {/* Top Right Corner Get Started Button (If passed) */}
        {onGetStarted && (
          <button
            type="button"
            onClick={onGetStarted}
            title="Click to proceed to Sign in"
            className="px-4 py-2 sm:px-5 sm:py-2.5 rounded-xl bg-[#96562c] hover:bg-[#7c4a27] text-white font-bold text-xs sm:text-sm shadow-md shadow-amber-950/20 flex items-center justify-center gap-2 transition-all duration-300 cursor-pointer border-2 border-slate-700 hover:border-amber-400 hover:scale-[1.04] hover:shadow-[0_0_25px_rgba(254,243,199,0.95)]"
          >
            <span>Get Started</span>
            <span className="font-mono text-xs">→</span>
          </button>
        )}

        {/* Version Metadata Badge */}
        <div className="text-xs font-medium tracking-wide text-slate-400 hidden md:block">
          Login <span className="mx-1 font-sans text-slate-500">·</span> <span>v0.1</span>
        </div>
      </div>
    </header>
  );
}
