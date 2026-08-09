import { NavLink, useNavigate } from 'react-router-dom'
import { MessageSquare, Users, BookOpen, BarChart2, Settings, LogOut, Zap } from 'lucide-react'
import { useAuthStore } from '@/store/auth.store'
import { authApi } from '@/api/auth'

const navItems = [
  { to: '/inbox', icon: MessageSquare, label: 'Inbox' },
  { to: '/contacts', icon: Users, label: 'Contacts' },
  { to: '/kb', icon: BookOpen, label: 'Knowledge Base' },
  { to: '/analytics', icon: BarChart2, label: 'Analytics' },
]

export default function Sidebar() {
  const { user, organization, clearAuth } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = async () => {
    try { await authApi.logout() } catch { /* ignore */ }
    clearAuth()
    navigate('/login')
  }

  const initials = user?.full_name
    ?.split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2) || '?'

  return (
    <div className="w-16 bg-gray-900 flex flex-col items-center py-4 gap-1 shrink-0">
      {/* Logo */}
      <div className="mb-4 p-2">
        <div className="w-8 h-8 bg-indigo-500 rounded-lg flex items-center justify-center">
          <Zap size={18} className="text-white" />
        </div>
      </div>

      {/* Nav items */}
      <div className="flex-1 flex flex-col gap-1 w-full px-2">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            title={label}
            className={({ isActive }) =>
              `flex items-center justify-center w-full h-10 rounded-lg transition-colors ${
                isActive
                  ? 'bg-indigo-600 text-white'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-white'
              }`
            }
          >
            <Icon size={20} />
          </NavLink>
        ))}
      </div>

      {/* Bottom */}
      <div className="flex flex-col items-center gap-2 w-full px-2">
        <NavLink
          to="/settings"
          title="Settings"
          className={({ isActive }) =>
            `flex items-center justify-center w-full h-10 rounded-lg transition-colors ${
              isActive ? 'bg-indigo-600 text-white' : 'text-gray-400 hover:bg-gray-800 hover:text-white'
            }`
          }
        >
          <Settings size={20} />
        </NavLink>

        <button
          onClick={handleLogout}
          title="Logout"
          className="flex items-center justify-center w-full h-10 rounded-lg text-gray-400 hover:bg-gray-800 hover:text-red-400 transition-colors"
        >
          <LogOut size={20} />
        </button>

        {/* Avatar */}
        <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-white text-xs font-medium mt-1" title={user?.full_name}>
          {initials}
        </div>
        {organization && (
          <div className="text-gray-500 text-[9px] text-center leading-tight max-w-full truncate px-1">
            {organization.name}
          </div>
        )}
      </div>
    </div>
  )
}
