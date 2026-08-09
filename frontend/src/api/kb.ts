import { apiClient } from './client'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

export const kbApi = {
  listCategories: (params?: any) => apiClient.get('/kb/categories', { params }).then(r => r.data),
  createCategory: (data: any) => apiClient.post('/kb/categories', data).then(r => r.data),
  updateCategory: (id: string, data: any) => apiClient.patch(`/kb/categories/${id}`, data).then(r => r.data),
  deleteCategory: (id: string) => apiClient.delete(`/kb/categories/${id}`).then(r => r.data),

  listArticles: (params?: any) => apiClient.get('/kb/articles', { params }).then(r => r.data),
  getArticle: (id: string) => apiClient.get(`/kb/articles/${id}`).then(r => r.data),
  getArticleBySlug: (slug: string) => apiClient.get(`/kb/articles/slug/${slug}`).then(r => r.data),
  createArticle: (data: any) => apiClient.post('/kb/articles', data).then(r => r.data),
  updateArticle: (id: string, data: any) => apiClient.patch(`/kb/articles/${id}`, data).then(r => r.data),
  deleteArticle: (id: string) => apiClient.delete(`/kb/articles/${id}`).then(r => r.data),

  search: (q: string, params?: any) => apiClient.get('/kb/search', { params: { q, ...params } }).then(r => r.data),

  searchPublic: (q: string, orgSlug: string) =>
    axios.get(`${API_BASE}/widget/kb/search`, { params: { q, org: orgSlug } }).then(r => r.data),

  // Public KB (no auth required)
  listPublicCategories: (orgSlug: string) =>
    axios.get(`${API_BASE}/public/kb/${orgSlug}/categories`).then(r => r.data),
  searchPublicArticles: (orgSlug: string, q: string) =>
    axios.get(`${API_BASE}/public/kb/${orgSlug}/search`, { params: { q } }).then(r => r.data),
  getPublicArticle: (orgSlug: string, slug: string) =>
    axios.get(`${API_BASE}/public/kb/${orgSlug}/articles/${slug}`).then(r => r.data),
}
