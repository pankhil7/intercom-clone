import { Routes, Route, Navigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { useAuthStore } from '@/store/auth.store'
import { authApi } from '@/api/auth'
import AppShell from '@/components/layout/AppShell'
import LoginPage from '@/pages/LoginPage'
import SignupPage from '@/pages/SignupPage'
import AcceptInvitePage from '@/pages/AcceptInvitePage'
import InboxPage from '@/pages/InboxPage'
import ContactsPage from '@/pages/ContactsPage'
import ContactDetailPage from '@/pages/ContactDetailPage'
import KBManagePage from '@/pages/KBManagePage'
import AnalyticsPage from '@/pages/AnalyticsPage'
import SettingsPage from '@/pages/SettingsPage'
import PublicKBPage from '@/pages/PublicKBPage'
import PublicArticlePage from '@/pages/PublicArticlePage'
import { Toaster } from '@/components/ui/toaster'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  const { setAuth } = useAuthStore()
  // true while we're checking if the user has a valid refresh cookie
  const [bootstrapping, setBootstrapping] = useState(true)

  useEffect(() => {
    // On every page load / refresh, silently exchange the HttpOnly refresh cookie
    // for a new access token. If there's no cookie (or it's expired) the call
    // fails quietly and the user sees the login page.
    authApi.refresh()
      .then(data => setAuth(data.user, data.organization, data.access_token))
      .catch(() => { /* no valid cookie — stay unauthenticated */ })
      .finally(() => setBootstrapping(false))
  }, [setAuth])

  // Avoid rendering protected routes (and triggering /auth/me calls) before
  // we know whether the session is valid.
  if (bootstrapping) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/accept-invite/:token" element={<AcceptInvitePage />} />
        <Route path="/kb/:orgSlug" element={<PublicKBPage />} />
        <Route path="/kb/:orgSlug/articles/:slug" element={<PublicArticlePage />} />
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <AppShell>
                <Routes>
                  <Route path="/" element={<Navigate to="/inbox" replace />} />
                  <Route path="/inbox" element={<InboxPage />} />
                  <Route path="/inbox/:id" element={<InboxPage />} />
                  <Route path="/contacts" element={<ContactsPage />} />
                  <Route path="/contacts/:id" element={<ContactDetailPage />} />
                  <Route path="/kb" element={<KBManagePage />} />
                  <Route path="/analytics" element={<AnalyticsPage />} />
                  <Route path="/settings" element={<SettingsPage />} />
                  <Route path="/settings/:tab" element={<SettingsPage />} />
                </Routes>
              </AppShell>
            </ProtectedRoute>
          }
        />
      </Routes>
      <Toaster />
    </>
  )
}
