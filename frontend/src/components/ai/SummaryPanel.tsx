import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { aiApi } from '@/api/ai'
import { Sparkles, RefreshCw, ChevronDown, ChevronUp } from 'lucide-react'

interface Props { conversationId: string }

const SENTIMENT_COLORS: Record<string, string> = {
  positive: 'bg-green-100 text-green-700',
  neutral: 'bg-gray-100 text-gray-700',
  negative: 'bg-orange-100 text-orange-700',
  frustrated: 'bg-red-100 text-red-700',
}

export default function SummaryPanel({ conversationId }: Props) {
  const [summary, setSummary] = useState<any>(null)
  const [expanded, setExpanded] = useState(true)

  const mut = useMutation({
    mutationFn: () => aiApi.summarize(conversationId),
    onSuccess: (data) => setSummary(data),
  })

  return (
    <div className="border-b border-gray-200 bg-indigo-50/50">
      <div className="flex items-center gap-2 px-4 py-2">
        <Sparkles size={14} className="text-indigo-500" />
        <span className="text-sm font-medium text-indigo-700 flex-1">AI Summary</span>
        {summary && (
          <button onClick={() => setExpanded(e => !e)} className="text-gray-400 hover:text-gray-600">
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
        )}
        <button
          onClick={() => { setExpanded(true); mut.mutate() }}
          disabled={mut.isPending}
          className="flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-700 font-medium"
        >
          {mut.isPending ? (
            <RefreshCw size={12} className="animate-spin" />
          ) : (
            <RefreshCw size={12} />
          )}
          {summary ? 'Refresh' : 'Generate'}
        </button>
      </div>

      {mut.isPending && (
        <div className="px-4 pb-3 space-y-2">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-3 bg-indigo-100 rounded animate-pulse" style={{ width: `${60 + i * 15}%` }} />
          ))}
        </div>
      )}

      {summary && expanded && (
        <div className="px-4 pb-3 space-y-2">
          <div className="flex items-start gap-2">
            <span className="text-xs font-medium text-gray-500 shrink-0 w-20">Problem</span>
            <p className="text-xs text-gray-700">{summary.problem}</p>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-xs font-medium text-gray-500 shrink-0 w-20">Sentiment</span>
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${SENTIMENT_COLORS[summary.sentiment] || SENTIMENT_COLORS.neutral}`}>
              {summary.sentiment}
            </span>
          </div>
          {summary.key_points?.length > 0 && (
            <div className="flex items-start gap-2">
              <span className="text-xs font-medium text-gray-500 shrink-0 w-20">Key points</span>
              <ul className="text-xs text-gray-700 space-y-0.5">
                {summary.key_points.map((p: string, i: number) => <li key={i}>• {p}</li>)}
              </ul>
            </div>
          )}
          <div className="flex items-start gap-2">
            <span className="text-xs font-medium text-gray-500 shrink-0 w-20">Next step</span>
            <p className="text-xs text-gray-700">{summary.suggested_action}</p>
          </div>
          <p className="text-[10px] text-gray-400 italic">AI-generated — verify before acting</p>
        </div>
      )}
    </div>
  )
}
