import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { settingsApi } from '@/api/settings'
import { useToast } from '@/components/ui/toaster'
import { Plus, Trash2, CheckCircle, XCircle, RefreshCw, Copy } from 'lucide-react'

export default function DomainSettings() {
  const qc = useQueryClient()
  const { toast } = useToast()
  const [showForm, setShowForm] = useState(false)
  const [domain, setDomain] = useState('')

  const { data } = useQuery({ queryKey: ['custom-domains'], queryFn: settingsApi.listDomains })
  const domains: any[] = data?.domains || []

  const createMut = useMutation({
    mutationFn: () => settingsApi.addDomain({ domain }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['custom-domains'] })
      toast({ title: 'Domain added' })
      setShowForm(false); setDomain('')
    },
    onError: () => toast({ title: 'Failed to add domain', variant: 'destructive' }),
  })

  const deleteMut = useMutation({
    mutationFn: (id: string) => settingsApi.deleteDomain(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['custom-domains'] }),
  })

  const verifyMut = useMutation({
    mutationFn: (id: string) => settingsApi.verifyDomain(id),
    onSuccess: (_, id) => {
      qc.invalidateQueries({ queryKey: ['custom-domains'] })
      const d = domains.find(x => x.id === id)
      if (d?.is_verified) toast({ title: 'Domain verified!' })
      else toast({ title: 'DNS not yet propagated — try again in a few minutes', variant: 'destructive' })
    },
  })

  const statusIcon = (d: any) => {
    if (d.is_verified) return <CheckCircle size={14} className="text-green-500" />
    return <XCircle size={14} className="text-gray-400" />
  }

  return (
    <div className="max-w-2xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Custom Domains</h2>
          <p className="text-sm text-gray-500 mt-0.5">Host your knowledge base on your own domain.</p>
        </div>
        <button onClick={() => setShowForm(true)} className="flex items-center gap-1.5 bg-indigo-600 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-indigo-700">
          <Plus size={14} /> Add domain
        </button>
      </div>

      {showForm && (
        <div className="mb-6 p-4 bg-gray-50 rounded-xl border border-gray-200 space-y-3">
          <input
            value={domain}
            onChange={e => setDomain(e.target.value)}
            placeholder="help.yourcompany.com"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <div className="flex gap-2 justify-end">
            <button onClick={() => setShowForm(false)} className="px-3 py-1.5 text-sm text-gray-600">Cancel</button>
            <button
              onClick={() => createMut.mutate()}
              disabled={!domain || createMut.isPending}
              className="px-4 py-1.5 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 disabled:opacity-50"
            >
              Add
            </button>
          </div>
        </div>
      )}

      <div className="space-y-3">
        {domains.map((d: any) => (
          <div key={d.id} className="p-4 bg-white border border-gray-200 rounded-xl space-y-3">
            <div className="flex items-center gap-3">
              {statusIcon(d)}
              <div className="flex-1">
                <div className="text-sm font-medium text-gray-900">{d.domain}</div>
                <div className="text-xs text-gray-500 mt-0.5">
                  {d.is_verified ? 'Verified and active' : 'Pending DNS verification'}
                </div>
              </div>
              <div className="flex gap-2">
                {!d.is_verified && (
                  <button
                    onClick={() => verifyMut.mutate(d.id)}
                    disabled={verifyMut.isPending}
                    className="flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-800 px-2 py-1 border border-indigo-200 rounded-lg"
                  >
                    <RefreshCw size={11} className={verifyMut.isPending ? 'animate-spin' : ''} />
                    Verify
                  </button>
                )}
                <button onClick={() => deleteMut.mutate(d.id)} className="text-gray-400 hover:text-red-500 p-1">
                  <Trash2 size={14} />
                </button>
              </div>
            </div>

            {!d.is_verified && d.txt_record && (
              <div className="bg-gray-50 rounded-lg p-3 space-y-2 text-xs">
                <p className="font-medium text-gray-700">Add this TXT record to your DNS:</p>
                <div className="grid grid-cols-[auto,1fr] gap-x-4 gap-y-1 text-gray-600">
                  <span className="font-mono font-medium">Type</span><span>TXT</span>
                  <span className="font-mono font-medium">Host</span><span>@</span>
                  <span className="font-mono font-medium">Value</span>
                  <div className="flex items-center gap-2">
                    <code className="break-all text-gray-800">{d.txt_record}</code>
                    <button onClick={() => { navigator.clipboard.writeText(d.txt_record); toast({ title: 'Copied!' }) }}>
                      <Copy size={11} className="text-gray-400 hover:text-gray-700 shrink-0" />
                    </button>
                  </div>
                </div>
                <p className="text-gray-400">DNS changes can take up to 48 hours to propagate.</p>
              </div>
            )}
          </div>
        ))}
        {domains.length === 0 && !showForm && (
          <p className="text-sm text-gray-400 text-center py-8">No custom domains configured.</p>
        )}
      </div>
    </div>
  )
}
