import type { Message, KBArticle } from '../types'
import { KBSuggest } from '../kb-suggest'
import type { WidgetAPI } from '../api'

export class WidgetUI {
  private panel: HTMLElement
  private btn: HTMLButtonElement
  private badge: HTMLElement
  private messagesEl: HTMLElement
  private inputEl: HTMLTextAreaElement
  private sendBtn: HTMLButtonElement
  private typingEl: HTMLElement
  private kbResultsEl: HTMLElement
  private emailGateEl: HTMLElement
  private isOpen = false
  private unreadCount = 0
  private kbSuggest: KBSuggest | null = null
  private typingTimer: ReturnType<typeof setTimeout> | null = null
  private onSendMessage: ((content: string) => void) | null = null
  private onTypingStart: (() => void) | null = null
  private onTypingStop: (() => void) | null = null
  private onEmailSubmit: ((email: string, name: string) => void) | null = null
  private conversationId: string | null = null

  constructor(greeting: string = 'Hi! How can we help?') {
    // Launcher button
    this.btn = document.createElement('button')
    this.btn.id = 'inbox-widget-btn'
    this.btn.setAttribute('aria-label', 'Open chat')
    this.btn.innerHTML = `
      <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
      </svg>
      <span id="inbox-widget-badge"></span>
    `
    this.badge = this.btn.querySelector('#inbox-widget-badge') as HTMLElement

    // Panel
    this.panel = document.createElement('div')
    this.panel.id = 'inbox-widget-panel'
    this.panel.setAttribute('role', 'dialog')
    this.panel.setAttribute('aria-label', 'Chat support')

    this.panel.innerHTML = `
      <div class="iw-header">
        <h3>Support</h3>
        <p>${greeting}</p>
      </div>
      <div class="iw-messages" id="iw-messages"></div>
      <div class="iw-typing" id="iw-typing">
        <span></span><span></span><span></span>
      </div>
      <div class="iw-kb-results" id="iw-kb-results"></div>
      <div class="iw-input-area" id="iw-input-area">
        <div class="iw-input-row">
          <textarea class="iw-input" id="iw-input" placeholder="Type a message..." rows="1"></textarea>
          <button class="iw-send-btn" id="iw-send-btn" disabled>
            <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
          </button>
        </div>
      </div>
      <div class="iw-email-gate" id="iw-email-gate" style="display:none;">
        <p>Enter your email to start chatting with our team:</p>
        <input type="email" id="iw-email-input" placeholder="your@email.com" />
        <input type="text" id="iw-name-input" placeholder="Your name (optional)" />
        <button id="iw-email-submit">Start chatting</button>
      </div>
    `

    this.messagesEl = this.panel.querySelector('#iw-messages') as HTMLElement
    this.inputEl = this.panel.querySelector('#iw-input') as HTMLTextAreaElement
    this.sendBtn = this.panel.querySelector('#iw-send-btn') as HTMLButtonElement
    this.typingEl = this.panel.querySelector('#iw-typing') as HTMLElement
    this.kbResultsEl = this.panel.querySelector('#iw-kb-results') as HTMLElement
    this.emailGateEl = this.panel.querySelector('#iw-email-gate') as HTMLElement

    // Append to body
    document.body.appendChild(this.btn)
    document.body.appendChild(this.panel)

    this.bindEvents()
  }

  attachKBSuggest(api: WidgetAPI): void {
    this.kbSuggest = new KBSuggest(api)
    this.kbSuggest.attach(this.inputEl, this.kbResultsEl, (article: KBArticle) => {
      this.showArticlePreview(article)
    })
  }

  private showArticlePreview(article: KBArticle): void {
    const preview = document.createElement('div')
    preview.style.cssText = `
      padding: 10px 12px;
      background: #eff6ff;
      border-top: 1px solid #bfdbfe;
      font-size: 12px;
      color: #1e40af;
    `
    preview.textContent = `📖 Related article: ${article.title}`
    this.messagesEl.appendChild(preview)
    this.scrollToBottom()
  }

  private bindEvents(): void {
    this.btn.addEventListener('click', () => this.toggle())

    this.inputEl.addEventListener('input', () => {
      this.sendBtn.disabled = !this.inputEl.value.trim()
      // Auto-resize
      this.inputEl.style.height = 'auto'
      this.inputEl.style.height = Math.min(this.inputEl.scrollHeight, 100) + 'px'
      // Typing events
      this.onTypingStart?.()
      if (this.typingTimer) clearTimeout(this.typingTimer)
      this.typingTimer = setTimeout(() => this.onTypingStop?.(), 2000)
    })

    this.inputEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        this.submit()
      }
    })

    this.sendBtn.addEventListener('click', () => this.submit())

    const emailSubmit = this.panel.querySelector('#iw-email-submit') as HTMLButtonElement
    emailSubmit?.addEventListener('click', () => {
      const email = (this.panel.querySelector('#iw-email-input') as HTMLInputElement).value.trim()
      const name = (this.panel.querySelector('#iw-name-input') as HTMLInputElement).value.trim()
      if (email) this.onEmailSubmit?.(email, name)
    })

    // Close on Escape
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isOpen) this.close()
    })
  }

  private submit(): void {
    const content = this.inputEl.value.trim()
    if (!content) return
    this.inputEl.value = ''
    this.inputEl.style.height = 'auto'
    this.sendBtn.disabled = true
    this.kbSuggest?.hide()
    if (this.typingTimer) clearTimeout(this.typingTimer)
    this.onTypingStop?.()
    this.onSendMessage?.(content)
  }

  toggle(): void {
    this.isOpen ? this.close() : this.open()
  }

  open(): void {
    this.isOpen = true
    this.panel.classList.add('open')
    this.btn.innerHTML = `
      <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
      </svg>
      <span id="inbox-widget-badge"></span>
    `
    this.badge = this.btn.querySelector('#inbox-widget-badge') as HTMLElement
    this.clearUnread()
    this.inputEl.focus()
  }

  close(): void {
    this.isOpen = false
    this.panel.classList.remove('open')
    this.btn.innerHTML = `
      <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
      </svg>
      <span id="inbox-widget-badge"></span>
    `
    this.badge = this.btn.querySelector('#inbox-widget-badge') as HTMLElement
    this.updateBadge()
  }

  showEmailGate(): void {
    const inputArea = this.panel.querySelector('#iw-input-area') as HTMLElement
    if (inputArea) inputArea.style.display = 'none'
    this.emailGateEl.style.display = 'flex'
    this.emailGateEl.style.flexDirection = 'column'
  }

  hideEmailGate(): void {
    this.emailGateEl.style.display = 'none'
    const inputArea = this.panel.querySelector('#iw-input-area') as HTMLElement
    if (inputArea) inputArea.style.display = 'flex'
  }

  addMessage(msg: Message): void {
    const el = document.createElement('div')
    el.className = `iw-message ${msg.sender_type}`

    if (msg.sender_type === 'agent' && msg.agent_name) {
      const sender = document.createElement('div')
      sender.className = 'iw-sender'
      sender.textContent = msg.agent_name
      el.appendChild(sender)
    }

    const content = document.createElement('div')
    // Sanitize — only render text, strip HTML tags
    content.textContent = msg.content
    el.appendChild(content)

    this.messagesEl.appendChild(el)
    this.scrollToBottom()

    if (msg.sender_type === 'agent' && !this.isOpen) {
      this.incrementUnread()
    }
  }

  setMessages(messages: Message[]): void {
    this.messagesEl.innerHTML = ''
    if (messages.length === 0) {
      const empty = document.createElement('div')
      empty.className = 'iw-empty'
      empty.innerHTML = `<span>👋</span><span>Send us a message to get started</span>`
      this.messagesEl.appendChild(empty)
      return
    }
    messages.forEach(m => this.addMessage(m))
  }

  showTyping(): void { this.typingEl.classList.add('visible') }
  hideTyping(): void { this.typingEl.classList.remove('visible') }

  private scrollToBottom(): void {
    requestAnimationFrame(() => {
      this.messagesEl.scrollTop = this.messagesEl.scrollHeight
    })
  }

  private incrementUnread(): void {
    this.unreadCount++
    this.updateBadge()
  }

  private clearUnread(): void {
    this.unreadCount = 0
    this.updateBadge()
  }

  private updateBadge(): void {
    if (this.unreadCount > 0 && !this.isOpen) {
      this.badge.textContent = String(this.unreadCount)
      this.badge.style.display = 'block'
    } else {
      this.badge.style.display = 'none'
    }
  }

  onSend(cb: (content: string) => void): void { this.onSendMessage = cb }
  onTypingStarted(cb: () => void): void { this.onTypingStart = cb }
  onTypingStopped(cb: () => void): void { this.onTypingStop = cb }
  onEmailGateSubmit(cb: (email: string, name: string) => void): void { this.onEmailSubmit = cb }
}
