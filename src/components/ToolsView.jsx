import React, { useState, useEffect, useMemo } from 'react';
import {
  Search,
  Wrench,
  Check,
  ArrowLeft,
  ExternalLink,
  Shield,
  Filter,
  Info,
  AlertTriangle,
  Trash2,
  Plus,
  X,
  Clock,
  BookOpen,
} from 'lucide-react';
import {
  getTools,
  getProjectTools,
  addProjectTool,
  removeProjectTool,
} from '../services/toolService';

export default function ToolsView({
  isDarkMode = true,
  activeProject = null,
  projects = [],
  currentUser = null,
  onSelectProject = null,
}) {
  // Navigation Sub-Tabs: 'All Tools' | 'My Used Tools'
  const [activeSubTab, setActiveSubTab] = useState('All Tools');

  // Search & Filter States
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('All categories');
  const [jurisdictionFilter, setJurisdictionFilter] = useState('All jurisdictions');
  const [reviewStatusFilter, setReviewStatusFilter] = useState('All statuses');

  // Interactive Card Selection & Detailed Tool Inspection
  const [activeCardId, setActiveCardId] = useState(null);
  const [selectedTool, setSelectedTool] = useState(null);
  const [toolNotesInput, setToolNotesInput] = useState('');

  // Master Data States
  const [toolsList, setToolsList] = useState([]);
  const [projectTools, setProjectTools] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [toastMsg, setToastMsg] = useState(null);

  // Active Project Context
  const effectiveProject =
    activeProject ||
    (projects && projects.length > 0 ? projects[0] : null) || {
      id: 'default-project',
      project_id: 'default-project',
      name: 'Default FCC Project',
      status: 'ACTIVE',
    };

  const currentProjectId = effectiveProject.id || effectiveProject.project_id || 'default-project';
  const isProjectDisabled = (effectiveProject.status || '').toUpperCase() === 'DISABLED';
  const userEmail = currentUser?.email || 'builder@finregtech.io';

  // -------------------------------------------------------------
  // Data Loading
  // -------------------------------------------------------------
  const loadCatalogueAndProjectTools = async () => {
    setIsLoading(true);
    try {
      const [allCatalogue, usedTools] = await Promise.all([
        getTools(),
        getProjectTools(currentProjectId),
      ]);
      setToolsList(allCatalogue);
      setProjectTools(usedTools);
    } catch (err) {
      console.warn('[ToolsView] Error loading tools data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadCatalogueAndProjectTools();
  }, [currentProjectId]);

  // Set of tool IDs currently associated with the active project
  const usedToolIdSet = useMemo(() => {
    return new Set(projectTools.map((t) => t.id || t.tool_id));
  }, [projectTools]);

  const usedCount = projectTools.length;

  // -------------------------------------------------------------
  // Filtering Logic
  // -------------------------------------------------------------
  const filteredTools = useMemo(() => {
    const list = activeSubTab === 'My Used Tools' ? projectTools : toolsList;

    return list.filter((tool) => {
      // Text search
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchName = (tool.name || '').toLowerCase().includes(q);
        const matchProvider = (tool.provider || '').toLowerCase().includes(q);
        const matchCategory = (tool.category || '').toLowerCase().includes(q);
        const matchDesc =
          (tool.short_description || tool.description || '').toLowerCase().includes(q) ||
          (tool.full_description || '').toLowerCase().includes(q);
        const matchUseCase = (tool.use_cases || []).some((u) => u.toLowerCase().includes(q));
        if (!matchName && !matchProvider && !matchCategory && !matchDesc && !matchUseCase) {
          return false;
        }
      }

      // Category filter
      if (categoryFilter !== 'All categories' && tool.category !== categoryFilter) {
        return false;
      }

      // Jurisdiction filter
      if (jurisdictionFilter !== 'All jurisdictions') {
        const hasJur = (tool.jurisdictions || []).some(
          (j) => j.toLowerCase() === jurisdictionFilter.toLowerCase()
        );
        if (!hasJur) return false;
      }

      // Review Status filter
      if (reviewStatusFilter !== 'All statuses') {
        if (tool.review_status !== reviewStatusFilter) return false;
      }

      return true;
    });
  }, [
    activeSubTab,
    toolsList,
    projectTools,
    searchQuery,
    categoryFilter,
    jurisdictionFilter,
    reviewStatusFilter,
  ]);

  const hasActiveFilters =
    searchQuery.trim() !== '' ||
    categoryFilter !== 'All categories' ||
    jurisdictionFilter !== 'All jurisdictions' ||
    reviewStatusFilter !== 'All statuses';

  const handleResetFilters = () => {
    setSearchQuery('');
    setCategoryFilter('All categories');
    setJurisdictionFilter('All jurisdictions');
    setReviewStatusFilter('All statuses');
  };

  // -------------------------------------------------------------
  // Add / Remove Tool Associations
  // -------------------------------------------------------------
  const showToast = (message) => {
    setToastMsg(message);
    setTimeout(() => setToastMsg(null), 3500);
  };

  const handleAddToolToProject = async (tool, customNotes = '') => {
    if (isProjectDisabled) {
      showToast('Action blocked: This project is disabled and locked in read-only mode.');
      return;
    }
    const targetToolId = tool.id || tool.tool_id;
    try {
      await addProjectTool(currentProjectId, targetToolId, userEmail, customNotes);
      const updated = await getProjectTools(currentProjectId);
      setProjectTools(updated);
      showToast(`Tool "${tool.name}" added to ${effectiveProject.name}!`);
      setToolNotesInput('');
    } catch (err) {
      console.warn('[ToolsView] Failed to add tool to project:', err);
      showToast(`Error adding "${tool.name}" to project.`);
    }
  };

  const handleRemoveToolFromProject = async (tool) => {
    if (isProjectDisabled) {
      showToast('Action blocked: This project is disabled and locked in read-only mode.');
      return;
    }
    const targetToolId = tool.id || tool.tool_id;
    try {
      await removeProjectTool(currentProjectId, targetToolId, userEmail);
      const updated = await getProjectTools(currentProjectId);
      setProjectTools(updated);
      showToast(`Tool "${tool.name}" removed from ${effectiveProject.name}.`);
    } catch (err) {
      console.warn('[ToolsView] Failed to remove tool from project:', err);
      showToast(`Error removing "${tool.name}" from project.`);
    }
  };

  // Helper for Status Badge Styling
  const getReviewStatusBadge = (status = '') => {
    const s = (status || '').toLowerCase();
    if (s.includes('reviewed')) {
      return {
        label: 'Reviewed for listing',
        badgeClass: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
        dotClass: 'bg-emerald-400',
        icon: Check,
      };
    }
    if (s.includes('pending')) {
      return {
        label: 'Pending review',
        badgeClass: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
        dotClass: 'bg-amber-400',
        icon: Clock,
      };
    }
    if (s.includes('update')) {
      return {
        label: 'Needs update',
        badgeClass: 'bg-orange-500/10 text-orange-400 border-orange-500/30',
        dotClass: 'bg-orange-400',
        icon: AlertTriangle,
      };
    }
    return {
      label: status || 'Archived',
      badgeClass: 'bg-slate-500/10 text-slate-400 border-slate-500/30',
      dotClass: 'bg-slate-400',
      icon: Shield,
    };
  };

  // -------------------------------------------------------------
  // VIEW B: TOOL DETAILS PAGE VIEW
  // -------------------------------------------------------------
  if (selectedTool) {
    const targetId = selectedTool.id || selectedTool.tool_id;
    const isCurrentlyUsed = usedToolIdSet.has(targetId);
    const statusMeta = getReviewStatusBadge(selectedTool.review_status);
    const StatusIcon = statusMeta.icon;

    return (
      <div className="space-y-6 animate-fadeIn text-left relative">
        {/* Toast Notification Banner */}
        {toastMsg && (
          <div className="fixed top-16 right-6 z-50 bg-[#7c4a27] dark:bg-[#96562c] text-white px-4 py-3 rounded-xl shadow-2xl flex items-center gap-2.5 animate-fadeIn font-semibold text-xs sm:text-sm border-2 border-amber-300">
            <Check className="w-5 h-5 text-amber-300 shrink-0" />
            <span>{toastMsg}</span>
          </div>
        )}

        {/* Top-Left Back Button */}
        <div>
          <button
            type="button"
            onClick={() => {
              setSelectedTool(null);
              setToolNotesInput('');
            }}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl border border-slate-700 dark:border-slate-800 bg-white dark:bg-slate-900/80 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white font-bold text-xs cursor-pointer transition-all group shadow-sm"
          >
            <ArrowLeft className="w-4 h-4 text-amber-500 group-hover:-translate-x-0.5 transition-transform" />
            <span>Back to tools catalogue</span>
          </button>
        </div>

        {/* Top Header Row */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 pb-6 border-b border-slate-200 dark:border-slate-800">
          <div className="flex items-start sm:items-center gap-5">
            <div className="w-14 h-14 rounded-2xl bg-[#7c4a27]/20 dark:bg-[#96562c]/30 text-amber-600 dark:text-amber-300 border-2 border-amber-500/40 font-bold text-xl flex items-center justify-center shrink-0 shadow-md">
              <Wrench className="w-7 h-7 stroke-[2.2]" />
            </div>

            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-[11px] font-extrabold tracking-widest text-[#7c4a27] dark:text-amber-400 uppercase">
                  {selectedTool.category}
                </span>
                <span className="text-slate-400 dark:text-slate-600">•</span>
                <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400">
                  {selectedTool.provider}
                </span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100 mt-1">
                {selectedTool.name}
              </h1>
              <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 mt-1 font-medium max-w-2xl leading-relaxed">
                {selectedTool.short_description || selectedTool.description}
              </p>
            </div>
          </div>

          {/* Status Badges */}
          <div className="flex flex-wrap sm:flex-col items-start sm:items-end gap-2">
            <span
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold border ${statusMeta.badgeClass}`}
            >
              <StatusIcon className="w-3.5 h-3.5 shrink-0" />
              {statusMeta.label}
            </span>
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-bold bg-blue-500/10 text-blue-500 dark:text-blue-400 border border-blue-500/20">
              <Shield className="w-3 h-3" />
              Directory Listing Only
            </span>
          </div>
        </div>

        {/* Regulatory Governance Disclaimer Banner */}
        <div className="p-4 rounded-xl border border-amber-500/30 bg-amber-500/5 dark:bg-amber-950/20 flex items-start gap-3 text-xs text-amber-800 dark:text-amber-300/90 leading-relaxed">
          <Info className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold">Directory Listing Notice: </span>
            A tool listed in this catalogue is not automatically connected to your project, does not
            receive project data, and is not necessarily an endorsement or statutory compliance approval.
            Recording this tool simply marks it as considered or used for your compliance evidence.
          </div>
        </div>

        {/* Main Details Grid */}
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#161619] p-6 sm:p-8 space-y-7 shadow-lg">
          {/* Section 1: Detailed Overview */}
          <div>
            <span className="block text-[11px] font-extrabold tracking-widest text-slate-500 uppercase mb-2">
              OVERVIEW &amp; CAPABILITIES
            </span>
            <p className="text-sm font-normal text-slate-700 dark:text-slate-200 leading-relaxed">
              {selectedTool.full_description ||
                selectedTool.fullDescription ||
                selectedTool.short_description ||
                `${selectedTool.name} is a curated software tool evaluated to support regulatory compliance delivery.`}
            </p>
          </div>

          {/* Section 2: Supported Use Cases */}
          <div className="pt-6 border-t border-slate-200 dark:border-slate-800/80">
            <span className="block text-[11px] font-extrabold tracking-widest text-slate-500 uppercase mb-2.5">
              SUPPORTED COMPLIANCE USE CASES
            </span>
            <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-semibold text-slate-800 dark:text-slate-200">
              {(selectedTool.use_cases || ['Regulatory verification', 'Evidence tracking']).map(
                (uc, i) => (
                  <li key={i} className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-500 shrink-0" />
                    <span>{uc}</span>
                  </li>
                )
              )}
            </ul>
          </div>

          {/* Section 3: Jurisdictions & Frameworks */}
          <div className="pt-6 border-t border-slate-200 dark:border-slate-800/80">
            <span className="block text-[11px] font-extrabold tracking-widest text-slate-500 uppercase mb-2">
              RELEVANT JURISDICTIONS &amp; FRAMEWORKS
            </span>
            <div className="flex flex-wrap gap-2">
              {(selectedTool.jurisdictions || ['UK FCA', 'Global']).map((j, idx) => (
                <span
                  key={idx}
                  className="px-2.5 py-1 rounded-md text-xs font-bold bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 border border-slate-300 dark:border-slate-700"
                >
                  {j}
                </span>
              ))}
            </div>
          </div>

          {/* Section 4: Information Source & Review Audit */}
          <div className="pt-6 border-t border-slate-200 dark:border-slate-800/80 grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <span className="block text-[11px] font-extrabold tracking-widest text-slate-500 uppercase mb-1">
                INFORMATION SOURCE &amp; VERIFICATION
              </span>
              <p className="text-xs font-bold text-slate-700 dark:text-slate-300">
                {selectedTool.source_reference || 'Official Provider Documentation'}
              </p>
              <p className="text-[11px] text-slate-500 mt-1">
                Last checked by catalogue editors: <span className="font-semibold text-slate-400">{selectedTool.last_checked_date || 'November 2026'}</span>
              </p>
            </div>

            <div>
              <span className="block text-[11px] font-extrabold tracking-widest text-slate-500 uppercase mb-1">
                OFFICIAL WEBSITE / DOCUMENTATION
              </span>
              {selectedTool.official_url && selectedTool.official_url !== '#' ? (
                <a
                  href={selectedTool.official_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-xs font-bold text-amber-600 dark:text-amber-400 hover:underline break-all"
                >
                  <span>{selectedTool.official_url}</span>
                  <ExternalLink className="w-3.5 h-3.5 shrink-0" />
                </a>
              ) : (
                <span className="text-xs text-slate-400">Available upon vendor contract</span>
              )}
            </div>
          </div>

          {/* Section 5: Limitations & Applicability Notes (Callout Box) */}
          <div className="pt-6 border-t border-slate-200 dark:border-slate-800/80">
            <span className="block text-[11px] font-extrabold tracking-widest text-slate-500 uppercase mb-2">
              LIMITATIONS &amp; APPLICABILITY NOTES
            </span>
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 text-xs text-slate-700 dark:text-slate-300 leading-relaxed flex items-start gap-3">
              <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
              <span>
                {selectedTool.limitations_notes ||
                  'Applicability must be confirmed for your specific entity, license permissions, and jurisdictional risk thresholds.'}
              </span>
            </div>
          </div>

          {/* Section 6: Project Association Controls */}
          <div className="pt-6 border-t border-slate-200 dark:border-slate-800/80 bg-slate-50/50 dark:bg-slate-900/40 p-5 rounded-xl border">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
              <div>
                <span className="text-[11px] font-extrabold tracking-widest text-slate-500 uppercase">
                  PROJECT RECORDING FOR:
                </span>
                <h4 className="text-sm font-extrabold text-slate-900 dark:text-slate-100 flex items-center gap-2 mt-0.5">
                  <span>{effectiveProject.name}</span>
                  {isCurrentlyUsed && (
                    <span className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                      <Check className="w-3 h-3" /> Recorded in Project
                    </span>
                  )}
                </h4>
              </div>

              {isProjectDisabled && (
                <span className="text-xs font-bold text-rose-500 flex items-center gap-1">
                  <AlertTriangle className="w-4 h-4" /> Project is locked / disabled
                </span>
              )}
            </div>

            {!isCurrentlyUsed ? (
              <div className="space-y-3">
                <input
                  type="text"
                  value={toolNotesInput}
                  disabled={isProjectDisabled}
                  onChange={(e) => setToolNotesInput(e.target.value)}
                  placeholder="Optional note: Why is this tool used? (e.g. 'PEP checks for tier-1 merchants')"
                  className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#161619] text-slate-900 dark:text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500"
                />
                <div className="flex justify-end gap-3">
                  <button
                    type="button"
                    onClick={() => setSelectedTool(null)}
                    className="px-4 py-2 text-xs font-bold rounded-xl border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    disabled={isProjectDisabled}
                    onClick={() => handleAddToolToProject(selectedTool, toolNotesInput)}
                    className="px-5 py-2 text-xs font-extrabold rounded-xl bg-amber-500 hover:bg-amber-600 disabled:opacity-50 text-slate-950 flex items-center gap-1.5 cursor-pointer shadow-md transition-transform hover:scale-[1.01]"
                  >
                    <Plus className="w-4 h-4" />
                    <span>Add to {effectiveProject.name}</span>
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pt-2">
                <p className="text-xs text-slate-500">
                  This tool is currently recorded as part of your project&apos;s compliance software stack.
                </p>
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={() => setSelectedTool(null)}
                    className="px-4 py-2 text-xs font-bold rounded-xl border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 cursor-pointer"
                  >
                    Close
                  </button>
                  <button
                    type="button"
                    disabled={isProjectDisabled}
                    onClick={() => handleRemoveToolFromProject(selectedTool)}
                    className="px-4 py-2 text-xs font-bold rounded-xl border border-rose-500/40 text-rose-500 hover:bg-rose-500/10 flex items-center gap-1.5 cursor-pointer transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                    <span>Remove from Project</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // -------------------------------------------------------------
  // VIEW A: TOOLS DIRECTORY LISTING
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

      {/* Header Banner */}
      <div>
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-extrabold tracking-widest text-[#7c4a27] dark:text-amber-400 uppercase">
            REGULATORY TOOLS MODULE
          </span>
          <span className="text-slate-400 dark:text-slate-600">•</span>
          <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
            Curated Compliance Directory
          </span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100 mt-1">
          Trusted Tools &amp; Software
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1.5 font-normal max-w-3xl leading-relaxed">
          Find and track software and services that support regulatory and technical project delivery.
          All listings are verified directory entries; adding a tool records usage for your project without transmitting project data.
        </p>
      </div>

      {/* Project Context & Selector Bar */}
      <div className="p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#161619] flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-500 flex items-center justify-center font-bold">
            <BookOpen className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">
              Active Project Context
            </span>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-slate-900 dark:text-slate-100">
                {effectiveProject.name}
              </span>
              {isProjectDisabled ? (
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/10 text-rose-500 border border-rose-500/20">
                  Disabled
                </span>
              ) : (
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  Active
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Project Switcher Dropdown (if multiple projects exist) */}
        {projects && projects.length > 1 && onSelectProject && (
          <div className="flex items-center gap-2">
            <label className="text-xs font-semibold text-slate-500 whitespace-nowrap">
              Switch Project:
            </label>
            <select
              value={currentProjectId}
              onChange={(e) => {
                const found = projects.find(
                  (p) => String(p.id || p.project_id) === String(e.target.value)
                );
                if (found) onSelectProject(found);
              }}
              className="px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 text-xs font-semibold text-slate-800 dark:text-slate-200 focus:outline-none focus:border-amber-500"
            >
              {projects.map((p) => {
                const pid = p.id || p.project_id;
                return (
                  <option key={pid} value={pid}>
                    {p.name}
                  </option>
                );
              })}
            </select>
          </div>
        )}
      </div>

      {/* Sub-Tabs Row: All Tools | My Used Tools */}
      <div className="border-b border-slate-200 dark:border-slate-800 flex items-center gap-6 pt-2">
        <button
          type="button"
          onClick={() => setActiveSubTab('All Tools')}
          className={`pb-3 text-xs sm:text-sm font-bold transition-all relative cursor-pointer flex items-center gap-2 ${
            activeSubTab === 'All Tools'
              ? 'text-slate-900 dark:text-slate-100 border-b-2 border-amber-400'
              : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
          }`}
        >
          <span>All Tools</span>
          <span className="w-5 h-5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-bold text-[11px] flex items-center justify-center">
            {toolsList.length}
          </span>
        </button>

        <button
          type="button"
          onClick={() => setActiveSubTab('My Used Tools')}
          className={`pb-3 text-xs sm:text-sm font-bold transition-all flex items-center gap-2 cursor-pointer ${
            activeSubTab === 'My Used Tools'
              ? 'text-slate-900 dark:text-slate-100 border-b-2 border-amber-400'
              : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
          }`}
        >
          <span>My Used Tools</span>
          <span
            className={`w-5 h-5 rounded-full font-bold text-[11px] flex items-center justify-center ${
              usedCount > 0
                ? 'bg-amber-500/20 text-amber-500 dark:text-amber-400'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-500'
            }`}
          >
            {usedCount}
          </span>
        </button>
      </div>

      {/* Search & Multi-Filter Controls Bar */}
      <div className="space-y-3 pt-1">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {/* Search Input (spans 2 cols on lg) */}
          <div className="lg:col-span-2 relative">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
              <Search className="w-4 h-4" />
            </div>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search tools, providers, use cases..."
              className="w-full pl-10 pr-9 py-2.5 text-xs sm:text-sm rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#161619] text-slate-900 dark:text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500 focus:ring-2 focus:ring-amber-500/20 transition-all"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery('')}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-200 cursor-pointer"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Category Dropdown */}
          <div>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#161619] text-slate-800 dark:text-slate-200 text-xs sm:text-sm font-semibold focus:outline-none focus:border-amber-500 cursor-pointer transition-all"
            >
              <option value="All categories">All categories</option>
              <option value="KYC & Screening">KYC &amp; Screening</option>
              <option value="Transaction Monitoring">Transaction Monitoring</option>
              <option value="Client Lifecycle & CDD">Client Lifecycle &amp; CDD</option>
              <option value="Crypto & Blockchain Compliance">Crypto &amp; Blockchain</option>
              <option value="Regulatory Reporting & Risk">Regulatory Reporting</option>
            </select>
          </div>

          {/* Jurisdiction Dropdown */}
          <div>
            <select
              value={jurisdictionFilter}
              onChange={(e) => setJurisdictionFilter(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#161619] text-slate-800 dark:text-slate-200 text-xs sm:text-sm font-semibold focus:outline-none focus:border-amber-500 cursor-pointer transition-all"
            >
              <option value="All jurisdictions">All jurisdictions</option>
              <option value="UK FCA">UK FCA</option>
              <option value="PRA">PRA</option>
              <option value="EU AMLD">EU AMLD</option>
              <option value="Global">Global</option>
            </select>
          </div>

          {/* Review Status Dropdown */}
          <div>
            <select
              value={reviewStatusFilter}
              onChange={(e) => setReviewStatusFilter(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#161619] text-slate-800 dark:text-slate-200 text-xs sm:text-sm font-semibold focus:outline-none focus:border-amber-500 cursor-pointer transition-all"
            >
              <option value="All statuses">All review statuses</option>
              <option value="Reviewed for listing">Reviewed for listing</option>
              <option value="Pending review">Pending review</option>
              <option value="Needs update">Needs update</option>
            </select>
          </div>
        </div>

        {/* Filter Summary & Reset Pill */}
        {hasActiveFilters && (
          <div className="flex items-center justify-between text-xs text-slate-500 px-1">
            <span>
              Showing <b className="text-slate-300">{filteredTools.length}</b> matching records
            </span>
            <button
              type="button"
              onClick={handleResetFilters}
              className="inline-flex items-center gap-1 text-amber-500 hover:text-amber-400 font-bold cursor-pointer"
            >
              <X className="w-3.5 h-3.5" />
              <span>Reset all filters</span>
            </button>
          </div>
        )}
      </div>

      {/* Tools Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 pt-2">
        {filteredTools.length === 0 ? (
          <div className="col-span-1 md:col-span-2 lg:col-span-3 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#161619] p-12 text-center text-slate-400 dark:text-slate-500 space-y-3">
            <div className="w-12 h-12 mx-auto rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-400">
              <Filter className="w-6 h-6" />
            </div>
            {activeSubTab === 'My Used Tools' ? (
              <div>
                <h3 className="text-base font-bold text-slate-300">
                  No tools currently recorded for {effectiveProject.name}
                </h3>
                <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
                  Browse the &quot;All Tools&quot; tab to explore vetted compliance software and record the ones your project uses.
                </p>
                <button
                  type="button"
                  onClick={() => setActiveSubTab('All Tools')}
                  className="mt-4 px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-xs cursor-pointer"
                >
                  Browse All Tools
                </button>
              </div>
            ) : (
              <div>
                <h3 className="text-base font-bold text-slate-300">
                  No catalogue tools match your filters
                </h3>
                <p className="text-xs text-slate-500 mt-1">
                  Try clearing your search query or adjusting your category/jurisdiction filters.
                </p>
                <button
                  type="button"
                  onClick={handleResetFilters}
                  className="mt-4 px-4 py-2 rounded-xl border border-slate-700 hover:bg-slate-800 text-slate-300 font-bold text-xs cursor-pointer"
                >
                  Clear Filters
                </button>
              </div>
            )}
          </div>
        ) : (
          filteredTools.map((tool) => {
            const targetId = tool.id || tool.tool_id;
            const isUsedInProject = usedToolIdSet.has(targetId);
            const statusMeta = getReviewStatusBadge(tool.review_status);
            const StatusIcon = statusMeta.icon;
            const isActive = activeCardId === targetId;

            return (
              <div
                key={targetId}
                onClick={() => setActiveCardId(isActive ? null : targetId)}
                className={`rounded-2xl border p-5 flex flex-col justify-between transition-all duration-200 cursor-pointer text-left relative ${
                  isActive
                    ? isDarkMode
                      ? 'bg-[#1e1e24] border-[#96562c] shadow-[0_0_30px_rgba(251,191,36,0.2)] ring-2 ring-[#96562c]/50'
                      : 'bg-white border-[#7c4a27] shadow-[0_0_30px_rgba(254,243,199,0.9)] ring-2 ring-amber-200'
                    : isDarkMode
                    ? 'bg-[#161619] border-slate-800/90 hover:border-slate-700 hover:scale-[1.01]'
                    : 'bg-white border-stone-200 hover:border-stone-300 hover:scale-[1.01]'
                }`}
              >
                <div>
                  {/* Card Header: Icon, Category & Review Status */}
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <div className="w-8 h-8 rounded-lg bg-[#7c4a27]/20 dark:bg-[#96562c]/30 text-amber-600 dark:text-amber-300 border border-amber-500/30 flex items-center justify-center font-bold">
                      <Wrench className="w-4 h-4 stroke-[2.2]" />
                    </div>

                    <span
                      className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${statusMeta.badgeClass}`}
                    >
                      <StatusIcon className="w-3 h-3 shrink-0" />
                      <span>{statusMeta.label}</span>
                    </span>
                  </div>

                  {/* Provider & Name */}
                  <span className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">
                    {tool.provider}
                  </span>
                  <h3 className="text-base font-extrabold text-slate-900 dark:text-slate-100 tracking-tight mt-0.5 line-clamp-1">
                    {tool.name}
                  </h3>

                  {/* Short Description */}
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-2 leading-relaxed line-clamp-2">
                    {tool.short_description || tool.description}
                  </p>

                  {/* Jurisdictions Badges & Tag */}
                  <div className="flex flex-wrap items-center gap-1.5 mt-3.5">
                    {(tool.jurisdictions || ['UK FCA']).map((j, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 dark:bg-slate-800/80 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700"
                      >
                        {j}
                      </span>
                    ))}
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-500/10 text-blue-500 dark:text-blue-400 border border-blue-500/20">
                      Directory
                    </span>
                  </div>

                  {/* Display Builder Note if in My Used Tools */}
                  {tool.notes && (
                    <div className="mt-3 p-2 rounded-lg bg-amber-500/5 border border-amber-500/20 text-[11px] text-amber-300/90 italic">
                      &quot;{tool.notes}&quot;
                    </div>
                  )}
                </div>

                {/* Card Action Footer */}
                <div className="pt-4 mt-4 border-t border-slate-100 dark:border-slate-800/80 flex items-center gap-2">
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedTool(tool);
                    }}
                    className="flex-1 py-2 rounded-xl text-xs font-bold border border-slate-300 dark:border-slate-700 bg-stone-50 dark:bg-slate-800/80 hover:bg-stone-100 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 cursor-pointer transition-colors"
                  >
                    View details
                  </button>

                  {isUsedInProject ? (
                    <button
                      type="button"
                      disabled={isProjectDisabled}
                      title="Click to remove from project"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRemoveToolFromProject(tool);
                      }}
                      className="px-3 py-2 rounded-xl text-xs font-bold bg-emerald-500/10 hover:bg-rose-500/10 border border-emerald-500/30 hover:border-rose-500/30 text-emerald-400 hover:text-rose-400 flex items-center gap-1 cursor-pointer transition-colors group"
                    >
                      <Check className="w-3.5 h-3.5 group-hover:hidden" />
                      <Trash2 className="w-3.5 h-3.5 hidden group-hover:inline" />
                      <span className="group-hover:hidden">Used</span>
                      <span className="hidden group-hover:inline">Remove</span>
                    </button>
                  ) : (
                    <button
                      type="button"
                      disabled={isProjectDisabled}
                      title={`Add tool to ${effectiveProject.name}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleAddToolToProject(tool);
                      }}
                      className="px-3 py-2 rounded-xl text-xs font-bold bg-amber-500/10 hover:bg-amber-500 border border-amber-500/30 hover:border-amber-500 text-amber-400 hover:text-slate-950 flex items-center gap-1 cursor-pointer transition-all"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      <span>Use</span>
                    </button>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
