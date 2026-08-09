import { apiClient } from './client'

export const aiApi = {
  summarize: (conversationId: string) =>
    apiClient.post(`/ai/summarize/${conversationId}`).then(r => r.data),

  generateDraft: (conversationId: string) =>
    apiClient.post(`/ai/draft/${conversationId}`).then(r => r.data),

  updateDraft: (draftId: string, data: { status: string; edited_content?: string }) =>
    apiClient.patch(`/ai/draft/${draftId}`, data).then(r => r.data),

  kbSuggest: (q: string) =>
    apiClient.get('/ai/kb-suggest', { params: { q } }).then(r => r.data),
}
