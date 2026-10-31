import React, { useState, useEffect } from 'react';
import {
  Search,
  Sparkles,
  ArrowRight,
  ExternalLink,
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Copy,
  Check,
  RefreshCw,
  Sliders,
  Scale,
  GitCompare,
  Layers,
  HelpCircle,
  FileQuestion,
  BookOpen,
  ChevronDown,
  ChevronUp,
  Info,
} from 'lucide-react';
import {
  checkRAGHealth,
  submitRegulatoryQuery,
  compareAdvisorPositions,
} from '../services/ragService';

export default function AiRagFindingsView({
  isDarkMode = true,
  activeProject,
  onNavigateTab,
}) {
  // Tab state: 'query' (Regulatory Query Workspace) | 'compare' (Advisor Advice Comparison)
  const [activeTabMode, setActiveTabMode] = useState('query');

  // Backend Health state
  const [healthStatus, setHealthStatus] = useState({ isOnline: true, status: 'CHECKING' });

  // Query Workspace States
  const [queryInput, setQueryInput] = useState(
    'What are the customer due diligence (CDD) verification timelines under MLR 2017?'
  );
  const [useTenantScope, setUseTenantScope] = useState(false); // false = Public Corpus (null project_id), true = Tenant Project
  const [isQuerying, setIsQuerying] = useState(false);
  const [queryResult, setQueryResult] = useState(null);
  const [queryError, setQueryError] = useState(null);
  const [evidenceActiveSubTab, setEvidenceActiveSubTab] = useState('evidence'); // 'evidence' | 'citations' | 'provenance' | 'conflicts' | 'gaps'

  // Advisor Comparison States
  const [isComparing, setIsComparing] = useState(false);
  const [compareResult, setCompareResult] = useState(null);
  const [compareTopic, setCompareTopic] = useState('Timing of Customer Due Diligence Verification');
  const [copiedId, setCopiedId] = useState(null);
  const [expandedChunkId, setExpandedChunkId] = useState(null);

  const targetProjectId = activeProject?.id || activeProject?.project_id || 'PRJ-ABC-001';
  const targetProjectName = activeProject?.name || 'Regulatory Compliance Framework';
  const targetJurisdiction = activeProject?.jurisdiction || 'United Kingdom - FCA';
  const targetRegulatoryArea = activeProject?.type || 'AML / CTF & MLR 2017';

  // 1. Initial health check and automatic initial query run
  useEffect(() => {
    let isMounted = true;
    async function init() {
      const health = await checkRAGHealth();
      if (isMounted) setHealthStatus(health);

      // Execute baseline default query demonstration
      setIsQuerying(true);
      try {
        const initialRes = await submitRegulatoryQuery({
          project_id: useTenantScope ? targetProjectId : null,
          query: queryInput,
        });
        if (isMounted) setQueryResult(initialRes);
      } catch (err) {
        if (isMounted) setQueryError(err.message);
      } finally {
        if (isMounted) setIsQuerying(false);
      }

      // Execute baseline comparison demonstration
      try {
        const initialCmp = await compareAdvisorPositions({
          project_id: targetProjectId,
          advisor_1_id: 'ADV-101',
          advisor_2_id: 'ADV-102',
          topic: compareTopic,
        });
        if (isMounted) setCompareResult(initialCmp);
      } catch (e) {}
    }

    init();
    return () => {
      isMounted = false;
    };
  }, [activeProject]);

  // Copy helper
  const handleCopy = (text, id) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2500);
  };

  // Submit Query Handler
  const handleQuerySubmit = async (e) => {
    if (e) e.preventDefault();
    if (!queryInput.trim() || isQuerying) return;

    setIsQuerying(true);
    setQueryError(null);
    try {
      const res = await submitRegulatoryQuery({
        project_id: useTenantScope ? targetProjectId : null,
        query: queryInput.trim(),
      });
      setQueryResult(res);
    } catch (err) {
      setQueryError(err.message || 'Regulatory query failed. Please verify connection.');
    } finally {
      setIsQuerying(false);
    }
  };

  // Run Advisor Comparison Handler
  const handleCompareSubmit = async () => {
    setIsComparing(true);
    try {
      const cmp = await compareAdvisorPositions({
        project_id: targetProjectId,
        advisor_1_id: 'ADV-101',
        advisor_2_id: 'ADV-102',
        topic: compareTopic,
      });
      setCompareResult(cmp);
    } catch (err) {
      console.warn('[AiRagFindingsView] Comparison error:', err);
    } finally {
      setIsComparing(false);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn text-left relative max-w-7xl mx-auto pb-12">
      {/* 1. TOP HEADER & CONTEXT BAR (Section 3: Page Context) */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-mono tracking-widest text-amber-500 font-bold uppercase">
              AI / RAG REGULATORY FINDINGS &amp; CONFLICT DETECTION
            </span>
            <span className="text-slate-600">·</span>
            <span
              className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold border ${
                healthStatus.isOnline
                  ? 'border-emerald-800/60 bg-emerald-950/40 text-emerald-400'
                  : 'border-amber-800/60 bg-amber-950/40 text-amber-300'
              }`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  healthStatus.isOnline ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'
                }`}
              />
              <span>{healthStatus.isOnline ? 'RAG Engine Active' : 'Standalone RAG Engine'}</span>
            </span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white flex items-center gap-2.5">
            <span>AI / RAG Findings</span>
          </h1>

          <p className="text-xs sm:text-sm text-slate-400 mt-1 font-normal max-w-3xl">
            Traceable regulatory evidence retrieval, similarity scoring, provenance lineage, and independent advisor position comparisons.
          </p>
        </div>

        {/* Project Context Badge Card */}
        <div className="bg-[#161619] border border-slate-800 rounded-xl px-4 py-2.5 shrink-0 flex flex-col justify-center">
          <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold">
            ACTIVE PROJECT CONTEXT
          </div>
          <div className="text-sm font-bold text-white flex items-center gap-2 mt-0.5">
            <span>{targetProjectName}</span>
            <span className="text-xs font-mono px-1.5 py-0.5 rounded bg-slate-800 text-amber-400 border border-slate-700">
              {targetProjectId}
            </span>
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5 font-medium">
            {targetJurisdiction} · {targetRegulatoryArea}
          </div>
        </div>
      </div>

      {/* 2. MODE NAVIGATION TABS */}
      <div className="flex items-center justify-between border-b border-slate-800">
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setActiveTabMode('query')}
            className={`px-5 py-3 text-xs sm:text-sm font-bold flex items-center gap-2 border-b-2 transition-colors cursor-pointer ${
              activeTabMode === 'query'
                ? 'border-amber-500 text-amber-400 bg-amber-500/5'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Search className="w-4 h-4" />
            <span>Regulatory Query Workspace</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTabMode('compare')}
            className={`px-5 py-3 text-xs sm:text-sm font-bold flex items-center gap-2 border-b-2 transition-colors cursor-pointer ${
              activeTabMode === 'compare'
                ? 'border-amber-500 text-amber-400 bg-amber-500/5'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <GitCompare className="w-4 h-4" />
            <span>Advisor Advice Comparison</span>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/20 font-mono">
              Compare
            </span>
          </button>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* VIEW 1: REGULATORY QUERY WORKSPACE (POST /api/v1/query)                    */}
      {/* ========================================================================= */}
      {activeTabMode === 'query' && (
        <div className="space-y-6">
          {/* QUERY INPUT PANEL */}
          <div className="rounded-2xl border border-slate-800/90 bg-[#161619] p-6 sm:p-7 shadow-xl space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h2 className="text-base sm:text-lg font-bold text-white flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-amber-400" />
                  <span>Submit Regulatory Query</span>
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Query supervisory rulebooks, statutory obligations, and tenant policy documents.
                </p>
              </div>

              {/* Tenant Scope vs Public Corpus Toggle */}
              <div className="flex items-center gap-2 bg-[#121214] border border-slate-800 rounded-lg p-1 text-xs font-semibold">
                <button
                  type="button"
                  onClick={() => setUseTenantScope(false)}
                  className={`px-3 py-1.5 rounded-md transition-colors cursor-pointer ${
                    !useTenantScope
                      ? 'bg-amber-500/20 text-amber-300 font-bold border border-amber-500/30'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                  title="Query the general public regulatory corpus (FCA, MLR, JMLSG)"
                >
                  Public Regulatory Corpus
                </button>
                <button
                  type="button"
                  onClick={() => setUseTenantScope(true)}
                  className={`px-3 py-1.5 rounded-md transition-colors cursor-pointer ${
                    useTenantScope
                      ? 'bg-amber-500/20 text-amber-300 font-bold border border-amber-500/30'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                  title={`Scope strictly to active tenant project ${targetProjectId}`}
                >
                  Tenant Project ({targetProjectId})
                </button>
              </div>
            </div>

            <form onSubmit={handleQuerySubmit} className="space-y-3">
              <div className="relative">
                <textarea
                  rows={3}
                  value={queryInput}
                  onChange={(e) => setQueryInput(e.target.value)}
                  placeholder="Ask an exact compliance, KYC, AML, or supervisory obligation question..."
                  className="w-full bg-[#121214] border border-slate-800 rounded-xl p-4 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500/60 focus:ring-2 focus:ring-amber-500/10 transition-all resize-y leading-relaxed"
                />
              </div>

              {/* Quick Prompts */}
              <div className="flex flex-wrap items-center gap-2 text-xs">
                <span className="text-slate-500 font-mono text-[11px] font-bold">SUGGESTED:</span>
                {[
                  'CDD verification timelines under MLR 2017',
                  'Enhanced Due Diligence for PEPs under Regulation 33',
                  'FCA SYSC 6.1 financial crime systems & controls',
                ].map((sample) => (
                  <button
                    key={sample}
                    type="button"
                    onClick={() => {
                      setQueryInput(sample);
                    }}
                    className="px-2.5 py-1 rounded-md border border-slate-800 bg-[#121214] hover:bg-slate-800 text-slate-300 hover:text-white transition-colors cursor-pointer text-[11px]"
                  >
                    "{sample}"
                  </button>
                ))}
              </div>

              {/* Submit Action */}
              <div className="flex items-center justify-between pt-2">
                <div className="text-[11px] text-slate-500 font-mono">
                  {useTenantScope ? (
                    <span>Scoping query to tenant ID: <strong className="text-amber-400">{targetProjectId}</strong></span>
                  ) : (
                    <span>Scoping query to: <strong className="text-emerald-400">Public Regulatory Knowledge Base</strong></span>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={isQuerying || !queryInput.trim()}
                  className="px-6 py-2.5 rounded-xl bg-[#e6a13d] hover:bg-[#d8932f] disabled:opacity-50 text-slate-950 font-bold text-xs sm:text-sm flex items-center gap-2 shadow-md cursor-pointer transition-colors"
                >
                  {isQuerying ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Retrieving Evidence...</span>
                    </>
                  ) : (
                    <>
                      <span>Query Evidence Corpus</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>

          {/* QUERY ERROR NOTIFICATION */}
          {queryError && (
            <div className="rounded-xl border border-rose-900/80 bg-rose-950/30 p-4 text-xs sm:text-sm text-rose-300 flex items-start gap-3">
              <ShieldAlert className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-bold">Query Execution Warning</p>
                <p className="mt-0.5 opacity-90">{queryError}</p>
              </div>
            </div>
          )}

          {/* QUERY RESULTS WORKSPACE */}
          {queryResult && (
            <div className="space-y-6">
              {/* RESULT STATUS & METRICS ROW */}
              <div className="rounded-2xl border border-slate-800/90 bg-[#161619] p-6 shadow-xl space-y-5">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
                  <div className="flex items-center gap-3 flex-wrap">
                    <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400 font-bold">
                      RESULT STATUS:
                    </span>

                    {/* STATUS BADGE - Strictly according to Section 6 Dictionary */}
                    {queryResult.status === 'GROUNDED' && queryResult.grounded && (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border border-emerald-800/80 bg-emerald-950/60 text-emerald-400">
                        <span className="w-2 h-2 rounded-full bg-emerald-400" />
                        <span>Evidence retrieved (GROUNDED)</span>
                      </span>
                    )}

                    {queryResult.status === 'INSUFFICIENT_EVIDENCE' && (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border border-amber-800/80 bg-amber-950/60 text-amber-300">
                        <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                        <span>Insufficient evidence</span>
                      </span>
                    )}

                    {queryResult.status === 'OUT_OF_SCOPE' && (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border border-slate-700 bg-slate-800 text-slate-300">
                        <HelpCircle className="w-3.5 h-3.5 text-slate-400" />
                        <span>Outside current knowledge-base scope</span>
                      </span>
                    )}

                    {queryResult.status === 'UNAPPROVED_EVIDENCE' && (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border border-amber-800 bg-amber-950 text-amber-400">
                        <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                        <span>Evidence pending approval</span>
                      </span>
                    )}
                  </div>

                  {/* Request ID Traceability */}
                  {queryResult.request_id && (
                    <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
                      <span>TRACE ID:</span>
                      <span className="px-2 py-0.5 rounded bg-[#121214] border border-slate-800 text-slate-200">
                        {queryResult.request_id}
                      </span>
                      <button
                        type="button"
                        onClick={() => handleCopy(queryResult.request_id, 'trace_id')}
                        className="text-slate-500 hover:text-slate-300 p-1 cursor-pointer"
                        title="Copy Request ID"
                      >
                        {copiedId === 'trace_id' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                  )}
                </div>

                {/* 4 SUMMARY STATS (Section 3: Evidence summary) */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-4 rounded-xl border border-slate-800 bg-[#121214]">
                    <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                      RETRIEVED CHUNKS
                    </div>
                    <div className="text-2xl font-extrabold text-white mt-1">
                      {String(queryResult.metadata?.retrieved_count || queryResult.retrieved_evidence?.length || 0).padStart(2, '0')}
                    </div>
                    <div className="text-[11px] text-slate-500 mt-0.5">Top-k semantic matches</div>
                  </div>

                  <div className="p-4 rounded-xl border border-slate-800 bg-[#121214]">
                    <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                      OFFICIAL CITATIONS
                    </div>
                    <div className="text-2xl font-extrabold text-white mt-1">
                      {String(queryResult.metadata?.citation_count || queryResult.citations?.length || 0).padStart(2, '0')}
                    </div>
                    <div className="text-[11px] text-slate-500 mt-0.5">Primary regulatory sources</div>
                  </div>

                  <div className="p-4 rounded-xl border border-slate-800 bg-[#121214]">
                    <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                      RELATIONSHIPS / OVERLAPS
                    </div>
                    <div className="text-2xl font-extrabold text-amber-400 mt-1">
                      {String(queryResult.metadata?.conflict_count || queryResult.conflicts?.length || 0).padStart(2, '0')}
                    </div>
                    <div className="text-[11px] text-slate-500 mt-0.5">Cross-rule analysis</div>
                  </div>

                  <div className="p-4 rounded-xl border border-slate-800 bg-[#121214]">
                    <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                      APPROVED EVIDENCE
                    </div>
                    <div className="text-2xl font-extrabold text-amber-400 mt-1">
                      {String(queryResult.metadata?.approved_evidence_count || 0).padStart(2, '0')}
                    </div>
                    <div className="text-[11px] text-amber-400/80 mt-0.5">Pending SME validation</div>
                  </div>
                </div>

                {/* PROMINENT MANDATORY HUMAN REVIEW WARNING (Section 3 & 6) */}
                {queryResult.metadata?.requires_human_review && (
                  <div className="rounded-xl border border-amber-900/80 bg-amber-950/30 p-4 text-xs sm:text-sm text-amber-200 flex items-start gap-3 shadow-sm">
                    <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
                    <div className="space-y-1">
                      <p className="font-bold text-amber-300">
                        Human Review Required · Retrieved Evidence Pending SME Sign-Off
                      </p>
                      <p className="text-xs text-amber-200/90 leading-relaxed font-normal">
                        AI retrieval identifies factual regulatory excerpts and semantic similarity. Per platform governance, evidence is not certified as formal legal advice or binding supervisory approval until reviewed by an authorised Compliance Officer.
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* MAIN SYNTHESIZED ANSWER OR EVIDENCE GAP PANEL */}
              {queryResult.answer ? (
                <div className="rounded-2xl border border-slate-800/90 bg-[#161619] p-6 sm:p-7 shadow-xl space-y-3">
                  <div className="text-[11px] font-mono uppercase tracking-wider text-amber-400 font-bold">
                    SYNTHESIZED REGULATORY ANSWER
                  </div>
                  <div className="text-sm sm:text-base text-slate-100 font-medium leading-relaxed bg-[#121214] p-5 rounded-xl border border-slate-800">
                    {queryResult.answer}
                  </div>
                </div>
              ) : queryResult.gap ? (
                <div className="rounded-2xl border border-amber-900/60 bg-amber-950/20 p-6 sm:p-7 shadow-xl space-y-4">
                  <div className="flex items-center gap-2 text-amber-400 text-xs font-mono font-bold tracking-wider uppercase">
                    <AlertTriangle className="w-4 h-4" />
                    <span>Evidence Gap Identified ({queryResult.gap.gap_type || 'GAP_DETECTED'})</span>
                  </div>

                  <div className="text-sm text-slate-200 leading-relaxed font-medium">
                    {queryResult.gap.user_safe_message || queryResult.gap.message}
                  </div>

                  {queryResult.gap.recommended_next_action && (
                    <div className="p-4 rounded-xl border border-amber-900/50 bg-[#121214] text-xs space-y-1">
                      <span className="text-[10px] font-mono font-bold text-amber-400 uppercase tracking-wider block">
                        RECOMMENDED NEXT ACTION:
                      </span>
                      <p className="text-slate-300 font-normal">
                        {queryResult.gap.recommended_next_action}
                      </p>
                    </div>
                  )}

                  {onNavigateTab && (
                    <div className="pt-2">
                      <button
                        type="button"
                        onClick={() => onNavigateTab('Project Details')}
                        className="px-4 py-2 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 text-xs font-bold border border-amber-500/40 cursor-pointer transition-colors"
                      >
                        Navigate to Project Documents &rarr;
                      </button>
                    </div>
                  )}
                </div>
              ) : null}

              {/* DETAILED EVIDENCE TABS (Section 3: Retrieved evidence, Citations, Provenance, Conflicts, Gaps) */}
              <div className="rounded-2xl border border-slate-800/90 bg-[#161619] shadow-xl overflow-hidden">
                {/* Tab Header */}
                <div className="flex flex-wrap border-b border-slate-800 bg-[#121214] px-4 pt-2">
                  {[
                    { id: 'evidence', label: 'Retrieved Evidence', count: queryResult.retrieved_evidence?.length },
                    { id: 'citations', label: 'Citations', count: queryResult.citations?.length },
                    { id: 'provenance', label: 'Provenance Table', count: queryResult.provenance?.length },
                    { id: 'conflicts', label: 'Conflicts & Overlaps', count: queryResult.conflicts?.length },
                    { id: 'gaps', label: 'Evidence Gaps', count: queryResult.gap ? 1 : 0 },
                  ].map((subTab) => (
                    <button
                      key={subTab.id}
                      type="button"
                      onClick={() => setEvidenceActiveSubTab(subTab.id)}
                      className={`px-4 py-3 text-xs sm:text-sm font-bold border-b-2 flex items-center gap-2 transition-colors cursor-pointer ${
                        evidenceActiveSubTab === subTab.id
                          ? 'border-amber-500 text-amber-400 bg-[#161619]'
                          : 'border-transparent text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      <span>{subTab.label}</span>
                      {subTab.count !== undefined && (
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                          {subTab.count}
                        </span>
                      )}
                    </button>
                  ))}
                </div>

                <div className="p-6">
                  {/* TAB 1: RETRIEVED EVIDENCE CARDS (Section 7: Recommended evidence card) */}
                  {evidenceActiveSubTab === 'evidence' && (
                    <div className="space-y-4">
                      {(!queryResult.retrieved_evidence || queryResult.retrieved_evidence.length === 0) ? (
                        <div className="text-center py-8 text-slate-500 text-sm">
                          No evidence chunks retrieved for this query.
                        </div>
                      ) : (
                        queryResult.retrieved_evidence.map((chunk, idx) => (
                          <div
                            key={chunk.chunk_id || idx}
                            className="rounded-xl border border-slate-800 bg-[#121214] p-5 space-y-4 hover:border-slate-700 transition-colors"
                          >
                            {/* Header: Regulation Name & Article */}
                            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
                              <div>
                                <span className="text-sm sm:text-base font-extrabold text-white">
                                  {chunk.regulation} · {chunk.section_article}
                                </span>
                                <div className="text-xs text-slate-400 mt-0.5 font-medium">
                                  {chunk.title} {chunk.regulator && `(${chunk.regulator})`} · {chunk.jurisdiction || 'United Kingdom'}
                                </div>
                              </div>

                              {/* Approval Status Badge (Section 6: is_approved_for_rag rule) */}
                              <div>
                                {chunk.is_approved_for_rag ? (
                                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border border-emerald-800/80 bg-emerald-950/60 text-emerald-400">
                                    <CheckCircle2 className="w-3.5 h-3.5" />
                                    <span>Approved for RAG</span>
                                  </span>
                                ) : (
                                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border border-amber-800/80 bg-amber-950/40 text-amber-300">
                                    <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                                    <span>Pending SME validation – not approved for RAG</span>
                                  </span>
                                )}
                              </div>
                            </div>

                            {/* Excerpt Text */}
                            <div className="p-4 rounded-lg bg-[#0c0e12] border border-slate-800/80 text-xs sm:text-sm text-slate-200 leading-relaxed font-mono">
                              "{chunk.text}"
                            </div>

                            {/* Metadata & Traceability Row */}
                            <div className="flex flex-wrap items-center justify-between gap-3 text-xs pt-1">
                              <div className="flex items-center gap-3 flex-wrap">
                                {/* Similarity Score Rule: Retrieval relevance signal, not legal confidence! */}
                                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-900 border border-slate-800 font-mono text-slate-300">
                                  <span>Retrieval Similarity:</span>
                                  <strong className="text-amber-400">{chunk.similarity_score}</strong>
                                </span>

                                <span className="font-mono text-slate-400 text-[11px]">
                                  CHUNK: <strong>{chunk.chunk_id}</strong>
                                </span>

                                <span className="font-mono text-slate-400 text-[11px]">
                                  SOURCE: <strong>{chunk.source_id}</strong>
                                </span>
                              </div>

                              {/* Official Legal Source Link */}
                              {chunk.official_source && (
                                <a
                                  href={chunk.official_source}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-flex items-center gap-1.5 text-xs text-amber-400 hover:text-amber-300 font-semibold transition-colors"
                                >
                                  <span>Official Legal Source</span>
                                  <ExternalLink className="w-3.5 h-3.5" />
                                </a>
                              )}
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  )}

                  {/* TAB 2: CITATIONS */}
                  {evidenceActiveSubTab === 'citations' && (
                    <div className="space-y-3">
                      {(!queryResult.citations || queryResult.citations.length === 0) ? (
                        <div className="text-center py-8 text-slate-500 text-sm">
                          No citations generated.
                        </div>
                      ) : (
                        queryResult.citations.map((cit, idx) => (
                          <div
                            key={cit.citation_id || idx}
                            className="rounded-xl border border-slate-800 bg-[#121214] p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                          >
                            <div className="space-y-1">
                              <div className="text-sm font-bold text-white">
                                {cit.formatted_citation}
                              </div>
                              <div className="text-xs text-slate-400">
                                {cit.regulator} · {cit.jurisdiction} · {cit.version_date || 'Current'}
                              </div>
                            </div>

                            <div className="flex items-center gap-3 shrink-0">
                              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-amber-950/40 border border-amber-800/60 text-amber-300">
                                {cit.is_approved_for_rag ? 'Approved' : 'Pending SME Review'}
                              </span>

                              {cit.official_source && (
                                <a
                                  href={cit.official_source}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-colors"
                                >
                                  <span>View Source</span>
                                  <ExternalLink className="w-3 h-3" />
                                </a>
                              )}
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  )}

                  {/* TAB 3: PROVENANCE TABLE */}
                  {evidenceActiveSubTab === 'provenance' && (
                    <div className="overflow-x-auto rounded-xl border border-slate-800 bg-[#121214]">
                      <table className="w-full text-left text-xs border-collapse min-w-[700px]">
                        <thead>
                          <tr className="border-b border-slate-800 bg-slate-900/60 text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">
                            <th className="py-3 px-4">RECORD ID</th>
                            <th className="py-3 px-4">CHUNK ID</th>
                            <th className="py-3 px-4">REGULATION / SECTION</th>
                            <th className="py-3 px-4">REGULATOR</th>
                            <th className="py-3 px-4">SIMILARITY</th>
                            <th className="py-3 px-4">GOVERNANCE</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/60 font-medium">
                          {(!queryResult.provenance || queryResult.provenance.length === 0) ? (
                            <tr>
                              <td colSpan={6} className="py-8 text-center text-slate-500">
                                No provenance lineage recorded.
                              </td>
                            </tr>
                          ) : (
                            queryResult.provenance.map((p, idx) => (
                              <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                                <td className="py-3 px-4 font-mono text-amber-400">{p.record_id}</td>
                                <td className="py-3 px-4 font-mono text-slate-300">{p.chunk_id}</td>
                                <td className="py-3 px-4 text-white font-semibold">
                                  {p.regulation} ({p.section_article})
                                </td>
                                <td className="py-3 px-4 text-slate-400">{p.regulator}</td>
                                <td className="py-3 px-4 font-mono text-amber-400 font-bold">{p.similarity_score}</td>
                                <td className="py-3 px-4">
                                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950/40 text-amber-300 border border-amber-800/50">
                                    {p.validation_status || 'VALIDATED'}
                                  </span>
                                </td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {/* TAB 4: CONFLICTS & RELATIONSHIPS */}
                  {evidenceActiveSubTab === 'conflicts' && (
                    <div className="space-y-4">
                      {(!queryResult.conflicts || queryResult.conflicts.length === 0) ? (
                        <div className="text-center py-8 text-slate-500 text-sm">
                          No regulatory conflicts or overlaps identified for this query.
                        </div>
                      ) : (
                        queryResult.conflicts.map((conf, idx) => (
                          <div
                            key={conf.conflict_id || idx}
                            className="rounded-xl border border-slate-800 bg-[#121214] p-5 space-y-3"
                          >
                            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
                              <div className="flex items-center gap-2">
                                <span className="font-mono text-xs font-bold text-amber-400">{conf.conflict_id}</span>
                                <span className="text-slate-500">·</span>
                                <span className="text-sm font-bold text-white">{conf.topic}</span>
                              </div>

                              <div>
                                {conf.conflict_type === 'OVERLAP' ? (
                                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold border border-blue-800/80 bg-blue-950/40 text-blue-300">
                                    <span>Complementary Overlap (OVERLAP)</span>
                                  </span>
                                ) : (
                                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold border border-rose-800/80 bg-rose-950/40 text-rose-300">
                                    <span>Potential Contradiction</span>
                                  </span>
                                )}
                              </div>
                            </div>

                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
                              <div className="p-3 rounded bg-slate-900 border border-slate-800">
                                <span className="text-slate-400 font-bold block mb-1">SOURCE 1:</span>
                                <span className="text-white font-semibold">{conf.source_1}</span>
                              </div>
                              <div className="p-3 rounded bg-slate-900 border border-slate-800">
                                <span className="text-slate-400 font-bold block mb-1">SOURCE 2:</span>
                                <span className="text-white font-semibold">{conf.source_2}</span>
                              </div>
                            </div>

                            <div className="text-xs text-slate-300 leading-relaxed pt-1">
                              {conf.requirement_comparison}
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  )}

                  {/* TAB 5: EVIDENCE GAPS */}
                  {evidenceActiveSubTab === 'gaps' && (
                    <div>
                      {queryResult.gap ? (
                        <div className="rounded-xl border border-amber-900/60 bg-[#121214] p-5 space-y-3">
                          <div className="flex items-center gap-2 text-amber-400 text-xs font-bold font-mono">
                            <AlertTriangle className="w-4 h-4" />
                            <span>GAP TYPE: {queryResult.gap.gap_type}</span>
                          </div>
                          <p className="text-sm text-slate-200">{queryResult.gap.message}</p>
                          <div className="text-xs text-slate-400 font-mono">
                            NATURE: {queryResult.gap.coverage_nature || 'PARTIAL'}
                          </div>
                          {queryResult.gap.recommended_next_action && (
                            <div className="p-3 rounded bg-amber-950/20 border border-amber-900/50 text-xs text-amber-200">
                              <strong>Recommended Action:</strong> {queryResult.gap.recommended_next_action}
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="text-center py-8 text-slate-500 text-sm">
                          No evidence gaps detected. All query concepts mapped to indexed regulatory chunks.
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* VIEW 2: ADVISOR ADVICE COMPARISON WORKSPACE (POST /api/v1/compare)         */}
      {/* ========================================================================= */}
      {activeTabMode === 'compare' && (
        <div className="space-y-6">
          {/* COMPARISON HEADER BAR */}
          <div className="rounded-2xl border border-slate-800/90 bg-[#161619] p-6 shadow-xl space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
              <div>
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <GitCompare className="w-5 h-5 text-amber-400" />
                  <span>Advisor Position Comparative Analysis</span>
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Automated conflict detection and statutory relationship mapping between independent advisory opinions.
                </p>
              </div>

              {compareResult?.comparison_id && (
                <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
                  <span>COMPARISON ID:</span>
                  <span className="px-2 py-0.5 rounded bg-[#121214] border border-slate-800 text-amber-400 font-bold">
                    {compareResult.comparison_id}
                  </span>
                  <button
                    type="button"
                    onClick={() => handleCopy(compareResult.comparison_id, 'compare_id')}
                    className="text-slate-500 hover:text-slate-300 p-1 cursor-pointer"
                    title="Copy Comparison ID"
                  >
                    {copiedId === 'compare_id' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              )}
            </div>

            {/* Topic & Compare Trigger */}
            <div className="flex flex-col sm:flex-row items-center gap-3">
              <div className="flex-1 w-full">
                <label className="block text-[11px] font-mono uppercase tracking-wider text-slate-400 font-bold mb-1.5">
                  COMPARATIVE REGULATORY TOPIC
                </label>
                <input
                  type="text"
                  value={compareTopic}
                  onChange={(e) => setCompareTopic(e.target.value)}
                  className="w-full bg-[#121214] border border-slate-800 rounded-xl px-4 py-2.5 text-xs sm:text-sm text-slate-100 focus:outline-none focus:border-amber-500/60"
                />
              </div>

              <div className="shrink-0 pt-5">
                <button
                  type="button"
                  onClick={handleCompareSubmit}
                  disabled={isComparing}
                  className="px-6 py-2.5 rounded-xl bg-[#e6a13d] hover:bg-[#d8932f] text-slate-950 font-bold text-xs sm:text-sm flex items-center gap-2 shadow-md cursor-pointer transition-colors"
                >
                  {isComparing ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Comparing Positions...</span>
                    </>
                  ) : (
                    <>
                      <span>Re-Run Comparison</span>
                      <RefreshCw className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* COMPARISON RESULTS WORKSPACE */}
          {compareResult && (
            <div className="space-y-6">
              {/* SIDE-BY-SIDE ADVISOR PANELS (Section 5) */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Advisor 1 Panel */}
                <div className="rounded-2xl border border-slate-800 bg-[#161619] p-6 space-y-4 shadow-xl">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                    <div>
                      <span className="text-[10px] font-mono text-amber-400 uppercase tracking-wider font-bold">
                        ADVISOR 1 · {compareResult.advisor_1?.advice_id}
                      </span>
                      <h3 className="text-base font-bold text-white mt-0.5">
                        {compareResult.advisor_1?.advisor_name}
                      </h3>
                      <p className="text-xs text-slate-400">
                        {compareResult.advisor_1?.firm} ({compareResult.advisor_1?.domain})
                      </p>
                    </div>
                    <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                      {compareResult.advisor_1?.source_ref}
                    </span>
                  </div>

                  <div className="p-4 rounded-xl bg-[#121214] border border-slate-800 text-xs sm:text-sm text-slate-200 leading-relaxed font-normal">
                    "{compareResult.advisor_1?.advice_text}"
                  </div>
                </div>

                {/* Advisor 2 Panel */}
                <div className="rounded-2xl border border-slate-800 bg-[#161619] p-6 space-y-4 shadow-xl">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                    <div>
                      <span className="text-[10px] font-mono text-amber-400 uppercase tracking-wider font-bold">
                        ADVISOR 2 · {compareResult.advisor_2?.advice_id}
                      </span>
                      <h3 className="text-base font-bold text-white mt-0.5">
                        {compareResult.advisor_2?.advisor_name}
                      </h3>
                      <p className="text-xs text-slate-400">
                        {compareResult.advisor_2?.firm} ({compareResult.advisor_2?.domain})
                      </p>
                    </div>
                    <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                      {compareResult.advisor_2?.source_ref}
                    </span>
                  </div>

                  <div className="p-4 rounded-xl bg-[#121214] border border-slate-800 text-xs sm:text-sm text-slate-200 leading-relaxed font-normal">
                    "{compareResult.advisor_2?.advice_text}"
                  </div>
                </div>
              </div>

              {/* DIFFERENCES & CONTRADICTIONS ANALYSIS (Section 5 & 6) */}
              <div className="rounded-2xl border border-slate-800/90 bg-[#161619] p-6 sm:p-7 shadow-xl space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                    <Scale className="w-4 h-4 text-amber-400" />
                    <span>Factual Difference Analysis</span>
                  </h3>

                  <div>
                    {compareResult.differences?.[0]?.is_contradiction ? (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border border-rose-800/80 bg-rose-950/40 text-rose-300">
                        <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                        <span>Potential contradiction identified</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border border-blue-800/80 bg-blue-950/40 text-blue-300">
                        <Info className="w-3.5 h-3.5 text-blue-400" />
                        <span>Substantive Difference (No Contradiction)</span>
                      </span>
                    )}
                  </div>
                </div>

                {compareResult.differences?.map((diff, idx) => (
                  <div key={idx} className="space-y-4">
                    <p className="text-xs sm:text-sm text-slate-200 leading-relaxed font-medium bg-[#121214] p-4 rounded-xl border border-slate-800">
                      {diff.summary}
                    </p>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
                      <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800">
                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                          ADVISOR 1 POSITION:
                        </span>
                        <span className="text-slate-200 font-medium">{diff.advisor_1_position}</span>
                      </div>

                      <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800">
                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                          ADVISOR 2 POSITION:
                        </span>
                        <span className="text-slate-200 font-medium">{diff.advisor_2_position}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* STATUTORY RELATIONSHIPS & SUPPORTING EVIDENCE */}
              <div className="rounded-2xl border border-slate-800/90 bg-[#161619] p-6 sm:p-7 shadow-xl space-y-4">
                <h3 className="text-base font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
                  <Layers className="w-4 h-4 text-amber-400" />
                  <span>Regulatory Relationship &amp; Supporting Corpus Chunks</span>
                </h3>

                {compareResult.relationships?.map((rel, idx) => (
                  <div key={idx} className="p-4 rounded-xl bg-[#121214] border border-slate-800 space-y-2 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-mono font-bold text-amber-400">{rel.conflict_id}</span>
                      <span className="px-2 py-0.5 rounded bg-blue-950/60 border border-blue-800/60 text-blue-300 font-mono font-bold">
                        {rel.conflict_type === 'OVERLAP' ? 'Complementary overlap' : rel.conflict_type}
                      </span>
                    </div>
                    <p className="text-slate-300 font-medium leading-relaxed">{rel.requirement_comparison}</p>
                  </div>
                ))}

                {/* Per-Advisor Supporting Evidence */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                  {compareResult.supporting_evidence?.map((supp, idx) => (
                    <div key={idx} className="p-4 rounded-xl bg-[#121214] border border-slate-800 space-y-2 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-mono font-bold text-white">ADVISOR {supp.advisor_id}</span>
                        <span className="px-2 py-0.5 rounded bg-emerald-950/40 border border-emerald-800/60 text-emerald-300 font-mono">
                          {supp.evidence_status}
                        </span>
                      </div>
                      <p className="text-slate-400">{supp.notes}</p>
                      <div className="text-[11px] font-mono text-slate-500">
                        CHUNKS: {supp.chunk_ids?.join(', ')}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* STRICT RULE FROM PADMA: NO AUTOMATED DECISION (decision = null) */}
              <div className="rounded-2xl border border-slate-800 bg-[#141418] p-6 shadow-xl space-y-2">
                <div className="text-[11px] font-mono uppercase tracking-wider text-slate-400 font-bold">
                  AUTOMATED ADJUDICATION STATUS
                </div>

                <div className="flex items-center gap-3">
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border border-slate-700 bg-slate-800 text-slate-200">
                    <Scale className="w-3.5 h-3.5 text-slate-400" />
                    <span>No automated decision</span>
                  </span>

                  <span className="text-xs text-slate-400">
                    The system identifies factual differences and regulatory provenance. It does not select a "winner" or resolve legal interpretations.
                  </span>
                </div>

                {onNavigateTab && (
                  <div className="pt-3">
                    <button
                      type="button"
                      onClick={() => onNavigateTab('Advice & Decisions')}
                      className="px-4 py-2 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 text-xs font-bold border border-amber-500/40 cursor-pointer transition-colors"
                    >
                      Record Governance Decision in Advice &amp; Decisions &rarr;
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 3. REVIEW FOOTER & DISCLAIMER (Section 3, 10, & 14) */}
      <div className="rounded-2xl border border-slate-800/80 bg-[#121214] p-5 sm:p-6 text-xs text-slate-400 space-y-2 mt-8">
        <div className="flex items-center gap-2 font-mono font-bold text-amber-400 uppercase tracking-wider">
          <Info className="w-4 h-4 shrink-0" />
          <span>Non-Negotiable Regulatory Governance Rules (Padma Spec)</span>
        </div>
        <p className="text-slate-300 leading-relaxed font-normal">
          <strong>Retrieved does not mean approved.</strong> GROUNDED status indicates text retrieval relevance, not compliance certification. OVERLAP reflects complementary co-application, not normative contradiction. AI comparative output is provided strictly for operational triage; final legal dispositions require human review by an authorised Compliance Officer.
        </p>
        <div className="text-[11px] font-mono text-slate-500 pt-1 border-t border-slate-800/60 flex flex-wrap justify-between gap-2">
          <span>RAG Service: {healthStatus.status} · API Base: {import.meta.env.VITE_RAG_API_URL || 'Configurable'}</span>
          <span>FinRegTech ShipYard AI/RAG Engine v1.0.4</span>
        </div>
      </div>
    </div>
  );
}
