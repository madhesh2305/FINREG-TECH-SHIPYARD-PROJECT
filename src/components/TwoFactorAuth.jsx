import React, { useState, useEffect, useRef } from 'react';
import { BarChart3, Check } from 'lucide-react';

export default function TwoFactorAuth({ onBackToSignIn, onVerifySuccess, isDarkMode }) {
  const [code, setCode] = useState(['', '', '', '', '', '']);
  const [timeLeft, setTimeLeft] = useState(262); // 4 minutes 22 seconds
  const [isResending, setIsResending] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const inputRefs = useRef([]);

  // Live countdown timer
  useEffect(() => {
    if (timeLeft <= 0) return;
    const timer = setInterval(() => {
      setTimeLeft((prev) => prev - 1);
    }, 1000);
    return () => clearInterval(timer);
  }, [timeLeft]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  const handleInputChange = (index, value) => {
    if (value && !/^\d+$/.test(value)) return;

    const newCode = [...code];
    newCode[index] = value.slice(-1);
    setCode(newCode);

    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !code[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').trim();
    if (!/^\d{6}$/.test(pastedData)) return;

    const digits = pastedData.split('');
    setCode(digits);
    inputRefs.current[5]?.focus();
  };

  const handleResend = () => {
    setIsResending(true);
    setTimeout(() => {
      setTimeLeft(300);
      setCode(['', '', '', '', '', '']);
      setIsResending(false);
      inputRefs.current[0]?.focus();
    }, 600);
  };

  const isCodeComplete = code.every((digit) => digit !== '');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!isCodeComplete || isVerifying) return;

    setIsVerifying(true);
    setTimeout(() => {
      setIsVerifying(false);
      if (onVerifySuccess) {
        onVerifySuccess(code.join(''));
      }
    }, 800);
  };

  return (
    <div className="text-center py-2 animate-fadeIn">
      {/* Top Icon Box (Rich Brown Badge) */}
      <div className="flex justify-center mb-5">
        <div className="w-13 h-13 bg-[#7c4a27] dark:bg-[#96562c] rounded-2xl flex items-center justify-center shadow-md shadow-amber-950/20">
          <BarChart3 className="w-7 h-7 text-white stroke-[2.5]" />
        </div>
      </div>

      {/* Header Titles */}
      <div className="text-center mb-6">
        <h1 className={`text-2xl sm:text-[26px] font-bold tracking-tight ${
          isDarkMode ? 'text-slate-100' : 'text-slate-900'
        }`}>
          Two-factor verification
        </h1>
        <p className={`text-sm mt-1.5 font-normal max-w-sm mx-auto ${
          isDarkMode ? 'text-slate-400' : 'text-slate-500'
        }`}>
          Enter the 6-digit code from your authenticator app or registered device.
        </p>
      </div>

      {/* 3-Step Workflow Progress Bar (Brown & Grey Theme) */}
      <div className="flex items-center justify-center max-w-xs mx-auto mb-8 my-6">
        {/* Step 1: Sign In */}
        <div className="flex flex-col items-center">
          <div className="w-7 h-7 rounded-full bg-[#7c4a27] dark:bg-amber-600 text-white flex items-center justify-center text-xs font-bold shadow-sm">
            <Check className="w-4 h-4 stroke-[3]" />
          </div>
          <span className="text-[11px] font-semibold text-[#7c4a27] dark:text-amber-500 mt-1.5">Sign In</span>
        </div>

        {/* Line 1 -> 2 */}
        <div className="flex-1 h-[2px] bg-[#7c4a27] dark:bg-amber-600 mx-2 -mt-4" />

        {/* Step 2: Verify */}
        <div className="flex flex-col items-center">
          <div className={`w-7 h-7 rounded-full border-2 border-[#7c4a27] dark:border-amber-500 flex items-center justify-center text-xs font-bold shadow-sm ${
            isDarkMode ? 'bg-[#1a1a1e] text-amber-400' : 'bg-white text-[#7c4a27]'
          }`}>
            2
          </div>
          <span className="text-[11px] font-semibold text-[#7c4a27] dark:text-amber-400 mt-1.5">Verify</span>
        </div>

        {/* Line 2 -> 3 */}
        <div className={`flex-1 h-[2px] mx-2 -mt-4 ${
          isDarkMode ? 'bg-slate-700' : 'bg-slate-200'
        }`} />

        {/* Step 3: Dashboard */}
        <div className="flex flex-col items-center">
          <div className={`w-7 h-7 rounded-full border-2 flex items-center justify-center text-xs font-medium ${
            isDarkMode ? 'border-slate-700 bg-[#1a1a1e] text-slate-500' : 'border-slate-200 bg-white text-slate-400'
          }`}>
            3
          </div>
          <span className={`text-[11px] font-medium mt-1.5 ${
            isDarkMode ? 'text-slate-500' : 'text-slate-400'
          }`}>Dashboard</span>
        </div>
      </div>

      {/* 2FA Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Verification Code Inputs */}
        <div className="text-left">
          <label className={`block text-sm font-semibold mb-2 ${
            isDarkMode ? 'text-slate-200' : 'text-slate-700'
          }`}>
            Verification Code
          </label>

          {/* 6 OTP Digit Inputs (Enlightened with Brown on Focus) */}
          <div className="flex items-center justify-between gap-2 sm:gap-3" onPaste={handlePaste}>
            {code.map((digit, idx) => (
              <input
                key={idx}
                ref={(el) => (inputRefs.current[idx] = el)}
                type="text"
                inputMode="numeric"
                maxLength={1}
                value={digit}
                onChange={(e) => handleInputChange(idx, e.target.value)}
                onKeyDown={(e) => handleKeyDown(idx, e)}
                className={`w-11 sm:w-13 h-12 sm:h-13 text-center text-xl font-bold border rounded-xl focus:outline-none transition-all ${
                  isDarkMode
                    ? 'bg-slate-800/80 border-slate-700 text-slate-100 hover:border-[#96562c] focus:border-[#96562c] focus:ring-4 focus:ring-[#96562c]/20'
                    : 'bg-white border-slate-200 text-slate-800 hover:border-[#7c4a27] focus:border-[#7c4a27] focus:ring-4 focus:ring-[#7c4a27]/15'
                }`}
              />
            ))}
          </div>

          {/* Sub-row: Expiration Timer & Resend Code */}
          <div className="flex items-center justify-between mt-3 text-xs sm:text-sm">
            <span className={isDarkMode ? 'text-slate-400' : 'text-slate-400'}>
              Expires in {formatTime(timeLeft)}
            </span>
            <button
              type="button"
              onClick={handleResend}
              disabled={isResending}
              className="text-[#7c4a27] dark:text-amber-400 hover:underline font-semibold cursor-pointer transition-colors"
            >
              {isResending ? 'Sending...' : 'Resend code'}
            </button>
          </div>
        </div>

        {/* Submit Button (Brown) */}
        <button
          type="submit"
          disabled={!isCodeComplete || isVerifying}
          className={`w-full py-3.5 px-4 rounded-xl font-semibold text-sm transition-all duration-200 flex items-center justify-center gap-2 ${
            isCodeComplete && !isVerifying
              ? 'bg-[#7c4a27] hover:bg-[#633a1e] dark:bg-[#96562c] dark:hover:bg-[#7c4a27] text-white shadow-md shadow-amber-950/20 active:scale-[0.99] cursor-pointer'
              : isDarkMode
              ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
              : 'bg-slate-200 text-slate-400 cursor-not-allowed'
          }`}
        >
          {isVerifying ? (
            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : (
            'Verify & Continue'
          )}
        </button>
      </form>

      {/* Bottom Footer Navigation Links */}
      <div className={`flex items-center justify-center gap-3 mt-6 text-xs sm:text-sm font-medium ${
        isDarkMode ? 'text-slate-400' : 'text-slate-500'
      }`}>
        <button
          type="button"
          onClick={onBackToSignIn}
          className="hover:text-slate-800 dark:hover:text-slate-200 flex items-center gap-1 cursor-pointer transition-colors"
        >
          <span>← Back to sign in</span>
        </button>
        <span className={isDarkMode ? 'text-slate-700' : 'text-slate-300'}>|</span>
        <button
          type="button"
          onClick={() => alert('Option for SMS / Authenticator app selection')}
          className="hover:text-slate-800 dark:hover:text-slate-200 cursor-pointer transition-colors"
        >
          Use a different method
        </button>
      </div>
    </div>
  );
}
