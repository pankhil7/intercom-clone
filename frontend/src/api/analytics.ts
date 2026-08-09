import { apiClient } from './client'

export const analyticsApi = {
  getOverview: (start: string, end: string) =>
    apiClient.get('/analytics/overview', { params: { start, end } }).then(r => r.data),

  getAgentPerformance: (start: string, end: string) =>
    apiClient.get('/analytics/agent-performance', { params: { start, end } }).then(r => r.data),

  getBusiestHours: (start: string, end: string) =>
    apiClient.get('/analytics/busiest-hours', { params: { start, end } }).then(r => r.data),

  getResolutionRate: (start: string, end: string, group_by = 'day') =>
    apiClient.get('/analytics/resolution-rate', { params: { start, end, group_by } }).then(r => r.data),
}
