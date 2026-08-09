import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { kbApi } from '@/api/kb'
import { Plus, BookOpen, FileText, Edit, Trash2, Globe } from 'lucide-react'
import { useAuthStore } from '@/store/auth.store'
import ArticleEditorModal from '@/components/kb/ArticleEditorModal'
import { useToast } from '@/components/ui/toaster'

export default function KBManagePage() {
  const qc = useQueryClient()
  const { organization } = useAuthStore()
  const { toast } = useToast()
  const [selectedCategoryId, setSelectedCategoryId] = useState<string | null>(null)
  const [editingArticle, setEditingArticle] = useState<any>(null)
  const [showEditor, setShowEditor] = useState(false)
  const [showNewCategory, setShowNewCategory] = useState(false)
  const [newCategoryName, setNewCategoryName] = useState('')

  const { data: catData } = useQuery({ queryKey: ['kb-categories'], queryFn: kbApi.listCategories })
  const { data: artData } = useQuery({
    queryKey: ['kb-articles', selectedCategoryId],
    queryFn: () => kbApi.listArticles({ category_id: selectedCategoryId || undefined }),
  })

  const categories: any[] = catData?.categories || []
  const articles: any[] = artData?.articles || []

  const createCatMut = useMutation({
    mutationFn: (name: string) => kbApi.createCategory({ name }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['kb-categories'] }); setShowNewCategory(false); setNewCategoryName('') },
  })

  const deleteArtMut = useMutation({
    mutationFn: (id: string) => kbApi.deleteArticle(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['kb-articles'] }); toast({ title: 'Article deleted' }) },
  })

  const kbUrl = organization ? `/kb/${organization.slug}` : '#'

  return (
    <div className="h-full flex bg-white">
      {/* Categories sidebar */}
      <div className="w-64 border-r border-gray-200 flex flex-col">
        <div className="px-4 py-4 border-b border-gray-100">
          <div className="flex items-center justify-between mb-2">
            <h2 className="font-semibold text-gray-900">Knowledge Base</h2>
            <a href={kbUrl} target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-indigo-600" title="View public KB">
              <Globe size={14} />
            </a>
          </div>
          <button
            onClick={() => setShowNewCategory(true)}
            className="flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-700 font-medium"
          >
            <Plus size={12} /> New category
          </button>
        </div>

        {showNewCategory && (
          <div className="px-4 py-2 border-b border-gray-100">
            <input
              autoFocus
              value={newCategoryName}
              onChange={e => setNewCategoryName(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && newCategoryName.trim()) createCatMut.mutate(newCategoryName.trim())
                if (e.key === 'Escape') setShowNewCategory(false)
              }}
              className="w-full text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              placeholder="Category name..."
            />
          </div>
        )}

        <div className="flex-1 overflow-y-auto py-2">
          <button
            onClick={() => setSelectedCategoryId(null)}
            className={`w-full text-left px-4 py-2 text-sm flex items-center gap-2 ${!selectedCategoryId ? 'bg-indigo-50 text-indigo-700 font-medium' : 'text-gray-600 hover:bg-gray-50'}`}
          >
            <BookOpen size={14} /> All articles
          </button>
          {categories.map((c: any) => (
            <button
              key={c.id}
              onClick={() => setSelectedCategoryId(c.id)}
              className={`w-full text-left px-4 py-2 text-sm flex items-center gap-2 ${selectedCategoryId === c.id ? 'bg-indigo-50 text-indigo-700 font-medium' : 'text-gray-600 hover:bg-gray-50'}`}
            >
              <FileText size={14} /> {c.name}
              <span className="ml-auto text-xs text-gray-400">{c.article_count || 0}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Articles */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h3 className="font-medium text-gray-900">
            {selectedCategoryId ? categories.find(c => c.id === selectedCategoryId)?.name : 'All Articles'}
            <span className="text-gray-400 font-normal ml-2 text-sm">({articles.length})</span>
          </h3>
          <button
            onClick={() => { setEditingArticle(null); setShowEditor(true) }}
            className="flex items-center gap-1.5 bg-indigo-600 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-indigo-700"
          >
            <Plus size={14} /> New article
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {articles.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-gray-400">
              <FileText size={40} className="mb-3 opacity-30" />
              <p className="font-medium">No articles yet</p>
              <p className="text-sm mt-1">Create your first article to help customers</p>
            </div>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left text-xs font-medium text-gray-500 px-6 py-3">Title</th>
                  <th className="text-left text-xs font-medium text-gray-500 px-6 py-3">Status</th>
                  <th className="text-left text-xs font-medium text-gray-500 px-6 py-3">Views</th>
                  <th className="px-6 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {articles.map((a: any) => (
                  <tr key={a.id} className="hover:bg-gray-50">
                    <td className="px-6 py-3">
                      <span className="text-sm font-medium text-gray-900">{a.title}</span>
                    </td>
                    <td className="px-6 py-3">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        a.status === 'published' ? 'bg-green-100 text-green-700' :
                        a.status === 'archived' ? 'bg-gray-100 text-gray-600' :
                        'bg-yellow-100 text-yellow-700'
                      }`}>{a.status}</span>
                    </td>
                    <td className="px-6 py-3 text-sm text-gray-500">{a.views || 0}</td>
                    <td className="px-6 py-3">
                      <div className="flex items-center gap-2 justify-end">
                        <button onClick={() => { setEditingArticle(a); setShowEditor(true) }} className="text-gray-400 hover:text-indigo-600 p-1">
                          <Edit size={14} />
                        </button>
                        <button onClick={() => deleteArtMut.mutate(a.id)} className="text-gray-400 hover:text-red-500 p-1">
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {showEditor && (
        <ArticleEditorModal
          article={editingArticle}
          categories={categories}
          defaultCategoryId={selectedCategoryId}
          onClose={() => { setShowEditor(false); setEditingArticle(null) }}
          onSaved={() => { qc.invalidateQueries({ queryKey: ['kb-articles'] }); setShowEditor(false) }}
        />
      )}
    </div>
  )
}
