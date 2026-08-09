import type { WidgetAPI } from './api'
import type { KBArticle } from './types'

export class KBSuggest {
  private api: WidgetAPI
  private debounceTimer: ReturnType<typeof setTimeout> | null = null
  private container: HTMLElement | null = null
  private onSelect: ((article: KBArticle) => void) | null = null

  constructor(api: WidgetAPI) {
    this.api = api
  }

  attach(inputEl: HTMLInputElement, container: HTMLElement, onSelect: (article: KBArticle) => void): void {
    this.container = container
    this.onSelect = onSelect

    inputEl.addEventListener('input', () => {
      const q = inputEl.value.trim()
      if (q.length < 2) {
        this.hide()
        return
      }
      if (this.debounceTimer) clearTimeout(this.debounceTimer)
      this.debounceTimer = setTimeout(() => this.search(q), 300)
    })

    inputEl.addEventListener('blur', () => {
      // Delay to allow click events on results
      setTimeout(() => this.hide(), 200)
    })
  }

  private async search(q: string): Promise<void> {
    const articles = await this.api.searchKB(q)
    this.render(articles)
  }

  private render(articles: KBArticle[]): void {
    if (!this.container) return
    if (articles.length === 0) { this.hide(); return }

    this.container.innerHTML = ''
    this.container.style.display = 'block'

    const label = document.createElement('p')
    label.textContent = 'Articles that might help:'
    label.style.cssText = 'font-size:11px;color:#6b7280;padding:8px 12px 4px;margin:0;font-weight:500'
    this.container.appendChild(label)

    articles.slice(0, 4).forEach(article => {
      const item = document.createElement('button')
      item.type = 'button'
      item.textContent = article.title
      item.style.cssText = `
        display:block;width:100%;text-align:left;padding:8px 12px;
        font-size:12px;color:#111827;border:none;background:none;cursor:pointer;
        border-bottom:1px solid #f3f4f6;line-height:1.4;
      `
      item.addEventListener('mouseenter', () => { item.style.background = '#f9fafb' })
      item.addEventListener('mouseleave', () => { item.style.background = 'none' })
      item.addEventListener('click', () => {
        this.onSelect?.(article)
        this.hide()
      })
      this.container!.appendChild(item)
    })
  }

  hide(): void {
    if (this.container) {
      this.container.innerHTML = ''
      this.container.style.display = 'none'
    }
  }
}
