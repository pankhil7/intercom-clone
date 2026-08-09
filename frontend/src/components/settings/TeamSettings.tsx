import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { teamApi } from '@/api/team'
import { useToast } from '@/components/ui/toaster'
import { Plus, Trash2, Mail } from 'lucide-react'
import { timeAgo } from '@/utils/format'

export default function TeamSettings() {
  const qc = useQueryClient()
  const { toast } = useToast()
  const [showInvite, setShowInvite] = useState(false)
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState('agent')

  const { data: membersData } = useQuery({ queryKey: ['team-members'], queryFn: teamApi.listMembers })
  const { data: invitesData } = useQuery({ queryKey: ['team-invitations'], queryFn: teamApi.listInvitations })

  const members: any[] = membersData?.members || []
  const invitations: any[] = invitesData?.invitations || []

  const inviteMut = useMutation({
    mutationFn: () => teamApi.sendInvite({ email: inviteEmail, role: inviteRole }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['team-invitations'] })
      toast({ title: `Invitation sent to ${inviteEmail}` })
      setShowInvite(false); setInviteEmail(''); setInviteRole('agent')
    },
    onError: () => toast({ title: 'Failed to send invitation', variant: 'destructive' }),
  })

  const deleteInviteMut = useMutation({
    mutationFn: (id: string) => teamApi.deleteInvitation(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['team-invitations'] }),
  })

  const updateMemberMut = useMutation({
    mutationFn: ({ id, role }: { id: string; role: string }) => teamApi.updateMember(id, { role }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['team-members'] }); toast({ title: 'Member updated' }) },
  })

  return (
    <div className="max-w-2xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Team Members</h2>
          <p className="text-sm text-gray-500 mt-0.5">Manage who has access to your workspace</p>
        </div>
        <button
          onClick={() => setShowInvite(true)}
          className="flex items-center gap-1.5 bg-indigo-600 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-indigo-700"
        >
          <Plus size={14} /> Invite member
        </button>
      </div>

      {showInvite && (
        <div className="mb-6 p-4 bg-gray-50 rounded-xl border border-gray-200">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Invite a team member</h3>
          <div className="flex gap-3">
            <input
              type="email" value={inviteEmail} onChange={e => setInviteEmail(e.target.value)}
              placeholder="colleague@company.com"
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <select value={inviteRole} onChange={e => setInviteRole(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500">
              <option value="agent">Agent</option>
              <option value="admin">Admin</option>
            </select>
            <button
              onClick={() => inviteMut.mutate()}
              disabled={!inviteEmail || inviteMut.isPending}
              className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 disabled:opacity-50"
            >
              Send
            </button>
            <button onClick={() => setShowInvite(false)} className="px-3 py-2 text-sm text-gray-500 hover:text-gray-700">Cancel</button>
          </div>
        </div>
      )}

      {/* Members */}
      <div className="space-y-2 mb-6">
        {members.map((m: any) => (
          <div key={m.id} className="flex items-center gap-3 p-3 bg-white border border-gray-200 rounded-xl">
            <div className="w-9 h-9 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 text-sm font-medium">
              {m.full_name?.[0]?.toUpperCase()}
            </div>
            <div className="flex-1">
              <div className="text-sm font-medium text-gray-900">{m.full_name}</div>
              <div className="text-xs text-gray-500">{m.email}</div>
            </div>
            <select
              value={m.role}
              onChange={e => updateMemberMut.mutate({ id: m.id, role: e.target.value })}
              className="text-xs border border-gray-200 rounded-lg px-2 py-1 text-gray-700"
            >
              <option value="agent">Agent</option>
              <option value="admin">Admin</option>
            </select>
            <span className={`text-xs px-2 py-0.5 rounded-full ${m.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
              {m.is_active ? 'Active' : 'Inactive'}
            </span>
          </div>
        ))}
      </div>

      {/* Pending invitations */}
      {invitations.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-3">Pending Invitations</h3>
          <div className="space-y-2">
            {invitations.map((inv: any) => (
              <div key={inv.id} className="flex items-center gap-3 p-3 bg-yellow-50 border border-yellow-200 rounded-xl">
                <Mail size={16} className="text-yellow-600" />
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-900">{inv.email}</div>
                  <div className="text-xs text-gray-500">Invited as {inv.role} · Expires {timeAgo(inv.expires_at)}</div>
                </div>
                <button onClick={() => deleteInviteMut.mutate(inv.id)} className="text-gray-400 hover:text-red-500">
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
