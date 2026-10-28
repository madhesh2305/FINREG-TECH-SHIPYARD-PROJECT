import React from 'react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[ErrorBoundary caught error]:', error, errorInfo);
  }

  handleReset = () => {
    try {
      localStorage.removeItem('authToken');
      localStorage.removeItem('currentUser');
    } catch {}
    this.setState({ hasError: false, error: null });
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center p-6 bg-[#0f1013] text-slate-100 font-sans">
          <div className="max-w-lg w-full bg-[#18191d] border border-red-500/30 rounded-2xl p-8 shadow-2xl text-center space-y-4">
            <div className="w-12 h-12 rounded-full bg-red-950/60 border border-red-500/50 flex items-center justify-center mx-auto text-red-400 font-bold text-xl">
              !
            </div>
            <h2 className="text-xl font-bold text-slate-100">Application View Recovered</h2>
            <p className="text-xs sm:text-sm text-slate-400">
              A component error occurred while rendering this view.
            </p>
            {this.state.error && (
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-left font-mono text-xs text-rose-400 overflow-x-auto max-h-32">
                {this.state.error.message || String(this.state.error)}
              </div>
            )}
            <div className="pt-2 flex gap-3 justify-center">
              <button
                type="button"
                onClick={() => window.location.reload()}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold cursor-pointer transition-colors"
              >
                Reload Page
              </button>
              <button
                type="button"
                onClick={this.handleReset}
                className="px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-500 text-slate-950 text-xs font-bold cursor-pointer transition-colors"
              >
                Reset Session & Login
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
