import { apiClient } from './client'

export const authApi = {
  signup: (data: { organization_name: string; email: string; password: string; full_name: string }) =>
    apiClient.post('/auth/signup', data).then(r => r.data),

  login: (data: { email: string; password: string }) =>
    apiClient.post('/auth/login', data).then(r => r.data),

  refresh: (refresh_token: string) =>
    apiClient.post('/auth/refresh', { refresh_token }).then(r => r.data),

  getMe: () => apiClient.get('/auth/me').then(r => r.data),

  logout: () => apiClient.post('/auth/logout').then(r => r.data),
}
