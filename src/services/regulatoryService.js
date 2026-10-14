import { apiCall } from './api';

const MOCK_REQUIREMENTS = [
  {
    id: 'REQ-142',
    code: 'SYSC 6.3.8',
    reference: 'SYSC 6.3.8',
    title: 'Risk-sensitive customer due diligence',
    requirement: 'Risk-sensitive customer due diligence',
    authority: 'FCA',
    jurisdiction: 'United Kingdom',
    source: 'FCA Handbook',
    provenance: 'FCA Handbook',
    dateVersion: 'Release 126 · Sep 2026',
    lastReviewed: 'Release 126 · Sep 2026',
    category: 'FCA Rules / Principles',
    layer: 'FCA Rules / Principles',
    applicability: 'Applicable to all UK-authorised firms conducting customer onboarding',
    description: 'Firms must establish and maintain effective systems and controls for compliance with applicable financial crime requirements.',
    sourceUrl: 'https://www.handbook.fca.org.uk/handbook/SYSC/6/3.html',
    status: 'Validated',
    validationStatus: 'Validated',
    officialSource: 'Linked source record available in prototype',
    notesLimitations: 'This prototype does not claim legal validation. Interpretation and final applicability require appropriate human review.',
    topic: 'Customer Due Diligence',
  },
  {
    id: 'REQ-157',
    code: 'Part I, 5.7',
    reference: 'Part I, 5.7',
    title: 'Ongoing transaction monitoring',
    requirement: 'Ongoing transaction monitoring',
    authority: 'JMLSG',
    jurisdiction: 'United Kingdom',
    source: 'JMLSG Guidance',
    provenance: 'JMLSG Guidance',
    dateVersion: 'Jul 2024 revision',
    lastReviewed: 'Jul 2024 revision',
    category: 'Government Guidance',
    layer: 'Government Guidance',
    applicability: 'Applicable to UK financial services firms conducting ongoing customer activity',
    description: 'Continuous monitoring of customer accounts and transactions to detect unusual patterns and potential money laundering indicators.',
    sourceUrl: 'https://www.jmlsg.org.uk/guidance/part-i/',
    status: 'Review due',
    validationStatus: 'Review due',
    officialSource: 'Linked source record available in prototype',
    notesLimitations: 'This prototype does not claim legal validation. Interpretation and final applicability require appropriate human review.',
    topic: 'Transaction Monitoring',
  },
  {
    id: 'REQ-163',
    code: 'Chapter 3',
    reference: 'Chapter 3',
    title: 'Suspicious activity escalation',
    requirement: 'Suspicious activity escalation',
    authority: 'NCA',
    jurisdiction: 'United Kingdom',
    source: 'SAR Guidance',
    provenance: 'SAR Guidance',
    dateVersion: 'Version 3.1 · Jan 2025',
    lastReviewed: 'Version 3.1 · Jan 2025',
    category: 'Statutory Law',
    layer: 'Statutory Law',
    applicability: 'Applicable to all UK-based firms subject to the Money Laundering Regulations',
    description: 'Mandatory obligation to report suspicious activity reports (SARs) directly to the UK National Crime Agency without tipping off.',
    sourceUrl: 'https://www.nationalcrimeagency.gov.uk/who-we-are/publications/sar-guidance',
    status: 'Validated',
    validationStatus: 'Validated',
    officialSource: 'Linked source record available in prototype',
    notesLimitations: 'This prototype does not claim legal validation. Interpretation and final applicability require appropriate human review.',
    topic: 'Suspicious Activity Reporting',
  },
  {
    id: 'REQ-178',
    code: 'Recommendation 12',
    reference: 'Recommendation 12',
    title: 'Politically exposed persons (PEP) screening',
    requirement: 'Politically exposed persons (PEP) screening',
    authority: 'FATF',
    jurisdiction: 'Global / International',
    source: 'FATF Recommendations',
    provenance: 'FATF Recommendations',
    dateVersion: 'Updated Feb 2026',
    lastReviewed: 'Updated Feb 2026',
    category: 'International Standard',
    layer: 'International Standard',
    applicability: 'Applicable to All Financial Institutions',
    description: 'Enhanced due diligence requirements for PEPs, family members, and close associates across all onboarding channels.',
    sourceUrl: 'https://www.fatf-gafi.org/recommendations.html',
    status: 'Validated',
    validationStatus: 'Validated',
    officialSource: 'Linked source record available in prototype',
    notesLimitations: 'This prototype does not claim legal validation. Interpretation and final applicability require appropriate human review.',
    topic: 'PEP Screening',
  },
  {
    id: 'REQ-189',
    code: 'PRIN 2A.8',
    reference: 'PRIN 2A.8',
    title: 'Consumer Duty governance & oversight',
    requirement: 'Consumer Duty governance & oversight',
    authority: 'FCA',
    jurisdiction: 'United Kingdom',
    source: 'FCA FG22/5',
    provenance: 'FCA FG22/5',
    dateVersion: 'Release 124 · Jun 2026',
    lastReviewed: 'Release 124 · Jun 2026',
    category: 'FCA Rules / Principles',
    layer: 'FCA Rules / Principles',
    applicability: 'Applicable to Retail Financial Products & Services',
    description: 'Boards must monitor customer outcomes, pricing value, and product governance to ensure good outcomes for retail customers.',
    sourceUrl: 'https://www.fca.org.uk/firms/consumer-duty',
    status: 'Review due',
    validationStatus: 'Review due',
    officialSource: 'Linked source record available in prototype',
    notesLimitations: 'This prototype does not claim legal validation. Interpretation and final applicability require appropriate human review.',
    topic: 'Consumer Duty',
  },
];

/**
 * Fetches regulatory requirements list via GET /regulatory-requirements
 */
export async function getRegulatoryRequirements() {
  try {
    const data = await apiCall('/regulatory-requirements', 'GET');
    return Array.isArray(data) && data.length > 0 ? data : MOCK_REQUIREMENTS;
  } catch (err) {
    console.warn('[regulatoryService] GET /regulatory-requirements failed. Returning mock corpus.');
    return MOCK_REQUIREMENTS;
  }
}

/**
 * Fetches specific regulatory requirement details & provenance via GET /regulatory-requirements/{reqId}
 */
export async function getRequirementDetails(reqId) {
  try {
    return await apiCall(`/regulatory-requirements/${reqId}`, 'GET');
  } catch (err) {
    console.warn(`[regulatoryService] GET /regulatory-requirements/${reqId} failed. Returning mock fallback.`);
    return MOCK_REQUIREMENTS.find((r) => r.id === reqId) || MOCK_REQUIREMENTS[0];
  }
}
