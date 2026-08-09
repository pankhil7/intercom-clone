import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { teamApi } from '@/api/team'
import { conversationsApi } from '@/api/conversations'
import { useEffect, useRef } from 'react'
import { initials } from '@/utils/format'

interface Props {
  conversationId: string
  currentAssigneeId?: string
  onClose: () => void
}

export default function AssigneeSelector({ conversationId, currentAssigneeId, onClose }: Props) {
  const qc = useQueryClient()
  const ref = useRef<HTMLDivElement>(null)

  const { data } = useQuery({ queryKey: ['team-members'], queryFn: teamApi.listMembers })
  const members: any[] = data?.members || []

  const assignMut = useMutation({
    mutationFn: (userId: string) => conversationsApi.assign(conversationId, userId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['conversation', conversationId] })
      qc.invalidateQueries({ queryKey: ['conversations'] })
      onClose()
    },
  })

  const unassignMut = useMutation({
    mutationFn: () => conversationsApi.unassign(conversationId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['conversation', conversationId] })
      qc.invalidateQueries({ queryKey: ['conversations'] })
      onClose()
    },
  })

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose()
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [onClose])

  return (
    <div ref={ref} className="absolute right-0 top-full mt-1 w-56 bg-white border border-gray-200 rounded-xl shadow-lg z-50 py-1">
      <div className="px-3 py-2 border-b border-gray-100 text-xs font-medium text-gray-500">Assign to</div>
      {members.map((m: any) => (
        <button
          key={m.id}
          onClick={() => assignMut.mutate(m.id)}
          className={`w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-gray-50 ${
            m.id === currentAssigneeId ? 'bg-indigo-50 text-indigo-700' : 'text-gray-700'
          }`}
        >
          <div className="w-6 h-6 rounded-full bg-indigo-200 flex items-center justify-center text-indigo-700 text-xs font-medium">
            {initials(m.full_name)}
          </div>
          {m.full_name}
          {m.id === currentAssigneeId && <span className="ml-auto text-xs">✓</span>}
        </button>
      ))}
      {currentAssigneeId && (
        <button
          onClick={() => unassignMut.mutate()}
          className="w-full text-left px-3 py-2 text-xs text-gray-400 hover:bg-gray-50 border-t border-gray-100"
        >
          Remove assignment
        </button>
      )}
    </div>
  )
}
