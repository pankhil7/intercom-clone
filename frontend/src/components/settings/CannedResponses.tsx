import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { settingsApi } from '@/api/settings'
import { useToast } from '@/components/ui/toaster'
import { Plus, Edit, Trash2 } from 'lucide-react'

export default function CannedResponses() {
  const qc = useQueryClient()
  const { toast } = useToast()
  const [editing, setEditing] = useState<any>(null)
  const [form, setForm] = useState({ name: '', shortcut: '', content: '' })
  const [showForm, setShowForm] = useState(false)

  const { data } = useQuery({ queryKey: ['canned-responses'], queryFn: settingsApi.listCannedResponses })
  const items: any[] = data?.canned_responses || []

  const saveMut = useMutation({
    mutationFn: () => editing
      ? settingsApi.updateCannedResponse(editing.id, form)
      : settingsApi.createCannedResponse(form),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['canned-responses'] })
      toast({ title: editing ? 'Response updated' : 'Response created' })
      setShowForm(false); setEditing(null); setForm({ name: '', shortcut: '', content: '' })
    },
  })

  const deleteMut = useMutation({
    mutationFn: (id: string) => settingsApi.deleteCannedResponse(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['canned-responses'] }),
  })

  const openEdit = (item: any) => {
    setEditing(item); setForm({ name: item.name, shortcut: item.shortcut || '', content: item.content }); setShowForm(true)
  }

  const openNew = () => {
    setEditing(null); setForm({ name: '', shortcut: '', content: '' }); setShowForm(true)
  }

  return (
    <div className="max-w-2xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Canned Responses</h2>
          <p className="text-sm text-gray-500 mt-0.5">Save and reuse common replies. Type / in the reply box to insert.</p>
        </div>
        <button onClick={openNew} className="flex items-center gap-1.5 bg-indigo-600 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-indigo-700">
          <Plus size={14} /> New response
        </button>
      </div>

      {showForm && (
        <div className="mb-6 p-4 bg-gray-50 rounded-xl border border-gray-200 space-y-3">
          <input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} placeholder="Name (e.g. Greeting)" className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
          <input value={form.shortcut} onChange={e => setForm(f => ({ ...f, shortcut: e.target.value }))} placeholder="Shortcut (e.g. /greet) — optional" className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
          <textarea value={form.content} onChange={e => setForm(f => ({ ...f, content: e.target.value }))} placeholder="Response content..." rows={4} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none" />
          <div className="flex gap-2 justify-end">
            <button onClick={() => setShowForm(false)} className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800">Cancel</button>
            <button onClick={() => saveMut.mutate()} disabled={!form.name || !form.content || saveMut.isPending} className="px-4 py-1.5 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 disabled:opacity-50">
              {saveMut.isPending ? 'Saving...' : (editing ? 'Update' : 'Create')}
            </button>
          </div>
        </div>
      )}

      <div className="space-y-2">
        {items.map((item: any) => (
          <div key={item.id} className="flex items-start gap-3 p-4 bg-white border border-gray-200 rounded-xl">
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-900">{item.name}</span>
                {item.shortcut && <span className="text-xs font-mono bg-gray-100 px-1.5 py-0.5 rounded text-gray-600">{item.shortcut}</span>}
              </div>
              <p className="text-xs text-gray-500 mt-1 line-clamp-2">{item.content}</p>
            </div>
            <div className="flex gap-1 shrink-0">
              <button onClick={() => openEdit(item)} className="text-gray-400 hover:text-indigo-600 p-1"><Edit size={14} /></button>
              <button onClick={() => deleteMut.mutate(item.id)} className="text-gray-400 hover:text-red-500 p-1"><Trash2 size={14} /></button>
            </div>
          </div>
        ))}
        {items.length === 0 && !showForm && (
          <p className="text-sm text-gray-400 text-center py-8">No canned responses yet. Create one to get started.</p>
        )}
      </div>
    </div>
  )
}
