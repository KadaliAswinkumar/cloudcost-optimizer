import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

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
}

export default apiClient

