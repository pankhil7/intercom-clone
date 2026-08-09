export interface WidgetConfig {
  widgetKey: string
  apiBase?: string
  socketUrl?: string
  primaryColor?: string
  greeting?: string
  position?: 'bottom-right' | 'bottom-left'
}

export interface Session {
  token: string
  contactId: string
  conversationId?: string
  expiresAt: number
}

export interface Message {
  id: string
  content: string
  sender_type: 'contact' | 'agent'
  created_at: string
  agent_name?: string
}

export interface KBArticle {
  id: string
  title: string
  slug: string
  excerpt?: string
}

export interface PageView {
  url: string
  title: string
  timestamp: number
}

declare global {
  interface Window {
    InboxWidget: WidgetConfig
  }
}
