import React, { useEffect, useState } from 'react';
import { Ship, Copyright, Anchor, ShieldCheck, Waves } from 'lucide-react';

export default function FlashPage({ isDarkMode, onFinish }) {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    // 3 seconds timer with smooth progress bar tracking
    const startTime = Date.now();
    const duration = 3000;

    const interval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const pct = Math.min(100, Math.floor((elapsed / duration) * 100));
      setProgress(pct);

      if (elapsed >= duration) {
        clearInterval(interval);
        onFinish();
      }
    }, 30);

    return () => clearInterval(interval);
  }, [onFinish]);

  return (
    <div className={`relative min-h-screen w-full flex flex-col justify-between items-center p-6 overflow-hidden select-none transition-colors duration-500 ${
      isDarkMode ? 'bg-[#121214] text-slate-100' : 'bg-[#e2e8f0] text-slate-800'
    }`}>
      {/* Background Ambient Radial Glow & Watermark Pattern */}
      <div className="absolute inset-0 pointer-events-none flex items-center justify-center overflow-hidden">
        {/* Central Warm Ambient Spotlight */}
        <div className={`w-[500px] h-[500px] rounded-full blur-3xl opacity-40 transition-all duration-700 animate-pulseGlow ${
          isDarkMode
            ? 'bg-gradient-to-tr from-[#96562c]/30 via-amber-600/20 to-transparent'
            : 'bg-gradient-to-tr from-[#7c4a27]/25 via-amber-200/50 to-transparent'
        }`} />

        {/* Subtle Background Grid overlay */}
        <div className="absolute inset-0 bg-[radial-gradient(#7c4a27_1px,transparent_1px)] [background-size:32px_32px] opacity-[0.07] dark:opacity-[0.12]" />
      </div>

      {/* Top Section / Header Badge */}
      <div className="w-full flex items-center justify-between z-10 pt-2 opacity-80 animate-fadeIn">
        <div className="flex items-center gap-2 text-xs font-extrabold uppercase tracking-widest text-[#7c4a27] dark:text-amber-400">
          <Anchor className="w-4 h-4 text-[#7c4a27] dark:text-amber-400" />
          <span>FinRegTech ShipYard</span>
        </div>
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-mono font-bold bg-[#7c4a27]/10 dark:bg-amber-400/10 text-[#7c4a27] dark:text-amber-300 border border-[#7c4a27]/20">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
          <span>INITIALIZING</span>
        </div>
      </div>

      {/* Main Center Box Section */}
      <div className="relative z-10 flex flex-col items-center text-center max-w-xl mx-auto space-y-7 animate-fadeIn my-auto">
        
        {/* Creative Ship Badge Container with Double Ambient Halo */}
        <div className="relative group cursor-pointer">
          {/* Outer Pulsing Glow Halo */}
          <div className="absolute -inset-4 bg-gradient-to-r from-[#7c4a27] via-amber-500 to-[#96562c] rounded-3xl blur-xl opacity-50 animate-pulseGlow" />

          {/* Main Brown Button Badge with Floating Animation */}
          <div className="relative w-24 h-24 sm:w-28 sm:h-28 bg-gradient-to-br from-[#7c4a27] via-[#8d542c] to-[#5c371d] dark:from-[#96562c] dark:via-[#7c4a27] dark:to-[#4a2912] rounded-3xl flex items-center justify-center shadow-[0_20px_50px_rgba(124,74,39,0.35),0_0_30px_rgba(254,243,199,0.4)] border-2 border-amber-200/50 transition-all duration-300 transform group-hover:scale-105 animate-floatSlow">
            {/* Cream Color Ship Icon inside */}
            <Ship className="w-12 h-12 sm:w-14 sm:h-14 text-[#fef3c7] stroke-[2.2] drop-shadow-md" />
          </div>

          {/* Decorative Waves Accent below icon button */}
          <div className="absolute -bottom-3 left-1/2 -translate-x-1/2 bg-[#7c4a27] dark:bg-[#96562c] border border-amber-200/60 px-2.5 py-0.5 rounded-full shadow-md">
            <Waves className="w-4 h-4 text-[#fef3c7] animate-pulse" />
          </div>
        </div>

        {/* Title: FINREG TECH SHIPYARD */}
        <div className="space-y-2 pt-2">
          <h1 className="text-3xl sm:text-4xl md:text-[42px] font-black tracking-tight text-[#7c4a27] dark:text-amber-400 uppercase drop-shadow-xs">
            FinReg Tech ShipYard
          </h1>
          <div className="h-1 w-16 mx-auto bg-gradient-to-r from-transparent via-[#7c4a27] dark:via-amber-400 to-transparent rounded-full" />
        </div>

        {/* Subtitle in normal font size in center */}
        <p className={`text-sm sm:text-base font-medium max-w-lg leading-relaxed ${
          isDarkMode ? 'text-slate-300' : 'text-slate-700'
        }`}>
          Users creates financial projects with all the requirements and advisors available at one Ship
        </p>

        {/* Loading Section: Three Dots & Glowing Progress Track */}
        <div className="flex flex-col items-center gap-3 pt-2 w-full max-w-xs">
          {/* Three Dots Loading */}
          <div className="flex items-center justify-center gap-2.5">
            <span className="w-3 h-3 rounded-full bg-[#7c4a27] dark:bg-amber-400 animate-bounce [animation-delay:-0.3s] shadow-xs" />
            <span className="w-3 h-3 rounded-full bg-[#7c4a27] dark:bg-amber-400 animate-bounce [animation-delay:-0.15s] shadow-xs" />
            <span className="w-3 h-3 rounded-full bg-[#7c4a27] dark:bg-amber-400 animate-bounce shadow-xs" />
          </div>

          {/* Sleek Progress Line */}
          <div className="w-full h-1.5 bg-stone-300/60 dark:bg-slate-800 rounded-full overflow-hidden p-0.5 border border-amber-900/10">
            <div
              className="h-full bg-gradient-to-r from-[#7c4a27] via-amber-500 to-[#96562c] dark:from-amber-500 dark:to-[#96562c] rounded-full transition-all duration-75 ease-out shadow-[0_0_10px_rgba(254,243,199,0.8)]"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </div>

      {/* Footer: Copyright Icon | FinReg Tech ShipYard */}
      <footer className="w-full pb-3 pt-4 text-center z-10">
        <div className={`inline-flex items-center justify-center gap-2 text-xs font-semibold px-4 py-1.5 rounded-full border transition-colors ${
          isDarkMode
            ? 'bg-slate-900/80 border-slate-800 text-slate-400'
            : 'bg-white/80 border-stone-200 text-slate-600 shadow-xs'
        }`}>
          <Copyright className="w-3.5 h-3.5 text-[#7c4a27] dark:text-amber-400" />
          <span className="text-slate-300 dark:text-slate-700">|</span>
          <span className="tracking-wide font-bold">FinReg Tech ShipYard</span>
        </div>
      </footer>
    </div>
  );
}
