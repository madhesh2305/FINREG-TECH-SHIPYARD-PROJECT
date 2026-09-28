import React from 'react';
import LoginForm from './components/LoginForm';

function App() {
  // Static theme fixed to Dark Theme permanently
  const isDarkMode = true;

  return (
    <div className="dark bg-[#121214] text-slate-100 min-h-screen font-sans">
      <LoginForm isDarkMode={isDarkMode} />
    </div>
  );
}

export default App;
