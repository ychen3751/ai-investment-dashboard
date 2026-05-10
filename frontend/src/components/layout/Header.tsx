import { useState } from 'react'
import { useAuthStore } from '../../store/authStore'
import { Button } from '../ui/Button'
import client from '../../api/client'

export function Header() {
  const { user, refreshToken, logout } = useAuthStore()
  const [loggingOut, setLoggingOut] = useState(false)

  const handleLogout = async () => {
    setLoggingOut(true)
    try {
      if (refreshToken) {
        await client.post('/auth/logout', { refresh_token: refreshToken })
      }
    } catch {
      // Best-effort: backend logout is a courtesy, not a requirement
    } finally {
      logout()
    }
  }

  return (
    <header className="h-14 bg-gray-900 border-b border-gray-800 flex items-center justify-between px-6">
      <div className="text-sm text-gray-400">
        {user ? (
          <span>Welcome, <span className="text-gray-200 font-medium">{user.username}</span></span>
        ) : (
          <span>AI Investment Dashboard</span>
        )}
      </div>
      <div className="flex items-center gap-4">
        {user && (
          <Button variant="ghost" size="sm" onClick={handleLogout} disabled={loggingOut}>
            {loggingOut ? 'Signing out...' : 'Sign Out'}
          </Button>
        )}
      </div>
    </header>
  )
}
