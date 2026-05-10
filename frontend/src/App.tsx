import { useEffect, useState } from 'react'
import { RouterProvider } from 'react-router-dom'
import { router } from './router'
import { ToastContainer } from './components/ui/Toast'
import { Spinner } from './components/ui/Spinner'
import { AIChat } from './components/chat/AIChat'
import client from './api/client'
import { useAuthStore } from './store/authStore'

/** Verifies the stored JWT is still valid on cold page load.
 *  If /auth/me 401s the persisted tokens are stale and the user is
 *  silently logged out.  The spinner prevents a flash of the login page
 *  before the check completes. */
function AuthGate({ children }: { children: React.ReactNode }) {
  const [checking, setChecking] = useState(true)
  const { accessToken, setUser, logout, isAuthenticated } = useAuthStore()

  useEffect(() => {
    // Only verify if we have a stored token (avoid call for non-auth users)
    if (!accessToken) {
      setChecking(false)
      return
    }
    client
      .get('/auth/me')
      .then((res) => setUser(res.data))
      .catch(() => {
        // Stored token is stale — wipe it
        logout()
      })
      .finally(() => setChecking(false))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Show nothing while checking — avoids login-page flash
  if (checking && isAuthenticated) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-950">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-gray-500">Loading...</p>
        </div>
      </div>
    )
  }

  return <>{children}</>
}

export default function App() {
  return (
    <AuthGate>
      <RouterProvider router={router} />
      <ToastContainer />
      <AIChat />
    </AuthGate>
  )
}
