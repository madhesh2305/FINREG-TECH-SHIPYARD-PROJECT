import React, { useState, useEffect } from 'react';
import { Search, Wrench, Check, ArrowLeft } from 'lucide-react';
import { getTools, toggleToolUsage } from '../services/toolService';

export default function ToolsView({ isDarkMode }) {
  const [activeSubTab, setActiveSubTab] = useState('All Tools'); // 'All Tools' | 'My Used Tools'
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('All categories');
  const [activeCardId, setActiveCardId] = useState(null);

  // Selected Tool State for Tool Details Page
  const [selectedTool, setSelectedTool] = useState(null);
  const [toastMsg, setToastMsg] = useState(null);

  // Master Tools List matching reference image
  const [toolsList, setToolsList] = useState([
    {
      id: 'TOOL-001',
      name: 'ControlMap',
      category: 'Compliance',
      description: 'Control mapping and evidence management',
      fullDescription: 'ControlMap is a trusted platform used to support controlled regulatory delivery.',
      mainFunctionality: 'Control mapping and evidence management',
      useCase: 'Integrate structured outputs into project evidence and workflow reviews.',
      supportedArea: 'Requirements',
      developerProvider: 'ControlMap Ltd',
      status: 'Approved',
      statusColor: 'bg-emerald-950/60 text-emerald-400 border-emerald-800/80',
      dotColor: 'bg-emerald-500',
      isUsed: true,
    },
    {
      id: 'TOOL-002',
      name: 'RiskLens',
      category: 'Risk Management',
      description: 'Quantitative operational risk analysis',
      fullDescription: 'RiskLens provides FAIR-based quantitative operational risk modeling and financial impact estimation.',
      mainFunctionality: 'Quantitative operational risk analysis',
      useCase: 'Model financial exposure and stress-test capital adequacy controls.',
      supportedArea: 'Risk assessment',
      developerProvider: 'RiskLens Inc',
      status: 'Approved',
      statusColor: 'bg-emerald-950/60 text-emerald-400 border-emerald-800/80',
      dotColor: 'bg-emerald-500',
      isUsed: true,
    },
    {
      id: 'TOOL-003',
      name: 'ModelGuard',
      category: 'AI / ML',
      description: 'Model governance and explainability testing',
      fullDescription: 'ModelGuard evaluates algorithmic bias, explainability metrics, and model lineage for compliance sign-off.',
      mainFunctionality: 'Model governance and explainability testing',
      useCase: 'Validate machine learning models used in automated customer onboarding.',
      supportedArea: 'AI governance',
      developerProvider: 'ModelGuard Systems Ltd',
      status: 'Review due',
      statusColor: 'bg-amber-950/60 text-amber-400 border-amber-800/80',
      dotColor: 'bg-amber-500',
      isUsed: true,
    },
  ]);

  useEffect(() => {
    let isMounted = true;
    async function loadToolsData() {
      try {
        const liveTools = await getTools();
        if (isMounted && Array.isArray(liveTools) && liveTools.length > 0) {
          setToolsList(liveTools);
        }
      } catch (err) {
        console.warn('[ToolsView] API load warning:', err);
      }
    }
    loadToolsData();
    return () => { isMounted = false; };
  }, []);

  const usedCount = toolsList.filter((t) => t.isUsed).length;

  // Filtering Logic
  const filteredTools = toolsList.filter((tool) => {
    if (activeSubTab === 'My Used Tools' && !tool.isUsed) return false;

    const matchesSearch =
      tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tool.category.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tool.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tool.supportedArea.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesCategory =
      categoryFilter === 'All categories' || tool.category === categoryFilter;

    return matchesSearch && matchesCategory;
  });

  const handleUseToolToggle = async (tool) => {
    setToolsList(
      toolsList.map((t) => (t.id === tool.id ? { ...t, isUsed: true } : t))
    );
    try {
      await toggleToolUsage(tool.id, true);
    } catch (err) {
      console.warn('[ToolsView] toggleToolUsage warning:', err);
    }
    setToastMsg(`Tool "${tool.name}" activated and added to My Used Tools!`);
    setTimeout(() => setToastMsg(null), 3000);
  };

  // -------------------------------------------------------------
  // VIEW B: TOOL DETAILS PAGE VIEW (Matching media_1790750982213.png & media_1790750996452.png)
  // -------------------------------------------------------------
  if (selectedTool) {
    const currentTool = toolsList.find((t) => t.id === selectedTool.id) || selectedTool;

    return (
      <div className="space-y-6 animate-fadeIn text-left relative">
        {/* Toast Notification Banner */}
        {toastMsg && (
          <div className="fixed top-16 right-6 z-50 bg-[#7c4a27] dark:bg-[#96562c] text-white px-4 py-3 rounded-xl shadow-2xl flex items-center gap-2.5 animate-fadeIn font-semibold text-xs sm:text-sm border-2 border-amber-300">
            <Check className="w-5 h-5 text-amber-300 shrink-0" />
            <span>{toastMsg}</span>
          </div>
        )}

        {/* Top-Left Back to Tools Option */}
        <div>
          <button
            type="button"
            onClick={() => setSelectedTool(null)}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl border border-slate-800 bg-slate-900/80 hover:bg-slate-800 text-slate-300 hover:text-white font-bold text-xs cursor-pointer transition-all group"
          >
            <ArrowLeft className="w-4 h-4 text-amber-400 group-hover:-translate-x-0.5 transition-transform" />
            <span>Back to tools</span>
          </button>
        </div>

        {/* Top Header Row matching media_1790750982213.png */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 pb-6 border-b border-slate-800">
          <div className="flex items-center gap-5">
            {/* Wrench Square Badge */}
            <div className="w-14 h-14 rounded-xl bg-[#7c4a27]/30 dark:bg-[#96562c]/30 text-amber-300 border-2 border-[#96562c]/60 font-bold text-xl flex items-center justify-center shrink-0 shadow-md">
              <Wrench className="w-6 h-6 stroke-[2.2]" />
            </div>

            <div>
              <span className="text-[11px] font-extrabold tracking-widest text-slate-400 dark:text-slate-500 uppercase">
                {currentTool.category}
              </span>
              <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-100 mt-0.5">
                {currentTool.name}
              </h1>
              <p className="text-xs sm:text-sm text-slate-400 mt-1 font-medium">
                {currentTool.description}
              </p>
            </div>
          </div>

          {/* Top Right Status Pill */}
          <div className="self-start sm:self-center">
            <span className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-bold border ${currentTool.statusColor}`}>
              <span className={`w-1.5 h-1.5 rounded-full ${currentTool.dotColor}`} />
              {currentTool.status}
            </span>
          </div>
        </div>

        {/* Main Details Card Container matching media_1790750982213.png */}
        <div className="rounded-2xl border border-slate-800 bg-[#161619] p-6 sm:p-8 space-y-7 shadow-lg">
          {/* Section 1: DESCRIPTION */}
          <div>
            <span className="block text-[11px] font-extrabold tracking-widest text-slate-500 uppercase mb-2">
              DESCRIPTION
            </span>
            <p className="text-sm font-bold text-slate-200 leading-relaxed">
              {currentTool.fullDescription || `${currentTool.name} is a trusted platform used to support controlled regulatory delivery.`}
            </p>
          </div>

          {/* Section 2: MAIN FUNCTIONALITY */}
          <div className="pt-6 border-t border-slate-800/80">
            <span className="block text-[11px] font-extrabold tracking-widest text-slate-500 uppercase mb-2">
              MAIN FUNCTIONALITY
            </span>
            <p className="text-sm font-bold text-slate-200">
              {currentTool.mainFunctionality || currentTool.description}
            </p>
          </div>

          {/* Section 3: USE CASE */}
          <div className="pt-6 border-t border-slate-800/80">
            <span className="block text-[11px] font-extrabold tracking-widest text-slate-500 uppercase mb-2">
              USE CASE
            </span>
            <p className="text-sm font-bold text-slate-200">
              {currentTool.useCase || 'Integrate structured outputs into project evidence and workflow reviews.'}
            </p>
          </div>

          {/* Section 4: RELEVANT PROJECT AREA */}
          <div className="pt-6 border-t border-slate-800/80">
            <span className="block text-[11px] font-extrabold tracking-widest text-slate-500 uppercase mb-2">
              RELEVANT PROJECT AREA
            </span>
            <p className="text-sm font-bold text-slate-200">
              {currentTool.supportedArea}
            </p>
          </div>

          {/* Section 5: DEVELOPER / PROVIDER */}
          <div className="pt-6 border-t border-slate-800/80">
            <span className="block text-[11px] font-extrabold tracking-widest text-slate-500 uppercase mb-2">
              DEVELOPER / PROVIDER
            </span>
            <p className="text-sm font-bold text-slate-200">
              {currentTool.developerProvider || `${currentTool.name} Ltd`}
            </p>
          </div>

          {/* Section 6: STATUS */}
          <div className="pt-6 border-t border-slate-800/80">
            <span className="block text-[11px] font-extrabold tracking-widest text-slate-500 uppercase mb-2">
              STATUS
            </span>
            <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase border ${currentTool.statusColor}`}>
              <span className={`w-1.5 h-1.5 rounded-full ${currentTool.dotColor}`} />
              {currentTool.status}
            </span>
          </div>

          {/* Bottom Action Footer matching media_1790750996452.png */}
          <div className="flex items-center justify-end gap-3 pt-6 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setSelectedTool(null)}
              className="px-5 py-2.5 rounded-xl border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-200 font-bold text-xs cursor-pointer transition-colors"
            >
              Back to tools
            </button>

            <button
              type="button"
              onClick={() => handleUseToolToggle(currentTool)}
              className="px-6 py-2.5 rounded-xl bg-[#f59e0b] hover:bg-[#d97706] text-slate-950 font-extrabold text-xs shadow-md transition-all cursor-pointer border border-amber-300/60 hover:scale-[1.02]"
            >
              Use tool
            </button>
          </div>
        </div>
      </div>
    );
  }

  // -------------------------------------------------------------
  // VIEW A: TOOLS DIRECTORY CARDS GRID (Matching media_1790750500020.png)
  // -------------------------------------------------------------
  return (
    <div className="space-y-6 animate-fadeIn text-left relative">
      {/* Toast Notification Banner */}
      {toastMsg && (
        <div className="fixed top-16 right-6 z-50 bg-[#7c4a27] dark:bg-[#96562c] text-white px-4 py-3 rounded-xl shadow-2xl flex items-center gap-2.5 animate-fadeIn font-semibold text-xs sm:text-sm border-2 border-amber-300">
          <Check className="w-5 h-5 text-amber-300 shrink-0" />
          <span>{toastMsg}</span>
        </div>
      )}

      {/* Header Banner matching reference image media_1790750500020.png */}
      <div>
        <span className="text-[11px] font-extrabold tracking-widest text-[#7c4a27] dark:text-amber-400/90 uppercase">
          APPROVED ECOSYSTEM
        </span>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100 mt-1">
          Trusted Tools &amp; Software
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1.5 font-normal max-w-2xl">
          Discover reviewed software for secure regulatory and technical delivery.
        </p>
      </div>

      {/* Sub-Tabs Row (All Tools | My Used Tools) */}
      <div className="border-b border-slate-200 dark:border-slate-800 flex items-center gap-6 pt-2">
        <button
          type="button"
          onClick={() => setActiveSubTab('All Tools')}
          className={`pb-3 text-xs sm:text-sm font-bold transition-all relative cursor-pointer ${
            activeSubTab === 'All Tools'
              ? 'text-slate-900 dark:text-slate-100 border-b-2 border-amber-400'
              : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
          }`}
        >
          All Tools
        </button>

        <button
          type="button"
          onClick={() => setActiveSubTab('My Used Tools')}
          className={`pb-3 text-xs sm:text-sm font-semibold transition-all flex items-center gap-2 cursor-pointer ${
            activeSubTab === 'My Used Tools'
              ? 'text-slate-900 dark:text-slate-100 border-b-2 border-amber-400'
              : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
          }`}
        >
          <span>My Used Tools</span>
          <span className="w-5 h-5 rounded-full bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-bold text-[11px] flex items-center justify-center">
            {usedCount}
          </span>
        </button>
      </div>

      {/* Search & Filter Controls Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5 pt-1">
        {/* Search Input (Spans 2 cols on md/lg) */}
        <div className="sm:col-span-2 relative">
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
            <Search className="w-4 h-4" />
          </div>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search trusted tools"
            className="w-full pl-10 pr-4 py-2.5 text-xs sm:text-sm rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#161619] text-slate-900 dark:text-slate-100 placeholder-slate-500 focus:outline-none focus:border-[#96562c] focus:ring-2 focus:ring-[#96562c]/30 transition-all"
          />
        </div>

        {/* Category Dropdown */}
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#161619] text-slate-800 dark:text-slate-200 text-xs sm:text-sm font-semibold focus:outline-none focus:border-[#96562c] cursor-pointer transition-all"
        >
          <option value="All categories">All categories</option>
          <option value="Compliance">Compliance</option>
          <option value="Risk Management">Risk Management</option>
          <option value="AI / ML">AI / ML</option>
        </select>
      </div>

      {/* Tools Cards Grid (3 columns matching reference screenshot) */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 pt-2">
        {filteredTools.map((tool) => {
          const isActive = activeCardId === tool.id;
          const isApproved = tool.status?.toLowerCase() === 'approved';

          return (
            <div
              key={tool.id}
              onClick={() => setActiveCardId(isActive ? null : tool.id)}
              title="Click box to toggle brown border, cream edge lighting glow & zoom-in"
              className={`rounded-2xl border p-5 flex flex-col justify-between transition-all duration-300 cursor-pointer ${
                isActive
                  ? isDarkMode
                    ? 'bg-[#1e1e24] border-[#96562c] scale-[1.015] shadow-[0_0_35px_rgba(251,191,36,0.25),0_12px_36px_rgba(150,86,44,0.35)] ring-2 ring-[#96562c]/40'
                    : 'bg-[#fdfdf9] border-[#7c4a27] scale-[1.015] shadow-[0_0_40px_rgba(254,243,199,0.95),0_14px_40px_rgba(124,74,39,0.22)] ring-4 ring-amber-100/90'
                  : isDarkMode
                  ? 'bg-[#161619] border-slate-800/90 shadow-md hover:border-[#96562c] hover:scale-[1.01]'
                  : 'bg-white border-stone-200/90 shadow-xs hover:border-[#7c4a27] hover:scale-[1.01]'
              }`}
            >
              <div>
                {/* Header Row: Wrench Icon Badge & Status Pill */}
                <div className="flex items-center justify-between mb-4">
                  <div className="w-8 h-8 rounded-md bg-[#7c4a27]/30 dark:bg-[#96562c]/30 text-amber-700 dark:text-amber-300 border border-amber-300/30 dark:border-[#96562c]/50 font-bold text-xs flex items-center justify-center">
                    <Wrench className="w-4 h-4 stroke-[2.2]" />
                  </div>
                  <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border ${tool.statusColor}`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${tool.dotColor}`} />
                    {tool.status}
                  </span>
                </div>

                {/* Tool Name, Category & Description */}
                <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 tracking-tight">
                  {tool.name}
                </h3>
                <p className="text-xs sm:text-sm font-semibold text-slate-600 dark:text-slate-400 mt-1">
                  {tool.category}
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-2 leading-relaxed font-normal">
                  {tool.description}
                </p>

                {/* Supported Area Footer Label */}
                <p className="text-xs text-slate-400 dark:text-slate-500 font-mono mt-4">
                  Supported area: <span className="font-semibold text-slate-300 dark:text-slate-400">{tool.supportedArea}</span>
                </p>
              </div>

              {/* Bottom Action Button */}
              <div className="pt-5 mt-5 border-t border-slate-100 dark:border-slate-800/80">
                <button
                  type="button"
                  disabled={isApproved}
                  onClick={(e) => {
                    e.stopPropagation();
                    if (!isApproved) {
                      setSelectedTool(tool);
                    }
                  }}
                  className={`w-full py-2.5 rounded-xl text-xs font-bold border transition-colors ${
                    isApproved
                      ? 'border-slate-800/80 bg-slate-900/50 text-slate-500 cursor-not-allowed opacity-50'
                      : 'border-slate-300 dark:border-slate-700 bg-stone-50 dark:bg-slate-800/80 hover:bg-stone-100 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-100 cursor-pointer'
                  }`}
                >
                  View details
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

