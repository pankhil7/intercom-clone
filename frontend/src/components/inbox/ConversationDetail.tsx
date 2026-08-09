import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { conversationsApi } from '@/api/conversations'
import { useState } from 'react'
import { CheckCircle, RotateCcw, UserPlus, Clock, Sparkles, Mail, MessageSquare } from 'lucide-react'
import MessageThread from './MessageThread'
import ReplyBox from './ReplyBox'
import SummaryPanel from '@/components/ai/SummaryPanel'
import DraftSuggestion from '@/components/ai/DraftSuggestion'
import AssigneeSelector from './AssigneeSelector'
import { timeAgo } from '@/utils/format'
import { useToast } from '@/components/ui/toaster'

interface Props { conversationId: string }

export default function ConversationDetail({ conversationId }: Props) {
  const qc = useQueryClient()
  const { toast } = useToast()
  const [showSummary, setShowSummary] = useState(false)
  const [showAssign, setShowAssign] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['conversation', conversationId],
    queryFn: () => conversationsApi.get(conversationId),
    enabled: !!conversationId,
  })

  const conv = data?.conversation || data
  const contact = data?.contact || conv?.contact
  const messages = data?.messages || []

  const resolveMut = useMutation({
    mutationFn: () => conversationsApi.resolve(conversationId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['conversations'] })
      qc.invalidateQueries({ queryKey: ['conversation', conversationId] })
      toast({ title: 'Conversation resolved' })
    },
  })

  const reopenMut = useMutation({
    mutationFn: () => conversationsApi.reopen(conversationId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['conversations'] })
      qc.invalidateQueries({ queryKey: ['conversation', conversationId] })
    },
  })

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full" />
      </div>
    )
  }

  if (!conv) return <div className="flex-1 flex items-center justify-center text-gray-400">Not found</div>

  const contactName = contact?.name || contact?.email || 'Unknown'
  const ChannelIcon = conv.channel === 'email' ? Mail : MessageSquare

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Top bar */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-200 shrink-0">
        <ChannelIcon size={16} className="text-gray-400 shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-gray-900 truncate">{contactName}</div>
          {conv.subject && <div className="text-xs text-gray-500 truncate">{conv.subject}</div>}
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {/* Status badge */}
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
            conv.status === 'open' ? 'bg-green-100 text-green-700' :
            conv.status === 'resolved' ? 'bg-gray-100 text-gray-600' :
            'bg-yellow-100 text-yellow-700'
          }`}>
            {conv.status}
          </span>

          {/* SLA breach */}
          {conv.sla_breach && (
            <span className="flex items-center gap-1 text-xs bg-red-50 text-red-600 px-2 py-0.5 rounded-full">
              <Clock size={11} /> SLA Breach
            </span>
          )}

          {/* AI Summary */}
          <button
            onClick={() => setShowSummary(s => !s)}
            className="flex items-center gap-1 text-xs px-2 py-1 rounded-lg border border-gray-200 hover:bg-gray-50 text-gray-600"
          >
            <Sparkles size={12} className="text-indigo-500" /> Summary
          </button>

          {/* Assign */}
          <div className="relative">
            <button
              onClick={() => setShowAssign(s => !s)}
              className="flex items-center gap-1 text-xs px-2 py-1 rounded-lg border border-gray-200 hover:bg-gray-50 text-gray-600"
            >
              <UserPlus size={12} />
              {conv.assignee ? conv.assignee.full_name.split(' ')[0] : 'Assign'}
            </button>
            {showAssign && (
              <AssigneeSelector
                conversationId={conversationId}
                currentAssigneeId={conv.assigned_to}
                onClose={() => setShowAssign(false)}
              />
            )}
          </div>

          {/* Resolve/Reopen */}
          {conv.status !== 'resolved' ? (
            <button
              onClick={() => resolveMut.mutate()}
              disabled={resolveMut.isPending}
              className="flex items-center gap-1 text-xs px-3 py-1.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
            >
              <CheckCircle size={12} /> Resolve
            </button>
          ) : (
            <button
              onClick={() => reopenMut.mutate()}
              disabled={reopenMut.isPending}
              className="flex items-center gap-1 text-xs px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
            >
              <RotateCcw size={12} /> Reopen
            </button>
          )}
        </div>
      </div>

      {/* AI Summary */}
      {showSummary && <SummaryPanel conversationId={conversationId} />}

      {/* AI Draft */}
      <DraftSuggestion conversationId={conversationId} />

      {/* Messages */}
      <MessageThread conversationId={conversationId} initialMessages={messages} />

      {/* Reply box */}
      {conv.status !== 'resolved' && (
        <ReplyBox conversationId={conversationId} channel={conv.channel} />
      )}
      {conv.status === 'resolved' && (
        <div className="px-4 py-3 bg-gray-50 border-t border-gray-200 text-center text-sm text-gray-500">
          Conversation resolved · <button onClick={() => reopenMut.mutate()} className="text-indigo-600 hover:underline">Reopen</button>
        </div>
      )}
    </div>
  )
}
