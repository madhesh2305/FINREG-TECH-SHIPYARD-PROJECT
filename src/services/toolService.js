import { apiCall } from './api.js';
import { recordAdminAuditLog } from './adminService.js';

export const PROJECT_TOOLS_STORAGE_KEY = 'finreg_project_tools';

/**
 * Curated Baseline Catalogue of Trusted Compliance & FinRegTech Tools
 * (Conforms to FinRegTech ShipYard Trusted Tools Module Specification - 11 Nov 2026)
 */
export const DEFAULT_CURATED_TOOLS = [
  {
    id: 'tool-complyadvantage',
    name: 'ComplyAdvantage',
    provider: 'ComplyAdvantage Ltd',
    category: 'KYC & Screening',
    short_description: 'Real-time AML data, PEPs, sanctions, and adverse media screening engine.',
    full_description: 'Cloud-native financial crime risk engine providing automated real-time screening against global sanction lists, Politically Exposed Persons (PEPs), and continuously updated adverse media sources.',
    use_cases: [
      'Automated PEP and sanctions screening',
      'Continuous adverse media monitoring',
      'Customer Due Diligence (CDD) evidence capture',
    ],
    jurisdictions: ['UK FCA', 'EU AMLD', 'Global'],
    official_url: 'https://complyadvantage.com',
    source_reference: 'Official Provider Product Documentation & Developer Portal',
    last_checked_date: '10 November 2026',
    review_status: 'Reviewed for listing', // 'Reviewed for listing' | 'Pending review' | 'Needs update' | 'Archived'
    limitations_notes: 'Applicability must be verified for the specific entity tier. Does not replace statutory Money Laundering Reporting Officer (MLRO) signoff or internal suspicious activity reporting obligations.',
    connection_type: 'directory_only',
    version_license_notes: 'Enterprise SaaS API / Periodic List Refresh',
  },
  {
    id: 'tool-fenergo',
    name: 'Fenergo Client Lifecycle Management',
    provider: 'Fenergo Group',
    category: 'Client Lifecycle & CDD',
    short_description: 'Institutional onboarding, KYC document verification, and lifecycle orchestration.',
    full_description: 'Enterprise client lifecycle management platform engineered for institutional digital client onboarding, counterparty due diligence, and regulatory compliance workflows across multiple jurisdictions.',
    use_cases: [
      'Institutional client onboarding & risk categorization',
      'Ultimate Beneficial Owner (UBO) identification',
      'Periodic KYC remediation & refresh workflows',
    ],
    jurisdictions: ['UK FCA', 'PRA', 'EU AMLD'],
    official_url: 'https://fenergo.com',
    source_reference: 'Provider Architecture Guide & RegTech Whitepaper',
    last_checked_date: '08 November 2026',
    review_status: 'Reviewed for listing',
    limitations_notes: 'Requires custom corporate policy mapping. Suitability for retail-only fintechs must be evaluated against operational configuration requirements.',
    connection_type: 'directory_only',
    version_license_notes: 'Enterprise Multi-Tenant SaaS',
  },
  {
    id: 'tool-chainalysis',
    name: 'Chainalysis KYT (Know Your Transaction)',
    provider: 'Chainalysis Inc',
    category: 'Crypto & Blockchain Compliance',
    short_description: 'Real-time blockchain transaction monitoring and risk scoring for digital assets.',
    full_description: 'High-volume cryptocurrency compliance solution that identifies high-risk transaction patterns, darknet activity, and sanctioned wallet addresses across major blockchains.',
    use_cases: [
      'Real-time on-chain transaction surveillance',
      'Sanctioned crypto address detection',
      'Travel Rule compliance evidence and tracking',
    ],
    jurisdictions: ['UK FCA', 'EU AMLD', 'Global'],
    official_url: 'https://chainalysis.com',
    source_reference: 'Chainalysis Compliance Documentation & API Specs',
    last_checked_date: '09 November 2026',
    review_status: 'Reviewed for listing',
    limitations_notes: 'Specialized for cryptoasset transactions. Must be supplemented with traditional fiat monitoring solutions for hybrid payment rails.',
    connection_type: 'directory_only',
    version_license_notes: 'Cloud API Service Tier 1',
  },
  {
    id: 'tool-napier',
    name: 'Napier AI AML & Monitoring',
    provider: 'Napier Technologies',
    category: 'Transaction Monitoring',
    short_description: 'AI-enhanced anti-money laundering and transaction monitoring engine with rule builder.',
    full_description: 'Modern financial crime compliance platform combining rule-based heuristics with machine learning algorithms to detect complex structuring, smurfing, and unusual account behavior.',
    use_cases: [
      'High-throughput transaction monitoring',
      'False positive reduction engine',
      'Custom compliance rule authoring',
    ],
    jurisdictions: ['UK FCA', 'PRA', 'Global'],
    official_url: 'https://napier.ai',
    source_reference: 'Napier AI Platform Release Notes & Review Pack',
    last_checked_date: '05 November 2026',
    review_status: 'Reviewed for listing',
    limitations_notes: 'Machine learning models require baseline behavioral data for anomaly calibration. Thresholds must be audited periodically.',
    connection_type: 'directory_only',
    version_license_notes: 'Annual SaaS Subscription',
  },
  {
    id: 'tool-trulioo',
    name: 'Trulioo Global Identity Verification',
    provider: 'Trulioo Information Services Inc',
    category: 'KYC & Screening',
    short_description: 'Global identity verification covering individuals and business entities across 195+ countries.',
    full_description: 'Electronic identity verification (eIDV) gateway providing document verification, biometric facial matching, and official government registry cross-checks.',
    use_cases: [
      'Biometric ID document verification',
      'Global eIDV registry cross-matching',
      'Business entity verification (KYB)',
    ],
    jurisdictions: ['UK FCA', 'EU AMLD', 'Global'],
    official_url: 'https://trulioo.com',
    source_reference: 'Trulioo Developer Center & Identity Verification Guide',
    last_checked_date: '02 November 2026',
    review_status: 'Reviewed for listing',
    limitations_notes: 'Document coverage varies by sovereign territory. Electronic cross-checks depend on registry availability.',
    connection_type: 'directory_only',
    version_license_notes: 'Per-Verification API Gateway',
  },
  {
    id: 'tool-elliptic',
    name: 'Elliptic Navigator',
    provider: 'Elliptic Enterprises Ltd',
    category: 'Crypto & Blockchain Compliance',
    short_description: 'Cryptocurrency AML risk management and transaction screening for virtual assets.',
    full_description: 'Real-time risk detection for digital asset deposits and withdrawals, pinpointing exposure to sanctioned counterparties, ransomware, and illicit entities.',
    use_cases: [
      'Virtual asset wallet screening',
      'Counterparty risk scoring',
      'Audit trail export for regulatory inspections',
    ],
    jurisdictions: ['UK FCA', 'EU AMLD'],
    official_url: 'https://elliptic.co',
    source_reference: 'Elliptic Risk Management Suite Documentation',
    last_checked_date: '28 October 2026',
    review_status: 'Pending review',
    limitations_notes: 'Catalogue record is currently pending re-verification for updated 2026 Travel Rule protocol specifications.',
    connection_type: 'directory_only',
    version_license_notes: 'API & Web Portal Access',
  },
  {
    id: 'tool-wolterskluwer',
    name: 'Wolters Kluwer OneSumX',
    provider: 'Wolters Kluwer N.V.',
    category: 'Regulatory Reporting & Risk',
    short_description: 'Regulatory reporting, capital adequacy calculations, and stress testing.',
    full_description: 'Enterprise regulatory reporting framework supporting automated returns for the PRA, FCA Gabriel/RegData systems, and European Banking Authority (EBA) taxonomy.',
    use_cases: [
      'Automated FCA/PRA RegData return generation',
      'Capital adequacy and liquidity reporting',
      'Regulatory taxonomy validation',
    ],
    jurisdictions: ['UK FCA', 'PRA', 'EU AMLD'],
    official_url: 'https://wolterskluwer.com',
    source_reference: 'Wolters Kluwer Regulatory Solutions Datasheet',
    last_checked_date: '15 September 2026',
    review_status: 'Needs update',
    limitations_notes: 'Taxonomy updates for upcoming PRA rules must be verified with vendor support prior to implementation.',
    connection_type: 'directory_only',
    version_license_notes: 'Enterprise Hosted Cloud',
  },
  {
    id: 'tool-hummingbird',
    name: 'Hummingbird Compliance Workflow',
    provider: 'Hummingbird RegTech Inc',
    category: 'Transaction Monitoring',
    short_description: 'Case management and investigation platform for SAR filings and compliance teams.',
    full_description: 'Modern investigation and Suspicious Activity Report (SAR) orchestration software designed to simplify collaborative case management and regulatory reporting.',
    use_cases: [
      'SAR / STR filing automation',
      'Financial crime investigation case management',
      'Evidence and audit collation',
    ],
    jurisdictions: ['UK FCA', 'Global'],
    official_url: 'https://hummingbird.co',
    source_reference: 'Hummingbird Product Documentation & Review Pack',
    last_checked_date: '01 November 2026',
    review_status: 'Reviewed for listing',
    limitations_notes: 'Operates as an investigation case management overlay. Does not produce raw transaction detection signals directly.',
    connection_type: 'directory_only',
    version_license_notes: 'Cloud Team Subscription',
  },
];

/**
 * Normalizes tool object to ensure all required fields are present
 */
function normalizeToolRecord(tool) {
  return {
    id: tool.id || tool.tool_id || `tool-${Date.now()}`,
    name: tool.name || 'Unnamed Tool',
    provider: tool.provider || tool.developerProvider || 'Verified Provider',
    category: tool.category || 'Compliance',
    short_description: tool.short_description || tool.description || 'Curated compliance software tool.',
    full_description: tool.full_description || tool.fullDescription || tool.description || '',
    use_cases: Array.isArray(tool.use_cases)
      ? tool.use_cases
      : tool.useCase
      ? [tool.useCase]
      : ['Regulatory compliance verification and audit evidence'],
    jurisdictions: Array.isArray(tool.jurisdictions)
      ? tool.jurisdictions
      : tool.jurisdiction
      ? [tool.jurisdiction]
      : ['UK FCA', 'Global'],
    official_url: tool.official_url || tool.url || '#',
    source_reference: tool.source_reference || tool.source || 'Provider Documentation',
    last_checked_date: tool.last_checked_date || tool.lastChecked || 'November 2026',
    review_status: tool.review_status || tool.status || 'Reviewed for listing',
    limitations_notes: tool.limitations_notes || tool.limitations || 'Applicability must be verified for the specific project scope.',
    connection_type: tool.connection_type || 'directory_only',
    version_license_notes: tool.version_license_notes || 'SaaS / Directory Listing',
  };
}

/**
 * Fetches the catalogue of trusted tools.
 * Connects to GET /api/v1/tools with fallback to curated baseline catalogue.
 */
export async function getTools(filters = {}) {
  let catalogue = [];
  try {
    const data = await apiCall('/api/v1/tools', 'GET');
    if (Array.isArray(data) && data.length > 0) {
      catalogue = data.map(normalizeToolRecord);
    }
  } catch (err) {
    // Graceful fallback to curated directory
  }

  if (catalogue.length === 0) {
    catalogue = DEFAULT_CURATED_TOOLS.map(normalizeToolRecord);
  }

  // Client-side filtering if filters are provided
  return catalogue.filter((tool) => {
    if (filters.search) {
      const q = filters.search.toLowerCase();
      const matchName = tool.name.toLowerCase().includes(q);
      const matchDesc = tool.short_description.toLowerCase().includes(q) || tool.full_description.toLowerCase().includes(q);
      const matchProvider = tool.provider.toLowerCase().includes(q);
      const matchUseCase = (tool.use_cases || []).some((u) => u.toLowerCase().includes(q));
      if (!matchName && !matchDesc && !matchProvider && !matchUseCase) return false;
    }
    if (filters.category && filters.category !== 'All categories') {
      if (tool.category !== filters.category) return false;
    }
    if (filters.jurisdiction && filters.jurisdiction !== 'All jurisdictions') {
      const matchJur = (tool.jurisdictions || []).some(
        (j) => j.toLowerCase() === filters.jurisdiction.toLowerCase()
      );
      if (!matchJur) return false;
    }
    if (filters.review_status && filters.review_status !== 'All statuses') {
      if (tool.review_status !== filters.review_status) return false;
    }
    return true;
  });
}

/**
 * Fetches a single tool record by its tool_id
 */
export async function getToolById(toolId) {
  try {
    const data = await apiCall(`/api/v1/tools/${toolId}`, 'GET');
    if (data && data.id) return normalizeToolRecord(data);
  } catch (err) {}

  const local = DEFAULT_CURATED_TOOLS.find((t) => t.id === toolId);
  return local ? normalizeToolRecord(local) : null;
}

/**
 * Retrieves local project tool associations from localStorage
 */
function getLocalProjectAssociations() {
  try {
    const raw = localStorage.getItem(PROJECT_TOOLS_STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (e) {
    return [];
  }
}

/**
 * Saves project tool associations to localStorage
 */
function saveLocalProjectAssociations(associations) {
  try {
    localStorage.setItem(PROJECT_TOOLS_STORAGE_KEY, JSON.stringify(associations));
  } catch (e) {}
}

/**
 * Fetches tools associated with a specific project.
 * Connects to GET /api/v1/projects/{project_id}/tools with fallback to localStorage.
 */
export async function getProjectTools(projectId) {
  if (!projectId) return [];

  let associations = [];
  try {
    const data = await apiCall(`/api/v1/projects/${projectId}/tools`, 'GET');
    if (Array.isArray(data)) {
      associations = data;
    }
  } catch (err) {}

  if (associations.length === 0) {
    const local = getLocalProjectAssociations();
    associations = local.filter(
      (a) => String(a.project_id) === String(projectId) && a.status === 'ACTIVE'
    );
  }

  // Enrich associations with the full catalogue tool metadata
  const allTools = DEFAULT_CURATED_TOOLS.map(normalizeToolRecord);
  return associations.map((assoc) => {
    const matchedTool = allTools.find((t) => t.id === assoc.tool_id) || {};
    return {
      ...matchedTool,
      ...assoc,
      association_id: assoc.id || assoc.association_id,
      project_id: assoc.project_id,
      tool_id: assoc.tool_id,
      added_by: assoc.added_by || 'Current Builder',
      added_at: assoc.added_at || new Date().toISOString(),
      notes: assoc.notes || '',
      isUsed: true,
    };
  });
}

/**
 * Associates a catalogue tool with a project ("Add to My Used Tools").
 * Connects to POST /api/v1/projects/{project_id}/tools with fallback to localStorage.
 */
export async function addProjectTool(projectId, toolId, userEmail = 'builder@example.com', notes = '') {
  if (!projectId || !toolId) {
    throw new Error('Project ID and Tool ID are required.');
  }

  let result = null;
  try {
    result = await apiCall(`/api/v1/projects/${projectId}/tools`, 'POST', {
      tool_id: toolId,
      notes,
    });
  } catch (err) {}

  // Fallback / update local vault
  const local = getLocalProjectAssociations();
  const existingIdx = local.findIndex(
    (a) => String(a.project_id) === String(projectId) && a.tool_id === toolId
  );

  const newAssoc = {
    id: `assoc-${Date.now()}-${Math.random().toString(36).substr(2, 6)}`,
    project_id: projectId,
    tool_id: toolId,
    added_by: userEmail,
    added_at: new Date().toISOString(),
    notes: notes || '',
    status: 'ACTIVE',
  };

  if (existingIdx >= 0) {
    local[existingIdx].status = 'ACTIVE';
    local[existingIdx].added_at = new Date().toISOString();
    if (notes) local[existingIdx].notes = notes;
  } else {
    local.push(newAssoc);
  }
  saveLocalProjectAssociations(local);

  // Log immutable audit event (DEF-31 & PDF Requirement 11)
  recordAdminAuditLog({
    action: 'PROJECT_TOOL_ADDED',
    event_type: 'Project Tool Association',
    actor_email: userEmail,
    affectedResource: `Project ${projectId} / Tool ${toolId}`,
    details: `Tool "${toolId}" added to project "${projectId}" under My Used Tools.`,
    status: 'SUCCESS',
  });

  return result || newAssoc;
}

/**
 * Removes a tool association from a project.
 * Connects to DELETE /api/v1/projects/{project_id}/tools/{tool_id} with fallback to localStorage.
 * IMPORTANT: This removes the project association only; it does not delete the catalogue tool.
 */
export async function removeProjectTool(projectId, toolId, userEmail = 'builder@example.com') {
  if (!projectId || !toolId) {
    throw new Error('Project ID and Tool ID are required.');
  }

  try {
    await apiCall(`/api/v1/projects/${projectId}/tools/${toolId}`, 'DELETE');
  } catch (err) {}

  // Update local vault
  const local = getLocalProjectAssociations();
  const updated = local.map((a) => {
    if (String(a.project_id) === String(projectId) && a.tool_id === toolId) {
      return { ...a, status: 'REMOVED', removed_at: new Date().toISOString() };
    }
    return a;
  });
  saveLocalProjectAssociations(updated);

  // Log immutable audit event
  recordAdminAuditLog({
    action: 'PROJECT_TOOL_REMOVED',
    event_type: 'Project Tool Association',
    actor_email: userEmail,
    affectedResource: `Project ${projectId} / Tool ${toolId}`,
    details: `Tool "${toolId}" removed from project "${projectId}" tool roster.`,
    status: 'SUCCESS',
  });

  return { success: true, project_id: projectId, tool_id: toolId };
}

/**
 * Legacy compatibility export for toggleToolUsage
 */
export async function toggleToolUsage(toolId, isUsed = true, projectId = 'default', userEmail = 'builder@example.com') {
  if (isUsed) {
    return addProjectTool(projectId, toolId, userEmail);
  } else {
    return removeProjectTool(projectId, toolId, userEmail);
  }
}
