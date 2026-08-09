import { create } from 'zustand'

interface Toast { id: string; title: string; description?: string; variant?: 'default' | 'destructive' }

interface UIStore {
  sidebarCollapsed: boolean
  toasts: Toast[]
  setSidebarCollapsed: (v: boolean) => void
  addToast: (t: Omit<Toast, 'id'>) => void
  removeToast: (id: string) => void
}

export const useUIStore = create<UIStore>((set) => ({
  sidebarCollapsed: false,
  toasts: [],

  setSidebarCollapsed: (v) => set({ sidebarCollapsed: v }),

  addToast: (t) => {
    const id = Date.now().toString()
    set((s) => ({ toasts: [...s.toasts, { ...t, id }] }))
    setTimeout(() => set((s) => ({ toasts: s.toasts.filter(x => x.id !== id) })), 5000)
  },

  removeToast: (id) => set((s) => ({ toasts: s.toasts.filter(t => t.id !== id) })),
}))
