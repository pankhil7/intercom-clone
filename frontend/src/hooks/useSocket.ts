import { useEffect, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '@/store/auth.store'
import { useConversationStore } from '@/store/conversation.store'
import { useUIStore } from '@/store/ui.store'
import { connectSocket, disconnectSocket, getSocket } from '@/socket/socket'

export function useSocket() {
  const { isAuthenticated } = useAuthStore()
  const { setTyping } = useConversationStore()
  const { addToast } = useUIStore()
  const queryClient = useQueryClient()
  const initialized = useRef(false)

  useEffect(() => {
    if (!isAuthenticated || initialized.current) return
    const token = localStorage.getItem('access_token')
    if (!token) return

    initialized.current = true
    const socket = connectSocket(token)

    socket.on('connect', () => {
      console.log('[Socket] Connected')
    })

    socket.on('message:created', (data: any) => {
      // Invalidate conversation queries so list + detail update
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
      queryClient.invalidateQueries({ queryKey: ['messages', data.conversation_id] })
      queryClient.invalidateQueries({ queryKey: ['conversation', data.conversation_id] })

      // Show toast for new messages in other conversations
      const { activeConversationId } = useConversationStore.getState()
      if (data.conversation_id !== activeConversationId && data.message?.sender_type === 'contact') {
        addToast({ title: 'New message', description: data.message?.content?.substring(0, 60) })
      }
    })

    socket.on('conversation:created', () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    })

    socket.on('conversation:updated', (data: any) => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
      queryClient.invalidateQueries({ queryKey: ['conversation', data.conversation_id] })
    })

    socket.on('typing:start', (data: any) => {
      if (data.sender_type === 'contact') setTyping(data.conversation_id, true)
    })

    socket.on('typing:stop', (data: any) => {
      setTyping(data.conversation_id, false)
    })

    socket.on('sla:breach', (data: any) => {
      addToast({
        title: 'SLA Breach',
        description: `Conversation ${data.conversation_id.slice(0, 8)} has breached SLA`,
        variant: 'destructive',
      })
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    })

    socket.on('ai:draft_ready', () => {
      queryClient.invalidateQueries({ queryKey: ['ai-draft'] })
    })

    socket.on('disconnect', () => {
      console.log('[Socket] Disconnected')
      initialized.current = false
    })

    return () => {
      disconnectSocket()
      initialized.current = false
    }
  }, [isAuthenticated, queryClient, setTyping, addToast])

  return getSocket()
}
