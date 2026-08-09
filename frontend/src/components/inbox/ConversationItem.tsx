import { MessageSquare, Mail, Clock } from 'lucide-react'
import { timeAgo, stripHtml, initials } from '@/utils/format'

interface Props {
  conversation: any
  isActive: boolean
  onClick: () => void
}

export default function ConversationItem({ conversation: c, isActive, onClick }: Props) {
  const name = c.contact?.name || c.contact?.email || 'Unknown'
  const lastMsg = c.last_message ? stripHtml(c.last_message.content).slice(0, 60) : 'No messages'
  const ChannelIcon = c.channel === 'email' ? Mail : MessageSquare

  return (
    <button
      onClick={onClick}
      className={`w-full text-left px-4 py-3 border-b border-gray-50 hover:bg-gray-50 transition-colors ${
        isActive ? 'bg-indigo-50 border-l-2 border-l-indigo-500' : ''
      } ${c.sla_breach ? 'border-l-2 border-l-red-400' : ''}`}
    >
      <div className="flex gap-3 items-start">
        {/* Avatar */}
        <div className={`w-9 h-9 rounded-full flex items-center justify-center text-white text-xs font-medium shrink-0 ${
          isActive ? 'bg-indigo-500' : 'bg-gray-400'
        }`}>
          {initials(name)}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <span className={`text-sm font-medium truncate ${isActive ? 'text-indigo-700' : 'text-gray-900'}`}>
              {name}
            </span>
            <div className="flex items-center gap-1 shrink-0">
              {c.sla_breach && <Clock size={11} className="text-red-500" />}
              <span className="text-[11px] text-gray-400">
                {c.updated_at ? timeAgo(c.updated_at) : ''}
              </span>
            </div>
          </div>

          <div className="flex items-center justify-between gap-2 mt-0.5">
            <span className="text-xs text-gray-500 truncate flex-1">{lastMsg}</span>
            <div className="flex items-center gap-1 shrink-0">
              <ChannelIcon size={11} className="text-gray-400" />
              {c.unread_count > 0 && (
                <span className="bg-indigo-600 text-white text-[10px] rounded-full w-4 h-4 flex items-center justify-center font-medium">
                  {c.unread_count > 9 ? '9+' : c.unread_count}
                </span>
              )}
            </div>
          </div>

          {c.assignee && (
            <div className="text-[11px] text-gray-400 mt-0.5 truncate">
              → {c.assignee.full_name}
            </div>
          )}
        </div>
      </div>
    </button>
  )
}
