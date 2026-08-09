// Entry point re-export for library usage
export { WidgetAPI } from './api'
export { WidgetSocket } from './socket'
export { WidgetUI } from './ui/widget-ui'
export { injectStyles } from './styles'
export { loadSession, saveSession, clearSession } from './session'
export type { WidgetConfig, Session, Message, KBArticle } from './types'

// Auto-initialize when loaded as script tag
import './widget'
