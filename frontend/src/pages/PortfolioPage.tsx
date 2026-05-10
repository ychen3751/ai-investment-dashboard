import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Spinner } from '../components/ui/Spinner'
import { ConfirmDialog } from '../components/ui/ConfirmDialog'
import { toast } from '../components/ui/Toast'
import { fetchPortfolios, createPortfolio, deletePortfolio } from '../api/portfolios'
import { num } from '../utils/formatters'

function fmt(n: number | null | undefined) {
  if (n == null) return '-'
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2 }).format(num(n))
}

export function PortfolioPage() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null)

  const { data: portfolios, isLoading, error: loadError } = useQuery({ queryKey: ['portfolios'], queryFn: fetchPortfolios })

  const createMutation = useMutation({
    mutationFn: () => createPortfolio({ name, description: description || undefined }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['portfolios'] })
      setShowForm(false)
      setName('')
      setDescription('')
      toast('Portfolio created', 'success')
    },
    onError: () => {
      toast('Failed to create portfolio', 'error')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deletePortfolio(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['portfolios'] })
      setDeleteTarget(null)
      toast('Portfolio deleted', 'success')
    },
    onError: () => {
      toast('Failed to delete portfolio', 'error')
      setDeleteTarget(null)
    },
  })

  if (isLoading) return <Spinner />
  if (loadError) return <Card><p className="text-red-400 text-sm">Failed to load portfolios.</p></Card>

  const isMutating = createMutation.isPending || deleteMutation.isPending

  return (
    <div className="flex flex-col gap-6">
      {/* Delete confirmation */}
      <ConfirmDialog
        open={!!deleteTarget}
        title="Delete Portfolio"
        message="Are you sure you want to delete this portfolio? All holdings and transaction history will be lost."
        confirmLabel="Delete"
        onConfirm={() => deleteTarget && deleteMutation.mutate(deleteTarget)}
        onCancel={() => setDeleteTarget(null)}
      />

      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Portfolios</h2>
        <Button onClick={() => setShowForm(!showForm)} disabled={isMutating}>{showForm ? 'Cancel' : 'New Portfolio'}</Button>
      </div>

      {showForm && (
        <Card className="flex flex-col gap-3">
          <Input label="Portfolio Name" value={name} onChange={(e) => setName(e.target.value)} placeholder="My Portfolio" disabled={isMutating} />
          <Input label="Description (optional)" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Long-term investments" disabled={isMutating} />
          <Button onClick={() => createMutation.mutate()} disabled={!name || isMutating}>
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
            <div key={p.id} className="cursor-pointer" onClick={() => navigate(`/portfolios/${p.id}`)}>
              <Card className="hover:border-primary-500/50 transition-colors">
                <div className="flex justify-between items-start mb-3">
                  <h3 className="text-lg font-semibold">{p.name}</h3>
                  <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); setDeleteTarget(p.id) }} disabled={isMutating}>✕</Button>
                </div>
                {p.description && <p className="text-sm text-gray-500 mb-2">{p.description}</p>}
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div><span className="text-gray-500">Value</span><p className="font-medium">{fmt(p.total_value)}</p></div>
                  <div>
                    <span className="text-gray-500">P&L</span>
                    <p className={p.total_pnl && p.total_pnl >= 0 ? 'text-gain font-medium' : 'text-loss font-medium'}>
                      {p.total_pnl != null ? fmt(p.total_pnl) : '-'}
                      {p.total_pnl_pct != null ? ` (${p.total_pnl_pct >= 0 ? '+' : ''}${p.total_pnl_pct.toFixed(2)}%)` : ''}
                    </p>
                  </div>
                  <div><span className="text-gray-500">Holdings</span><p className="font-medium">{p.holding_count}</p></div>
                  <div><span className="text-gray-500">Cost Basis</span><p className="font-medium">{fmt(p.total_cost)}</p></div>
                </div>
              </Card>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
