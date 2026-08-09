import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { settingsApi } from '@/api/settings'
import { useToast } from '@/components/ui/toaster'
import { Plus, Trash2, Copy } from 'lucide-react'

const EVENT_OPTIONS = [
  'conversation.created', 'conversation.resolved', 'conversation.assigned',
  'message.created', 'contact.created', 'sla.breached'
]

export default function WebhookSettings() {
  const qc = useQueryClient()
  const { toast } = useToast()
  const [showForm, setShowForm] = useState(false)
  const [url, setUrl] = useState('')
  const [events, setEvents] = useState<string[]>([])
  const [createdSecret, setCreatedSecret] = useState<string | null>(null)

  const { data } = useQuery({ queryKey: ['webhooks'], queryFn: settingsApi.listWebhooks })
  const webhooks: any[] = data?.webhooks || []

  const createMut = useMutation({
    mutationFn: () => settingsApi.createWebhook({ url, events }),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['webhooks'] })
      setCreatedSecret(data?.webhook?.secret || data?.secret || null)
      setShowForm(false); setUrl(''); setEvents([])
      toast({ title: 'Webhook created' })
    },
  })

  const deleteMut = useMutation({
    mutationFn: (id: string) => settingsApi.deleteWebhook(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['webhooks'] }),
  })

  const toggleEvent = (e: string) =>
    setEvents(prev => prev.includes(e) ? prev.filter(x => x !== e) : [...prev, e])

  return (
    <div className="max-w-2xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Webhooks</h2>
          <p className="text-sm text-gray-500 mt-0.5">Receive HTTP POST notifications for events. Signed with HMAC-SHA256.</p>
        </div>
        <button onClick={() => setShowForm(true)} className="flex items-center gap-1.5 bg-indigo-600 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-indigo-700">
          <Plus size={14} /> Add webhook
        </button>
      </div>

      {createdSecret && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-xl">
          <p className="text-sm font-medium text-green-800 mb-2">Webhook created! Copy your signing secret — it won't be shown again.</p>
          <div className="flex items-center gap-2 bg-white border border-green-300 rounded-lg px-3 py-2">
            <code className="flex-1 text-xs font-mono text-gray-800 break-all">{createdSecret}</code>
            <button onClick={() => { navigator.clipboard.writeText(createdSecret); toast({ title: 'Copied!' }) }}>
              <Copy size={14} className="text-green-600" />
            </button>
          </div>
          <button onClick={() => setCreatedSecret(null)} className="text-xs text-green-700 mt-2 hover:underline">Dismiss</button>
        </div>
      )}

      {showForm && (
        <div className="mb-6 p-4 bg-gray-50 rounded-xl border border-gray-200 space-y-3">
          <input value={url} onChange={e => setUrl(e.target.value)} placeholder="https://yourapp.com/webhook" className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
          <div>
            <p className="text-xs font-medium text-gray-600 mb-2">Events to subscribe:</p>
            <div className="grid grid-cols-2 gap-1.5">
              {EVENT_OPTIONS.map(e => (
                <label key={e} className="flex items-center gap-2 text-xs text-gray-700 cursor-pointer">
                  <input type="checkbox" checked={events.includes(e)} onChange={() => toggleEvent(e)} className="accent-indigo-600" />
                  {e}
                </label>
              ))}
            </div>
          </div>
          <div className="flex gap-2 justify-end">
            <button onClick={() => setShowForm(false)} className="px-3 py-1.5 text-sm text-gray-600">Cancel</button>
            <button onClick={() => createMut.mutate()} disabled={!url || events.length === 0 || createMut.isPending} className="px-4 py-1.5 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 disabled:opacity-50">Create</button>
          </div>
        </div>
      )}

      <div className="space-y-2">
        {webhooks.map((w: any) => (
          <div key={w.id} className="p-4 bg-white border border-gray-200 rounded-xl">
            <div className="flex items-center gap-3">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <code className="text-sm font-mono text-gray-800 truncate">{w.url}</code>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${w.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>{w.is_active ? 'Active' : 'Disabled'}</span>
                </div>
                <div className="flex flex-wrap gap-1 mt-1.5">
                  {(w.events || []).map((e: string) => (
                    <span key={e} className="text-[10px] bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">{e}</span>
                  ))}
                </div>
              </div>
              <button onClick={() => deleteMut.mutate(w.id)} className="text-gray-400 hover:text-red-500 p-1"><Trash2 size={14} /></button>
            </div>
          </div>
        ))}
        {webhooks.length === 0 && !showForm && <p className="text-sm text-gray-400 text-center py-8">No webhooks configured yet.</p>}
      </div>
    </div>
  )
}
