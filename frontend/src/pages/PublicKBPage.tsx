import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { kbApi } from '@/api/kb'
import { Search, BookOpen, ChevronRight } from 'lucide-react'

export default function PublicKBPage() {
  const { orgSlug } = useParams<{ orgSlug: string }>()
  const [search, setSearch] = useState('')

  const { data: categoriesData } = useQuery({
    queryKey: ['public-kb-categories', orgSlug],
    queryFn: () => kbApi.listPublicCategories(orgSlug!),
    enabled: !!orgSlug,
  })

  const { data: searchData, isFetching: searching } = useQuery({
    queryKey: ['public-kb-search', orgSlug, search],
    queryFn: () => kbApi.searchPublicArticles(orgSlug!, search),
    enabled: !!orgSlug && search.trim().length > 1,
  })

  const categories: any[] = categoriesData?.categories || []
  const searchResults: any[] = searchData?.articles || []

  return (
    <div className="min-h-screen bg-gradient-to-b from-indigo-50 to-white">
      {/* Header */}
      <div className="bg-indigo-600 text-white py-16 px-4 text-center">
        <div className="max-w-2xl mx-auto">
          <div className="flex items-center justify-center gap-2 mb-4">
            <BookOpen size={28} />
            <h1 className="text-3xl font-bold">Help Center</h1>
          </div>
          <p className="text-indigo-200 mb-8">Search our knowledge base or browse by category</p>
          <div className="relative">
            <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search articles..."
              className="w-full pl-10 pr-4 py-3 rounded-xl text-gray-900 bg-white shadow-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
            />
          </div>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-4 py-12">
        {/* Search results */}
        {search.trim().length > 1 && (
          <div className="mb-8">
            <h2 className="text-sm font-medium text-gray-500 mb-3">
              {searching ? 'Searching...' : `${searchResults.length} result${searchResults.length !== 1 ? 's' : ''} for "${search}"`}
            </h2>
            {searchResults.length > 0 ? (
              <div className="space-y-2">
                {searchResults.map((article: any) => (
                  <Link
                    key={article.id}
                    to={`/kb/${orgSlug}/articles/${article.slug}`}
                    className="flex items-center justify-between p-4 bg-white rounded-xl border border-gray-200 hover:border-indigo-300 hover:shadow-sm transition-all"
                  >
                    <div>
                      <div className="text-sm font-medium text-gray-900">{article.title}</div>
                      {article.excerpt && <div className="text-xs text-gray-500 mt-1 line-clamp-1">{article.excerpt}</div>}
                    </div>
                    <ChevronRight size={14} className="text-gray-400 shrink-0" />
                  </Link>
                ))}
              </div>
            ) : !searching && (
              <div className="text-center py-8 text-gray-400">
                <p className="text-sm">No articles found. Try a different search term.</p>
              </div>
            )}
          </div>
        )}

        {/* Categories */}
        {!search.trim() && (
          <>
            {categories.length > 0 ? (
              <div className="grid gap-4 sm:grid-cols-2">
                {categories.map((cat: any) => (
                  <div key={cat.id} className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                    <div className="p-4 border-b border-gray-100">
                      <h3 className="font-semibold text-gray-900 text-sm">{cat.name}</h3>
                      {cat.description && <p className="text-xs text-gray-500 mt-1">{cat.description}</p>}
                    </div>
                    <div className="divide-y divide-gray-50">
                      {(cat.articles || []).slice(0, 5).map((article: any) => (
                        <Link
                          key={article.id}
                          to={`/kb/${orgSlug}/articles/${article.slug}`}
                          className="flex items-center justify-between px-4 py-2.5 hover:bg-gray-50 transition-colors"
                        >
                          <span className="text-xs text-gray-700">{article.title}</span>
                          <ChevronRight size={12} className="text-gray-400" />
                        </Link>
                      ))}
                      {(cat.articles || []).length === 0 && (
                        <p className="px-4 py-3 text-xs text-gray-400">No articles yet</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-16 text-gray-400">
                <BookOpen size={40} className="mx-auto mb-4 opacity-30" />
                <p className="text-sm">No articles published yet.</p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
