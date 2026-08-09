import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { aiApi } from '@/api/ai'
import { Sparkles, X, ArrowRight } from 'lucide-react'

interface Props { conversationId: string }

export default function DraftSuggestion({ conversationId }: Props) {
  const [draft, setDraft] = useState<any>(null)
  const [dismissed, setDismissed] = useState(false)
  const qc = useQueryClient()

  const genMut = useMutation({
    mutationFn: () => aiApi.generateDraft(conversationId),
    onSuccess: (data) => { setDraft(data); setDismissed(false) },
  })

  const updateMut = useMutation({
    mutationFn: (status: string) => aiApi.updateDraft(draft.id, { status }),
  })

  if (dismissed || !draft) {
    return (
      <div className="px-4 py-2 border-b border-gray-100 bg-gray-50/50">
        <button
          onClick={() => genMut.mutate()}
          disabled={genMut.isPending}
          className="flex items-center gap-1.5 text-xs text-indigo-600 hover:text-indigo-700 font-medium"
        >
          <Sparkles size={12} />
          {genMut.isPending ? 'Generating draft...' : 'Generate AI reply draft'}
        </button>
      </div>
    )
  }

  return (
    <div className="px-4 py-3 border-b border-indigo-100 bg-indigo-50/30">
      <div className="flex items-center gap-2 mb-2">
        <Sparkles size={13} className="text-indigo-500" />
        <span className="text-xs font-medium text-indigo-700">AI Draft</span>
        <button
          onClick={() => { setDismissed(true); updateMut.mutate('dismissed') }}
          className="ml-auto text-gray-400 hover:text-gray-600"
        >
          <X size={13} />
        </button>
      </div>
      <p className="text-sm text-gray-700 leading-relaxed mb-2">{draft.draft_content || draft.content}</p>
      <div className="flex items-center gap-2">
        <button
          onClick={() => {
            // Dispatch event to insert into ReplyBox
            window.dispatchEvent(new CustomEvent('insert-draft', { detail: { content: draft.draft_content || draft.content } }))
            setDismissed(true)
            updateMut.mutate('accepted')
          }}
          className="flex items-center gap-1 text-xs bg-indigo-600 text-white px-3 py-1.5 rounded-lg hover:bg-indigo-700"
        >
          <ArrowRight size={11} /> Use this draft
        </button>
        <span className="text-[10px] text-gray-400 italic">AI-generated — review before sending</span>
      </div>
    </div>
  )
}
