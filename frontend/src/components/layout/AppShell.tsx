import { useSocket } from '@/hooks/useSocket'
import Sidebar from './Sidebar'

export default function AppShell({ children }: { children: React.ReactNode }) {
  useSocket()

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-hidden">{children}</main>
    </div>
  )
}
