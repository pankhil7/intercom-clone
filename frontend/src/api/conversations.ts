import { apiClient } from './client'

export const conversationsApi = {
  list: (params?: Record<string, any>) =>
    apiClient.get('/conversations', { params }).then(r => r.data),

  get: (id: string) => apiClient.get(`/conversations/${id}`).then(r => r.data),

  create: (data: any) => apiClient.post('/conversations', data).then(r => r.data),

  update: (id: string, data: any) => apiClient.patch(`/conversations/${id}`, data).then(r => r.data),

  sendMessage: (id: string, data: { content: string; content_type?: string }) =>
    apiClient.post(`/conversations/${id}/messages`, data).then(r => r.data),

  getMessages: (id: string, params?: any) =>
    apiClient.get(`/conversations/${id}/messages`, { params }).then(r => r.data),

  assign: (id: string, user_id: string) =>
    apiClient.post(`/conversations/${id}/assign`, { user_id }).then(r => r.data),

  unassign: (id: string) => apiClient.post(`/conversations/${id}/unassign`).then(r => r.data),

  resolve: (id: string) => apiClient.post(`/conversations/${id}/resolve`).then(r => r.data),

  reopen: (id: string) => apiClient.post(`/conversations/${id}/reopen`).then(r => r.data),

  snooze: (id: string, until: string) =>
    apiClient.patch(`/conversations/${id}`, { status: 'snoozed', snoozed_until: until }).then(r => r.data),
}
