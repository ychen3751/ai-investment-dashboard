import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen gap-4">
      <h2 className="text-4xl font-bold">404</h2>
      <p className="text-gray-400">Page not found</p>
      <Link to="/" className="text-primary-400 hover:underline">Go home</Link>
    </div>
  )
}
