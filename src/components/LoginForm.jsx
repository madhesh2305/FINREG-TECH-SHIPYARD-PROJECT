import React, { useState, useEffect } from 'react';
import { Mail, Lock, Eye, EyeOff, BarChart3, ChevronDown, ArrowLeft } from 'lucide-react';
import Navbar from './Navbar';
import FlashPage from './FlashPage';
import LandingPage from './LandingPage';
import CredentialsVerified from './CredentialsVerified';
import TwoFactorAuth from './TwoFactorAuth';
import VerificationSuccessful from './VerificationSuccessful';
import DashboardView from './DashboardView';
import AdvisorDashboardView from './AdvisorDashboardView';

import { loginUser } from '../services/authService';

export default function LoginForm({ isDarkMode = true }) {
  // Steps: 'flash' | 'landing' | 'login' | 'verifying' | 'dashboard'
  const [step, setStep] = useState('flash');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loginError, setLoginError] = useState('');
  const [userRole, setUserRole] = useState('BUILDER'); // 'BUILDER' | 'ADVISOR'
  const [selectedRole, setSelectedRole] = useState('Builder / Project Owner');

  // Administrator Sign In states matching media_1791714229768_980157a3.png
  const [adminEmail, setAdminEmail] = useState('');
  const [adminPassword, setAdminPassword] = useState('');
  const [adminId, setAdminId] = useState('');
  const [adminAccessKey, setAdminAccessKey] = useState('');
  const [adminResponse, setAdminResponse] = useState('Authorized Admin session');
  const [adminRememberMe, setAdminRememberMe] = useState(false);
  const [adminShowPassword, setAdminShowPassword] = useState(false);
  const [adminError, setAdminError] = useState('');

  const handleAdminSubmit = (e) => {
    e.preventDefault();
    setAdminError('');

    if (adminResponse === 'Unauthorized Admin session') {
      setAdminError('Access denied: Selected backend response indicates an unauthorized session.');
      return;
    }

    setUserRole('BUILDER');
    setStep('verifying');
  };

  // Handle Login submission via POST /auth/login with strict credential and role validation
  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setLoginError('');

    const cleanEmail = email.toLowerCase().trim();
    const cleanPassword = password.trim();

    if (!cleanEmail || !cleanPassword) return;

    const isBuilderRole =
      selectedRole === 'Builder / Project Owner' || selectedRole === 'Builder';
    const isAdvisorRole = selectedRole === 'Advisor';

    // 1. Builder login: requires builder@gmail.com + pwd 'builder' + Prototype role as Builder
    if (
      cleanEmail === 'builder@gmail.com' &&
      cleanPassword === 'builder' &&
      isBuilderRole
    ) {
      setUserRole('BUILDER');
      setIsSubmitting(true);
      try {
        await loginUser(cleanEmail, cleanPassword);
      } catch (err) {
        console.warn('Login call processed:', err.message);
      } finally {
        setIsSubmitting(false);
        setStep('verifying');
      }
    }
    // 2. Advisor login: requires advisor@gmail.com + pwd 'advisor' + Prototype role as Advisor
    else if (
      cleanEmail === 'advisor@gmail.com' &&
      cleanPassword === 'advisor' &&
      isAdvisorRole
    ) {
      setUserRole('ADVISOR');
      setIsSubmitting(true);
      try {
        await loginUser(cleanEmail, cleanPassword);
      } catch (err) {
        console.warn('Login call processed:', err.message);
      } finally {
        setIsSubmitting(false);
        setStep('verifying');
      }
    }
    // 3. Detailed role/credential mismatch validation
    else {
      if (cleanEmail === 'builder@gmail.com' && cleanPassword === 'builder' && !isBuilderRole) {
        setLoginError("Role mismatch. Please select 'Builder / Project Owner' as the role for builder@gmail.com.");
      } else if (cleanEmail === 'advisor@gmail.com' && cleanPassword === 'advisor' && !isAdvisorRole) {
        setLoginError("Role mismatch. Please select 'Advisor' as the role for advisor@gmail.com.");
      } else if (isBuilderRole) {
        setLoginError("Invalid credentials for Builder role. Use builder@gmail.com with password 'builder'.");
      } else if (isAdvisorRole) {
        setLoginError("Invalid credentials for Advisor role. Use advisor@gmail.com with password 'advisor'.");
      } else {
        setLoginError("Invalid credentials or role mismatch. Please select the matching role and enter valid credentials.");
      }
    }
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

  // STEP 5: FULL DASHBOARD VIEW (Renders Builder Workspace or Advisor Workspace dynamically)
  if (step === 'dashboard') {
    if (userRole === 'ADVISOR') {
      return (
        <AdvisorDashboardView
          isDarkMode={isDarkMode}
          onSignOut={() => setStep('login')}
        />
      );
    }

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
          className={`w-full max-w-[700px] mx-auto rounded-3xl p-8 sm:p-10 md:p-12 transition-all duration-300 border ${
            isDarkMode
              ? 'bg-[#161619] border-slate-800 text-slate-100 shadow-[0_12px_40px_rgba(0,0,0,0.45)]'
              : 'bg-white border-slate-200/90 text-slate-800 shadow-[0_12px_40px_rgba(0,0,0,0.08)]'
          }`}
        >
          {/* STEP 1: INITIAL LOGIN FORM MATCHING media_1791713110077_089f810b.png */}
          {step === 'login' && (
            <div className="space-y-6 animate-fadeIn">
              {/* Top Left Navigation: Back to home */}
              <div className="text-left">
                <button
                  type="button"
                  onClick={() => setStep('landing')}
                  className="inline-flex items-center gap-2 text-xs sm:text-sm font-semibold text-slate-400 hover:text-amber-400 transition-colors cursor-pointer group"
                >
                  <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
                  <span>Back to home</span>
                </button>
              </div>

              {/* Header Titles */}
              <div className="text-left">
                <span className="text-[11px] font-mono font-extrabold tracking-widest text-slate-500 uppercase block mb-2">
                  FINREGTECH SHIPYARD
                </span>
                <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-100">
                  Welcome back
                </h1>
                <p className="text-xs sm:text-sm text-slate-400 mt-2 font-normal">
                  Sign in to manage your regulatory projects and workflows.
                </p>
              </div>

              {/* Login Form */}
              <form onSubmit={handleLoginSubmit} className="space-y-5">
                {/* Login Error Alert */}
                {loginError && (
                  <div className="p-3 rounded-xl bg-rose-950/70 border border-rose-800 text-rose-300 text-xs font-semibold text-left animate-fadeIn">
                    {loginError}
                  </div>
                )}

                {/* Email Field */}
                <div className="space-y-1.5 text-left">
                  <label htmlFor="email-input" className="block text-xs sm:text-sm font-semibold text-slate-200">
                    Email Address
                  </label>
                  <input
                    id="email-input"
                    type="email"
                    required
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      if (loginError) setLoginError('');
                    }}
                    placeholder="name@organization.com"
                    className="w-full px-4 py-3 rounded-xl text-xs sm:text-sm bg-[#121214] border border-slate-700/80 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500 transition-colors"
                  />
                </div>

                {/* Password Field */}
                <div className="space-y-1.5 text-left">
                  <label htmlFor="password-input" className="block text-xs sm:text-sm font-semibold text-slate-200">
                    Password
                  </label>
                  <div className="relative">
                    <input
                      id="password-input"
                      type={showPassword ? 'text' : 'password'}
                      required
                      value={password}
                      onChange={(e) => {
                        setPassword(e.target.value);
                        if (loginError) setLoginError('');
                      }}
                      placeholder="Enter your password"
                      className="w-full px-4 py-3 rounded-xl text-xs sm:text-sm bg-[#121214] border border-slate-700/80 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500 transition-colors pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-500 hover:text-slate-300 cursor-pointer transition-colors"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                {/* Prototype assigned account role */}
                <div className="space-y-1.5 text-left">
                  <label htmlFor="role-select" className="block text-xs sm:text-sm font-semibold text-slate-200">
                    Prototype assigned account role
                  </label>
                  <div className="relative">
                    <select
                      id="role-select"
                      value={selectedRole}
                      onChange={(e) => setSelectedRole(e.target.value)}
                      className="w-full px-4 py-3 rounded-xl text-xs sm:text-sm bg-[#121214] border border-slate-700/80 text-slate-100 focus:outline-none focus:border-amber-500 appearance-none cursor-pointer pr-10 transition-colors"
                    >
                      <option value="Builder / Project Owner">Builder / Project Owner</option>
                      <option value="Advisor">Advisor</option>
                    </select>
                    <div className="absolute inset-y-0 right-0 pr-3.5 flex items-center pointer-events-none text-slate-400">
                      <ChevronDown className="w-4 h-4" />
                    </div>
                  </div>
                </div>

                {/* Information hint box */}
                <div className="p-3.5 rounded-xl border border-slate-800 bg-[#121214] text-xs text-slate-400 font-normal leading-relaxed text-left">
                  Prototype selector only. Production access is determined by the authenticated account's backend-assigned role.
                </div>

                {/* Remember Me & Forgot Password */}
                <div className="flex items-center justify-between pt-1 text-xs sm:text-sm">
                  <label className="flex items-center gap-2.5 cursor-pointer select-none text-slate-300">
                    <input
                      type="checkbox"
                      checked={rememberMe}
                      onChange={(e) => setRememberMe(e.target.checked)}
                      className="w-4 h-4 rounded border-slate-700 bg-[#121214] text-amber-500 focus:ring-amber-500 accent-amber-500 cursor-pointer"
                    />
                    <span>Remember me</span>
                  </label>

                  <a
                    href="#forgot-password"
                    onClick={(e) => e.preventDefault()}
                    className="text-amber-500 hover:text-amber-400 font-bold text-xs sm:text-sm transition-colors cursor-pointer"
                  >
                    Forgot password?
                  </a>
                </div>

                {/* Log in Button */}
                <button
                  type="submit"
                  disabled={!isFormValid}
                  className={`w-full py-3.5 px-4 rounded-xl font-bold text-xs sm:text-sm transition-all duration-200 flex items-center justify-center ${
                    isFormValid
                      ? 'bg-[#e59b38] hover:bg-[#d68a27] text-slate-950 shadow-md cursor-pointer active:scale-[0.99]'
                      : 'bg-[#e59b38]/50 text-slate-950/60 cursor-not-allowed'
                  }`}
                >
                  Log in
                </button>
              </form>

              {/* Footer matching media_1791713597320_8e3c87db.png */}
              <div className="pt-6 -mx-8 sm:-mx-10 md:-mx-12 px-8 sm:px-10 md:px-12 border-t border-slate-800 text-center">
                <p className="text-xs sm:text-sm text-slate-400">
                  New to ShipYard?{' '}
                  <button
                    type="button"
                    onClick={() => setStep('signup')}
                    className="text-amber-500 hover:text-amber-400 font-semibold cursor-pointer transition-colors inline"
                  >
                    Sign up
                  </button>
                  <span className="mx-1.5 text-slate-400 font-bold">·</span>
                  <button
                    type="button"
                    onClick={() => {
                      setStep('admin-login');
                    }}
                    className="text-amber-500 hover:text-amber-400 font-semibold cursor-pointer transition-colors inline"
                  >
                    Admin Login
                  </button>
                </p>
              </div>
            </div>
          )}

          {/* STEP: ADMINISTRATOR SIGN IN (Matching media_1791714229768_980157a3.png & media_1791714241674_8afcfed5.png) */}
          {step === 'admin-login' && (
            <div className="space-y-6 animate-fadeIn">
              {/* Header Titles */}
              <div className="text-left">
                <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-100">
                  Administrator sign in
                </h1>
                <p className="text-xs sm:text-sm text-slate-400 mt-2 font-normal leading-relaxed">
                  Enter company-provisioned credentials for the global Admin workspace.
                </p>
              </div>

              {/* Form */}
              <form onSubmit={handleAdminSubmit} className="space-y-4">
                {/* Admin Error Alert */}
                {adminError && (
                  <div className="p-3 rounded-xl bg-rose-950/70 border border-rose-800 text-rose-300 text-xs font-semibold text-left animate-fadeIn">
                    {adminError}
                  </div>
                )}

                {/* Email Address */}
                <div className="space-y-1.5 text-left">
                  <label htmlFor="admin-email" className="block text-xs sm:text-sm font-semibold text-slate-200">
                    Email Address
                  </label>
                  <input
                    id="admin-email"
                    type="email"
                    required
                    value={adminEmail}
                    onChange={(e) => setAdminEmail(e.target.value)}
                    placeholder="name@organization.com"
                    className="w-full px-4 py-3 rounded-xl text-xs sm:text-sm bg-[#121214] border border-slate-700/80 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500 transition-colors"
                  />
                </div>

                {/* Password */}
                <div className="space-y-1.5 text-left">
                  <label htmlFor="admin-password" className="block text-xs sm:text-sm font-semibold text-slate-200">
                    Password
                  </label>
                  <div className="relative">
                    <input
                      id="admin-password"
                      type={adminShowPassword ? 'text' : 'password'}
                      required
                      value={adminPassword}
                      onChange={(e) => setAdminPassword(e.target.value)}
                      placeholder="Enter your password"
                      className="w-full px-4 py-3 rounded-xl text-xs sm:text-sm bg-[#121214] border border-slate-700/80 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500 transition-colors pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setAdminShowPassword(!adminShowPassword)}
                      className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-500 hover:text-slate-300 cursor-pointer transition-colors"
                    >
                      {adminShowPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                {/* Admin ID */}
                <div className="space-y-1.5 text-left">
                  <label htmlFor="admin-id" className="block text-xs sm:text-sm font-semibold text-slate-200">
                    Admin ID
                  </label>
                  <input
                    id="admin-id"
                    type="text"
                    required
                    value={adminId}
                    onChange={(e) => setAdminId(e.target.value)}
                    placeholder="Company-issued administrator ID"
                    className="w-full px-4 py-3 rounded-xl text-xs sm:text-sm bg-[#121214] border border-slate-700/80 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500 transition-colors"
                  />
                </div>

                {/* Admin Access Key */}
                <div className="space-y-1.5 text-left">
                  <label htmlFor="admin-key" className="block text-xs sm:text-sm font-semibold text-slate-200">
                    Admin Access Key
                  </label>
                  <input
                    id="admin-key"
                    type="text"
                    required
                    value={adminAccessKey}
                    onChange={(e) => setAdminAccessKey(e.target.value)}
                    placeholder="Enter company-issued access key"
                    className="w-full px-4 py-3 rounded-xl text-xs sm:text-sm bg-[#121214] border border-slate-700/80 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500 transition-colors"
                  />
                </div>

                {/* Prototype backend response */}
                <div className="space-y-1.5 text-left">
                  <label htmlFor="admin-response" className="block text-xs sm:text-sm font-semibold text-slate-200">
                    Prototype backend response
                  </label>
                  <div className="relative">
                    <select
                      id="admin-response"
                      value={adminResponse}
                      onChange={(e) => setAdminResponse(e.target.value)}
                      className="w-full px-4 py-3 rounded-xl text-xs sm:text-sm bg-[#121214] border border-slate-700/80 text-slate-100 focus:outline-none focus:border-amber-500 appearance-none cursor-pointer pr-10 transition-colors"
                    >
                      <option value="Authorized Admin session">Authorized Admin session</option>
                      <option value="Unauthorized Admin session">Unauthorized Admin session</option>
                    </select>
                    <div className="absolute inset-y-0 right-0 pr-3.5 flex items-center pointer-events-none text-slate-400">
                      <ChevronDown className="w-4 h-4" />
                    </div>
                  </div>
                </div>

                {/* Prototype Note Box */}
                <div className="p-3.5 rounded-xl border border-slate-800 bg-[#121214] text-xs text-slate-400 font-normal leading-relaxed text-left">
                  Prototype only: production authentication must verify credentials, assigned Admin role, and the additional key on the backend. No real key is stored or exposed here.
                </div>

                {/* Remember Me & Forgot Password */}
                <div className="flex items-center justify-between pt-1 text-xs sm:text-sm">
                  <label className="flex items-center gap-2.5 cursor-pointer select-none text-slate-300">
                    <input
                      type="checkbox"
                      checked={adminRememberMe}
                      onChange={(e) => setAdminRememberMe(e.target.checked)}
                      className="w-4 h-4 rounded border-slate-700 bg-[#121214] text-amber-500 focus:ring-amber-500 accent-amber-500 cursor-pointer"
                    />
                    <span>Remember me</span>
                  </label>

                  <a
                    href="#forgot-password"
                    onClick={(e) => e.preventDefault()}
                    className="text-amber-500 hover:text-amber-400 font-bold text-xs sm:text-sm transition-colors cursor-pointer"
                  >
                    Forgot password?
                  </a>
                </div>

                {/* Verify Admin credentials Button */}
                <button
                  type="submit"
                  className="w-full py-3.5 px-4 rounded-xl font-bold text-xs sm:text-sm transition-all duration-200 flex items-center justify-center bg-[#e59b38] hover:bg-[#d68a27] text-slate-950 shadow-md cursor-pointer active:scale-[0.99]"
                >
                  Verify Admin credentials
                </button>
              </form>

              {/* Bottom Footer: Back to user login */}
              <div className="pt-6 -mx-8 sm:-mx-10 md:-mx-12 px-8 sm:px-10 md:px-12 border-t border-slate-800 text-center">
                <button
                  type="button"
                  onClick={() => setStep('login')}
                  className="text-amber-500 hover:text-amber-400 font-semibold text-xs sm:text-sm cursor-pointer transition-colors"
                >
                  Back to user login
                </button>
              </div>
            </div>
          )}

          {/* STEP: CREATE YOUR ACCOUNT (Matching media_1791309101386.png) */}
          {step === 'signup' && (
            <div className="space-y-5 text-left animate-fadeIn">
              <div>
                <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-100">
                  Create your account
                </h1>
                <p className="text-xs sm:text-sm text-slate-400 mt-1">
                  Set up your secure ShipYard workspace account.
                </p>
              </div>

              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  setStep('verifying');
                }}
                className="space-y-4"
              >
                {/* Full name */}
                <div className="space-y-1.5">
                  <label className="block text-xs font-semibold text-slate-300">
                    Full name
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="Your full name"
                    className="w-full px-4 py-3 rounded-xl text-xs sm:text-sm bg-slate-800/80 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-[#96562c] focus:ring-2 focus:ring-[#96562c]/20 transition-all"
                  />
                </div>

                {/* Email */}
                <div className="space-y-1.5">
                  <label className="block text-xs font-semibold text-slate-300">
                    Email
                  </label>
                  <input
                    type="email"
                    required
                    placeholder="name@organization.com"
                    className="w-full px-4 py-3 rounded-xl text-xs sm:text-sm bg-slate-800/80 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-[#96562c] focus:ring-2 focus:ring-[#96562c]/20 transition-all"
                  />
                </div>

                {/* Password & Confirm Password */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="block text-xs font-semibold text-slate-300">
                      Password
                    </label>
                    <input
                      type="password"
                      required
                      placeholder="Create a password"
                      className="w-full px-4 py-3 rounded-xl text-xs sm:text-sm bg-slate-800/80 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-[#96562c] focus:ring-2 focus:ring-[#96562c]/20 transition-all"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="block text-xs font-semibold text-slate-300">
                      Confirm password
                    </label>
                    <input
                      type="password"
                      required
                      placeholder="Repeat password"
                      className="w-full px-4 py-3 rounded-xl text-xs sm:text-sm bg-slate-800/80 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-[#96562c] focus:ring-2 focus:ring-[#96562c]/20 transition-all"
                    />
                  </div>
                </div>

                {/* Organization */}
                <div className="space-y-1.5">
                  <label className="block text-xs font-semibold text-slate-300">
                    Organization
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="Organization name"
                    className="w-full px-4 py-3 rounded-xl text-xs sm:text-sm bg-slate-800/80 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-[#96562c] focus:ring-2 focus:ring-[#96562c]/20 transition-all"
                  />
                </div>

                {/* Role */}
                <div className="space-y-1.5">
                  <label className="block text-xs font-semibold text-slate-300">
                    Role
                  </label>
                  <select
                    defaultValue="Builder"
                    className="w-full px-4 py-3 rounded-xl text-xs sm:text-sm bg-slate-800/80 border border-slate-700 text-slate-100 focus:outline-none focus:border-[#96562c] cursor-pointer transition-all"
                  >
                    <option value="Builder">Builder</option>
                    <option value="Advisor">Advisor</option>
                    <option value="Administrator">Administrator</option>
                  </select>
                </div>

                {/* Information hint box */}
                <div className="p-3.5 rounded-xl border border-slate-800 bg-[#121214] text-xs text-slate-400 font-medium">
                  Complete all required fields to create your account.
                </div>

                {/* Create account primary button */}
                <button
                  type="submit"
                  className="w-full py-3.5 px-4 rounded-xl bg-[#f59e0b] hover:bg-[#d97706] text-slate-950 font-extrabold text-sm shadow-md transition-all cursor-pointer border border-amber-300/60 active:scale-[0.99]"
                >
                  Create account
                </button>

                {/* Back to Login button */}
                <button
                  type="button"
                  onClick={() => setStep('login')}
                  className="w-full py-3 px-4 rounded-xl border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-200 font-bold text-xs sm:text-sm cursor-pointer transition-colors mt-2"
                >
                  Back to Login
                </button>
              </form>
            </div>
          )}

          {/* STEP 2: CREDENTIALS VERIFIED LOADING SCREEN - LASTS 4 SECONDS THEN GOES DIRECTLY TO DASHBOARD */}
          {step === 'verifying' && <CredentialsVerified isDarkMode={isDarkMode} />}
        </div>
      </main>
    </div>
  );
}
