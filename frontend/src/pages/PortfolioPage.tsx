import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Spinner } from '../components/ui/Spinner'
import { fetchPortfolios, createPortfolio, deletePortfolio } from '../api/portfolios'
import { num, fmtPct } from '../utils/formatters'

function fmt(n: number | null | undefined) {
  if (n == null) return '-'
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2 }).format(n)
}

export function PortfolioPage() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')

  const { data: portfolios, isLoading } = useQuery({ queryKey: ['portfolios'], queryFn: fetchPortfolios })

  const createMutation = useMutation({
    mutationFn: () => createPortfolio({ name, description: description || undefined }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['portfolios'] }); setShowForm(false); setName(''); setDescription('') },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deletePortfolio(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['portfolios'] }),
  })

  if (isLoading) return <Spinner />

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Portfolios</h2>
        <Button onClick={() => setShowForm(!showForm)}>{showForm ? 'Cancel' : 'New Portfolio'}</Button>
      </div>

      {showForm && (
        <Card className="flex flex-col gap-3">
          <Input label="Portfolio Name" value={name} onChange={(e) => setName(e.target.value)} placeholder="My Portfolio" />
          <Input label="Description (optional)" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Long-term investments" />
          <Button onClick={() => createMutation.mutate()} disabled={!name || createMutation.isPending}>
            {createMutation.isPending ? 'Creating...' : 'Create'}
          </Button>
        </Card>
      )}

      {(!portfolios || portfolios.length === 0) ? (
        <Card>
          <p className="text-gray-500 text-sm">No portfolios yet. Create one to get started.</p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {portfolios.map((p) => (
            <div key={p.id} className="cursor-pointer" onClick={() => navigate(`/portfolios/${p.id}`)}><Card className="hover:border-primary-500/50 transition-colors">
              <div className="flex justify-between items-start mb-3">
                <h3 className="text-lg font-semibold">{p.name}</h3>
                <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); deleteMutation.mutate(p.id) }}>✕</Button>
              </div>
              {p.description && <p className="text-sm text-gray-500 mb-2">{p.description}</p>}
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div><span className="text-gray-500">Value</span><p className="font-medium">{fmt(p.total_value)}</p></div>
                <div><span className="text-gray-500">P&L</span><p className={p.total_pnl && p.total_pnl >= 0 ? 'text-gain font-medium' : 'text-loss font-medium'}>
                  {p.total_pnl != null ? fmt(p.total_pnl) : '-'} ({fmtPct(p.total_pnl_pct)})
                </p></div>
                <div><span className="text-gray-500">Holdings</span><p className="font-medium">{p.holding_count}</p></div>
                <div><span className="text-gray-500">Cost Basis</span><p className="font-medium">{fmt(p.total_cost)}</p></div>
              </div>
            </Card></div>
          ))}
        </div>
      )}
    </div>
  )
}
