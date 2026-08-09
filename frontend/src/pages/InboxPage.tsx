import { useParams, useNavigate } from 'react-router-dom'
import { useEffect } from 'react'
import { useConversationStore } from '@/store/conversation.store'
import ConversationList from '@/components/inbox/ConversationList'
import ConversationDetail from '@/components/inbox/ConversationDetail'
import { MessageSquare } from 'lucide-react'

export default function InboxPage() {
  const { id } = useParams<{ id?: string }>()
  const { setActiveConversation } = useConversationStore()
  const navigate = useNavigate()

  useEffect(() => {
    setActiveConversation(id || null)
  }, [id, setActiveConversation])

  return (
    <div className="flex h-full">
      {/* Left panel */}
      <div className="w-80 xl:w-96 border-r border-gray-200 bg-white flex flex-col shrink-0">
        <ConversationList
          activeId={id}
          onSelect={(cId) => navigate(`/inbox/${cId}`)}
        />
      </div>

      {/* Right panel */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {id ? (
          <ConversationDetail conversationId={id} />
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-gray-400">
            <MessageSquare size={48} className="mb-4 opacity-30" />
            <p className="text-lg font-medium">Select a conversation</p>
            <p className="text-sm mt-1">Choose from the list on the left</p>
          </div>
        )}
      </div>
    </div>
  )
}
