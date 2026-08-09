import { useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { conversationsApi } from '@/api/conversations'
import MessageBubble from './MessageBubble'
import TypingIndicator from './TypingIndicator'
import { useConversationStore } from '@/store/conversation.store'
import { formatDateGroup } from '@/utils/format'

interface Props {
  conversationId: string
  initialMessages?: any[]
}

export default function MessageThread({ conversationId, initialMessages = [] }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)
  const { typingConversations } = useConversationStore()
  const isTyping = typingConversations.has(conversationId)

  const { data } = useQuery({
    queryKey: ['messages', conversationId],
    queryFn: () => conversationsApi.getMessages(conversationId),
    initialData: initialMessages.length ? { messages: initialMessages } : undefined,
    refetchInterval: false,
  })

  const messages: any[] = data?.messages || initialMessages

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length, isTyping])

  // Group messages by day
  const groups: { date: string; msgs: any[] }[] = []
  messages.forEach(msg => {
    const date = formatDateGroup(msg.created_at)
    const last = groups[groups.length - 1]
    if (last && last.date === date) { last.msgs.push(msg) }
    else { groups.push({ date, msgs: [msg] }) }
  })

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4 space-y-1">
      {groups.map(group => (
        <div key={group.date}>
          <div className="flex items-center gap-3 my-4">
            <div className="flex-1 h-px bg-gray-100" />
            <span className="text-xs text-gray-400 font-medium">{group.date}</span>
            <div className="flex-1 h-px bg-gray-100" />
          </div>
          {group.msgs.map((msg: any) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
        </div>
      ))}

      {isTyping && <TypingIndicator />}
      <div ref={bottomRef} />
    </div>
  )
}
