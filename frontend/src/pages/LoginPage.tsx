import { useState, FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { AxiosError } from 'axios'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Card } from '../components/ui/Card'
import client from '../api/client'
import { useAuthStore } from '../store/authStore'

export function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { setUser, setTokens } = useAuthStore()

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await client.post('/auth/login', { email, password })
      setTokens(res.data.access_token, res.data.refresh_token)

      try {
        const me = await client.get('/auth/me')
        setUser(me.data)
      } catch {
        // Token works but profile fetch failed — navigate anyway
      }

      navigate('/', { replace: true })
    } catch (err) {
      const ax = err as AxiosError<{ detail?: string }>
      if (ax.response) {
        const detail = ax.response.data?.detail
        setError(typeof detail === 'string' ? detail : 'Invalid email or password')
      } else if (ax.request) {
        setError('Unable to connect to server. Please check your connection.')
      } else {
        setError('An unexpected error occurred. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card className="w-full max-w-sm">
      <div className="mb-6">
        <h2 className="text-xl font-bold">Sign In</h2>
        <p className="text-sm text-gray-500 mt-1">Access your investment dashboard</p>
      </div>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <Input
          label="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
          required
          autoFocus
        />
        <Input
          label="Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Enter your password"
          required
        />
        {error && (
          <div className="p-3 bg-red-900/30 border border-red-800/50 rounded-lg">
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}
        <Button type="submit" disabled={loading || !email || !password} className="w-full">
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Signing in...
            </span>
          ) : 'Sign In'}
        </Button>
        <p className="text-sm text-gray-500 text-center">
          Don't have an account?{' '}
          <Link to="/register" className="text-primary-400 hover:underline font-medium">Create one</Link>
        </p>
      </form>
    </Card>
  )
}
