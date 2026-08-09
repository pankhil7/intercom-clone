import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '@/api/analytics'
import { subDays, format } from 'date-fns'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { MessageSquare, CheckCircle, Clock, AlertTriangle } from 'lucide-react'

function getRange(days: number) {
  const end = new Date()
  const start = subDays(end, days)
  return { start: start.toISOString(), end: end.toISOString() }
}

export default function AnalyticsPage() {
  const [days, setDays] = useState(7)
  const { start, end } = getRange(days)

  const { data: overview } = useQuery({
    queryKey: ['analytics-overview', start, end],
    queryFn: () => analyticsApi.getOverview(start, end),
  })

  const { data: agentData } = useQuery({
    queryKey: ['analytics-agents', start, end],
    queryFn: () => analyticsApi.getAgentPerformance(start, end),
  })

  const { data: resData } = useQuery({
    queryKey: ['analytics-resolution', start, end],
    queryFn: () => analyticsApi.getResolutionRate(start, end),
  })

  const { data: heatData } = useQuery({
    queryKey: ['analytics-hours', start, end],
    queryFn: () => analyticsApi.getBusiestHours(start, end),
  })

  const o = overview || {}
  const agents: any[] = agentData?.agents || []
  const series: any[] = resData?.series || []
  const heatmap: number[][] = heatData?.heatmap || Array(7).fill(Array(24).fill(0))

  const maxHeat = Math.max(1, ...heatmap.flat())
  const days_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

  return (
    <div className="h-full overflow-y-auto bg-gray-50">
      <div className="max-w-6xl mx-auto px-6 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-xl font-semibold text-gray-900">Analytics</h1>
          <div className="flex gap-2">
            {[7, 14, 30].map(d => (
              <button
                key={d}
                onClick={() => setDays(d)}
                className={`px-3 py-1 text-sm rounded-lg border transition-colors ${
                  days === d ? 'bg-indigo-600 text-white border-indigo-600' : 'bg-white border-gray-200 text-gray-600 hover:border-indigo-300'
                }`}
              >
                {d}d
              </button>
            ))}
          </div>
        </div>

        {/* Overview cards */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          {[
            { label: 'Total Conversations', value: o.total_conversations ?? '—', icon: MessageSquare, color: 'text-blue-600 bg-blue-50' },
            { label: 'Resolved', value: o.resolved_conversations ?? '—', icon: CheckCircle, color: 'text-green-600 bg-green-50' },
            { label: 'Avg First Response', value: o.avg_first_response_mins ? `${Math.round(o.avg_first_response_mins)}m` : '—', icon: Clock, color: 'text-purple-600 bg-purple-50' },
            { label: 'SLA Breach Rate', value: o.sla_breach_rate != null ? `${(o.sla_breach_rate * 100).toFixed(1)}%` : '—', icon: AlertTriangle, color: 'text-red-600 bg-red-50' },
          ].map(({ label, value, icon: Icon, color }) => (
            <div key={label} className="bg-white rounded-xl border border-gray-200 p-4">
              <div className={`inline-flex p-2 rounded-lg mb-3 ${color}`}>
                <Icon size={18} />
              </div>
              <div className="text-2xl font-bold text-gray-900">{value}</div>
              <div className="text-sm text-gray-500 mt-0.5">{label}</div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-2 gap-6 mb-6">
          {/* Resolution Rate Chart */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="font-medium text-gray-900 mb-4">Resolution Rate</h3>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={series}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={d => format(new Date(d), 'MMM d')} />
                <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `${v}%`} />
                <Tooltip formatter={(v: any) => [`${v}%`, 'Rate']} />
                <Line type="monotone" dataKey="rate" stroke="#6366f1" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Busiest Hours Heatmap */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="font-medium text-gray-900 mb-4">Busiest Hours</h3>
            <div className="overflow-x-auto">
              <div className="flex gap-1">
                <div className="flex flex-col gap-1 mr-1">
                  <div className="h-4 w-7" />
                  {days_labels.map(d => (
                    <div key={d} className="h-4 flex items-center text-[10px] text-gray-400 w-7">{d}</div>
                  ))}
                </div>
                {Array.from({ length: 24 }, (_, h) => (
                  <div key={h} className="flex flex-col gap-1">
                    <div className="h-4 flex items-center justify-center text-[9px] text-gray-400">{h % 6 === 0 ? `${h}h` : ''}</div>
                    {heatmap.map((row, d) => {
                      const val = row[h] || 0
                      const intensity = val / maxHeat
                      return (
                        <div
                          key={d}
                          title={`${days_labels[d]} ${h}:00 — ${val} conversations`}
                          className="w-4 h-4 rounded-sm"
                          style={{ backgroundColor: intensity > 0 ? `rgba(99, 102, 241, ${0.1 + intensity * 0.9})` : '#f3f4f6' }}
                        />
                      )
                    })}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Agent Performance */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h3 className="font-medium text-gray-900 mb-4">Agent Performance</h3>
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-100">
                <th className="text-left text-xs font-medium text-gray-500 pb-3">Agent</th>
                <th className="text-right text-xs font-medium text-gray-500 pb-3">Conversations</th>
                <th className="text-right text-xs font-medium text-gray-500 pb-3">Resolved</th>
                <th className="text-right text-xs font-medium text-gray-500 pb-3">Avg Response</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {agents.map((a: any) => (
                <tr key={a.id}>
                  <td className="py-3 text-sm font-medium text-gray-900">{a.name}</td>
                  <td className="py-3 text-sm text-gray-600 text-right">{a.conversations_handled}</td>
                  <td className="py-3 text-sm text-gray-600 text-right">{a.resolved_count}</td>
                  <td className="py-3 text-sm text-gray-600 text-right">{a.avg_response_mins ? `${Math.round(a.avg_response_mins)}m` : '—'}</td>
                </tr>
              ))}
              {agents.length === 0 && (
                <tr><td colSpan={4} className="py-6 text-center text-sm text-gray-400">No data for this period</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
