import axios from 'axios'

// In dev: same origin + Vite proxy → backend (no CORS).
// Production: prefer VITE_API_URL at build time; if unset, use the deployed Render API.
// Override via GitHub repo variable VITE_API_URL in the Pages workflow.
const DEFAULT_PRODUCTION_API = 'https://cloudcost-api-3uy5.onrender.com'
const API_BASE_URL =
  (import.meta.env.VITE_API_URL && String(import.meta.env.VITE_API_URL).trim()) ||
  (import.meta.env.DEV ? '' : DEFAULT_PRODUCTION_API)

if (import.meta.env.DEV) {
  console.info('[api] baseURL:', API_BASE_URL || '(same-origin → Vite proxy)')
}

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

const intelligenceOrgBase = (orgId) => `/api/v1/intelligence/organizations/${orgId}`

// API endpoints
export const api = {
  // Direct axios methods
  get: (url, config) => apiClient.get(url, config),
  post: (url, data, config) => apiClient.post(url, data, config),
  
  // Health
  health: () => apiClient.get('/health'),
  
  // Instances (AWS)
  getInstances: (params) => apiClient.get('/api/v1/instances', { params }),
  getInstanceDetails: (instanceType) => apiClient.get(`/api/v1/instances/${instanceType}`),
  
  // Pricing
  getOnDemandPricing: (instanceType, region) => 
    apiClient.get(`/api/v1/pricing/on-demand/${instanceType}`, { params: { region } }),
  getSpotPricing: (instanceType, region) => 
    apiClient.get(`/api/v1/pricing/spot/${instanceType}`, { params: { region } }),
  comparePricing: (instanceType, region) => 
    apiClient.get(`/api/v1/pricing/compare/${instanceType}`, { params: { region } }),
  calculateCost: (params) => 
    apiClient.post('/api/v1/pricing/calculate', null, { params }),
  
  // Recommendations
  getRecommendations: (data) => apiClient.post('/api/v1/recommendations', data),
  getQuickRecommendation: (data) => apiClient.post('/api/v1/recommendations/quick', data),
  
  // Multi-Cloud
  getMulticloudRecommendations: (data) => 
    apiClient.post('/api/v1/multicloud/recommendations', data),
  getMulticloudInstances: (params) => 
    apiClient.get('/api/v1/multicloud/instances', { params }),
  findEquivalentInstances: (instanceType, provider) => 
    apiClient.get(`/api/v1/multicloud/compare/${instanceType}`, { params: { provider } }),
  compareCloudPricing: (vcpus, memoryGb) => 
    apiClient.get('/api/v1/multicloud/pricing/compare', { 
      params: { vcpus, memory_gb: memoryGb } 
    }),
  getProviders: () => apiClient.get('/api/v1/multicloud/providers'),

  /** FinOps / FOCUS-style dashboard (demo or live when billing connectors are configured) */
  getFinopsDashboard: (params) =>
    apiClient.get('/api/v1/finops/dashboard', { params }),
  getFinopsRecommendations: (organizationSlug) =>
    apiClient.get('/api/v1/finops/recommendations', { params: { organization_slug: organizationSlug } }),
  acceptFinopsRecommendation: (recommendationId, body) =>
    apiClient.post(`/api/v1/finops/recommendations/${recommendationId}/accept`, body),
  markFinopsRecommendationInProgress: (recommendationId, body) =>
    apiClient.post(`/api/v1/finops/recommendations/${recommendationId}/in-progress`, body),
  implementFinopsRecommendation: (recommendationId, body) =>
    apiClient.post(`/api/v1/finops/recommendations/${recommendationId}/implemented`, body),
  verifyFinopsRecommendation: (recommendationId, body) =>
    apiClient.post(`/api/v1/finops/recommendations/${recommendationId}/verify`, body),
  rollbackFinopsRecommendation: (recommendationId, body) =>
    apiClient.post(`/api/v1/finops/recommendations/${recommendationId}/rollback`, body),
  dismissFinopsRecommendation: (recommendationId, body) =>
    apiClient.post(`/api/v1/finops/recommendations/${recommendationId}/dismiss`, body),
  listFinopsOnboardingSources: (organizationSlug) =>
    apiClient.get('/api/v1/finops/onboarding/sources', { params: { organization_slug: organizationSlug } }),
  upsertFinopsOnboardingSource: (body) =>
    apiClient.post('/api/v1/finops/onboarding/sources', body),
  getFinopsOnboardingHealth: (organizationSlug) =>
    apiClient.get('/api/v1/finops/onboarding/health', { params: { organization_slug: organizationSlug } }),
  getFinopsWeeklyDigest: (organizationSlug) =>
    apiClient.get('/api/v1/finops/growth/weekly-digest', { params: { organization_slug: organizationSlug } }),
  getFinopsLeaderboard: () => apiClient.get('/api/v1/finops/growth/leaderboard'),
  getFinopsWhatIf: (body) => apiClient.post('/api/v1/finops/growth/what-if', body),
  getFinopsAnomalies: (organizationSlug, includeResolved = false) =>
    apiClient.get('/api/v1/finops/anomalies', {
      params: { organization_slug: organizationSlug, include_resolved: includeResolved },
    }),
  acknowledgeFinopsAnomaly: (anomalyId, body) =>
    apiClient.post(`/api/v1/finops/anomalies/${anomalyId}/acknowledge`, body),
  getFinopsInvestorKpis: (organizationSlug) =>
    apiClient.get('/api/v1/finops/investor/kpis', { params: { organization_slug: organizationSlug } }),
  getFinopsInvestorReport: (organizationSlug) =>
    apiClient.get('/api/v1/finops/investor/report', { params: { organization_slug: organizationSlug } }),
  exportFinopsInvestorReport: (organizationSlug) =>
    apiClient.get('/api/v1/finops/investor/report/export', {
      params: { organization_slug: organizationSlug },
      responseType: 'blob',
    }),
  getFinopsForecast: (organizationSlug, months = 6) =>
    apiClient.get('/api/v1/finops/forecast', { params: { organization_slug: organizationSlug, months } }),
  getFinopsCommitmentOptimizer: (organizationSlug) =>
    apiClient.get('/api/v1/finops/commitment/optimizer', { params: { organization_slug: organizationSlug } }),
  getFinopsExecutiveNarrative: (organizationSlug) =>
    apiClient.get('/api/v1/finops/executive/narrative', { params: { organization_slug: organizationSlug } }),
  createFinopsCopilotPlan: (body) => apiClient.post('/api/v1/finops/copilot/plan', body),
  runFinopsCopilotExecute: (body) => apiClient.post('/api/v1/finops/copilot/execute', body),
  evaluateFinopsPolicy: (body) => apiClient.post('/api/v1/finops/policies/validate', body),
  calculateFinopsUnitEconomics: (body) => apiClient.post('/api/v1/finops/unit-economics', body),

  // CloudCost AI™
  getAIRecommendations: (data) => 
    apiClient.post('/api/v1/ai/recommend', data),
  getWorkloadTypes: () => 
    apiClient.get('/api/v1/ai/workload-types'),
  
  // Conversational AI (Chat)
  chatWithAI: (data) => 
    apiClient.post('/api/v1/ai/chat', data),
  getChatSuggestions: (workloadType = 'general') => 
    apiClient.get('/api/v1/ai/suggestions', { params: { workload_type: workloadType } }),
  
  // Spot Intelligence™
  analyzeSpotInstance: (data) => 
    apiClient.post('/api/v1/spot-intelligence/analyze', data),
  compareSpotProviders: (data) => 
    apiClient.post('/api/v1/spot-intelligence/compare', data),
  quickSpotCheck: (provider, instanceType) => 
    apiClient.get('/api/v1/spot-intelligence/quick-check', { 
      params: { provider, instance_type: instanceType } 
    }),

  // Infrastructure Intelligence (orgs, connectors, async scans, findings, reports)
  intelligence: {
    createOrganization: (body) => apiClient.post('/api/v1/intelligence/organizations', body),
    getOrganization: (orgId) => apiClient.get(`/api/v1/intelligence/organizations/${orgId}`),
    listConnectors: (orgId) => apiClient.get(`${intelligenceOrgBase(orgId)}/connectors`),
    createConnector: (orgId, body) => apiClient.post(`${intelligenceOrgBase(orgId)}/connectors`, body),
    triggerScan: (orgId, connectorId, body) =>
      apiClient.post(
        `${intelligenceOrgBase(orgId)}/connectors/${connectorId}/scans`,
        body ?? {},
      ),
    listScans: (orgId, params) => apiClient.get(`${intelligenceOrgBase(orgId)}/scans`, { params }),
    getScan: (orgId, scanId) => apiClient.get(`${intelligenceOrgBase(orgId)}/scans/${scanId}`),
    getScanCostSummary: (orgId, scanId) =>
      apiClient.get(`${intelligenceOrgBase(orgId)}/scans/${scanId}/cost-summary`),
    getOptimizationBrief: (orgId, scanId) =>
      apiClient.get(`${intelligenceOrgBase(orgId)}/scans/${scanId}/optimization-brief`),
    listFindings: (orgId, params) => apiClient.get(`${intelligenceOrgBase(orgId)}/findings`, { params }),
    createReport: (orgId, body) => apiClient.post(`${intelligenceOrgBase(orgId)}/reports`, body),
    /** Absolute URL for opening report JSON export in a new tab (GitHub Pages + cross-origin API). */
    exportReportUrl: (orgId, reportId) => {
      const path = `${intelligenceOrgBase(orgId)}/reports/${reportId}/export`
      const base = String(apiClient.defaults.baseURL || '').replace(/\/$/, '')
      if (base) return `${base}${path}`
      if (typeof window !== 'undefined') return `${window.location.origin}${path}`
      return path
    },
  },
}

export default apiClient

