import { formatMessageTime } from '@/utils/format'
import { CheckCheck } from 'lucide-react'

interface Props { message: any }

export default function MessageBubble({ message: m }: Props) {
  const isAgent = m.sender_type === 'agent'
  const isSystem = m.sender_type === 'system'

  if (isSystem) {
    return (
      <div className="flex justify-center my-2">
        <span className="text-xs text-gray-400 bg-gray-100 px-3 py-1 rounded-full">{m.content}</span>
      </div>
    )
  }

  return (
    <div className={`flex mb-2 ${isAgent ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[75%] ${isAgent ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
        <div
          className={`px-3 py-2 rounded-2xl text-sm leading-relaxed ${
            isAgent
              ? 'bg-indigo-600 text-white rounded-tr-sm'
              : 'bg-gray-100 text-gray-900 rounded-tl-sm'
          }`}
        >
          {m.content_type === 'html' ? (
            <div
              className="prose-content text-sm"
              dangerouslySetInnerHTML={{ __html: m.content }}
            />
          ) : (
            <p className="whitespace-pre-wrap">{m.content}</p>
          )}
        </div>
        <div className={`flex items-center gap-1 ${isAgent ? 'flex-row-reverse' : ''}`}>
          <span className="text-[11px] text-gray-400">{formatMessageTime(m.created_at)}</span>
          {isAgent && m.is_read && <CheckCheck size={12} className="text-indigo-400" />}
          {isAgent && !m.is_read && <CheckCheck size={12} className="text-gray-300" />}
        </div>
      </div>
    </div>
  )
}
