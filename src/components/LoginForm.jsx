import React, { useState, useEffect } from 'react';
import { Mail, Lock, Eye, EyeOff, BarChart3 } from 'lucide-react';
import Navbar from './Navbar';
import FlashPage from './FlashPage';
import LandingPage from './LandingPage';
import CredentialsVerified from './CredentialsVerified';
import TwoFactorAuth from './TwoFactorAuth';
import VerificationSuccessful from './VerificationSuccessful';
import DashboardView from './DashboardView';

export default function LoginForm({ isDarkMode = true }) {
  // Steps: 'flash' | 'landing' | 'login' | 'verifying' | 'dashboard'
  const [step, setStep] = useState('flash');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);

  // Handle Login submission
  const handleLoginSubmit = (e) => {
    e.preventDefault();
    if (!email || !password) return;

    // Transition to Screen 2: Credentials Verified screen
    setStep('verifying');
  };

  // Timer Manager:
  // Auto-advance directly from 'verifying' (Credentials Verified) to 'dashboard' after 4 seconds
  useEffect(() => {
    if (step === 'verifying') {
      const timer = setTimeout(() => {
        setStep('dashboard');
      }, 4000); // 4 seconds delay
      return () => clearTimeout(timer);
    }
  }, [step]);

  const isFormValid = email.trim().length > 0 && password.trim().length > 0;

  // STEP 0: FLASH PAGE (3 seconds auto-timer)
  if (step === 'flash') {
    return (
      <FlashPage
        isDarkMode={isDarkMode}
        onFinish={() => setStep('landing')}
      />
    );
  }

  // STEP 0.5: LANDING PAGE
  if (step === 'landing') {
    return (
      <LandingPage
        isDarkMode={isDarkMode}
        onGetStarted={() => setStep('login')}
      />
    );
  }

  // STEP 5: FULL BUILDER DASHBOARD VIEW (Rendered full-screen matching uploaded reference image!)
  if (step === 'dashboard') {
    return (
      <DashboardView
        isDarkMode={isDarkMode}
        onSignOut={() => setStep('login')}
      />
    );
  }

  // STEPS 1-4: AUTHENTICATION FLOW CARDS WRAPPED WITH TOP NAVBAR
  return (
    <div className="min-h-screen flex flex-col bg-[#121214] text-slate-100">
      {/* Top Header Navigation */}
      <Navbar />

      {/* Centered Auth Card Container */}
      <main className="flex-1 flex items-center justify-center p-4 sm:p-6 md:p-10">
        <div
          className={`w-full max-w-[520px] mx-auto rounded-2xl p-8 sm:p-10 transition-all duration-300 border ${
            isDarkMode
              ? 'bg-[#1a1a1e] border-slate-800 text-slate-100 shadow-[0_4px_24px_rgba(0,0,0,0.3)] hover:border-[#96562c] hover:shadow-[0_8px_32px_rgba(150,86,44,0.25)]'
              : 'bg-white border-slate-200/90 text-slate-800 shadow-[0_4px_24px_rgba(0,0,0,0.06)] hover:border-[#7c4a27] hover:shadow-[0_8px_32px_rgba(124,74,39,0.18)]'
          }`}
        >
          {/* STEP 1: INITIAL LOGIN FORM */}
          {step === 'login' && (
            <div>
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

              {/* Login Form */}
              <form onSubmit={handleLoginSubmit} className="space-y-5">
                {/* Email Field */}
                <div className="space-y-1.5 text-left">
                  <label htmlFor="email-input" className={`block text-sm font-semibold ${
                    isDarkMode ? 'text-slate-200' : 'text-slate-700'
                  }`}>
                    Email Address
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                      <Mail className="w-5 h-5" />
                    </div>
                    <input
                      id="email-input"
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="you@organization.com"
                      className={`w-full pl-10 pr-4 py-3 rounded-xl text-sm placeholder-slate-400 focus:outline-none transition-all border ${
                        isDarkMode
                          ? 'bg-slate-800/80 border-slate-700 text-slate-100 hover:border-[#96562c] focus:border-[#96562c] focus:ring-4 focus:ring-[#96562c]/20'
                          : 'bg-white border-slate-200 text-slate-900 hover:border-[#7c4a27] focus:border-[#7c4a27] focus:ring-4 focus:ring-[#7c4a27]/15'
                      }`}
                    />
                  </div>
                </div>

                {/* Password Field */}
                <div className="space-y-1.5 text-left">
                  <label htmlFor="password-input" className={`block text-sm font-semibold ${
                    isDarkMode ? 'text-slate-200' : 'text-slate-700'
                  }`}>
                    Password
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                      <Lock className="w-5 h-5" />
                    </div>
                    <input
                      id="password-input"
                      type={showPassword ? 'text' : 'password'}
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Enter your password"
                      className={`w-full pl-10 pr-20 py-3 rounded-xl text-sm placeholder-slate-400 focus:outline-none transition-all border ${
                        isDarkMode
                          ? 'bg-slate-800/80 border-slate-700 text-slate-100 hover:border-[#96562c] focus:border-[#96562c] focus:ring-4 focus:ring-[#96562c]/20'
                          : 'bg-white border-slate-200 text-slate-900 hover:border-[#7c4a27] focus:border-[#7c4a27] focus:ring-4 focus:ring-[#7c4a27]/15'
                      }`}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className={`absolute inset-y-0 right-0 pr-3.5 flex items-center gap-1 text-xs font-medium cursor-pointer transition-colors ${
                        isDarkMode ? 'text-slate-400 hover:text-slate-200' : 'text-slate-500 hover:text-slate-800'
                      }`}
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      <span>{showPassword ? 'Hide' : 'Show'}</span>
                    </button>
                  </div>
                </div>

                {/* Remember Me & Forgot Password */}
                <div className="flex items-center justify-between pt-0.5 text-sm">
                  <label className={`flex items-center gap-2.5 cursor-pointer select-none text-xs sm:text-sm ${
                    isDarkMode ? 'text-slate-400' : 'text-slate-600'
                  }`}>
                    <input
                      type="checkbox"
                      checked={rememberMe}
                      onChange={(e) => setRememberMe(e.target.checked)}
                      className="w-4 h-4 text-[#7c4a27] rounded border-slate-300 focus:ring-[#7c4a27] accent-[#7c4a27] cursor-pointer"
                    />
                    <span className="font-normal">Remember me on this device</span>
                  </label>

                  <a
                    href="#forgot-password"
                    onClick={(e) => e.preventDefault()}
                    className="text-[#7c4a27] dark:text-amber-400 hover:underline font-semibold text-xs sm:text-sm transition-colors"
                  >
                    Forgot password?
                  </a>
                </div>

                {/* Login Button (Rich Brown) */}
                <button
                  type="submit"
                  disabled={!isFormValid}
                  className={`w-full py-3.5 px-4 rounded-xl font-semibold text-sm transition-all duration-200 flex items-center justify-center gap-2 ${
                    isFormValid
                      ? 'bg-[#7c4a27] hover:bg-[#633a1e] dark:bg-[#96562c] dark:hover:bg-[#7c4a27] text-white shadow-md shadow-amber-950/20 active:scale-[0.99] cursor-pointer'
                      : isDarkMode
                      ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                      : 'bg-slate-200 text-slate-400 cursor-not-allowed'
                  }`}
                >
                  Login
                </button>
              </form>

              {/* Divider */}
              <div className="relative my-7">
                <div className="absolute inset-0 flex items-center">
                  <div className={`w-full border-t ${isDarkMode ? 'border-slate-800' : 'border-slate-200'}`} />
                </div>
                <div className="relative flex justify-center text-xs">
                  <span className={`px-3 font-medium ${isDarkMode ? 'bg-[#1a1a1e] text-slate-500' : 'bg-white text-slate-400'}`}>
                    or
                  </span>
                </div>
              </div>

              {/* Sign Up Footer */}
              <p className={`text-center text-xs sm:text-sm ${isDarkMode ? 'text-slate-400' : 'text-slate-600'}`}>
                Don't have an account?{' '}
                <a
                  href="#signup"
                  onClick={(e) => e.preventDefault()}
                  className="text-[#7c4a27] dark:text-amber-400 hover:underline font-semibold ml-1 transition-colors"
                >
                  Sign Up
                </a>
              </p>
            </div>
          )}

          {/* STEP 2: CREDENTIALS VERIFIED LOADING SCREEN - LASTS 4 SECONDS THEN GOES DIRECTLY TO DASHBOARD */}
          {step === 'verifying' && <CredentialsVerified isDarkMode={isDarkMode} />}
        </div>
      </main>
    </div>
  );
}
