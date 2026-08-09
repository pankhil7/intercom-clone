import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { kbApi } from '@/api/kb'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Link from '@tiptap/extension-link'
import Placeholder from '@tiptap/extension-placeholder'
import { X, Bold, Italic, List, Link as LinkIcon, Code } from 'lucide-react'
import { useToast } from '@/components/ui/toaster'

interface Props {
  article?: any
  categories: any[]
  defaultCategoryId?: string | null
  onClose: () => void
  onSaved: () => void
}

export default function ArticleEditorModal({ article, categories, defaultCategoryId, onClose, onSaved }: Props) {
  const { toast } = useToast()
  const [title, setTitle] = useState(article?.title || '')
  const [status, setStatus] = useState(article?.status || 'draft')
  const [categoryId, setCategoryId] = useState(article?.category_id || defaultCategoryId || '')

  const editor = useEditor({
    extensions: [
      StarterKit,
      Link.configure({ openOnClick: false }),
      Placeholder.configure({ placeholder: 'Write your article content here...' }),
    ],
    content: article?.content || '',
    editorProps: {
      attributes: { class: 'tiptap min-h-[400px] px-6 py-4 focus:outline-none text-sm' }
    },
  })

  const saveMut = useMutation({
    mutationFn: (data: any) =>
      article?.id ? kbApi.updateArticle(article.id, data) : kbApi.createArticle(data),
    onSuccess: () => {
      toast({ title: article ? 'Article updated' : 'Article created' })
      onSaved()
    },
    onError: () => toast({ title: 'Failed to save article', variant: 'destructive' }),
  })

  const handleSave = () => {
    if (!title.trim()) { toast({ title: 'Title is required', variant: 'destructive' }); return }
    saveMut.mutate({
      title: title.trim(),
      content: editor?.getHTML() || '',
      status,
      category_id: categoryId || undefined,
    })
  }

  const setLink = () => {
    const url = window.prompt('URL:')
    if (url) editor?.chain().focus().setLink({ href: url }).run()
  }

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center gap-4 px-6 py-4 border-b border-gray-200">
          <input
            value={title}
            onChange={e => setTitle(e.target.value)}
            placeholder="Article title..."
            className="flex-1 text-lg font-semibold border-none outline-none placeholder:text-gray-300"
          />
          <select
            value={categoryId}
            onChange={e => setCategoryId(e.target.value)}
            className="text-sm border border-gray-200 rounded-lg px-2 py-1 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="">No category</option>
            {categories.map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
          <select
            value={status}
            onChange={e => setStatus(e.target.value)}
            className="text-sm border border-gray-200 rounded-lg px-2 py-1 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="draft">Draft</option>
            <option value="published">Published</option>
            <option value="archived">Archived</option>
          </select>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 p-1"><X size={20} /></button>
        </div>

        {/* Toolbar */}
        <div className="flex items-center gap-1 px-4 py-2 border-b border-gray-100 bg-gray-50">
          {[
            { icon: Bold, action: () => editor?.chain().focus().toggleBold().run(), label: 'Bold' },
            { icon: Italic, action: () => editor?.chain().focus().toggleItalic().run(), label: 'Italic' },
            { icon: List, action: () => editor?.chain().focus().toggleBulletList().run(), label: 'List' },
            { icon: Code, action: () => editor?.chain().focus().toggleCode().run(), label: 'Code' },
            { icon: LinkIcon, action: setLink, label: 'Link' },
          ].map(({ icon: Icon, action, label }) => (
            <button
              key={label}
              onClick={action}
              title={label}
              className="p-1.5 rounded hover:bg-gray-200 text-gray-600 hover:text-gray-900 transition-colors"
            >
              <Icon size={15} />
            </button>
          ))}
        </div>

        {/* Editor */}
        <div className="flex-1 overflow-y-auto">
          <EditorContent editor={editor} />
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancel</button>
          <button
            onClick={handleSave}
            disabled={saveMut.isPending}
            className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 disabled:opacity-50"
          >
            {saveMut.isPending ? 'Saving...' : (article ? 'Update article' : 'Create article')}
          </button>
        </div>
      </div>
    </div>
  )
}
