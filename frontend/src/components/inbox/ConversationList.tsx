import { useQuery } from '@tanstack/react-query'
import { conversationsApi } from '@/api/conversations'
import { useConversationStore } from '@/store/conversation.store'
import ConversationItem from './ConversationItem'
import { MessageSquare, Mail, RefreshCw } from 'lucide-react'

interface Props {
  activeId?: string
  onSelect: (id: string) => void
}

const STATUS_TABS = [
  { key: 'open', label: 'Open' },
  { key: 'snoozed', label: 'Snoozed' },
  { key: 'resolved', label: 'Resolved' },
]

export default function ConversationList({ activeId, onSelect }: Props) {
  const { filters, setFilters } = useConversationStore()

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['conversations', filters],
    queryFn: () => conversationsApi.list({
      status: filters.status || undefined,
      channel: filters.channel || undefined,
      assigned_to: filters.assigned_to || undefined,
      limit: 50,
    }),
    refetchInterval: 30_000,
  })

  const conversations = data?.conversations || []

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-100">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold text-gray-900">Inbox</h2>
          <button onClick={() => refetch()} className="text-gray-400 hover:text-gray-600 p-1 rounded">
            <RefreshCw size={14} />
          </button>
        </div>

        {/* Status tabs */}
        <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
          {STATUS_TABS.map(tab => (
            <button
              key={tab.key}
              onClick={() => setFilters({ status: tab.key })}
              className={`flex-1 text-xs py-1 rounded-md font-medium transition-colors ${
                filters.status === tab.key
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Channel filter */}
        <div className="flex gap-2 mt-2">
          {[
            { key: '', label: 'All', icon: null },
            { key: 'chat', label: 'Chat', icon: <MessageSquare size={12} /> },
            { key: 'email', label: 'Email', icon: <Mail size={12} /> },
          ].map(({ key, label, icon }) => (
            <button
              key={key}
              onClick={() => setFilters({ channel: key })}
              className={`flex items-center gap-1 text-xs px-2 py-1 rounded-full border transition-colors ${
                filters.channel === key
                  ? 'bg-indigo-50 border-indigo-200 text-indigo-700'
                  : 'border-gray-200 text-gray-500 hover:border-gray-300'
              }`}
            >
              {icon}{label}
            </button>
          ))}
        </div>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="p-4 space-y-3">
            {[1, 2, 3, 4, 5].map(i => (
              <div key={i} className="animate-pulse flex gap-3">
                <div className="w-9 h-9 bg-gray-200 rounded-full shrink-0" />
                <div className="flex-1 space-y-2">
                  <div className="h-3 bg-gray-200 rounded w-3/4" />
                  <div className="h-3 bg-gray-200 rounded w-1/2" />
                </div>
              </div>
            ))}
          </div>
        ) : conversations.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-40 text-gray-400">
            <MessageSquare size={32} className="mb-2 opacity-30" />
            <p className="text-sm">No conversations</p>
          </div>
        ) : (
          conversations.map((conv: any) => (
            <ConversationItem
              key={conv.id}
              conversation={conv}
              isActive={conv.id === activeId}
              onClick={() => onSelect(conv.id)}
            />
          ))
        )}
      </div>
    </div>
  )
}
