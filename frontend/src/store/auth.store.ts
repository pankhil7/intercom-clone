import { create } from 'zustand'

interface User {
  id: string; email: string; full_name: string; role: string; avatar_url?: string; organization_id: string
}
interface Organization {
  id: string; name: string; slug: string; plan: string; widget_color: string
}

interface AuthState {
  user: User | null
  organization: Organization | null
  accessToken: string | null   // lives in memory only — never persisted to disk
  isAuthenticated: boolean
  setAuth: (user: User, org: Organization, accessToken: string) => void
  setAccessToken: (token: string) => void
  clearAuth: () => void
  updateUser: (updates: Partial<User>) => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  organization: null,
  accessToken: null,
  isAuthenticated: false,

  // Called after login / signup / silent refresh
  // refresh_token arrives as an HttpOnly cookie — we never see or store it
  setAuth: (user, organization, accessToken) => {
    set({ user, organization, accessToken, isAuthenticated: true })
  },

  setAccessToken: (token) => set({ accessToken: token }),

  clearAuth: () => {
    set({ user: null, organization: null, accessToken: null, isAuthenticated: false })
  },

  updateUser: (updates) => set((s) => ({
    user: s.user ? { ...s.user, ...updates } : null,
  })),
}))
