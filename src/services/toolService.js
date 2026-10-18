import { apiCall } from './api';

export const TRUSTED_TOOLS = [
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
];

/**
 * Fetches directory of trusted ecosystem tools from platform catalog
 */
export async function getTools() {
  try {
    const stored = localStorage.getItem('ecosystem_tools');
    if (stored) {
      return JSON.parse(stored);
    }
  } catch (e) {
    // Ignore storage parsing errors
  }
  return TRUSTED_TOOLS;
}

/**
 * Toggles or updates tool usage status
 */
export async function toggleToolUsage(toolId, isUsed = true) {
  try {
    const tools = await getTools();
    const updated = tools.map((t) => (t.id === toolId ? { ...t, isUsed } : t));
    localStorage.setItem('ecosystem_tools', JSON.stringify(updated));
    return { success: true, toolId, isUsed };
  } catch (err) {
    console.error(`[toolService] toggleToolUsage failed:`, err);
    return { success: false, toolId, isUsed };
  }
}
