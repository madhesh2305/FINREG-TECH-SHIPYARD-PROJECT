import React, { useState, useEffect } from 'react';
import { Mail, Lock, Eye, EyeOff, BarChart3 } from 'lucide-react';
import Navbar from './Navbar';
import FlashPage from './FlashPage';
import LandingPage from './LandingPage';
import CredentialsVerified from './CredentialsVerified';
import TwoFactorAuth from './TwoFactorAuth';
import VerificationSuccessful from './VerificationSuccessful';
import DashboardView from './DashboardView';
import AdvisorDashboardView from './AdvisorDashboardView';
import AdminDashboardView from './AdminDashboardView';

import { loginUser, registerUser, requestPasswordReset, confirmPasswordReset, logoutUser } from '../services/authService';

export default function LoginForm({ isDarkMode = true }) {
  // Persisted auth session detection (DEF-17: preserve Admin and role dashboard on refresh)
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      const raw = localStorage.getItem('currentUser');
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  });

  const [userRole, setUserRole] = useState(() => {
    try {
      const raw = localStorage.getItem('currentUser');
      if (raw) {
        const u = JSON.parse(raw);
        const r = (u.platform_role || '').toUpperCase();
        if (r === 'ADMIN') return 'ADMIN';
        if (r === 'ADVISOR') return 'ADVISOR';
      }
    } catch {}
    return 'BUILDER';
  });

  // Steps: 'flash' | 'landing' | 'login' | 'signup' | 'verifying' | 'dashboard'
  const [step, setStep] = useState(() => {
    try {
      const token = localStorage.getItem('authToken');
      const raw = localStorage.getItem('currentUser');
      if (token && raw) {
        return 'dashboard';
      }
    } catch {}
    return 'flash';
  });
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loginError, setLoginError] = useState('');

  // DEF-15: Forgot password and full reset lifecycle states
  const [isForgotModalOpen, setIsForgotModalOpen] = useState(false);
  const [forgotEmail, setForgotEmail] = useState('');
  const [forgotResult, setForgotResult] = useState(null);
  const [isSendingReset, setIsSendingReset] = useState(false);
  const [resetStep, setResetStep] = useState('request'); // 'request' | 'confirm' | 'done'
  const [resetToken, setResetToken] = useState('');
  const [newResetPassword, setNewResetPassword] = useState('');
  const [confirmResetPassword, setConfirmResetPassword] = useState('');
  const [resetError, setResetError] = useState('');
  const [isResettingPassword, setIsResettingPassword] = useState(false);

  // Signup form states
  const [signupFullName, setSignupFullName] = useState('');
  const [signupEmail, setSignupEmail] = useState('');
  const [signupPassword, setSignupPassword] = useState('');
  const [signupConfirmPassword, setSignupConfirmPassword] = useState('');
  const [signupOrganization, setSignupOrganization] = useState('');
  const [signupRole, setSignupRole] = useState('Builder'); // 'Builder' | 'Advisor'
  const [signupError, setSignupError] = useState('');
  const [isRegistering, setIsRegistering] = useState(false);

  // DEF-04: Explicit form state reset function to ensure fresh sign-ups never retain earlier details
  const resetSignupForm = () => {
    setSignupFullName('');
    setSignupEmail('');
    setSignupPassword('');
    setSignupConfirmPassword('');
    setSignupOrganization('');
    setSignupRole('Builder');
    setSignupError('');
  };

  const openSignup = (defaultRole = 'Builder') => {
    resetSignupForm();
    setSignupRole(defaultRole);
    setLoginError('');
    setStep('signup');
  };

  // Handle Login submission via POST /auth/login with real credentials
  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setLoginError('');

    const cleanEmail = email.toLowerCase().trim();
    const cleanPassword = password.trim();

    if (!cleanEmail || !cleanPassword) return;

    setIsSubmitting(true);
    try {
      const data = await loginUser(cleanEmail, cleanPassword);
      setCurrentUser(data);
      const role = (data?.platform_role || '').toUpperCase();
      if (role === 'ADVISOR') {
        setUserRole('ADVISOR');
      } else if (role === 'ADMIN') {
        setUserRole('ADMIN');
      } else {
        setUserRole('BUILDER');
      }
      setLoginError('');
      resetSignupForm();
      setStep('verifying');
    } catch (err) {
      setLoginError(err.message || 'Invalid email or password');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSignOut = () => {
    logoutUser();
    setCurrentUser(null);
    resetSignupForm();
    setLoginError('');
    setStep('login');
  };

  const handleForgotSubmit = async (e) => {
    e.preventDefault();
    if (!forgotEmail.trim()) return;
    setIsSendingReset(true);
    setResetError('');
    try {
      const res = await requestPasswordReset(forgotEmail);
      if (res && res.status === 'delivery_failed') {
        setForgotResult({
          success: false,
          isUnconfigured: false,
          isDeliveryFailed: true,
          message: res.message || 'Password reset delivery is temporarily unavailable. Please try again later or contact support.',
          channel: res.delivery_channel || 'Email (Service Unavailable)'
        });
      } else if (res && (res.status === 'pending_configuration' || (res.delivery_channel && res.delivery_channel.includes('Unconfigured')))) {
        setForgotResult({
          success: false,
          isUnconfigured: true,
          isDeliveryFailed: false,
          message: res.message || 'Password recovery via email is currently unconfigured in this environment. Please contact your system administrator.',
          channel: res.delivery_channel || 'SMTP (Unconfigured)'
        });
      } else {
        setForgotResult({
          success: true,
          isUnconfigured: false,
          isDeliveryFailed: false,
          message: res.message || 'If an account associated with this email address exists, password recovery instructions have been dispatched.',
          channel: res.delivery_channel || 'Email'
        });
      }
    } catch (err) {
      setForgotResult({
        success: false,
        isUnconfigured: false,
        isDeliveryFailed: false,
        message: err.message || 'Failed to request password reset.'
      });
    } finally {
      setIsSendingReset(false);
    }
  };

  const handleConfirmResetSubmit = async (e) => {
    e.preventDefault();
    setResetError('');
    if (!resetToken.trim()) {
      setResetError('Reset token is required.');
      return;
    }
    if (newResetPassword.length < 6) {
      setResetError('New password must be at least 6 characters.');
      return;
    }
    if (newResetPassword !== confirmResetPassword) {
      setResetError('Passwords do not match.');
      return;
    }
    setIsResettingPassword(true);
    try {
      await confirmPasswordReset(resetToken, newResetPassword);
      setResetStep('done');
      setEmail(forgotEmail);
      setForgotResult({
        success: true,
        message: 'Password updated successfully! You can now sign in with your new credentials.'
      });
    } catch (err) {
      setResetError(err.message || 'Failed to reset password. Token may be invalid, expired, or already used.');
    } finally {
      setIsResettingPassword(false);
    }
  };

  // Handle Registration submission via POST /auth/register
  const handleSignupSubmit = async (e) => {
    e.preventDefault();
    setSignupError('');

    if (!signupFullName.trim() || !signupEmail.trim() || !signupPassword.trim()) {
      setSignupError('Please fill in all required fields.');
      return;
    }

    if (signupPassword !== signupConfirmPassword) {
      setSignupError('Passwords do not match.');
      return;
    }

    if (signupPassword.length < 6) {
      setSignupError('Password must be at least 6 characters.');
      return;
    }

    const normalizedRole = signupRole.toUpperCase() === 'ADVISOR' ? 'ADVISOR' : 'BUILDER';

    setIsRegistering(true);
    try {
      const data = await registerUser({
        email: signupEmail,
        password: signupPassword,
        full_name: signupFullName,
        role: normalizedRole,
        organization: signupOrganization,
      });

      setCurrentUser(data);
      setUserRole(normalizedRole);
      resetSignupForm();
      setLoginError('');
      setStep('verifying');
    } catch (err) {
      setSignupError(err.message || 'Registration failed. Please try again.');
    } finally {
      setIsRegistering(false);
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
    if (userRole === 'ADMIN') {
      return (
        <AdminDashboardView
          isDarkMode={isDarkMode}
          currentUser={currentUser}
          onSignOut={handleSignOut}
        />
      );
    }

    if (userRole === 'ADVISOR') {
      return (
        <AdvisorDashboardView
          isDarkMode={isDarkMode}
          currentUser={currentUser}
          onSignOut={handleSignOut}
        />
      );
    }

    return (
      <DashboardView
        isDarkMode={isDarkMode}
        currentUser={currentUser}
        onSignOut={handleSignOut}
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
                {/* Login Error Alert */}
                {loginError && (
                  <div className="p-3 rounded-xl bg-rose-950/70 border border-rose-800 text-rose-300 text-xs font-semibold text-left animate-fadeIn">
                    {loginError}
                  </div>
                )}

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
                      onChange={(e) => {
                        setEmail(e.target.value);
                        if (loginError) setLoginError('');
                      }}
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
                      onChange={(e) => {
                        setPassword(e.target.value);
                        if (loginError) setLoginError('');
                      }}
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

                  <button
                    type="button"
                    onClick={() => {
                      setIsForgotModalOpen(true);
                      setForgotEmail(email);
                      setForgotResult(null);
                    }}
                    className="text-[#7c4a27] dark:text-amber-400 hover:underline font-semibold text-xs sm:text-sm transition-colors cursor-pointer"
                  >
                    Forgot password?
                  </button>
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

              {/* Sign Up & Advisor Footer */}
              <div className="space-y-2 text-center pt-1">
                <p className={`text-xs sm:text-sm ${isDarkMode ? 'text-slate-400' : 'text-slate-600'}`}>
                  Don't have an account?{' '}
                  <a
                    href="#signup"
                    onClick={(e) => {
                      e.preventDefault();
                      openSignup('Builder');
                    }}
                    className="text-[#7c4a27] dark:text-amber-400 hover:underline font-semibold ml-1 transition-colors cursor-pointer"
                  >
                    Sign Up
                  </a>
                </p>

                <p className={`text-xs sm:text-sm ${isDarkMode ? 'text-slate-400' : 'text-slate-600'}`}>
                  Are you an Advisor?{' '}
                  <a
                    href="#advisor"
                    onClick={(e) => {
                      e.preventDefault();
                      openSignup('Advisor');
                    }}
                    className="text-[#7c4a27] dark:text-amber-400 hover:underline font-semibold ml-1 transition-colors cursor-pointer"
                  >
                    Advisor
                  </a>
                </p>
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

              {signupError && (
                <div className="p-3 rounded-xl bg-rose-950/70 border border-rose-800 text-rose-300 text-xs font-semibold text-left animate-fadeIn">
                  {signupError}
                </div>
              )}

              <form onSubmit={handleSignupSubmit} className="space-y-4" autoComplete="off">
                {/* Full name */}
                <div className="space-y-1.5">
                  <label className="block text-xs font-semibold text-slate-300">
                    Full name
                  </label>
                  <input
                    type="text"
                    required
                    value={signupFullName}
                    onChange={(e) => {
                      setSignupFullName(e.target.value);
                      if (signupError) setSignupError('');
                    }}
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
                    onChange={(e) => {
                      setSignupEmail(e.target.value);
                      if (signupError) setSignupError('');
                    }}
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
                      onChange={(e) => {
                        setSignupPassword(e.target.value);
                        if (signupError) setSignupError('');
                      }}
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
                      onChange={(e) => {
                        setSignupConfirmPassword(e.target.value);
                        if (signupError) setSignupError('');
                      }}
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
                    value={signupOrganization}
                    onChange={(e) => setSignupOrganization(e.target.value)}
                    placeholder="Organization or Firm name"
                    className="w-full px-4 py-3 rounded-xl text-xs sm:text-sm bg-slate-800/80 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-[#96562c] focus:ring-2 focus:ring-[#96562c]/20 transition-all"
                  />
                </div>

                {/* Role */}
                <div className="space-y-1.5">
                  <label className="block text-xs font-semibold text-slate-300">
                    Assigned Workplace (Role)
                  </label>
                  <select
                    value={signupRole}
                    onChange={(e) => setSignupRole(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl text-xs sm:text-sm bg-slate-800/80 border border-slate-700 text-slate-100 focus:outline-none focus:border-[#96562c] cursor-pointer transition-all"
                  >
                    <option value="Builder">Builder (Project Founder / Operator)</option>
                    <option value="Advisor">Advisor (Legal / Regulatory Expert)</option>
                    <option value="Administrator" disabled>Administrator (Platform Invite Only)</option>
                  </select>
                </div>

                {/* Information hint box */}
                <div className="p-3.5 rounded-xl border border-slate-800 bg-[#121214] text-xs text-slate-400 font-medium">
                  {signupRole === 'Advisor'
                    ? 'Advisors receive specialized FCC review workspaces, invitation management, and interpretative governance tools.'
                    : 'Builders can create and operate compliance projects, map regulatory requirements, and invite advisors.'}
                </div>

                {/* Create account primary button */}
                <button
                  type="submit"
                  disabled={isRegistering}
                  className={`w-full py-3.5 px-4 rounded-xl font-extrabold text-sm shadow-md transition-all cursor-pointer border border-amber-300/60 active:scale-[0.99] ${
                    isRegistering
                      ? 'bg-amber-600 text-slate-900 cursor-wait'
                      : 'bg-[#f59e0b] hover:bg-[#d97706] text-slate-950'
                  }`}
                >
                  {isRegistering ? 'Creating account...' : 'Create account'}
                </button>

                {/* Back to Login button */}
                <button
                  type="button"
                  onClick={() => {
                    resetSignupForm();
                    setLoginError('');
                    setStep('login');
                  }}
                  className="w-full py-3 px-4 rounded-xl border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-200 font-bold text-xs sm:text-sm cursor-pointer transition-colors mt-2"
                >
                  Back to Login
                </button>
              </form>
            </div>
          )}

          {/* STEP 2: CREDENTIALS VERIFIED LOADING SCREEN - LASTS 4 SECONDS THEN GOES DIRECTLY TO DASHBOARD */}
          {step === 'verifying' && <CredentialsVerified isDarkMode={isDarkMode} role={userRole} userRole={userRole} onProceed={() => setStep('dashboard')} />}
        </div>
      </main>

      {/* DEF-02 & DEF-15: PASSWORD RECOVERY & SECURE RESET LIFECYCLE MODAL */}
      {isForgotModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fadeIn">
          <div className="w-full max-w-md rounded-2xl bg-[#1a1a1e] border border-slate-700 p-6 sm:p-7 shadow-2xl text-left space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                <Lock className="w-5 h-5 text-amber-500" />
                {resetStep === 'confirm' ? 'Set New Password' : 'Password Recovery'}
              </h2>
              <button
                type="button"
                onClick={() => {
                  setIsForgotModalOpen(false);
                  setForgotResult(null);
                  setResetStep('request');
                  setResetToken('');
                  setNewResetPassword('');
                  setConfirmResetPassword('');
                  setResetError('');
                }}
                className="text-slate-400 hover:text-slate-200 text-sm font-semibold p-1 cursor-pointer"
              >
                ✕
              </button>
            </div>

            {resetStep === 'request' && (
              <p className="text-xs text-slate-400 leading-relaxed">
                Enter your registered ShipYard email address to request a time-limited password recovery token.
              </p>
            )}

            {forgotResult && (
              <div
                className={`p-3.5 rounded-xl text-xs font-medium space-y-1.5 ${
                  forgotResult.isUnconfigured
                    ? 'bg-amber-950/70 border border-amber-600 text-amber-200'
                    : forgotResult.success
                    ? 'bg-emerald-950/70 border border-emerald-700 text-emerald-200'
                    : 'bg-rose-950/70 border border-rose-800 text-rose-300'
                }`}
              >
                <div className="font-semibold flex items-center gap-1.5">
                  {forgotResult.isUnconfigured && (
                    <span className="px-1.5 py-0.5 rounded text-[10px] bg-amber-500/20 text-amber-300 border border-amber-500/40 font-bold uppercase">
                      Delivery Blocked / Unconfigured
                    </span>
                  )}
                  {forgotResult.isDeliveryFailed && (
                    <span className="px-1.5 py-0.5 rounded text-[10px] bg-rose-500/20 text-rose-300 border border-rose-500/40 font-bold uppercase">
                      Delivery Failed
                    </span>
                  )}
                  {forgotResult.message}
                </div>
                {forgotResult.channel && (
                  <div className="text-[11px] opacity-80 pt-1 border-t border-slate-700/50">
                    Channel Status: <span className="font-mono">{forgotResult.channel}</span>
                  </div>
                )}
                {forgotResult.success && !forgotResult.isUnconfigured && (
                  <div className="pt-1.5">
                    <button
                      type="button"
                      onClick={() => {
                        setResetStep('confirm');
                        setForgotResult(null);
                      }}
                      className="text-xs font-bold text-emerald-400 hover:underline cursor-pointer"
                    >
                      Enter Received Token & Set New Password &rarr;
                    </button>
                  </div>
                )}
              </div>
            )}

            {resetError && (
              <div className="p-3 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-300 text-xs font-semibold">
                {resetError}
              </div>
            )}

            {/* STEP 1: REQUEST RESET TOKEN */}
            {resetStep === 'request' && (
              <form onSubmit={handleForgotSubmit} className="space-y-4 pt-1">
                <div className="space-y-1.5">
                  <label className="block text-xs font-semibold text-slate-300">
                    Registered Email Address
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                      <Mail className="w-4 h-4" />
                    </div>
                    <input
                      type="email"
                      required
                      value={forgotEmail}
                      onChange={(e) => setForgotEmail(e.target.value)}
                      placeholder="you@organization.com"
                      className="w-full pl-9 pr-3 py-2.5 rounded-xl text-xs sm:text-sm bg-slate-800/80 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500"
                    />
                  </div>
                </div>

                <div className="flex gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => {
                      setIsForgotModalOpen(false);
                      setForgotResult(null);
                    }}
                    className="flex-1 py-2.5 px-4 rounded-xl border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs cursor-pointer transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSendingReset || !forgotEmail.trim()}
                    className="flex-1 py-2.5 px-4 rounded-xl bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-slate-950 font-bold text-xs cursor-pointer transition-colors"
                  >
                    {isSendingReset ? 'Verifying...' : 'Request Recovery'}
                  </button>
                </div>

                <div className="text-center pt-1">
                  <button
                    type="button"
                    onClick={() => {
                      setResetStep('confirm');
                      setForgotResult(null);
                    }}
                    className="text-xs text-amber-400 hover:underline cursor-pointer"
                  >
                    Already have a reset token? Enter it here
                  </button>
                </div>
              </form>
            )}

            {/* STEP 2: CONFIRM RESET WITH TOKEN & NEW PASSWORD */}
            {resetStep === 'confirm' && (
              <form onSubmit={handleConfirmResetSubmit} className="space-y-3 pt-1">
                <div className="space-y-1">
                  <label className="block text-xs font-semibold text-slate-300">
                    Reset Token
                  </label>
                  <input
                    type="text"
                    required
                    value={resetToken}
                    onChange={(e) => setResetToken(e.target.value)}
                    placeholder="Paste your reset token"
                    className="w-full px-3 py-2 rounded-xl text-xs bg-slate-800/80 border border-slate-700 text-slate-100 font-mono placeholder-slate-500 focus:outline-none focus:border-amber-500"
                  />
                </div>

                <div className="space-y-1">
                  <label className="block text-xs font-semibold text-slate-300">
                    New Password (min 6 characters)
                  </label>
                  <input
                    type="password"
                    required
                    value={newResetPassword}
                    onChange={(e) => setNewResetPassword(e.target.value)}
                    placeholder="Enter new password"
                    className="w-full px-3 py-2 rounded-xl text-xs sm:text-sm bg-slate-800/80 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500"
                  />
                </div>

                <div className="space-y-1">
                  <label className="block text-xs font-semibold text-slate-300">
                    Confirm New Password
                  </label>
                  <input
                    type="password"
                    required
                    value={confirmResetPassword}
                    onChange={(e) => setConfirmResetPassword(e.target.value)}
                    placeholder="Repeat new password"
                    className="w-full px-3 py-2 rounded-xl text-xs sm:text-sm bg-slate-800/80 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500"
                  />
                </div>

                <div className="flex gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setResetStep('request')}
                    className="flex-1 py-2 px-3 rounded-xl border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs cursor-pointer"
                  >
                    Back
                  </button>
                  <button
                    type="submit"
                    disabled={isResettingPassword || !resetToken.trim() || newResetPassword.length < 6}
                    className="flex-1 py-2 px-3 rounded-xl bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-slate-950 font-bold text-xs cursor-pointer"
                  >
                    {isResettingPassword ? 'Updating...' : 'Set New Password'}
                  </button>
                </div>
              </form>
            )}

            {/* STEP 3: DONE */}
            {resetStep === 'done' && (
              <div className="pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setIsForgotModalOpen(false);
                    setForgotResult(null);
                    setResetStep('request');
                    setResetToken('');
                    setNewResetPassword('');
                    setConfirmResetPassword('');
                  }}
                  className="w-full py-2.5 px-4 rounded-xl bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold text-xs cursor-pointer transition-colors"
                >
                  Return to Sign In with New Password
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
