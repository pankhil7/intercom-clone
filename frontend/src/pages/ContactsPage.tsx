import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { contactsApi } from '@/api/contacts'
import { Search, Users, Plus, X } from 'lucide-react'
import { timeAgo, initials } from '@/utils/format'

function NewContactModal({ onClose, onCreated }: { onClose: () => void; onCreated: (id: string) => void }) {
  const qc = useQueryClient()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')

  const mutation = useMutation({
    mutationFn: () => contactsApi.create({ name: name.trim() || undefined, email: email.trim() || undefined, phone: phone.trim() || undefined }),
    onSuccess: (contact: any) => {
      qc.invalidateQueries({ queryKey: ['contacts'] })
      onCreated(contact.id)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim() && !email.trim()) return
    mutation.mutate()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 p-6" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-semibold text-gray-900">New Contact</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 p-1 rounded"><X size={18} /></button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="Jane Doe"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="jane@example.com"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Phone <span className="text-gray-400 font-normal">(optional)</span></label>
            <input
              type="tel"
              value={phone}
              onChange={e => setPhone(e.target.value)}
              placeholder="+1 555 000 0000"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
            />
          </div>
          {!name.trim() && !email.trim() && (
            <p className="text-xs text-gray-400">Provide at least a name or email.</p>
          )}
          {mutation.isError && <p className="text-sm text-red-600">Failed to create contact. Please try again.</p>}
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50">Cancel</button>
            <button
              type="submit"
              disabled={mutation.isPending || (!name.trim() && !email.trim())}
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

export default function ContactsPage() {
  const [search, setSearch] = useState('')
  const [showModal, setShowModal] = useState(false)
  const navigate = useNavigate()

  const { data, isLoading } = useQuery({
    queryKey: ['contacts', search],
    queryFn: () => contactsApi.list({ search: search || undefined }),
    staleTime: 30_000,
  })

  const contacts: any[] = Array.isArray(data) ? data : []

  return (
    <>
    {showModal && (
      <NewContactModal
        onClose={() => setShowModal(false)}
        onCreated={(id) => { setShowModal(false); navigate(`/contacts/${id}`) }}
      />
    )}
    <div className="h-full flex flex-col bg-white">
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <h1 className="text-xl font-semibold text-gray-900">Contacts</h1>
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700"
          >
            <Plus size={14} /> New Contact
          </button>
        </div>
        <div className="relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search by name or email..."
            className="w-full pl-9 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="p-6 space-y-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="animate-pulse flex gap-3 items-center">
                <div className="w-10 h-10 bg-gray-200 rounded-full" />
                <div className="space-y-2 flex-1">
                  <div className="h-3 bg-gray-200 rounded w-40" />
                  <div className="h-3 bg-gray-200 rounded w-24" />
                </div>
              </div>
            ))}
          </div>
        ) : contacts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-400">
            <Users size={40} className="mb-3 opacity-30" />
            <p className="font-medium">No contacts yet</p>
            <p className="text-sm mt-1">Contacts appear when customers start conversations</p>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left text-xs font-medium text-gray-500 px-6 py-3">Name</th>
                <th className="text-left text-xs font-medium text-gray-500 px-6 py-3">Email</th>
                <th className="text-left text-xs font-medium text-gray-500 px-6 py-3">Last seen</th>
                <th className="text-left text-xs font-medium text-gray-500 px-6 py-3">First seen</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {contacts.map((c: any) => (
                <tr
                  key={c.id}
                  onClick={() => navigate(`/contacts/${c.id}`)}
                  className="hover:bg-gray-50 cursor-pointer transition-colors"
                >
                  <td className="px-6 py-3">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 text-xs font-medium">
                        {initials(c.name || c.email)}
                      </div>
                      <span className="text-sm font-medium text-gray-900">{c.name || '—'}</span>
                    </div>
                  </td>
                  <td className="px-6 py-3 text-sm text-gray-600">{c.email || '—'}</td>
                  <td className="px-6 py-3 text-sm text-gray-500">{c.last_seen_at ? timeAgo(c.last_seen_at) : '—'}</td>
                  <td className="px-6 py-3 text-sm text-gray-500">{c.first_seen_at ? timeAgo(c.first_seen_at) : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
    </>
  )
}
