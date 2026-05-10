import { useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AxiosError } from 'axios'
import { Card, MetricCard } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Spinner } from '../components/ui/Spinner'
import { ConfirmDialog } from '../components/ui/ConfirmDialog'
import { toast } from '../components/ui/Toast'
import { fetchPortfolio, fetchHoldings, addHolding, updateHolding, removeHolding, deletePortfolio, fetchPerformance } from '../api/portfolios'
import { PriceChange } from '../components/shared/PriceChange'
import { num, fmtPct, fmtCurrency } from '../utils/formatters'
import type { Holding } from '../types/portfolio'

interface FormErrors {
  symbol?: string
  quantity?: string
  avgCost?: string
  general?: string
}

interface EditState {
  holdingId: string
  quantity: string
  avgCost: string
}

function extractError(error: Error): string {
  const axErr = error as AxiosError
  const data = axErr.response?.data as Record<string, unknown> | undefined
  if (data?.detail) {
    if (typeof data.detail === 'string') return data.detail
    if (Array.isArray(data.detail)) return data.detail.map((d: Record<string, unknown>) => String(d.msg ?? '')).join('; ')
  }
  return error.message || 'Request failed'
}

export function PortfolioDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()

  const [showForm, setShowForm] = useState(false)
  const [symbol, setSymbol] = useState('')
  const [quantity, setQuantity] = useState('')
  const [avgCost, setAvgCost] = useState('')
  const [errors, setErrors] = useState<FormErrors>({})
  const [editState, setEditState] = useState<EditState | null>(null)
  const [confirmDeleteHolding, setConfirmDeleteHolding] = useState<string | null>(null)
  const [confirmDeletePortfolio, setConfirmDeletePortfolio] = useState(false)

  const { data: portfolio, isLoading: ploading } = useQuery({
    queryKey: ['portfolio', id],
    queryFn: () => fetchPortfolio(id!),
    enabled: !!id,
  })
  const { data: holdings, isLoading: hloading } = useQuery({
    queryKey: ['holdings', id],
    queryFn: () => fetchHoldings(id!),
    enabled: !!id,
  })
  const { data: perf } = useQuery({
    queryKey: ['performance', id],
    queryFn: () => fetchPerformance(id!),
    enabled: !!id,
  })

  const invalidateAll = useCallback(() => {
    qc.invalidateQueries({ queryKey: ['holdings', id] })
    qc.invalidateQueries({ queryKey: ['portfolio', id] })
    qc.invalidateQueries({ queryKey: ['performance', id] })
  }, [qc, id])

  const addHoldingMut = useMutation({
    mutationFn: () =>
      addHolding(id!, {
        symbol: symbol.toUpperCase().trim(),
        quantity: parseFloat(quantity),
        average_cost_basis: parseFloat(avgCost),
      }),
    onSuccess: () => {
      invalidateAll()
      setShowForm(false)
      setSymbol('')
      setQuantity('')
      setAvgCost('')
      setErrors({})
      toast('Holding added', 'success')
    },
    onError: (error: Error) => {
      setErrors({ general: extractError(error) })
    },
  })

  const updateHoldingMut = useMutation({
    mutationFn: ({ holdingId, qty, cost }: { holdingId: string; qty: number; cost: number }) =>
      updateHolding(id!, holdingId, { quantity: qty, average_cost_basis: cost }),
    onSuccess: () => {
      invalidateAll()
      setEditState(null)
      setErrors({})
      toast('Holding updated', 'success')
    },
    onError: (error: Error) => {
      const msg = extractError(error)
      setErrors({ general: msg })
      toast(msg, 'error')
    },
  })

  const removeHoldingMut = useMutation({
    mutationFn: (holdingId: string) => removeHolding(id!, holdingId),
    onSuccess: () => {
      invalidateAll()
      setConfirmDeleteHolding(null)
      toast('Holding removed', 'success')
    },
    onError: (error: Error) => {
      toast(extractError(error), 'error')
      setConfirmDeleteHolding(null)
    },
  })

  const deletePortfolioMut = useMutation({
    mutationFn: () => deletePortfolio(id!),
    onSuccess: () => {
      toast('Portfolio deleted', 'success')
      navigate('/portfolios')
    },
    onError: (error: Error) => {
      toast(extractError(error), 'error')
      setConfirmDeletePortfolio(false)
    },
  })

  const validate = useCallback((): boolean => {
    const e: FormErrors = {}
    const sym = symbol.trim().toUpperCase()
    if (!sym) e.symbol = 'Symbol is required'
    if (!quantity || parseFloat(quantity) <= 0 || isNaN(parseFloat(quantity))) e.quantity = 'Shares must be greater than 0'
    if (!avgCost || parseFloat(avgCost) <= 0 || isNaN(parseFloat(avgCost))) e.avgCost = 'Average cost must be greater than 0'
    setErrors(e)
    return Object.keys(e).length === 0
  }, [symbol, quantity, avgCost])

  const handleAddSubmit = () => {
    if (!validate()) return
    addHoldingMut.mutate()
  }

  const openForm = () => {
    setShowForm(true)
    setEditState(null)
    setErrors({})
  }

  const closeForm = () => {
    setShowForm(false)
    setSymbol('')
    setQuantity('')
    setAvgCost('')
    setErrors({})
  }

  const startEdit = (h: Holding) => {
    setEditState({
      holdingId: h.id,
      quantity: String(h.quantity),
      avgCost: String(num(h.average_cost_basis)),
    })
    setShowForm(false)
    setErrors({})
  }

  const cancelEdit = () => {
    setEditState(null)
    setErrors({})
  }

  const saveEdit = () => {
    if (!editState) return
    const qty = parseFloat(editState.quantity)
    const cost = parseFloat(editState.avgCost)
    if (isNaN(qty) || qty <= 0) {
      setErrors({ quantity: 'Shares must be greater than 0' })
      return
    }
    if (isNaN(cost) || cost <= 0) {
      setErrors({ avgCost: 'Average cost must be greater than 0' })
      return
    }
    setErrors({})
    updateHoldingMut.mutate({ holdingId: editState.holdingId, qty, cost })
  }

  if (ploading) return <Spinner />
  if (!portfolio) return <p className="text-gray-500">Portfolio not found</p>

  const isMutating = addHoldingMut.isPending || updateHoldingMut.isPending || removeHoldingMut.isPending || deletePortfolioMut.isPending

  return (
    <div className="flex flex-col gap-6">
      {/* Confirmations */}
      <ConfirmDialog
        open={!!confirmDeleteHolding}
        title="Remove Holding"
        message="Are you sure you want to remove this holding? This action cannot be undone."
        confirmLabel="Remove"
        onConfirm={() => confirmDeleteHolding && removeHoldingMut.mutate(confirmDeleteHolding)}
        onCancel={() => setConfirmDeleteHolding(null)}
      />
      <ConfirmDialog
        open={confirmDeletePortfolio}
        title="Delete Portfolio"
        message="Are you sure you want to delete this portfolio and all its holdings? This action cannot be undone."
        confirmLabel="Delete"
        onConfirm={() => deletePortfolioMut.mutate()}
        onCancel={() => setConfirmDeletePortfolio(false)}
      />

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <button onClick={() => navigate('/portfolios')} className="text-sm text-primary-400 hover:underline mb-1">&larr; Back</button>
          <h2 className="text-2xl font-bold">{portfolio.name}</h2>
          {portfolio.description && <p className="text-sm text-gray-500">{portfolio.description}</p>}
        </div>
        <Button variant="danger" size="sm" onClick={() => setConfirmDeletePortfolio(true)} disabled={isMutating}>Delete</Button>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard label="Total Value" value={fmtCurrency(portfolio.total_value)} />
        <MetricCard label="Total P&L" value={fmtCurrency(portfolio.total_pnl)} changePct={num(portfolio.total_pnl_pct)} change={portfolio.total_pnl != null ? fmtCurrency(portfolio.total_pnl) : undefined} />
        <MetricCard label="Cost Basis" value={fmtCurrency(portfolio.total_cost)} />
        <MetricCard label="Holdings" value={String(portfolio.holding_count)} />
      </div>

      {/* Performance */}
      {perf && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <MetricCard label="Return" value={perf.total_return_pct != null ? `${perf.total_return_pct >= 0 ? '+' : ''}${perf.total_return_pct.toFixed(2)}%` : 'N/A'} />
          <MetricCard label="Volatility (Ann.)" value={perf.volatility_pct != null ? `${perf.volatility_pct.toFixed(2)}%` : 'N/A'} />
          <MetricCard label="Sharpe Ratio" value={perf.sharpe_ratio != null ? perf.sharpe_ratio.toFixed(2) : 'N/A'} />
          <MetricCard label="Max Drawdown" value={perf.max_drawdown_pct != null ? `${perf.max_drawdown_pct.toFixed(2)}%` : 'N/A'} />
        </div>
      )}

      {/* Holdings */}
      <Card title="Holdings">
        <div className="mb-3 flex items-center gap-3">
          <Button size="sm" onClick={showForm ? closeForm : openForm} disabled={!!editState || isMutating}>
            {showForm ? 'Cancel' : 'Add Holding'}
          </Button>
          {addHoldingMut.isPending && <span className="text-xs text-gray-500">Adding...</span>}
          {updateHoldingMut.isPending && <span className="text-xs text-gray-500">Saving...</span>}
        </div>

        {/* Add Holding Form */}
        {showForm && (
          <div className="flex flex-col gap-3 mb-4 p-4 bg-gray-800/50 rounded-lg border border-gray-700/50">
            <div>
              <label className="text-sm text-gray-400 mb-1 block">Symbol</label>
              <Input
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                placeholder="e.g. AAPL, MSFT, NVDA..."
                className="w-full"
                disabled={isMutating}
              />
              {errors.symbol && <p className="text-xs text-red-400 mt-1">{errors.symbol}</p>}
            </div>
            <div>
              <Input label="Shares" type="number" value={quantity} onChange={(e) => setQuantity(e.target.value)} placeholder="100" min="0" step="any" disabled={isMutating} />
              {errors.quantity && <p className="text-xs text-red-400 mt-1">{errors.quantity}</p>}
            </div>
            <div>
              <Input label="Avg Cost Per Share ($)" type="number" value={avgCost} onChange={(e) => setAvgCost(e.target.value)} placeholder="150.00" min="0" step="any" disabled={isMutating} />
              {errors.avgCost && <p className="text-xs text-red-400 mt-1">{errors.avgCost}</p>}
            </div>
            {errors.general && (
              <div className="p-2 bg-red-900/30 border border-red-800/50 rounded-lg"><p className="text-xs text-red-400">{errors.general}</p></div>
            )}
            <div className="flex gap-2">
              <Button onClick={handleAddSubmit} disabled={isMutating}>{addHoldingMut.isPending ? 'Adding...' : 'Add Holding'}</Button>
              <Button variant="secondary" onClick={closeForm} disabled={isMutating}>Cancel</Button>
            </div>
          </div>
        )}

        {errors.general && !showForm && !editState && (
          <div className="mb-3 p-2 bg-red-900/30 border border-red-800/50 rounded-lg"><p className="text-xs text-red-400">{errors.general}</p></div>
        )}

        {/* Holdings Table */}
        {hloading ? (
          <Spinner />
        ) : !holdings || holdings.length === 0 ? (
          <p className="text-gray-500 text-sm">No holdings. Add stocks to track performance.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800 text-gray-500">
                  <th className="text-left py-2 px-2">Symbol</th>
                  <th className="text-right py-2 px-2">Shares</th>
                  <th className="text-right py-2 px-2">Avg Cost</th>
                  <th className="text-right py-2 px-2">Price</th>
                  <th className="text-right py-2 px-2">Day</th>
                  <th className="text-right py-2 px-2">Market Value</th>
                  <th className="text-right py-2 px-2">P&L</th>
                  <th className="text-right py-2 px-2">Alloc</th>
                  <th className="py-2 px-2"></th>
                </tr>
              </thead>
              <tbody>
                {holdings.map((h) => (
                  <tr key={h.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                    <td className="py-2 px-2 font-medium">{h.symbol}</td>

                    {editState?.holdingId === h.id ? (
                      <>
                        <td className="py-1 px-2">
                          <input type="number" value={editState.quantity}
                            onChange={(e) => setEditState({ ...editState, quantity: e.target.value })}
                            className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm text-right tabular-nums focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
                            min="0" step="any" disabled={isMutating} />
                        </td>
                        <td className="py-1 px-2">
                          <input type="number" value={editState.avgCost}
                            onChange={(e) => setEditState({ ...editState, avgCost: e.target.value })}
                            className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm text-right tabular-nums focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
                            min="0" step="any" disabled={isMutating} />
                        </td>
                        <td className="py-2 px-2 text-right tabular-nums">{fmtCurrency(h.current_price)}</td>
                        <td className="py-2 px-2 text-right">{h.day_change != null ? <PriceChange value={num(h.day_change)} pct={num(h.day_change_pct)} /> : '-'}</td>
                        <td className="py-2 px-2 text-right tabular-nums">{fmtCurrency(h.market_value)}</td>
                        <td className={`py-2 px-2 text-right tabular-nums ${num(h.total_pnl) >= 0 ? 'text-gain' : 'text-loss'}`}>
                          {fmtCurrency(h.total_pnl)} ({fmtPct(h.total_pnl_pct)})
                        </td>
                        <td className="py-2 px-2 text-right tabular-nums">{h.allocation_pct != null ? `${num(h.allocation_pct).toFixed(1)}%` : '-'}</td>
                        <td className="py-2 px-2 text-right whitespace-nowrap">
                          <Button size="sm" onClick={saveEdit} disabled={isMutating} className="mr-1">Save</Button>
                          <Button variant="ghost" size="sm" onClick={cancelEdit} disabled={isMutating}>Cancel</Button>
                        </td>
                      </>
                    ) : (
                      <>
                        <td className="py-2 px-2 text-right tabular-nums">{h.quantity}</td>
                        <td className="py-2 px-2 text-right tabular-nums">{fmtCurrency(h.average_cost_basis)}</td>
                        <td className="py-2 px-2 text-right tabular-nums">{fmtCurrency(h.current_price)}</td>
                        <td className="py-2 px-2 text-right">{h.day_change != null ? <PriceChange value={num(h.day_change)} pct={num(h.day_change_pct)} /> : '-'}</td>
                        <td className="py-2 px-2 text-right tabular-nums">{fmtCurrency(h.market_value)}</td>
                        <td className={`py-2 px-2 text-right tabular-nums ${num(h.total_pnl) >= 0 ? 'text-gain' : 'text-loss'}`}>
                          {fmtCurrency(h.total_pnl)} ({fmtPct(h.total_pnl_pct)})
                        </td>
                        <td className="py-2 px-2 text-right tabular-nums">{h.allocation_pct != null ? `${num(h.allocation_pct).toFixed(1)}%` : '-'}</td>
                        <td className="py-2 px-2 text-right whitespace-nowrap">
                          <Button variant="ghost" size="sm" onClick={() => startEdit(h)} title="Edit holding" disabled={isMutating}>✎</Button>
                          <Button variant="ghost" size="sm" onClick={() => setConfirmDeleteHolding(h.id)} title="Remove holding" disabled={isMutating}>✕</Button>
                        </td>
                      </>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}
