import type { WidgetAPI } from './api'

export class PageTracker {
  private api: WidgetAPI
  private debounceTimer: ReturnType<typeof setTimeout> | null = null

  constructor(api: WidgetAPI) {
    this.api = api
  }

  start(): void {
    // Track initial page
    this.track()

    // Track on history API navigation (SPA support)
    const origPushState = history.pushState.bind(history)
    const origReplaceState = history.replaceState.bind(history)

    history.pushState = (...args) => {
      origPushState(...args)
      this.trackDebounced()
    }

    history.replaceState = (...args) => {
      origReplaceState(...args)
      this.trackDebounced()
    }

    window.addEventListener('popstate', () => this.trackDebounced())
    window.addEventListener('hashchange', () => this.trackDebounced())
  }

  private trackDebounced(): void {
    if (this.debounceTimer) clearTimeout(this.debounceTimer)
    this.debounceTimer = setTimeout(() => this.track(), 500)
  }

  private track(): void {
    this.api.trackPageView({
      url: window.location.href,
      title: document.title,
    })
  }
}
