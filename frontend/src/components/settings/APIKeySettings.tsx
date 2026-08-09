import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { settingsApi } from '@/api/settings'
import { useToast } from '@/components/ui/toaster'
import { Plus, Trash2, Copy, Eye, EyeOff } from 'lucide-react'
import { timeAgo } from '@/utils/format'

export default function APIKeySettings() {
  const qc = useQueryClient()
  const { toast } = useToast()
  const [showForm, setShowForm] = useState(false)
  const [keyName, setKeyName] = useState('')
  const [createdKey, setCreatedKey] = useState<string | null>(null)
  const [revealed, setRevealed] = useState(false)

  const { data } = useQuery({ queryKey: ['api-keys'], queryFn: settingsApi.listAPIKeys })
  const keys: any[] = data?.api_keys || []

  const createMut = useMutation({
    mutationFn: () => settingsApi.createAPIKey({ name: keyName }),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['api-keys'] })
      setCreatedKey(data?.key || data?.api_key?.key || null)
      setShowForm(false); setKeyName('')
      toast({ title: 'API key created' })
    },
    onError: () => toast({ title: 'Failed to create API key', variant: 'destructive' }),
  })

  const revokeMut = useMutation({
    mutationFn: (id: string) => settingsApi.revokeAPIKey(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['api-keys'] }),
  })

  const copyKey = (text: string) => {
    navigator.clipboard.writeText(text)
    toast({ title: 'Copied to clipboard!' })
  }

  return (
    <div className="max-w-2xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">API Keys</h2>
          <p className="text-sm text-gray-500 mt-0.5">Use API keys to authenticate programmatic access. Pass as <code className="text-xs bg-gray-100 px-1 rounded">Authorization: Bearer &lt;key&gt;</code>.</p>
        </div>
        <button onClick={() => setShowForm(true)} className="flex items-center gap-1.5 bg-indigo-600 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-indigo-700">
          <Plus size={14} /> New key
        </button>
      </div>

      {createdKey && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-xl">
          <p className="text-sm font-medium text-green-800 mb-2">API key created! Copy it now — it won't be shown again.</p>
          <div className="flex items-center gap-2 bg-white border border-green-300 rounded-lg px-3 py-2">
            <code className="flex-1 text-xs font-mono text-gray-800 break-all">
              {revealed ? createdKey : createdKey.replace(/./g, '•').slice(0, 40)}
            </code>
            <button onClick={() => setRevealed(r => !r)} className="text-gray-400 hover:text-gray-700">
              {revealed ? <EyeOff size={14} /> : <Eye size={14} />}
            </button>
            <button onClick={() => copyKey(createdKey)}>
              <Copy size={14} className="text-green-600" />
            </button>
          </div>
          <button onClick={() => { setCreatedKey(null); setRevealed(false) }} className="text-xs text-green-700 mt-2 hover:underline">Dismiss</button>
        </div>
      )}

      {showForm && (
        <div className="mb-6 p-4 bg-gray-50 rounded-xl border border-gray-200 space-y-3">
          <input
            value={keyName}
            onChange={e => setKeyName(e.target.value)}
            placeholder="Key name (e.g. Production integration)"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <div className="flex gap-2 justify-end">
            <button onClick={() => setShowForm(false)} className="px-3 py-1.5 text-sm text-gray-600">Cancel</button>
            <button
              onClick={() => createMut.mutate()}
              disabled={!keyName || createMut.isPending}
              className="px-4 py-1.5 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 disabled:opacity-50"
            >
              Create
            </button>
          </div>
        </div>
      )}

      <div className="space-y-2">
        {keys.map((k: any) => (
          <div key={k.id} className="flex items-center gap-3 p-4 bg-white border border-gray-200 rounded-xl">
            <div className="flex-1">
              <div className="text-sm font-medium text-gray-900">{k.name}</div>
              <div className="text-xs text-gray-500 mt-0.5 font-mono">
                {k.key_prefix}••••••••
                {k.last_used_at && <span className="ml-2 font-sans">· Last used {timeAgo(k.last_used_at)}</span>}
                {!k.last_used_at && <span className="ml-2 font-sans">· Never used</span>}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className={`text-xs px-2 py-0.5 rounded-full ${k.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                {k.is_active ? 'Active' : 'Revoked'}
              </span>
              {k.is_active && (
                <button onClick={() => revokeMut.mutate(k.id)} className="text-gray-400 hover:text-red-500 p-1">
                  <Trash2 size={14} />
                </button>
              )}
            </div>
          </div>
        ))}
        {keys.length === 0 && !showForm && (
          <p className="text-sm text-gray-400 text-center py-8">No API keys yet. Create one to get started.</p>
        )}
      </div>
    </div>
  )
}
