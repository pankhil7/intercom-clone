import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { contactsApi } from '@/api/contacts'
import { Search, Users } from 'lucide-react'
import { timeAgo, initials } from '@/utils/format'

export default function ContactsPage() {
  const [search, setSearch] = useState('')
  const navigate = useNavigate()

  const { data, isLoading } = useQuery({
    queryKey: ['contacts', search],
    queryFn: () => contactsApi.list({ search: search || undefined }),
    staleTime: 30_000,
  })

  const contacts: any[] = data?.contacts || []

  return (
    <div className="h-full flex flex-col bg-white">
      <div className="px-6 py-4 border-b border-gray-200">
        <h1 className="text-xl font-semibold text-gray-900 mb-3">Contacts</h1>
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
  )
}
