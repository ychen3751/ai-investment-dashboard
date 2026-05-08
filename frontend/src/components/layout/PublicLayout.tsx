import { Outlet } from 'react-router-dom'

export function PublicLayout() {
  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <Outlet />
    </div>
  )
}
