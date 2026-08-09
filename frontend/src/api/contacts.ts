import { apiClient } from './client'

export const contactsApi = {
  list: (params?: any) => apiClient.get('/contacts', { params }).then(r => r.data),
  get: (id: string) => apiClient.get(`/contacts/${id}`).then(r => r.data),
  create: (data: { name?: string; email?: string; phone?: string }) =>
    apiClient.post('/contacts', data).then(r => r.data),
  update: (id: string, data: any) => apiClient.patch(`/contacts/${id}`, data).then(r => r.data),
  getTimeline: (id: string) => apiClient.get(`/contacts/${id}/timeline`).then(r => r.data),
  getConversations: (id: string) => apiClient.get(`/contacts/${id}/conversations`).then(r => r.data),
}
