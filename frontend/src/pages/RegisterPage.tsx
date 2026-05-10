import { useState, FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { AxiosError } from 'axios'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Card } from '../components/ui/Card'
import client from '../api/client'
import { useAuthStore } from '../store/authStore'

interface ValidationError {
  loc: string[]
  msg: string
  type: string
}

function extractRegisterError(err: unknown): string {
  const ax = err as AxiosError<{ detail?: string | ValidationError[] }>
  const data = ax.response?.data
  if (!data) return 'Unable to connect to server. Please check your connection.'
  if (typeof data.detail === 'string') return data.detail
  if (Array.isArray(data.detail)) {
    return data.detail.map((d) => d.msg).join(' ')
  }
  return 'Registration failed. Please try again.'
}

export function RegisterPage() {
  const [username, setUsername] = useState('')
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
      const res = await client.post('/auth/register', { username, email, password })
      setTokens(res.data.access_token, res.data.refresh_token)
      try {
        const me = await client.get('/auth/me')
        setUser(me.data)
      } catch {
        // proceed even if profile fetch fails
      }
      navigate('/', { replace: true })
    } catch (err) {
      setError(extractRegisterError(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card className="w-full max-w-sm">
      <div className="mb-6">
        <h2 className="text-xl font-bold">Create Account</h2>
        <p className="text-sm text-gray-500 mt-1">Start tracking your investments</p>
      </div>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <Input
          label="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="yourname"
          minLength={3}
          required
          autoFocus
        />
        <Input
          label="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
          required
        />
        <Input
          label="Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Min. 8 characters"
          required
          minLength={8}
        />
        {error && (
          <div className="p-3 bg-red-900/30 border border-red-800/50 rounded-lg">
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}
        <Button type="submit" disabled={loading || !username || !email || !password} className="w-full">
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Creating account...
            </span>
          ) : 'Create Account'}
        </Button>
        <p className="text-sm text-gray-500 text-center">
          Already have an account?{' '}
          <Link to="/login" className="text-primary-400 hover:underline font-medium">Sign In</Link>
        </p>
      </form>
    </Card>
  )
}
