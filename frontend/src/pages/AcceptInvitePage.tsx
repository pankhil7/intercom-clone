import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { teamApi } from '@/api/team'
import { useAuthStore } from '@/store/auth.store'
import { authApi } from '@/api/auth'
import { Zap } from 'lucide-react'

export default function AcceptInvitePage() {
  const { token } = useParams<{ token: string }>()
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()

  const [invite, setInvite] = useState<{ email: string; role: string; organization_name: string } | null>(null)
  const [form, setForm] = useState({ full_name: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!token) return
    teamApi.validateInvite(token)
      .then(data => setInvite(data.invitation || data))
      .catch(() => setError('Invalid or expired invitation link.'))
  }, [token])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!token) return
    setLoading(true)
    try {
      const data = await teamApi.acceptInvite({ token, ...form })
      localStorage.setItem('access_token', data.access_token)
      const me = await authApi.getMe()
      setAuth(me.user, me.organization, data.access_token, data.refresh_token)
      navigate('/inbox')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to accept invitation.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 bg-indigo-600 rounded-xl mb-4">
            <Zap size={24} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Accept Invitation</h1>
          {invite && (
            <p className="text-gray-500 mt-1">
              Join <strong>{invite.organization_name}</strong> as <strong>{invite.role}</strong>
            </p>
          )}
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
          {error && !invite && (
            <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700">{error}</div>
          )}
          {invite && (
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700">{error}</div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input value={invite.email} disabled className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-gray-50 text-gray-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Full name</label>
                <input
                  type="text" required value={form.full_name}
                  onChange={e => setForm(f => ({ ...f, full_name: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="Your full name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                <input
                  type="password" required minLength={8} value={form.password}
                  onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="Create a password (8+ characters)"
                />
              </div>
              <button type="submit" disabled={loading}
                className="w-full bg-indigo-600 text-white py-2.5 rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors">
                {loading ? 'Joining...' : 'Accept & Join'}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
