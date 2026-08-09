import { apiClient } from './client'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

export const teamApi = {
  listMembers: () => apiClient.get('/team/members').then(r => r.data),
  updateMember: (id: string, data: any) => apiClient.patch(`/team/members/${id}`, data).then(r => r.data),
  removeMember: (id: string) => apiClient.delete(`/team/members/${id}`).then(r => r.data),

  sendInvite: (data: { email: string; role: string }) =>
    apiClient.post('/team/invitations', data).then(r => r.data),
  listInvitations: () => apiClient.get('/team/invitations').then(r => r.data),
  deleteInvitation: (id: string) => apiClient.delete(`/team/invitations/${id}`).then(r => r.data),

  validateInvite: (token: string) =>
    axios.get(`${API_BASE}/team/invitations/validate/${token}`).then(r => r.data),
  acceptInvite: (data: { token: string; full_name: string; password: string }) =>
    axios.post(`${API_BASE}/team/invitations/accept`, data).then(r => r.data),
}
