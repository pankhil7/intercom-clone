import { injectStyles } from './styles'
import { WidgetUI } from './ui/widget-ui'
import { WidgetAPI } from './api'
import { WidgetSocket } from './socket'
import { PageTracker } from './page-tracker'
import { loadSession, saveSession, updateSessionConversation } from './session'
import type { WidgetConfig } from './types'

;(function () {
  // Guard against double-initialization
  if ((window as any).__inboxWidgetLoaded) return
  ;(window as any).__inboxWidgetLoaded = true

  const config: WidgetConfig = (window as any).InboxWidget || {}

  if (!config.widgetKey) {
    console.warn('[InboxWidget] No widgetKey configured. Set window.InboxWidget = { widgetKey: "..." }')
    return
  }

  // Determine base URLs
  const apiBase = config.apiBase || (window as any).INBOX_API_BASE || 'https://api.yourdomain.com/api/v1'
  const socketUrl = config.socketUrl || (window as any).INBOX_SOCKET_URL || 'https://api.yourdomain.com'

  // Apply styles
  injectStyles(config.primaryColor)

  // Init core services
  const api = new WidgetAPI({ ...config, apiBase })
  const socket = new WidgetSocket(socketUrl)
  const ui = new WidgetUI(config.greeting)

  let conversationId: string | null = null
  let contactId: string | null = null
  let isSessionReady = false

  async function initSession(email?: string, name?: string): Promise<void> {
    let session = loadSession()

    if (!session) {
      session = await api.initSession({ email, name })
      saveSession(session)
    } else {
      api.setToken(session.token)
    }

    contactId = session.contactId
    conversationId = session.conversationId || null

    if (!conversationId) {
      conversationId = await api.getOrCreateConversation(contactId)
      updateSessionConversation(conversationId)
    }

    // Connect socket and join room
    socket.connect(session.token)
    socket.joinConversation(conversationId)

    // Load message history
    const messages = await api.getMessages(conversationId)
    ui.setMessages(messages)

    isSessionReady = true
  }

  // Wire up socket events
  socket.onMessage((msg) => {
    ui.addMessage(msg)
  })

  socket.onTyping((isTyping) => {
    isTyping ? ui.showTyping() : ui.hideTyping()
  })

  // Wire up UI events
  ui.onSend(async (content) => {
    if (!isSessionReady || !conversationId) return
    ui.addMessage({ id: 'tmp', content, sender_type: 'contact', created_at: new Date().toISOString() })
    try {
      await api.sendMessage(conversationId, content)
    } catch (err) {
      console.error('[InboxWidget] Failed to send message', err)
    }
  })

  ui.onTypingStarted(() => {
    if (conversationId) socket.sendTypingStart(conversationId)
  })

  ui.onTypingStopped(() => {
    if (conversationId) socket.sendTypingStop(conversationId)
  })

  ui.onEmailGateSubmit(async (email, name) => {
    ui.hideEmailGate()
    try {
      await initSession(email, name)
      ui.attachKBSuggest(api)
    } catch (err) {
      console.error('[InboxWidget] Session init failed', err)
    }
  })

  // Check existing session on load
  const existingSession = loadSession()
  if (existingSession) {
    // Restore session silently
    initSession().then(() => {
      ui.attachKBSuggest(api)
    }).catch(() => {
      // Session expired or invalid — show email gate next open
    })
  } else {
    // Show email gate when user opens the widget
    const originalToggle = (ui as any).toggle.bind(ui)
    let gateShown = false
    ;(ui as any).toggle = function () {
      if (!gateShown && !isSessionReady) {
        ;(ui as any).open.call(ui)
        ui.showEmailGate()
        gateShown = true
      } else {
        originalToggle()
      }
    }
  }

  // Start page tracker (after session init)
  const tracker = new PageTracker(api)
  if (existingSession) {
    tracker.start()
  } else {
    const origEmailSubmit = ui.onEmailGateSubmit.bind(ui)
    const _orig = origEmailSubmit
    ui.onEmailGateSubmit(async (email, name) => {
      ui.hideEmailGate()
      try {
        await initSession(email, name)
        ui.attachKBSuggest(api)
        tracker.start()
      } catch (err) {
        console.error('[InboxWidget] Session init failed', err)
      }
    })
  }

  // Expose API for programmatic control
  ;(window as any).InboxWidgetAPI = {
    open: () => ui.open(),
    close: () => ui.close(),
    identify: (data: { email: string; name?: string }) => initSession(data.email, data.name),
    destroy: () => {
      socket.disconnect()
      document.getElementById('inbox-widget-btn')?.remove()
      document.getElementById('inbox-widget-panel')?.remove()
      document.getElementById('inbox-widget-styles')?.remove()
      ;(window as any).__inboxWidgetLoaded = false
    },
  }
})()
