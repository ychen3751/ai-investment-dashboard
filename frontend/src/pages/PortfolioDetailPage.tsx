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
import { fetchPortfolio, fetchHoldings, addHolding, updateHolding, removeHolding, deletePortfolio, fetchPerformance, fetchPortfolioInsights, fetchOptions, createOption, updateOption, deleteOption } from '../api/portfolios'
import type { OptionPosition } from '../types/option'
import { Badge } from '../components/ui/Badge'
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
  const [activeTab, setActiveTab] = useState<'stocks' | 'options'>('stocks')

  // Options form state
  const [optSymbol, setOptSymbol] = useState('')
  const [optType, setOptType] = useState<'call' | 'put'>('call')
  const [optSide, setOptSide] = useState<'long' | 'short'>('long')
  const [optStrike, setOptStrike] = useState('')
  const [optExpiry, setOptExpiry] = useState('')
  const [optContracts, setOptContracts] = useState('')
  const [optPremium, setOptPremium] = useState('')
  const [optEditId, setOptEditId] = useState<string | null>(null)
  const [optFormOpen, setOptFormOpen] = useState(false)
  const [optFormError, setOptFormError] = useState('')

  const { data: portfolio, isLoading: ploading } = useQuery({
    queryKey: ['portfolio', id],
    queryFn: () => fetchPortfolio(id!),
    enabled: !!id,
  })
  const { data: holdings, isLoading: hloading } = useQuery({
    queryKey: ['holdings', id],
    queryFn: () => fetchHoldings(id!),
    enabled: !!id,
    refetchInterval: 30_000,
  })
  const { data: perf } = useQuery({
    queryKey: ['performance', id],
    queryFn: () => fetchPerformance(id!),
    enabled: !!id,
  })
  const { data: insights } = useQuery({
    queryKey: ['insights', id],
    queryFn: () => fetchPortfolioInsights(id!),
    enabled: !!id,
  })
  const { data: options, isLoading: optsLoading } = useQuery({
    queryKey: ['options', id],
    queryFn: () => fetchOptions(id!),
    enabled: !!id,
  })

  const invalidateAll = useCallback(() => {
    qc.invalidateQueries({ queryKey: ['holdings', id] })
    qc.invalidateQueries({ queryKey: ['portfolio', id] })
    qc.invalidateQueries({ queryKey: ['performance', id] })
    qc.invalidateQueries({ queryKey: ['insights', id] })
    qc.invalidateQueries({ queryKey: ['options', id] })
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

  const createOptMut = useMutation({
    mutationFn: () => createOption(id!, {
      underlying_symbol: optSymbol.toUpperCase().trim(),
      option_type: optType, side: optSide,
      strike_price: parseFloat(optStrike),
      expiration_date: optExpiry,
      contracts: parseInt(optContracts),
      premium_per_contract: parseFloat(optPremium),
    }),
    onSuccess: () => { invalidateAll(); setOptFormOpen(false); clearOptForm(); toast('Option added', 'success') },
    onError: (error: Error) => { setOptFormError(extractError(error)) },
  })

  const updateOptMut = useMutation({
    mutationFn: () => updateOption(id!, optEditId!, { contracts: parseInt(optContracts), premium_per_contract: parseFloat(optPremium) }),
    onSuccess: () => { invalidateAll(); setOptEditId(null); clearOptForm(); toast('Option updated', 'success') },
    onError: (error: Error) => { setOptFormError(extractError(error)) },
  })

  const deleteOptMut = useMutation({
    mutationFn: (oid: string) => deleteOption(id!, oid),
    onSuccess: () => { invalidateAll(); toast('Option removed', 'success') },
    onError: (error: Error) => { toast(extractError(error), 'error') },
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

  const clearOptForm = () => {
    setOptSymbol(''); setOptType('call'); setOptSide('long')
    setOptStrike(''); setOptExpiry(''); setOptContracts(''); setOptPremium('')
    setOptFormError('')
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

      {/* Insights */}
      {insights !== null && insights !== undefined && (() => {
        const raw = (insights ?? {}) as Record<string, unknown>
        const cards = Object.entries(raw).filter(([k]) => k !== 'ai_enriched' && k !== 'ai_summary') as Array<[string, { label: string; summary: string; detail?: string; severity: string }]>
        const aiSummary = raw.ai_summary as string | undefined
        return (
          <div>
            <div className="flex items-center gap-2 mb-3">
              <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Portfolio Insights</h3>
              <div className="h-px flex-1 bg-gradient-to-r from-gray-800 to-transparent" />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {cards.map(([key, i]) => {
                const sc = i.severity === 'high' ? 'border-l-red-500/60' : i.severity === 'medium' ? 'border-l-yellow-500/60' : i.severity === 'positive' ? 'border-l-green-500/60' : 'border-l-gray-600/40'
                const bv = i.severity === 'high' ? 'danger' as const : i.severity === 'positive' ? 'success' as const : i.severity === 'medium' ? 'warning' as const : 'default' as const
                return (
                  <div key={key} className={`bg-gray-900/60 rounded-xl border border-gray-800/80 border-l-4 ${sc} p-4`}>
                    <div className="flex items-center gap-2 mb-1.5"><Badge variant={bv}>{i.label}</Badge></div>
                    <p className="text-sm text-gray-300 leading-relaxed">{i.summary}</p>
                    {i.detail && <p className="text-xs text-gray-600 mt-1.5">{i.detail}</p>}
                  </div>
                )
              })}
            </div>
            {aiSummary && (
              <div className="mt-3 p-3 bg-primary-600/5 border border-primary-800/20 rounded-xl">
                <p className="text-xs text-gray-500 mb-1">AI Summary</p>
                <p className="text-sm text-gray-300 leading-relaxed">{aiSummary}</p>
              </div>
            )}
          </div>
        )
      })()}

      {/* Tabs: Stocks | Options */}
      <div className="flex gap-1 border-b border-gray-800 pb-0">
        <button onClick={() => setActiveTab('stocks')}
          className={`px-4 py-2 text-sm font-medium rounded-t transition-colors ${activeTab === 'stocks' ? 'bg-gray-800 text-gray-100 border-b-2 border-primary-500' : 'text-gray-500 hover:text-gray-300'}`}>
          Stocks {holdings && holdings.length > 0 ? `(${holdings.length})` : ''}
        </button>
        <button onClick={() => setActiveTab('options')}
          className={`px-4 py-2 text-sm font-medium rounded-t transition-colors ${activeTab === 'options' ? 'bg-gray-800 text-gray-100 border-b-2 border-primary-500' : 'text-gray-500 hover:text-gray-300'}`}>
          Options {options && options.length > 0 ? `(${options.length})` : ''}
        </button>
      </div>

      {/* ── Stocks Tab ───────────────────────────────────────────── */}
      {activeTab === 'stocks' && (
      <Card title="Holdings">
        <div className="mb-3 flex items-center gap-3">
          <Button size="sm" onClick={showForm ? closeForm : openForm} disabled={!!editState || isMutating}>
            {showForm ? 'Cancel' : 'Add Holding'}
          </Button>
          {addHoldingMut.isPending && <span className="text-xs text-gray-500">Adding...</span>}
          {updateHoldingMut.isPending && <span className="text-xs text-gray-500">Saving...</span>}
        </div>

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
      )}

      {/* Options Tab */}
      {activeTab === 'options' && (
      <Card title="Options Positions">
        <div className="mb-3">
          <Button size="sm" onClick={() => { setOptFormOpen(!optFormOpen); clearOptForm() }} disabled={isMutating}>{optFormOpen ? 'Cancel' : 'Add Option'}</Button>
        </div>
        {optFormOpen && (
          <div className="flex flex-col gap-3 mb-4 p-4 bg-gray-800/50 rounded-lg border border-gray-700/50">
            <Input label="Underlying" value={optSymbol} onChange={(e) => setOptSymbol(e.target.value.toUpperCase())} placeholder="AAPL" />
            <div className="flex gap-2">
              <select value={optType} onChange={(e) => setOptType(e.target.value as 'call' | 'put')}
                className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100">
                <option value="call">Call</option><option value="put">Put</option>
              </select>
              <select value={optSide} onChange={(e) => setOptSide(e.target.value as 'long' | 'short')}
                className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100">
                <option value="long">Long</option><option value="short">Short</option>
              </select>
            </div>
            <div className="flex gap-2">
              <Input label="Strike ($)" type="number" value={optStrike} onChange={(e) => setOptStrike(e.target.value)} placeholder="300" min="0" step="any" />
              <Input label="Expiration" type="date" value={optExpiry} onChange={(e) => setOptExpiry(e.target.value)} />
            </div>
            <div className="flex gap-2">
              <Input label="Contracts" type="number" value={optContracts} onChange={(e) => setOptContracts(e.target.value)} placeholder="1" min="1" step="1" />
              <Input label="Premium/contract ($)" type="number" value={optPremium} onChange={(e) => setOptPremium(e.target.value)} placeholder="5.00" min="0" step="any" />
            </div>
            {optFormError && <p className="text-xs text-red-400">{optFormError}</p>}
            <Button onClick={() => {
              if (!optSymbol || !optStrike || !optExpiry || !optContracts || !optPremium) {
                setOptFormError('All fields required'); return
              }
              setOptFormError('')
              optEditId ? updateOptMut.mutate() : createOptMut.mutate()
            }} disabled={createOptMut.isPending || updateOptMut.isPending}>
              {optEditId ? 'Update' : 'Add Option'}
            </Button>
          </div>
        )}
        {optsLoading ? <Spinner /> : !options || options.length === 0 ? (
          <p className="text-gray-500 text-sm">No option positions.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800 text-gray-500">
                  <th className="text-left py-2 px-2">Symbol</th>
                  <th className="text-left py-2 px-2">Type/Side</th>
                  <th className="text-right py-2 px-2">Strike</th>
                  <th className="text-right py-2 px-2">Expiry</th>
                  <th className="text-right py-2 px-2">Ctr</th>
                  <th className="text-right py-2 px-2">Premium</th>
                  <th className="text-right py-2 px-2">Price</th>
                  <th className="text-right py-2 px-2">Mkt Val</th>
                  <th className="text-right py-2 px-2">P&L</th>
                  <th className="text-center py-2 px-2">Status</th>
                  <th className="py-2 px-2"></th>
                </tr>
              </thead>
              <tbody>
                {options.map((o: OptionPosition) => (
                  <tr key={o.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                    <td className="py-2 px-2 font-medium">{o.underlying_symbol}</td>
                    <td className="py-2 px-2">
                      <Badge variant={o.option_type === 'call' ? 'success' : 'danger'}>{o.option_type.toUpperCase()}</Badge>
                      <span className="ml-1 text-xs text-gray-500">{o.side.toUpperCase()}</span>
                    </td>
                    <td className="py-2 px-2 text-right tabular-nums">${num(o.strike_price).toFixed(2)}</td>
                    <td className="py-2 px-2 text-right tabular-nums text-xs">{o.expiration_date}</td>
                    <td className="py-2 px-2 text-right tabular-nums">{o.contracts}</td>
                    <td className="py-2 px-2 text-right tabular-nums">${num(o.premium_per_contract).toFixed(2)}</td>
                    <td className="py-2 px-2 text-right tabular-nums">{o.current_price ? `$${num(o.current_price).toFixed(2)}` : '—'}</td>
                    <td className="py-2 px-2 text-right tabular-nums">{o.market_value != null ? `$${num(o.market_value).toFixed(0)}` : '—'}</td>
                    <td className={`py-2 px-2 text-right tabular-nums ${num(o.unrealized_pnl) >= 0 ? 'text-gain' : 'text-loss'}`}>
                      {o.unrealized_pnl != null ? `${num(o.unrealized_pnl) >= 0 ? '+' : ''}$${num(o.unrealized_pnl).toFixed(0)}` : '—'}
                    </td>
                    <td className="py-2 px-2 text-center">
                      {o.status ? <Badge variant={o.status === 'ITM' ? 'success' : o.status === 'OTM' ? 'default' : 'warning'}>{o.status}</Badge> : '—'}
                    </td>
                    <td className="py-2 px-2 text-right">
                      <Button variant="ghost" size="sm" onClick={() => deleteOptMut.mutate(o.id)} disabled={isMutating} title="Delete">✕</Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
      )}

    </div>
  )
}
