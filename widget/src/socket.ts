import { io, Socket } from 'socket.io-client'

export class WidgetSocket {
  private socket: Socket | null = null
  private token: string | null = null
  private socketUrl: string
  private conversationId: string | null = null
  private onMessageCallback: ((msg: any) => void) | null = null
  private onTypingCallback: ((isTyping: boolean) => void) | null = null
  private onAgentJoinCallback: ((agent: any) => void) | null = null

  constructor(socketUrl: string) {
    this.socketUrl = socketUrl
  }

  connect(token: string): void {
    this.token = token
    this.socket = io(this.socketUrl, {
      path: '/socket.io',
      namespace: '/widget',
      auth: { token },
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 2000,
      reconnectionAttempts: 10,
    })

    this.socket.on('connect', () => {
      if (this.conversationId) {
        this.socket?.emit('join:conversation', { conversation_id: this.conversationId })
      }
    })

    this.socket.on('message:created', (data: any) => {
      if (data.sender_type === 'agent') {
        this.onMessageCallback?.(data)
      }
    })

    this.socket.on('typing:start', (data: any) => {
      if (data.sender_type === 'agent') this.onTypingCallback?.(true)
    })

    this.socket.on('typing:stop', (data: any) => {
      if (data.sender_type === 'agent') this.onTypingCallback?.(false)
    })

    this.socket.on('conversation:agent_joined', (data: any) => {
      this.onAgentJoinCallback?.(data)
    })

    this.socket.on('connect_error', (err) => {
      console.warn('[InboxWidget] Socket connect error:', err.message)
    })
  }

  joinConversation(conversationId: string): void {
    this.conversationId = conversationId
    if (this.socket?.connected) {
      this.socket.emit('join:conversation', { conversation_id: conversationId })
    }
  }

  sendTypingStart(conversationId: string): void {
    this.socket?.emit('typing:start', { conversation_id: conversationId })
  }

  sendTypingStop(conversationId: string): void {
    this.socket?.emit('typing:stop', { conversation_id: conversationId })
  }

  onMessage(cb: (msg: any) => void): void { this.onMessageCallback = cb }
  onTyping(cb: (isTyping: boolean) => void): void { this.onTypingCallback = cb }
  onAgentJoin(cb: (agent: any) => void): void { this.onAgentJoinCallback = cb }

  disconnect(): void {
    this.socket?.disconnect()
    this.socket = null
  }
}
