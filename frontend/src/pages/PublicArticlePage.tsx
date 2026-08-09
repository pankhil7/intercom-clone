import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { kbApi } from '@/api/kb'
import { ArrowLeft, BookOpen, Clock } from 'lucide-react'
import { formatMessageTime } from '@/utils/format'

export default function PublicArticlePage() {
  const { orgSlug, slug } = useParams<{ orgSlug: string; slug: string }>()

  const { data, isLoading, isError } = useQuery({
    queryKey: ['public-article', orgSlug, slug],
    queryFn: () => kbApi.getPublicArticle(orgSlug!, slug!),
    enabled: !!orgSlug && !!slug,
  })

  const article = data?.article

  if (isLoading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (isError || !article) {
    return (
      <div className="min-h-screen bg-white flex flex-col items-center justify-center gap-4">
        <BookOpen size={40} className="text-gray-300" />
        <h1 className="text-lg font-semibold text-gray-700">Article not found</h1>
        <Link to={`/kb/${orgSlug}`} className="text-sm text-indigo-600 hover:underline flex items-center gap-1">
          <ArrowLeft size={14} /> Back to Help Center
        </Link>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Top bar */}
      <div className="border-b border-gray-100 bg-white sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-4 py-3 flex items-center gap-3">
          <Link to={`/kb/${orgSlug}`} className="flex items-center gap-1 text-sm text-gray-500 hover:text-indigo-600">
            <ArrowLeft size={14} /> Help Center
          </Link>
          {article.category && (
            <>
              <span className="text-gray-300">/</span>
              <span className="text-sm text-gray-500">{article.category.name}</span>
            </>
          )}
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-4 py-12">
        {/* Article header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-3">{article.title}</h1>
          <div className="flex items-center gap-3 text-xs text-gray-400">
            {article.author && (
              <div className="flex items-center gap-1.5">
                <div className="w-5 h-5 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 text-[10px] font-medium">
                  {article.author.full_name?.[0]?.toUpperCase()}
                </div>
                <span>{article.author.full_name}</span>
              </div>
            )}
            <div className="flex items-center gap-1">
              <Clock size={11} />
              <span>Updated {article.updated_at ? formatMessageTime(article.updated_at) : '—'}</span>
            </div>
          </div>
        </div>

        {/* Article content */}
        <div
          className="prose-content max-w-none"
          dangerouslySetInnerHTML={{ __html: article.content }}
        />

        {/* Footer */}
        <div className="mt-12 pt-6 border-t border-gray-100">
          <p className="text-sm text-gray-400 text-center">Was this article helpful?</p>
          <div className="flex justify-center gap-3 mt-3">
            <button className="px-4 py-2 text-sm border border-gray-200 rounded-lg hover:bg-gray-50 text-gray-600">👍 Yes</button>
            <button className="px-4 py-2 text-sm border border-gray-200 rounded-lg hover:bg-gray-50 text-gray-600">👎 No</button>
          </div>
        </div>
      </div>
    </div>
  )
}
