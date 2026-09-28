import React, { useState } from 'react';
import { ArrowRight, Ship, ShieldCheck, Users, Landmark, Sparkles, CheckCircle2, ChevronRight } from 'lucide-react';
import Navbar from './Navbar';

export default function LandingPage({ isDarkMode = true, onGetStarted }) {
  const [isBtnTouched, setIsBtnTouched] = useState(false);
  const [activeCardId, setActiveCardId] = useState(null);

  const features = [
    {
      id: 1,
      icon: Landmark,
      title: 'Seamless Regulatory Navigation',
      text: 'Empowering financial institutions and builders to navigate complex regulatory landscapes seamlessly.',
    },
    {
      id: 2,
      icon: Sparkles,
      title: 'Centralized Compliance Workflows',
      text: 'Centralize your AML/CTF, KYC, and compliance workflows with real-time advisor oversight.',
    },
    {
      id: 3,
      icon: Users,
      title: 'Expert Collaboration & Audits',
      text: 'Collaborate directly with top-tier financial regulatory experts and automated audit toolkits.',
    },
    {
      id: 4,
      icon: ShieldCheck,
      title: 'Accelerated Time-To-Market',
      text: 'Accelerate time-to-market while guaranteeing strict adherence to global regulatory standards.',
    },
  ];

  return (
    <div className={`relative min-h-screen w-full flex flex-col justify-between font-sans transition-colors duration-500 overflow-x-hidden ${
      isDarkMode ? 'bg-[#121214] text-slate-100' : 'bg-[#e2e8f0] text-slate-800'
    }`}>
      {/* Background Ambient Radial Spotlight & Subtle Grid */}
      <div className="absolute inset-0 pointer-events-none flex items-center justify-center overflow-hidden">
        <div className={`w-[600px] h-[600px] rounded-full blur-3xl opacity-35 transition-all duration-700 animate-pulseGlow ${
          isDarkMode
            ? 'bg-gradient-to-tr from-[#96562c]/30 via-amber-600/20 to-transparent'
            : 'bg-gradient-to-tr from-[#7c4a27]/20 via-amber-200/50 to-transparent'
        }`} />
        <div className="absolute inset-0 bg-[radial-gradient(#7c4a27_1px,transparent_1px)] [background-size:32px_32px] opacity-[0.06] dark:opacity-[0.1]" />
      </div>

      {/* Top Header Navbar with Get Started in top right corner */}
      <Navbar onGetStarted={onGetStarted} />

      {/* Main Center Hero Section */}
      <main className="relative z-10 flex-1 flex flex-col items-center justify-center p-4 sm:p-8 md:p-12 text-center max-w-4xl mx-auto space-y-8 animate-fadeIn my-auto">
        
        {/* Floating Ship Icon Badge */}
        <div className="relative group cursor-pointer">
          <div className="absolute -inset-3 bg-gradient-to-r from-[#7c4a27] via-amber-500 to-[#96562c] rounded-3xl blur-lg opacity-40 animate-pulseGlow" />
          <div className="relative w-18 h-18 sm:w-22 sm:h-22 bg-gradient-to-br from-[#7c4a27] via-[#8d542c] to-[#5c371d] dark:from-[#96562c] dark:via-[#7c4a27] dark:to-[#4a2912] rounded-3xl flex items-center justify-center shadow-[0_15px_40px_rgba(124,74,39,0.3)] border-2 border-amber-200/50 animate-floatSlow transition-transform duration-300 group-hover:scale-105">
            <Ship className="w-10 h-10 sm:w-12 sm:h-12 text-[#fef3c7] stroke-[2.2] drop-shadow-md" />
          </div>
        </div>

        {/* Title Header */}
        <div className="space-y-2 max-w-2xl">
          <h1 className="text-3xl sm:text-5xl font-black tracking-tight text-[#7c4a27] dark:text-amber-400 uppercase drop-shadow-xs">
            FinReg Tech ShipYard
          </h1>
          <p className="text-xs sm:text-sm font-extrabold tracking-widest text-slate-500 dark:text-slate-400 uppercase">
            FCC Project Cockpit & Regulatory Ecosystem
          </p>
        </div>

        {/* 4 Lines Feature Card Box with Cream Lighting & Zoom-In Effects */}
        <div className={`w-full p-6 sm:p-8 rounded-3xl border transition-all duration-300 shadow-xl ${
          isDarkMode
            ? 'bg-[#1a1a1e]/90 border-slate-800 backdrop-blur-md shadow-black/40'
            : 'bg-white/95 border-stone-200/90 backdrop-blur-md shadow-stone-300/40'
        }`}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {features.map((feat) => {
              const Icon = feat.icon;
              const isCardActive = activeCardId === feat.id;

              return (
                <div
                  key={feat.id}
                  onClick={() => setActiveCardId(isCardActive ? null : feat.id)}
                  title="Click box to toggle enlighten glow & zoom-in"
                  className={`p-4 sm:p-5 rounded-2xl border text-left transition-all duration-300 cursor-pointer flex items-start gap-3.5 ${
                    isCardActive
                      ? isDarkMode
                        ? 'bg-slate-800/90 border-[#96562c] scale-[1.02] shadow-[0_0_25px_rgba(251,191,36,0.3)] ring-2 ring-[#96562c]/40'
                        : 'bg-[#fdfdf9] border-[#7c4a27] scale-[1.02] shadow-[0_0_30px_rgba(254,243,199,0.95),0_10px_28px_rgba(124,74,39,0.2)] ring-4 ring-amber-100/90'
                      : isDarkMode
                      ? 'bg-slate-900/60 border-slate-800 hover:border-[#96562c] hover:scale-[1.01] hover:bg-slate-800/60'
                      : 'bg-stone-50/70 border-stone-200/80 hover:border-[#7c4a27] hover:scale-[1.01] hover:bg-stone-100/80'
                  }`}
                >
                  <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border mt-0.5 transition-colors ${
                    isCardActive || isDarkMode
                      ? 'bg-[#96562c] text-white border-amber-400/40'
                      : 'bg-stone-100 text-[#7c4a27] border-stone-200'
                  }`}>
                    <Icon className="w-5 h-5 stroke-[2.2]" />
                  </div>
                  <div className="space-y-1 flex-1">
                    <h3 className={`text-xs sm:text-sm font-bold tracking-tight ${
                      isDarkMode ? 'text-slate-100' : 'text-slate-900'
                    }`}>
                      {feat.title}
                    </h3>
                    <p className={`text-xs sm:text-xs leading-relaxed font-medium ${
                      isDarkMode ? 'text-slate-400' : 'text-slate-600'
                    }`}>
                      {feat.text}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Category Pill Bar: Finance | Regulatory | Advisors */}
        <div className="pt-1 flex flex-col items-center gap-4 w-full">
          <div className={`inline-flex items-center justify-center gap-3 px-6 py-2.5 rounded-full border text-xs sm:text-sm font-extrabold uppercase tracking-wider transition-colors shadow-xs ${
            isDarkMode
              ? 'bg-slate-900/80 border-slate-800 text-amber-400'
              : 'bg-white/90 border-stone-200 text-[#7c4a27]'
          }`}>
            <span className="flex items-center gap-1.5">
              <Landmark className="w-3.5 h-3.5 text-[#7c4a27] dark:text-amber-400" />
              Finance
            </span>
            <span className="text-slate-300 dark:text-slate-700">|</span>
            <span className="flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-[#7c4a27] dark:text-amber-400" />
              Regulatory
            </span>
            <span className="text-slate-300 dark:text-slate-700">|</span>
            <span className="flex items-center gap-1.5">
              <Users className="w-3.5 h-3.5 text-[#7c4a27] dark:text-amber-400" />
              Advisors
            </span>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 w-full py-4 text-center text-xs font-semibold text-slate-500 border-t border-slate-200/60 dark:border-slate-800/60">
        © | FinReg Tech ShipYard
      </footer>
    </div>
  );
}
