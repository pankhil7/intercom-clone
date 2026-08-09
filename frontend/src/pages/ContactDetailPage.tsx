import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { contactsApi } from '@/api/contacts'
import { timeAgo, formatMessageTime, initials } from '@/utils/format'
import { ArrowLeft, Mail, Globe, MessageSquare, Clock } from 'lucide-react'

export default function ContactDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const { data: contactData } = useQuery({
    queryKey: ['contact', id],
    queryFn: () => contactsApi.get(id!),
    enabled: !!id,
  })

  const { data: timelineData } = useQuery({
    queryKey: ['contact-timeline', id],
    queryFn: () => contactsApi.getTimeline(id!),
    enabled: !!id,
  })

  const { data: convsData } = useQuery({
    queryKey: ['contact-conversations', id],
    queryFn: () => contactsApi.getConversations(id!),
    enabled: !!id,
  })

  const contact = contactData?.contact || contactData
  const timeline: any[] = timelineData?.events || []
  const conversations: any[] = convsData?.conversations || []

  if (!contact) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full" />
      </div>
    )
  }

  return (
    <div className="h-full overflow-y-auto bg-white">
      <div className="max-w-4xl mx-auto px-6 py-6">
        {/* Back */}
        <button onClick={() => navigate('/contacts')} className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 mb-6">
          <ArrowLeft size={16} /> Back to contacts
        </button>

        <div className="grid grid-cols-3 gap-6">
          {/* Profile */}
          <div className="col-span-1">
            <div className="bg-white border border-gray-200 rounded-xl p-6">
              <div className="text-center mb-4">
                <div className="w-16 h-16 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 text-2xl font-semibold mx-auto mb-3">
                  {initials(contact.name || contact.email)}
                </div>
                <h2 className="font-semibold text-gray-900">{contact.name || 'Unknown'}</h2>
                {contact.email && <p className="text-sm text-gray-500 mt-0.5">{contact.email}</p>}
              </div>

              <div className="space-y-3 text-sm">
                {contact.email && (
                  <div className="flex items-center gap-2 text-gray-600">
                    <Mail size={14} className="text-gray-400" /> {contact.email}
                  </div>
                )}
                {contact.timezone && (
                  <div className="flex items-center gap-2 text-gray-600">
                    <Clock size={14} className="text-gray-400" /> {contact.timezone}
                  </div>
                )}
                {contact.browser && (
                  <div className="flex items-center gap-2 text-gray-600">
                    <Globe size={14} className="text-gray-400" /> {contact.browser} · {contact.os}
                  </div>
                )}
              </div>

              <div className="mt-4 pt-4 border-t border-gray-100 space-y-1 text-xs text-gray-500">
                <div>First seen: {contact.first_seen_at ? timeAgo(contact.first_seen_at) : '—'}</div>
                <div>Last seen: {contact.last_seen_at ? timeAgo(contact.last_seen_at) : '—'}</div>
              </div>

              {Object.keys(contact.custom_attributes || {}).length > 0 && (
                <div className="mt-4 pt-4 border-t border-gray-100">
                  <p className="text-xs font-medium text-gray-500 mb-2">Custom attributes</p>
                  {Object.entries(contact.custom_attributes).map(([k, v]) => (
                    <div key={k} className="flex justify-between text-xs py-1">
                      <span className="text-gray-500">{k}</span>
                      <span className="text-gray-700 font-medium">{String(v)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Timeline + Conversations */}
          <div className="col-span-2 space-y-6">
            {/* Conversations */}
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                <MessageSquare size={14} /> Conversations ({conversations.length})
              </h3>
              <div className="space-y-2">
                {conversations.map((conv: any) => (
                  <button
                    key={conv.id}
                    onClick={() => navigate(`/inbox/${conv.id}`)}
                    className="w-full text-left bg-white border border-gray-200 rounded-lg px-4 py-3 hover:border-indigo-300 hover:bg-indigo-50/30 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-900">{conv.subject || `${conv.channel} conversation`}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        conv.status === 'open' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                      }`}>{conv.status}</span>
                    </div>
                    <p className="text-xs text-gray-400 mt-1">{timeAgo(conv.created_at)}</p>
                  </button>
                ))}
                {conversations.length === 0 && (
                  <p className="text-sm text-gray-400">No conversations yet</p>
                )}
              </div>
            </div>

            {/* Timeline */}
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Activity Timeline</h3>
              <div className="space-y-2">
                {timeline.map((event: any, i: number) => (
                  <div key={i} className="flex gap-3 items-start">
                    <div className="w-2 h-2 rounded-full bg-gray-300 mt-2 shrink-0" />
                    <div className="flex-1 bg-gray-50 rounded-lg px-3 py-2">
                      {event.type === 'page_view' ? (
                        <div>
                          <p className="text-xs text-gray-700 font-medium truncate">{event.data.title || event.data.url}</p>
                          <p className="text-[11px] text-gray-400 truncate">{event.data.url}</p>
                        </div>
                      ) : (
                        <p className="text-xs text-gray-700">{event.type}: {event.data.subject || event.data.channel}</p>
                      )}
                      <p className="text-[11px] text-gray-400 mt-0.5">{formatMessageTime(event.created_at)}</p>
                    </div>
                  </div>
                ))}
                {timeline.length === 0 && (
                  <p className="text-sm text-gray-400">No activity recorded yet</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
