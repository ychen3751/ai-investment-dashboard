import { useState, FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Card } from '../components/ui/Card'
import client from '../api/client'
import { useAuthStore } from '../store/authStore'

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
      const me = await client.get('/auth/me')
      setUser(me.data)
      navigate('/')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card className="w-full max-w-sm">
      <h2 className="text-xl font-bold mb-6">Create Account</h2>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <Input label="Username" value={username} onChange={(e) => setUsername(e.target.value)} required />
        <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <Input label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} />
        {error && <p className="text-sm text-red-400">{error}</p>}
        <Button type="submit" disabled={loading}>{loading ? 'Creating...' : 'Create Account'}</Button>
        <p className="text-sm text-gray-500 text-center">
          Already have an account? <Link to="/login" className="text-primary-400 hover:underline">Sign In</Link>
        </p>
      </form>
    </Card>
  )
}
