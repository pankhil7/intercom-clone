import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { conversationsApi } from '@/api/conversations'
import { contactsApi } from '@/api/contacts'
import { X, MessageSquare, Mail, Search } from 'lucide-react'

interface Props {
  onClose: () => void
  onCreated: (id: string) => void
}

export default function NewConversationModal({ onClose, onCreated }: Props) {
  const qc = useQueryClient()
  const [channel, setChannel] = useState<'chat' | 'email'>('chat')
  const [subject, setSubject] = useState('')
  const [contactSearch, setContactSearch] = useState('')
  const [selectedContact, setSelectedContact] = useState<{ id: string; name: string; email: string } | null>(null)
  const [showDropdown, setShowDropdown] = useState(false)

  const { data: contactsData } = useQuery({
    queryKey: ['contacts-search', contactSearch],
    queryFn: () => contactsApi.list({ search: contactSearch, limit: 10 }),
    enabled: contactSearch.length > 0,
  })

  const contacts: any[] = Array.isArray(contactsData) ? contactsData : []

  const mutation = useMutation({
    mutationFn: (payload: any) => conversationsApi.create(payload),
    onSuccess: (conv: any) => {
      qc.invalidateQueries({ queryKey: ['conversations'] })
      onCreated(conv.id)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    mutation.mutate({
      contact_id: selectedContact?.id || null,
      channel,
      subject: subject.trim() || null,
    })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div
        className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 p-6"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-semibold text-gray-900">New Conversation</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 p-1 rounded">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Channel */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Channel</label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setChannel('chat')}
                className={`flex items-center gap-2 flex-1 py-2 px-3 rounded-lg border text-sm font-medium transition-colors ${
                  channel === 'chat'
                    ? 'bg-indigo-50 border-indigo-300 text-indigo-700'
                    : 'border-gray-200 text-gray-500 hover:border-gray-300'
                }`}
              >
                <MessageSquare size={14} /> Chat
              </button>
              <button
                type="button"
                onClick={() => setChannel('email')}
                className={`flex items-center gap-2 flex-1 py-2 px-3 rounded-lg border text-sm font-medium transition-colors ${
                  channel === 'email'
                    ? 'bg-indigo-50 border-indigo-300 text-indigo-700'
                    : 'border-gray-200 text-gray-500 hover:border-gray-300'
                }`}
              >
                <Mail size={14} /> Email
              </button>
            </div>
          </div>

          {/* Contact search */}
          <div className="relative">
            <label className="block text-sm font-medium text-gray-700 mb-1">Contact</label>
            {selectedContact ? (
              <div className="flex items-center justify-between px-3 py-2 border border-gray-300 rounded-lg bg-gray-50">
                <div>
                  <span className="text-sm font-medium text-gray-900">{selectedContact.name || selectedContact.email}</span>
                  {selectedContact.name && (
                    <span className="text-xs text-gray-500 ml-2">{selectedContact.email}</span>
                  )}
                </div>
                <button
                  type="button"
                  onClick={() => { setSelectedContact(null); setContactSearch('') }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X size={14} />
                </button>
              </div>
            ) : (
              <div className="relative">
                <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  value={contactSearch}
                  onChange={e => { setContactSearch(e.target.value); setShowDropdown(true) }}
                  onFocus={() => setShowDropdown(true)}
                  placeholder="Search by name or email…"
                  className="w-full pl-8 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
                />
                {showDropdown && contacts.length > 0 && (
                  <div className="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                    {contacts.map((c: any) => (
                      <button
                        key={c.id}
                        type="button"
                        onClick={() => {
                          setSelectedContact({ id: c.id, name: c.name, email: c.email })
                          setShowDropdown(false)
                          setContactSearch('')
                        }}
                        className="w-full text-left px-3 py-2 hover:bg-gray-50 text-sm"
                      >
                        <span className="font-medium text-gray-900">{c.name || c.email}</span>
                        {c.name && <span className="text-gray-400 ml-2 text-xs">{c.email}</span>}
                      </button>
                    ))}
                  </div>
                )}
                {showDropdown && contactSearch.length > 0 && contacts.length === 0 && (
                  <div className="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-sm px-3 py-2 text-sm text-gray-400">
                    No contacts found
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Subject */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Subject <span className="text-gray-400 font-normal">(optional)</span>
            </label>
            <input
              type="text"
              value={subject}
              onChange={e => setSubject(e.target.value)}
              placeholder="e.g. Issue with billing"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
            />
          </div>

          {/* Error */}
          {mutation.isError && (
            <p className="text-sm text-red-600">Failed to create conversation. Please try again.</p>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={mutation.isPending}
              className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {mutation.isPending ? 'Creating…' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
