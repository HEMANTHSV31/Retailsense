import api from './api';

export const authService = {
  login: (username, password) =>
    api.post('/auth/login', { username, password }),

  register: (email, username, password) =>
    api.post('/auth/register', { email, username, password }),

  refresh: (refreshToken) =>
    api.post('/auth/refresh', { refresh_token: refreshToken }),

  getProfile: () => api.get('/users/me'),

  updateProfile: (data) => api.put('/users/me', data),
};

export const forecastService = {
  generate: (params) => api.post('/forecast/generate', params),
  options: () => api.get('/forecast/options'),
  history: () => api.get('/forecast/history'),
  getById: (id) => api.get(`/forecast/${id}`),
};

export const inventoryService = {
  generateRecommendations: (params) => api.post('/inventory/recommendations', params),
  demandMultiplier: () => api.get('/inventory/demand-multiplier'),
  seasonalAdvice: () => api.get('/inventory/seasonal-advice'),
};

export const analyticsService = {
  overview: () => api.get('/analytics/overview'),
  salesTrend: (days = 90) => api.get(`/analytics/sales-trend?days=${days}`),
  topProducts: (limit = 10) => api.get(`/analytics/top-products?limit=${limit}`),
  storePerformance: () => api.get('/analytics/store-performance'),
  seasonal: () => api.get('/analytics/seasonal'),
  dayOfWeek: () => api.get('/analytics/day-of-week'),
};

export const uploadService = {
  upload: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/upload/', formData);
  },
  history: () => api.get('/upload/history'),
  clean: (datasetId) => api.post(`/upload/${datasetId}/clean`),
  reset: () => api.post('/upload/reset'),
};

export const modelService = {
  train: (params) => api.post('/model/train', params),
  history: () => api.get('/model/history'),
  best: () => api.get('/model/best'),
  features: () => api.get('/model/features'),
};

export const insightsService = {
  generate: () => api.post('/insights/generate'),
  list: () => api.get('/insights/list'),
  seasonContext: () => api.get('/insights/season-context'),
};

export const weatherService = {
  current: (city = 'Lahore') => api.get(`/weather/current?city=${city}`),
  forecast: (city = 'Lahore', days = 7) => api.get(`/weather/forecast?city=${city}&days=${days}`),
  holidaysUpcoming: (limit = 10) => api.get(`/weather/holidays/upcoming?limit=${limit}`),
  holidaysCurrent: () => api.get('/weather/holidays/current'),
};

export const organizationService = {
  create: (data) => api.post('/organizations', data),
  me: () => api.get('/organizations/me'),
  update: (data) => api.patch('/organizations/me', data),
  members: () => api.get('/organizations/members'),
  invitations: () => api.get('/organizations/invitations'),
  createInvitation: (data) => api.post('/organizations/invitations', data),
  revokeInvitation: (id) => api.post(`/organizations/invitations/${id}/revoke`),
  acceptInvitation: (data) => api.post('/organizations/invitations/accept', data),
  updateMemberRole: (userId, role) => api.patch(`/organizations/members/${userId}`, { role }),
  removeMember: (userId) => api.delete(`/organizations/members/${userId}`),
  switchOrg: (orgId) => api.post(`/organizations/switch/${orgId}`),
};

export const dataService = {
  upload: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/data/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  bulk: (rows) => api.post('/data/bulk', { rows }),
  summary: () => api.get('/data/summary'),
  webhooks: () => api.get('/data/webhooks'),
  createWebhook: () => api.post('/data/webhooks'),
};

export const registryService = {
  overview: () => api.get('/model-registry/overview'),
  train: (params) => api.post('/model-registry/train', params),
  versions: () => api.get('/model-registry/versions'),
  promote: (id) => api.post(`/model-registry/promote/${id}`),
  rollback: (version) => api.post('/model-registry/rollback', { version }),
  accuracy: (params = {}) => api.get('/model-registry/accuracy', { params }),
  accuracySummary: () => api.get('/model-registry/accuracy/summary'),
  evaluate: () => api.post('/model-registry/evaluate'),
};

export const purchaseService = {
  decisions: (params) => api.post('/purchase/decisions', params),
  financialSummary: (params) => api.post('/purchase/financial-summary', params),
  whatIf: (params) => api.post('/purchase/what-if', params),
};

export const alertsService = {
  list: (params = {}) => api.get('/alerts', { params }),
  counts: () => api.get('/alerts/counts'),
  markRead: (id) => api.post(`/alerts/${id}/read`),
  resolve: (id) => api.post(`/alerts/${id}/resolve`),
  detect: () => api.post('/alerts/detect'),
};

export const intelligenceService = {
  executive: () => api.get('/intelligence/executive'),
  stores: () => api.get('/intelligence/stores'),
  storeDetail: (id) => api.get(`/intelligence/stores/${id}`),
  products: () => api.get('/intelligence/products'),
  productDetail: (id) => api.get(`/intelligence/products/${id}`),
};

export const advisorService = {
  ask: (question, history = []) => api.post('/advisor/ask', { question, history }),
  history: () => api.get('/advisor/history'),
};

export const dataHealthService = {
  report: () => api.get('/data-health/report'),
  anomalies: () => api.get('/data-health/anomalies'),
};

export const reportsService = {
  get: (type, params = {}) => api.get(`/reports/${type}`, { params }),
  export: (type, format = 'pdf', params = {}) =>
    api.get(`/reports/${type}/export`, { params: { format, ...params }, responseType: 'blob' }),
};

export const opsService = {
  health: () => api.get('/ops/system/health'),
  info: () => api.get('/ops/system/info'),
  jobs: () => api.get('/ops/jobs'),
  jobStatus: (id) => api.get(`/ops/jobs/${id}`),
  retryJob: (id) => api.post(`/ops/jobs/${id}/retry`),
  templates: () => api.get('/ops/task-templates'),
};

export const decisionService = {
  getDecisions: (params) => api.get('/decisions', { params }),
  enrichReasoning: (decision) => api.post('/decisions/reason', { decision }),
  executeAction: (decisionId, operatorNotes) =>
    api.post(`/decisions/${decisionId}/execute`, { operator_notes: operatorNotes }),
  getBaselineComparison: () => api.get('/decisions/baseline'),
};



