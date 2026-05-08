import { useAuthStore } from '../../store/authStore'
import { Button } from '../ui/Button'

export function Header() {
  const { user, logout } = useAuthStore()

  return (
    <header className="h-14 bg-gray-900 border-b border-gray-800 flex items-center justify-between px-6">
      <div className="text-sm text-gray-400">Welcome, {user?.username || 'Investor'}</div>
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={logout}>
          Logout
        </Button>
      </div>
    </header>
  )
}
