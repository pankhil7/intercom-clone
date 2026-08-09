import { useState, useRef, useCallback } from 'react'
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query'
import { conversationsApi } from '@/api/conversations'
import { settingsApi } from '@/api/settings'
import { Send, Command } from 'lucide-react'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'
import { getSocket } from '@/socket/socket'

interface Props { conversationId: string; channel: string }

export default function ReplyBox({ conversationId, channel }: Props) {
  const qc = useQueryClient()
  const [showCanned, setShowCanned] = useState(false)
  const [cannedSearch, setCannedSearch] = useState('')
  const typingTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const { data: cannedData } = useQuery({
    queryKey: ['canned-responses'],
    queryFn: settingsApi.listCannedResponses,
    staleTime: 60_000,
  })
  const cannedResponses: any[] = cannedData?.canned_responses || []

  const editor = useEditor({
    extensions: [
      StarterKit,
      Placeholder.configure({ placeholder: channel === 'email' ? 'Type your reply...' : 'Type a message...' }),
    ],
    editorProps: {
      attributes: { class: 'tiptap min-h-[80px] max-h-[200px] overflow-y-auto text-sm focus:outline-none' },
      handleKeyDown(_, event) {
        if (event.key === '/') {
          setShowCanned(true)
          setCannedSearch('')
        }
        if (event.key === 'Escape') setShowCanned(false)
        if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
          sendMessage()
          return true
        }
        // Emit typing
        const socket = getSocket()
        if (socket) {
          socket.emit('typing:start', { conversation_id: conversationId })
          if (typingTimer.current) clearTimeout(typingTimer.current)
          typingTimer.current = setTimeout(() => {
            socket.emit('typing:stop', { conversation_id: conversationId })
          }, 2000)
        }
        return false
      }
    },
  })

  const sendMut = useMutation({
    mutationFn: (content: string) =>
      conversationsApi.sendMessage(conversationId, { content, content_type: 'html' }),
    onSuccess: () => {
      editor?.commands.clearContent()
      qc.invalidateQueries({ queryKey: ['messages', conversationId] })
      qc.invalidateQueries({ queryKey: ['conversations'] })
      setShowCanned(false)
    },
  })

  const sendMessage = useCallback(() => {
    if (!editor) return
    const html = editor.getHTML()
    const text = editor.getText().trim()
    if (!text) return
    sendMut.mutate(html)
  }, [editor, sendMut])

  const insertCanned = (content: string) => {
    editor?.commands.setContent(content)
    setShowCanned(false)
  }

  const filtered = cannedSearch
    ? cannedResponses.filter(c =>
        c.name.toLowerCase().includes(cannedSearch.toLowerCase()) ||
        c.shortcut?.toLowerCase().includes(cannedSearch.toLowerCase())
      )
    : cannedResponses.slice(0, 8)

  return (
    <div className="border-t border-gray-200 bg-white shrink-0">
      {/* Canned responses picker */}
      {showCanned && (
        <div className="border-b border-gray-100 px-3 py-2">
          <div className="flex items-center gap-2 mb-2">
            <Command size={12} className="text-gray-400" />
            <input
              autoFocus
              value={cannedSearch}
              onChange={e => setCannedSearch(e.target.value)}
              placeholder="Search canned responses..."
              className="flex-1 text-xs border-none outline-none text-gray-700"
            />
            <button onClick={() => setShowCanned(false)} className="text-gray-400 hover:text-gray-600 text-xs">✕</button>
          </div>
          <div className="max-h-48 overflow-y-auto space-y-1">
            {filtered.map((c: any) => (
              <button
                key={c.id}
                onClick={() => insertCanned(c.content)}
                className="w-full text-left px-2 py-2 rounded-lg hover:bg-gray-50 text-xs"
              >
                <div className="font-medium text-gray-700">{c.name}</div>
                <div className="text-gray-400 truncate">{c.content.slice(0, 60)}</div>
              </button>
            ))}
            {filtered.length === 0 && (
              <p className="text-xs text-gray-400 px-2">No canned responses found</p>
            )}
          </div>
        </div>
      )}

      <div className="px-4 pt-3 pb-2">
        <EditorContent editor={editor} />
      </div>

      <div className="flex items-center justify-between px-4 pb-3">
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400">
            {channel === 'email' ? '📧 Email reply' : '💬 Chat message'}
          </span>
          <span className="text-xs text-gray-300">·</span>
          <span className="text-xs text-gray-400">Type / for canned responses</span>
        </div>
        <button
          onClick={sendMessage}
          disabled={sendMut.isPending}
          className="flex items-center gap-1.5 bg-indigo-600 text-white px-4 py-1.5 rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
        >
          <Send size={14} />
          {sendMut.isPending ? 'Sending...' : 'Send'}
        </button>
      </div>
    </div>
  )
}
