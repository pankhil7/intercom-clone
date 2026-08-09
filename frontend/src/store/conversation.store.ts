import { create } from 'zustand'

export interface ConversationFilters {
  status: string
  channel: string
  assigned_to: string
}

interface ConversationStore {
  activeConversationId: string | null
  filters: ConversationFilters
  unreadCounts: Record<string, number>
  typingConversations: Set<string>
  setActiveConversation: (id: string | null) => void
  setFilters: (f: Partial<ConversationFilters>) => void
  setUnread: (conversationId: string, count: number) => void
  setTyping: (conversationId: string, isTyping: boolean) => void
}

export const useConversationStore = create<ConversationStore>((set) => ({
  activeConversationId: null,
  filters: { status: 'open', channel: '', assigned_to: '' },
  unreadCounts: {},
  typingConversations: new Set(),

  setActiveConversation: (id) => set({ activeConversationId: id }),

  setFilters: (f) => set((s) => ({ filters: { ...s.filters, ...f } })),

  setUnread: (conversationId, count) =>
    set((s) => ({ unreadCounts: { ...s.unreadCounts, [conversationId]: count } })),

  setTyping: (conversationId, isTyping) =>
    set((s) => {
      const next = new Set(s.typingConversations)
      isTyping ? next.add(conversationId) : next.delete(conversationId)
      return { typingConversations: next }
    }),
}))
