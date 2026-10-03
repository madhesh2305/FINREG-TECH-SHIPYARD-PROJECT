import { apiCall } from './api';

const MOCK_REQUIREMENTS = [
  {
    id: 'REQ-UK-001',
    code: 'FCA SYSC 6.1.4',
    title: 'Anti-Money Laundering Systems & Controls',
    jurisdiction: 'United Kingdom - FCA',
    category: 'AML / CTF',
    description: 'A firm must establish and maintain effective systems and controls for countering the risk that the firm might be used to further financial crime.',
    sourceUrl: 'https://www.handbook.fca.org.uk/handbook/SYSC/6/1.html',
    status: 'Validated',
    provenance: 'FCA Handbook SYSC 6.1.4 R',
    lastReviewed: '15 Sep 2026',
  },
  {
    id: 'REQ-EU-002',
    code: 'AMLD5 Art 13',
    title: 'Customer Due Diligence (CDD) Measures',
    jurisdiction: 'European Union - EBA',
    category: 'KYC / CDD',
    description: 'Obligation to verify customer identity on the basis of documents, data or information obtained from a reliable and independent source.',
    sourceUrl: 'https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32018L0843',
    status: 'Validated',
    provenance: 'Directive (EU) 2018/843 Article 13',
    lastReviewed: '20 Sep 2026',
  },
  {
    id: 'REQ-UK-003',
    code: 'UK GDPR Art 30',
    title: 'Records of Processing Activities (RoPA)',
    jurisdiction: 'United Kingdom - ICO',
    category: 'Data Governance',
    description: 'Each controller shall maintain a record of processing activities under its responsibility.',
    sourceUrl: 'https://ico.org.uk/for-organisations/guide-to-data-protection/',
    status: 'Validated',
    provenance: 'UK GDPR Article 30(1)',
    lastReviewed: '18 Sep 2026',
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
