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
  isAuthenticated: boolean
  setAuth: (user: User, org: Organization, accessToken: string, refreshToken: string) => void
  clearAuth: () => void
  loadFromStorage: () => void
  updateUser: (updates: Partial<User>) => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  organization: null,
  isAuthenticated: false,

  setAuth: (user, organization, accessToken, refreshToken) => {
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('refresh_token', refreshToken)
    localStorage.setItem('user', JSON.stringify(user))
    localStorage.setItem('organization', JSON.stringify(organization))
    set({ user, organization, isAuthenticated: true })
  },

  clearAuth: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    localStorage.removeItem('organization')
    set({ user: null, organization: null, isAuthenticated: false })
  },

  loadFromStorage: () => {
    const token = localStorage.getItem('access_token')
    const userStr = localStorage.getItem('user')
    const orgStr = localStorage.getItem('organization')
    if (token && userStr && orgStr) {
      try {
        set({
          user: JSON.parse(userStr),
          organization: JSON.parse(orgStr),
          isAuthenticated: true,
        })
      } catch { /* invalid storage */ }
    }
  },

  updateUser: (updates) => set((s) => ({
    user: s.user ? { ...s.user, ...updates } : null
  })),
}))
