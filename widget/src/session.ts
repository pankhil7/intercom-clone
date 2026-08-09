import type { Session } from './types'

const STORAGE_KEY = 'inbox_widget_session'

export function saveSession(session: Session): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(session))
  } catch {
    // localStorage might be unavailable (private mode, iframe restrictions)
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(session))
  }
}

export function loadSession(): Session | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY) || sessionStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const session: Session = JSON.parse(raw)
    // Check if expired
    if (Date.now() > session.expiresAt) {
      clearSession()
      return null
    }
    return session
  } catch {
    return null
  }
}

export function clearSession(): void {
  try { localStorage.removeItem(STORAGE_KEY) } catch {}
  try { sessionStorage.removeItem(STORAGE_KEY) } catch {}
}

export function updateSessionConversation(conversationId: string): void {
  const session = loadSession()
  if (session) {
    session.conversationId = conversationId
    saveSession(session)
  }
}
