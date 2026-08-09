import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { settingsApi } from '@/api/settings'
import { useToast } from '@/components/ui/toaster'
import { Plus, Trash2 } from 'lucide-react'

export default function SLASettings() {
  const qc = useQueryClient()
  const { toast } = useToast()
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: '', first_response_hours: 8, resolution_hours: 48 })

  const { data } = useQuery({ queryKey: ['sla-policies'], queryFn: settingsApi.listSLAPolicies })
  const policies: any[] = data?.policies || []

  const createMut = useMutation({
    mutationFn: () => settingsApi.createSLAPolicy(form),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['sla-policies'] }); toast({ title: 'SLA policy created' }); setShowForm(false); setForm({ name: '', first_response_hours: 8, resolution_hours: 48 }) },
  })

  const deleteMut = useMutation({
    mutationFn: (id: string) => settingsApi.deleteSLAPolicy(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['sla-policies'] }),
  })

  return (
    <div className="max-w-2xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">SLA Policies</h2>
          <p className="text-sm text-gray-500 mt-0.5">Set response time targets. Breaches show red indicators in the inbox.</p>
        </div>
        <button onClick={() => setShowForm(true)} className="flex items-center gap-1.5 bg-indigo-600 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-indigo-700">
          <Plus size={14} /> New policy
        </button>
      </div>

      {showForm && (
        <div className="mb-6 p-4 bg-gray-50 rounded-xl border border-gray-200 space-y-3">
          <input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} placeholder="Policy name (e.g. Standard)" className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">First response (hours)</label>
              <input type="number" min={1} value={form.first_response_hours} onChange={e => setForm(f => ({ ...f, first_response_hours: +e.target.value }))} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Resolution (hours)</label>
              <input type="number" min={1} value={form.resolution_hours} onChange={e => setForm(f => ({ ...f, resolution_hours: +e.target.value }))} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
            </div>
          </div>
          <div className="flex gap-2 justify-end">
            <button onClick={() => setShowForm(false)} className="px-3 py-1.5 text-sm text-gray-600">Cancel</button>
            <button onClick={() => createMut.mutate()} disabled={!form.name || createMut.isPending} className="px-4 py-1.5 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 disabled:opacity-50">Create</button>
          </div>
        </div>
      )}

      <div className="space-y-2">
        {policies.map((p: any) => (
          <div key={p.id} className="flex items-center gap-4 p-4 bg-white border border-gray-200 rounded-xl">
            <div className="flex-1">
              <div className="text-sm font-medium text-gray-900">{p.name}</div>
              <div className="text-xs text-gray-500 mt-0.5">First response: {p.first_response_hours}h · Resolution: {p.resolution_hours}h</div>
            </div>
            <button onClick={() => deleteMut.mutate(p.id)} className="text-gray-400 hover:text-red-500 p-1"><Trash2 size={14} /></button>
          </div>
        ))}
        {policies.length === 0 && !showForm && <p className="text-sm text-gray-400 text-center py-8">No SLA policies yet.</p>}
      </div>
    </div>
  )
}
