import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { settingsApi } from '@/api/settings'
import { useToast } from '@/components/ui/toaster'
import { Plus, Trash2, Mail, MessageSquare, Globe, Copy } from 'lucide-react'

const CHANNEL_ICONS: Record<string, any> = {
  email: Mail,
  chat: MessageSquare,
  web: Globe,
}

export default function InboxSettings() {
  const qc = useQueryClient()
  const { toast } = useToast()
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: '', channel: 'chat', email_address: '' })

  const { data } = useQuery({ queryKey: ['inboxes'], queryFn: settingsApi.listInboxes })
  const inboxes: any[] = data?.inboxes || []

  const createMut = useMutation({
    mutationFn: () => settingsApi.createInbox(form),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['inboxes'] })
      toast({ title: 'Inbox created' })
      setShowForm(false); setForm({ name: '', channel: 'chat', email_address: '' })
    },
    onError: () => toast({ title: 'Failed to create inbox', variant: 'destructive' }),
  })

  const deleteMut = useMutation({
    mutationFn: (id: string) => settingsApi.deleteInbox(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['inboxes'] }),
  })

  const copyWidget = (widgetKey: string) => {
    const snippet = `<script>
  window.InboxWidget = { widgetKey: '${widgetKey}' };
  (function(d, s, id) {
    var js, fjs = d.getElementsByTagName(s)[0];
    if (d.getElementById(id)) return;
    js = d.createElement(s); js.id = id;
    js.src = '${import.meta.env.VITE_WIDGET_URL || 'https://widget.yourapp.com'}/widget.js';
    fjs.parentNode.insertBefore(js, fjs);
  }(document, 'script', 'inbox-widget'));
</script>`
    navigator.clipboard.writeText(snippet)
    toast({ title: 'Widget snippet copied!' })
  }

  return (
    <div className="max-w-2xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Inboxes</h2>
          <p className="text-sm text-gray-500 mt-0.5">Each inbox represents a channel (live chat, email) where conversations come in.</p>
        </div>
        <button onClick={() => setShowForm(true)} className="flex items-center gap-1.5 bg-indigo-600 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-indigo-700">
          <Plus size={14} /> New inbox
        </button>
      </div>

      {showForm && (
        <div className="mb-6 p-4 bg-gray-50 rounded-xl border border-gray-200 space-y-3">
          <input
            value={form.name}
            onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
            placeholder="Inbox name (e.g. Website Chat)"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Channel type</label>
            <select
              value={form.channel}
              onChange={e => setForm(f => ({ ...f, channel: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="chat">Live Chat</option>
              <option value="email">Email</option>
            </select>
          </div>
          {form.channel === 'email' && (
            <input
              value={form.email_address}
              onChange={e => setForm(f => ({ ...f, email_address: e.target.value }))}
              placeholder="support@yourcompany.com"
              type="email"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          )}
          <div className="flex gap-2 justify-end">
            <button onClick={() => setShowForm(false)} className="px-3 py-1.5 text-sm text-gray-600">Cancel</button>
            <button
              onClick={() => createMut.mutate()}
              disabled={!form.name || createMut.isPending}
              className="px-4 py-1.5 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 disabled:opacity-50"
            >
              Create
            </button>
          </div>
        </div>
      )}

      <div className="space-y-3">
        {inboxes.map((inbox: any) => {
          const Icon = CHANNEL_ICONS[inbox.channel] || MessageSquare
          return (
            <div key={inbox.id} className="p-4 bg-white border border-gray-200 rounded-xl space-y-3">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-indigo-50 flex items-center justify-center">
                  <Icon size={14} className="text-indigo-600" />
                </div>
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-900">{inbox.name}</div>
                  <div className="text-xs text-gray-500 capitalize">{inbox.channel} inbox</div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${inbox.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                    {inbox.is_active ? 'Active' : 'Inactive'}
                  </span>
                  <button onClick={() => deleteMut.mutate(inbox.id)} className="text-gray-400 hover:text-red-500 p-1">
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>

              {inbox.channel === 'chat' && inbox.widget_key && (
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-xs font-medium text-gray-700">Widget installation snippet</p>
                    <button
                      onClick={() => copyWidget(inbox.widget_key)}
                      className="flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-800"
                    >
                      <Copy size={11} /> Copy snippet
                    </button>
                  </div>
                  <code className="text-[10px] text-gray-500 font-mono">Widget key: {inbox.widget_key}</code>
                </div>
              )}

              {inbox.channel === 'email' && inbox.email_address && (
                <div className="text-xs text-gray-500">
                  Inbound: <code className="font-mono text-gray-700">{inbox.email_address}</code>
                </div>
              )}
            </div>
          )
        })}
        {inboxes.length === 0 && !showForm && (
          <p className="text-sm text-gray-400 text-center py-8">No inboxes yet. Create one to start receiving conversations.</p>
        )}
      </div>
    </div>
  )
}
