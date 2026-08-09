import type { WidgetConfig, Session, Message, KBArticle } from './types'

export class WidgetAPI {
  private baseUrl: string
  private widgetKey: string
  private token: string | null = null

  constructor(config: WidgetConfig) {
    this.baseUrl = config.apiBase || 'https://api.yourapp.com/api/v1'
    this.widgetKey = config.widgetKey
  }

  setToken(token: string) {
    this.token = token
  }

  private headers(): Record<string, string> {
    const h: Record<string, string> = { 'Content-Type': 'application/json' }
    if (this.token) h['Authorization'] = `Bearer ${this.token}`
    return h
  }

  async initSession(data: {
    email?: string
    name?: string
    identifier?: string
    hmac?: string
  }): Promise<Session> {
    const res = await fetch(`${this.baseUrl}/widget/session`, {
      method: 'POST',
      headers: this.headers(),
      body: JSON.stringify({ widget_key: this.widgetKey, ...data }),
    })
    if (!res.ok) throw new Error('Failed to init session')
    const json = await res.json()
    this.token = json.token
    return {
      token: json.token,
      contactId: json.contact_id,
      conversationId: json.conversation_id,
      expiresAt: Date.now() + 24 * 60 * 60 * 1000,
    }
  }

  async getOrCreateConversation(contactId: string): Promise<string> {
    const res = await fetch(`${this.baseUrl}/widget/conversations`, {
      method: 'POST',
      headers: this.headers(),
      body: JSON.stringify({ contact_id: contactId }),
    })
    if (!res.ok) throw new Error('Failed to create conversation')
    const json = await res.json()
    return json.conversation_id || json.id
  }

  async getMessages(conversationId: string): Promise<Message[]> {
    const res = await fetch(`${this.baseUrl}/widget/conversations/${conversationId}/messages`, {
      headers: this.headers(),
    })
    if (!res.ok) throw new Error('Failed to fetch messages')
    const json = await res.json()
    return json.messages || []
  }

  async sendMessage(conversationId: string, content: string): Promise<Message> {
    const res = await fetch(`${this.baseUrl}/widget/conversations/${conversationId}/messages`, {
      method: 'POST',
      headers: this.headers(),
      body: JSON.stringify({ content, sender_type: 'contact' }),
    })
    if (!res.ok) throw new Error('Failed to send message')
    const json = await res.json()
    return json.message || json
  }

  async searchKB(q: string): Promise<KBArticle[]> {
    const res = await fetch(`${this.baseUrl}/widget/kb/search?q=${encodeURIComponent(q)}&widget_key=${this.widgetKey}`, {
      headers: this.headers(),
    })
    if (!res.ok) return []
    const json = await res.json()
    return json.articles || []
  }

  async trackPageView(data: { url: string; title: string }): Promise<void> {
    if (!this.token) return
    fetch(`${this.baseUrl}/widget/page-views`, {
      method: 'POST',
      headers: this.headers(),
      body: JSON.stringify({ ...data, widget_key: this.widgetKey }),
    }).catch(() => {/* fire-and-forget */})
  }
}
