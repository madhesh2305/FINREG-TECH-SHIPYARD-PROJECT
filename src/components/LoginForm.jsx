import React, { useState, useEffect } from 'react';
import { Mail, Lock, Eye, EyeOff, BarChart3, ChevronDown, ArrowLeft, Loader2, CheckCircle2 } from 'lucide-react';
import Navbar from './Navbar';
import FlashPage from './FlashPage';
import LandingPage from './LandingPage';
import CredentialsVerified from './CredentialsVerified';
import TwoFactorAuth from './TwoFactorAuth';
import VerificationSuccessful from './VerificationSuccessful';
import DashboardView from './DashboardView';
import AdvisorDashboardView from './AdvisorDashboardView';
import AdvisorExpertiseView, { ADVISOR_PROFILES } from './AdvisorExpertiseView';
import AdminDashboardView from './AdminDashboardView';

import { loginUser, registerUser, resetPassword, getCurrentUser, logoutUser } from '../services/authService';

export default function LoginForm({ isDarkMode = true }) {
  // Steps: 'flash' | 'landing' | 'login' | 'signup' | 'forgot-password' | 'admin-login' | 'verifying' | 'advisor-expertise' | 'dashboard'
  const [step, setStep] = useState('flash');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loginError, setLoginError] = useState('');
  const [userRole, setUserRole] = useState('BUILDER'); // 'BUILDER' | 'ADVISOR' | 'ADMIN'
  const [selectedRole, setSelectedRole] = useState('Builder / Project Owner');
  const [activeExpertise, setActiveExpertise] = useState(ADVISOR_PROFILES[0]);
  const [currentUser, setCurrentUser] = useState(null);

  // Sign up state (DEF-13)
  const [signupName, setSignupName] = useState('');
  const [signupEmail, setSignupEmail] = useState('');
  const [signupPassword, setSignupPassword] = useState('');
  const [signupConfirmPassword, setSignupConfirmPassword] = useState('');
  const [signupOrg, setSignupOrg] = useState('');
  const [signupRole, setSignupRole] = useState('Builder');
  const [signupError, setSignupError] = useState('');
  const [signupSuccess, setSignupSuccess] = useState('');
  const [isSigningUp, setIsSigningUp] = useState(false);

  // Forgot password state (DEF-02)
  const [resetEmail, setResetEmail] = useState('');
  const [resetError, setResetError] = useState('');
  const [resetSuccess, setResetSuccess] = useState('');
  const [isResetting, setIsResetting] = useState(false);

  // Administrator Sign In states matching media_1791714229768_980157a3.png
  const [adminEmail, setAdminEmail] = useState('');
  const [adminPassword, setAdminPassword] = useState('');
  const [adminId, setAdminId] = useState('');
  const [adminAccessKey, setAdminAccessKey] = useState('');
  const [adminResponse, setAdminResponse] = useState('Authorized Admin session');
  const [adminRememberMe, setAdminRememberMe] = useState(false);
  const [adminShowPassword, setAdminShowPassword] = useState(false);
  const [adminError, setAdminError] = useState('');

  // Pre-load persisted session if any
  useEffect(() => {
    async function initUser() {
      const user = await getCurrentUser();
      if (user) {
        setCurrentUser(user);
        const effectiveRole = (user.platform_role || user.role || '').toUpperCase();
        if (effectiveRole.includes('ADVISOR')) setUserRole('ADVISOR');
        else if (effectiveRole.includes('ADMIN')) setUserRole('ADMIN');
        else setUserRole('BUILDER');
      }
    }
    initUser();
  }, []);

  const handleAdminSubmit = async (e) => {
    e.preventDefault();
    setAdminError('');

    const cleanEmail = adminEmail.toLowerCase().trim();
    const cleanPassword = adminPassword.trim();
    const cleanId = adminId.trim();
    const cleanKey = adminAccessKey.trim();

    if (adminResponse === 'Unauthorized Admin session') {
      setAdminError('Access denied: Selected backend response indicates an unauthorized session.');
      return;
    }

    const isEmailValid = cleanEmail === 'admin@gmail.com';
    const isPasswordValid = cleanPassword === 'admin';
    const isIdValid = cleanId === '1234' || cleanId === 'admin';
    const isKeyValid = cleanKey === '1234' || cleanKey === 'admin';

    if (isEmailValid && isPasswordValid && isIdValid && isKeyValid) {
      const adminUser = {
        id: 'usr_admin_001',
        name: 'System Administrator',
        email: cleanEmail,
        role: 'ADMIN',
        platform_role: 'ADMIN',
      };
      setCurrentUser(adminUser);
      setUserRole('ADMIN');
      try {
        await loginUser(cleanEmail, cleanPassword);
      } catch (err) {
        // Fallback already saved
      }
      setStep('verifying');
    } else {
      setAdminError(
        'Invalid admin credentials. Please enter email "admin@gmail.com", password "admin", Admin ID "1234", and Admin Access Key "1234".'
      );
    }
  };

  // Handle Login submission with dynamic credentials and authoritative role routing (DEF-01, DEF-07)
  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setLoginError('');

    const cleanEmail = email.toLowerCase().trim();
    const cleanPassword = password.trim();

    if (!cleanEmail || !cleanPassword) return;

    setIsSubmitting(true);
    try {
      const authResult = await loginUser(cleanEmail, cleanPassword);
      const user = authResult?.user || {
        name: cleanEmail.split('@')[0],
        email: cleanEmail,
        role: selectedRole.toLowerCase().includes('advisor') ? 'ADVISOR' : selectedRole.toLowerCase().includes('admin') ? 'ADMIN' : 'BUILDER',
      };

      setCurrentUser(user);

      // DEF-01: Open dashboard and navigation appropriate to the authenticated user's effective role.
      // An Advisor should NOT be shown as a Builder.
      const effectiveRole = (user.platform_role || user.role || '').toUpperCase();
      if (effectiveRole.includes('ADVISOR')) {
        setUserRole('ADVISOR');
      } else if (effectiveRole.includes('ADMIN')) {
        setUserRole('ADMIN');
      } else {
        setUserRole('BUILDER');
      }

      setStep('verifying');
    } catch (err) {
      setLoginError(err.message || 'Invalid email or password. Please verify your credentials or sign up.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle User Registration Submission (DEF-13)
  const handleSignupSubmit = async (e) => {
    e.preventDefault();
    setSignupError('');
    setSignupSuccess('');

    if (signupPassword !== signupConfirmPassword) {
      setSignupError('Passwords do not match. Please verify your password entry.');
      return;
    }

    if (signupPassword.length < 4) {
      setSignupError('Password must be at least 4 characters long.');
      return;
    }

    setIsSigningUp(true);
    try {
      const res = await registerUser({
        name: signupName,
        email: signupEmail,
        password: signupPassword,
        organization: signupOrg,
        role: signupRole,
      });

      setSignupSuccess(`Account created successfully for ${res.user.name}! Proceeding to security verification...`);
      setCurrentUser(res.user);

      const effectiveRole = (res.user.platform_role || res.user.role || '').toUpperCase();
      if (effectiveRole.includes('ADVISOR')) setUserRole('ADVISOR');
      else if (effectiveRole.includes('ADMIN')) setUserRole('ADMIN');
      else setUserRole('BUILDER');

      setTimeout(() => {
        setStep('verifying');
      }, 1200);
    } catch (err) {
      // DEF-13: Report success only after confirmed record; show error when saving fails
      setSignupError(err.message || 'Failed to register account. Please check your details and retry.');
    } finally {
      setIsSigningUp(false);
    }
  };

  // Handle Password Reset Submission (DEF-02)
  const handleResetSubmit = async (e) => {
    e.preventDefault();
    setResetError('');
    setResetSuccess('');

    if (!resetEmail) {
      setResetError('Please enter your registered email address.');
      return;
    }

    setIsResetting(true);
    try {
      const res = await resetPassword(resetEmail);
      setResetSuccess(res.message);
    } catch (err) {
      // DEF-02: Show a message reflecting the actual result. Do not claim an email was sent if failed
      setResetError(err.message || 'Unable to process reset request. Please ensure the email is registered.');
    } finally {
      setIsResetting(false);
    }
  };

  // Auto-advance from 'verifying' (Credentials Verified) after 4 seconds
  useEffect(() => {
    if (step === 'verifying') {
      const timer = setTimeout(() => {
        if (userRole === 'ADVISOR') {
          setStep('advisor-expertise');
        } else {
          setStep('dashboard');
        }
      }, 3500);
      return () => clearTimeout(timer);
    }
  }, [step, userRole]);

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

  // STEP 4.5: ADVISOR EXPERTISE CONFIGURATION (media_1791949806618_d36c812d.png & media_1791949816973_0a1a9589.png)
  if (step === 'advisor-expertise') {
    return (
      <AdvisorExpertiseView
        isDarkMode={isDarkMode}
        initialSelectedId={activeExpertise ? activeExpertise.id : 'legal-partner'}
        onSelectExpertise={(profile) => {
          setActiveExpertise(profile);
          setStep('dashboard');
        }}
      />
    );
  }

  // STEP 5: FULL DASHBOARD VIEW (Renders Builder Workspace, Advisor Workspace, or Admin Workspace dynamically)
  if (step === 'dashboard') {
    if (userRole === 'ADVISOR') {
      return (
        <AdvisorDashboardView
          isDarkMode={isDarkMode}
          currentUser={currentUser}
          activeExpertise={activeExpertise}
          onChangeExpertise={() => setStep('advisor-expertise')}
          onSignOut={() => {
            logoutUser();
            setCurrentUser(null);
            setStep('login');
          }}
        />
      );
    }

    if (userRole === 'ADMIN') {
      return (
        <AdminDashboardView
          isDarkMode={isDarkMode}
          currentUser={currentUser}
          onSignOut={() => {
            logoutUser();
            setCurrentUser(null);
            setStep('login');
          }}
        />
      );
    }

    return (
      <DashboardView
        isDarkMode={isDarkMode}
        currentUser={currentUser}
        onSignOut={() => {
          logoutUser();
          setCurrentUser(null);
          setStep('login');
        }}
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
                  <div className="p-3.5 rounded-xl bg-rose-950/70 border border-rose-800 text-rose-300 text-xs font-semibold text-left animate-fadeIn">
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
                      <option value="Administrator">Administrator</option>
                    </select>
                    <div className="absolute inset-y-0 right-0 pr-3.5 flex items-center pointer-events-none text-slate-400">
                      <ChevronDown className="w-4 h-4" />
                    </div>
                  </div>
                </div>

                {/* Information hint box */}
                <div className="p-3.5 rounded-xl border border-slate-800 bg-[#121214] text-xs text-slate-400 font-normal leading-relaxed text-left">
                  Tip: Use default test accounts <span className="text-amber-400 font-mono">builder@gmail.com</span>, <span className="text-amber-400 font-mono">advisor@gmail.com</span>, or any account created via Sign up.
                </div>

                {/* Remember Me & Forgot Password (DEF-02) */}
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

                  <button
                    type="button"
                    onClick={() => {
                      setResetEmail(email);
                      setResetError('');
                      setResetSuccess('');
                      setStep('forgot-password');
                    }}
                    className="text-amber-500 hover:text-amber-400 font-bold text-xs sm:text-sm transition-colors cursor-pointer"
                  >
                    Forgot password?
                  </button>
                </div>

                {/* Log in Button */}
                <button
                  type="submit"
                  disabled={!isFormValid || isSubmitting}
                  className={`w-full py-3.5 px-4 rounded-md font-bold text-xs sm:text-sm transition-all duration-200 flex items-center justify-center gap-2 ${
                    isFormValid && !isSubmitting
                      ? 'bg-[#e59b38] hover:bg-[#d68a27] text-slate-950 shadow-md cursor-pointer active:scale-[0.99]'
                      : 'bg-[#e59b38]/50 text-slate-950/60 cursor-not-allowed'
                  }`}
                >
                  {isSubmitting && <Loader2 className="w-4 h-4 animate-spin text-slate-950" />}
                  <span>{isSubmitting ? 'Authenticating...' : 'Log in'}</span>
                </button>
              </form>

              {/* Footer matching media_1791713597320_8e3c87db.png */}
              <div className="pt-6 -mx-8 sm:-mx-10 md:-mx-12 px-8 sm:px-10 md:px-12 border-t border-slate-800 text-center">
                <p className="text-xs sm:text-sm text-slate-400">
                  New to ShipYard?{' '}
                  <button
                    type="button"
                    onClick={() => {
                      setSignupError('');
                      setSignupSuccess('');
                      setStep('signup');
                    }}
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

          {/* STEP: FORGOT PASSWORD (DEF-02) */}
          {step === 'forgot-password' && (
            <div className="space-y-6 text-left animate-fadeIn">
              <div className="text-left">
                <button
                  type="button"
                  onClick={() => setStep('login')}
                  className="inline-flex items-center gap-2 text-xs sm:text-sm font-semibold text-slate-400 hover:text-amber-400 transition-colors cursor-pointer group"
                >
                  <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
                  <span>Back to login</span>
                </button>
              </div>

              <div>
                <span className="text-[11px] font-mono font-extrabold tracking-widest text-slate-500 uppercase block mb-1">
                  SECURITY &amp; ACCOUNT RECOVERY
                </span>
                <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-100">
                  Reset your password
                </h1>
                <p className="text-xs sm:text-sm text-slate-400 mt-2 font-normal">
                  Enter your registered account email to request a secure password reset link.
                </p>
              </div>

              {resetError && (
                <div className="p-3.5 rounded-xl bg-rose-950/70 border border-rose-800 text-rose-300 text-xs font-semibold leading-relaxed animate-fadeIn">
                  {resetError}
                </div>
              )}

              {resetSuccess && (
                <div className="p-4 rounded-xl bg-emerald-950/60 border border-emerald-700/80 text-emerald-300 text-xs sm:text-sm font-semibold flex items-start gap-3 animate-fadeIn">
                  <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                  <div className="leading-relaxed">{resetSuccess}</div>
                </div>
              )}

              <form onSubmit={handleResetSubmit} className="space-y-4">
                <div className="space-y-1.5">
                  <label htmlFor="reset-email-input" className="block text-xs sm:text-sm font-semibold text-slate-200">
                    Email Address
                  </label>
                  <input
                    id="reset-email-input"
                    type="email"
                    required
                    value={resetEmail}
                    onChange={(e) => {
                      setResetEmail(e.target.value);
                      if (resetError) setResetError('');
                    }}
                    placeholder="name@organization.com"
                    className="w-full px-4 py-3 rounded-xl text-xs sm:text-sm bg-[#121214] border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500 transition-colors"
                  />
                </div>

                <div className="p-3.5 rounded-xl border border-slate-800 bg-[#121214] text-xs text-slate-400 font-normal leading-relaxed">
                  Notice: Password reset requests trigger verification against active records. If the address is unrecognized, access will be safely rejected.
                </div>

                <button
                  type="submit"
                  disabled={isResetting || !resetEmail.trim()}
                  className="w-full py-3.5 px-4 rounded-md font-bold text-xs sm:text-sm bg-[#e59b38] hover:bg-[#d68a27] text-slate-950 shadow-md transition-all cursor-pointer flex items-center justify-center gap-2 active:scale-[0.99] disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isResetting && <Loader2 className="w-4 h-4 animate-spin text-slate-950" />}
                  <span>{isResetting ? 'Verifying email request...' : 'Send reset instructions'}</span>
                </button>

                <button
                  type="button"
                  onClick={() => setStep('login')}
                  className="w-full py-3 px-4 rounded-md border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-200 font-bold text-xs sm:text-sm cursor-pointer transition-colors"
                >
                  Cancel and return to Sign in
                </button>
              </form>
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
                  <div className="p-3.5 rounded-xl bg-rose-950/70 border border-rose-800 text-rose-300 text-xs font-semibold text-left animate-fadeIn">
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
                  Prototype only: production authentication must verify credentials, assigned Admin role, and the additional key on the backend.
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

                  <button
                    type="button"
                    onClick={() => {
                      setResetEmail(adminEmail);
                      setResetError('');
                      setResetSuccess('');
                      setStep('forgot-password');
                    }}
                    className="text-amber-500 hover:text-amber-400 font-bold text-xs sm:text-sm transition-colors cursor-pointer"
                  >
                    Forgot password?
                  </button>
                </div>

                {/* Verify Admin credentials Button */}
                <button
                  type="submit"
                  className="w-full py-3.5 px-4 rounded-md font-bold text-xs sm:text-sm transition-all duration-200 flex items-center justify-center bg-[#e59b38] hover:bg-[#d68a27] text-slate-950 shadow-md cursor-pointer active:scale-[0.99]"
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

          {/* STEP: CREATE YOUR ACCOUNT (DEF-13 matching media_1791309101386.png) */}
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

              {signupError && (
                <div className="p-3.5 rounded-xl bg-rose-950/70 border border-rose-800 text-rose-300 text-xs font-semibold leading-relaxed animate-fadeIn">
                  {signupError}
                </div>
              )}

              {signupSuccess && (
                <div className="p-4 rounded-xl bg-emerald-950/60 border border-emerald-700/80 text-emerald-300 text-xs sm:text-sm font-semibold flex items-start gap-3 animate-fadeIn">
                  <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                  <div className="leading-relaxed">{signupSuccess}</div>
                </div>
              )}

              <form onSubmit={handleSignupSubmit} className="space-y-4">
                {/* Full name */}
                <div className="space-y-1.5">
                  <label className="block text-xs font-semibold text-slate-300">
                    Full name
                  </label>
                  <input
                    type="text"
                    required
                    value={signupName}
                    onChange={(e) => setSignupName(e.target.value)}
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
                    value={signupEmail}
                    onChange={(e) => setSignupEmail(e.target.value)}
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
                      value={signupPassword}
                      onChange={(e) => setSignupPassword(e.target.value)}
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
                      value={signupConfirmPassword}
                      onChange={(e) => setSignupConfirmPassword(e.target.value)}
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
                    value={signupOrg}
                    onChange={(e) => setSignupOrg(e.target.value)}
                    placeholder="Organization name"
                    className="w-full px-4 py-3 rounded-xl text-xs sm:text-sm bg-slate-800/80 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-[#96562c] focus:ring-2 focus:ring-[#96562c]/20 transition-all"
                  />
                </div>

                {/* Role (DEF-01: Builder, Advisor, or Administrator) */}
                <div className="space-y-1.5">
                  <label className="block text-xs font-semibold text-slate-300">
                    Assigned Workspace Role
                  </label>
                  <select
                    value={signupRole}
                    onChange={(e) => setSignupRole(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl text-xs sm:text-sm bg-slate-800/80 border border-slate-700 text-slate-100 focus:outline-none focus:border-[#96562c] cursor-pointer transition-all"
                  >
                    <option value="Builder">Builder / Project Owner</option>
                    <option value="Advisor">Advisor</option>
                    <option value="Administrator">Administrator</option>
                  </select>
                </div>

                {/* Information hint box */}
                <div className="p-3.5 rounded-xl border border-slate-800 bg-[#121214] text-xs text-slate-400 font-medium">
                  Registration validates credentials against system records before provisioning your workspace.
                </div>

                {/* Create account primary button */}
                <button
                  type="submit"
                  disabled={isSigningUp}
                  className="w-full py-3.5 px-4 rounded-md bg-[#f59e0b] hover:bg-[#d97706] text-slate-950 font-extrabold text-sm shadow-md transition-all cursor-pointer border border-amber-300/60 active:scale-[0.99] flex items-center justify-center gap-2 disabled:opacity-60"
                >
                  {isSigningUp && <Loader2 className="w-4 h-4 animate-spin text-slate-950" />}
                  <span>{isSigningUp ? 'Registering user account...' : 'Create account'}</span>
                </button>

                {/* Back to Login button */}
                <button
                  type="button"
                  onClick={() => setStep('login')}
                  className="w-full py-3 px-4 rounded-md border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-200 font-bold text-xs sm:text-sm cursor-pointer transition-colors mt-2"
                >
                  Back to Login
                </button>
              </form>
            </div>
          )}

          {/* STEP 2: CREDENTIALS VERIFIED LOADING SCREEN */}
          {step === 'verifying' && (
            <CredentialsVerified
              isDarkMode={isDarkMode}
              userRole={userRole}
              onProceed={() => {
                if (userRole === 'ADVISOR') {
                  setStep('advisor-expertise');
                } else {
                  setStep('dashboard');
                }
              }}
            />
          )}
        </div>
      </main>
    </div>
  );
}
