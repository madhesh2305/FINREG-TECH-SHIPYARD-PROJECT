import React from 'react';
import { Check } from 'lucide-react';

export default function VerificationSuccessful({ isDarkMode }) {
  return (
    <div className="text-center py-6 my-2 animate-fadeIn">
      {/* Light Green Checkmark Circle Badge */}
      <div className={`w-14 h-14 rounded-full flex items-center justify-center mx-auto mb-5 ring-8 ${
        isDarkMode
          ? 'bg-emerald-950/60 text-emerald-400 ring-emerald-900/40'
          : 'bg-emerald-100/90 text-emerald-600 ring-emerald-50/80'
      }`}>
        <Check className="w-7 h-7 stroke-[3]" />
      </div>

      {/* Main Heading */}
      <h2 className={`text-xl sm:text-2xl font-bold tracking-tight ${
        isDarkMode ? 'text-slate-100' : 'text-slate-900'
      }`}>
        Verification successful
      </h2>

      {/* Subtitle Message */}
      <p className={`text-sm mt-1.5 font-normal ${
        isDarkMode ? 'text-slate-400' : 'text-slate-500'
      }`}>
        Redirecting you to the Builder Dashboard...
      </p>

      {/* 3 Animated Pulsing Loading Dots */}
      <div className="flex items-center justify-center gap-2 mt-7">
        <span className="w-2.5 h-2.5 bg-[#7c4a27] dark:bg-amber-500 rounded-full animate-bounce [animation-delay:-0.3s]" />
        <span className="w-2.5 h-2.5 bg-[#7c4a27] dark:bg-amber-500 rounded-full animate-bounce [animation-delay:-0.15s]" />
        <span className="w-2.5 h-2.5 bg-[#7c4a27] dark:bg-amber-500 rounded-full animate-bounce" />
      </div>
    </div>
  );
}
