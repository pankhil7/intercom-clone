import { useUIStore } from '@/store/ui.store'
import { X } from 'lucide-react'

export function Toaster() {
  const { toasts, removeToast } = useUIStore()
  if (toasts.length === 0) return null

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`flex items-start gap-3 p-4 rounded-lg shadow-lg border text-sm animate-in slide-in-from-bottom-2 ${
            t.variant === 'destructive'
              ? 'bg-red-50 border-red-200 text-red-800'
              : 'bg-white border-gray-200 text-gray-800'
          }`}
        >
          <div className="flex-1">
            <div className="font-medium">{t.title}</div>
            {t.description && <div className="text-xs mt-0.5 opacity-80">{t.description}</div>}
          </div>
          <button onClick={() => removeToast(t.id)} className="text-gray-400 hover:text-gray-600">
            <X size={14} />
          </button>
        </div>
      ))}
    </div>
  )
}

export function useToast() {
  const { addToast } = useUIStore()
  return {
    toast: (opts: { title: string; description?: string; variant?: 'default' | 'destructive' }) =>
      addToast(opts),
  }
}
