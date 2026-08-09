import { apiClient } from './client'

export const authApi = {
  signup: (data: { organization_name: string; email: string; password: string; full_name: string }) =>
    apiClient.post('/auth/signup', data).then(r => r.data),
  // returns { access_token, user, organization }
  // refresh_token arrives automatically as HttpOnly cookie — not in response body

  login: (data: { email: string; password: string }) =>
    apiClient.post('/auth/login', data).then(r => r.data),
  // same shape as signup

  // No argument needed — refresh_token cookie is sent automatically by the browser
  refresh: () => apiClient.post('/auth/refresh', {}).then(r => r.data),

  getMe: () => apiClient.get('/auth/me').then(r => r.data),

  // Clears the HttpOnly cookie server-side
  logout: () => apiClient.post('/auth/logout').then(r => r.data),
}
