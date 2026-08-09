import { apiClient } from './client'

export const settingsApi = {
  // Inboxes
  listInboxes: () => apiClient.get('/inboxes').then(r => r.data),
  createInbox: (data: any) => apiClient.post('/inboxes', data).then(r => r.data),
  updateInbox: (id: string, data: any) => apiClient.patch(`/inboxes/${id}`, data).then(r => r.data),
  deleteInbox: (id: string) => apiClient.delete(`/inboxes/${id}`).then(r => r.data),

  // Canned responses
  listCannedResponses: (params?: any) => apiClient.get('/canned-responses', { params }).then(r => r.data),
  createCannedResponse: (data: any) => apiClient.post('/canned-responses', data).then(r => r.data),
  updateCannedResponse: (id: string, data: any) => apiClient.patch(`/canned-responses/${id}`, data).then(r => r.data),
  deleteCannedResponse: (id: string) => apiClient.delete(`/canned-responses/${id}`).then(r => r.data),

  // SLA policies
  listSLAPolicies: () => apiClient.get('/sla/policies').then(r => r.data),
  createSLAPolicy: (data: any) => apiClient.post('/sla/policies', data).then(r => r.data),
  updateSLAPolicy: (id: string, data: any) => apiClient.patch(`/sla/policies/${id}`, data).then(r => r.data),
  deleteSLAPolicy: (id: string) => apiClient.delete(`/sla/policies/${id}`).then(r => r.data),

  // Webhooks
  listWebhooks: () => apiClient.get('/webhooks').then(r => r.data),
  createWebhook: (data: any) => apiClient.post('/webhooks', data).then(r => r.data),
  updateWebhook: (id: string, data: any) => apiClient.patch(`/webhooks/${id}`, data).then(r => r.data),
  deleteWebhook: (id: string) => apiClient.delete(`/webhooks/${id}`).then(r => r.data),

  // API keys
  listAPIKeys: () => apiClient.get('/api-keys').then(r => r.data),
  createAPIKey: (data: any) => apiClient.post('/api-keys', data).then(r => r.data),
  deleteAPIKey: (id: string) => apiClient.delete(`/api-keys/${id}`).then(r => r.data),
  revokeAPIKey: (id: string) => apiClient.post(`/api-keys/${id}/revoke`).then(r => r.data),

  // Custom domains
  listDomains: () => apiClient.get('/domains').then(r => r.data),
  addDomain: (data: any) => apiClient.post('/domains', data).then(r => r.data),
  verifyDomain: (id: string) => apiClient.post(`/domains/${id}/verify`).then(r => r.data),
  deleteDomain: (id: string) => apiClient.delete(`/domains/${id}`).then(r => r.data),
}
