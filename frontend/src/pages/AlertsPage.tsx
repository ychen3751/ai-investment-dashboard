import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AxiosError } from 'axios'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Spinner } from '../components/ui/Spinner'
import { Badge } from '../components/ui/Badge'
import { toast } from '../components/ui/Toast'
import { fetchAlerts, createAlert, updateAlert, deleteAlert } from '../api/alerts'

const ALERT_TYPES = [
  { value: 'price_above', label: 'Price Above' },
  { value: 'price_below', label: 'Price Below' },
  { value: 'daily_pct_change', label: 'Daily Change %' },
  { value: 'volume_surge', label: 'Volume Spike' },
  { value: 'rsi_above', label: 'RSI Above' },
  { value: 'rsi_below', label: 'RSI Below' },
] as const

function typeBadge(t: string) {
  if (t === 'price_above' || t === 'rsi_above') return 'info' as const
  if (t === 'price_below' || t === 'rsi_below') return 'danger' as const
  if (t === 'volume_surge') return 'warning' as const
  return 'default' as const
}

function typeLabel(t: string) { return ALERT_TYPES.find((a) => a.value === t)?.label ?? t }

function renderCondition(condition: Record<string, unknown>, alertType: string) {
  if (alertType === 'price_above' || alertType === 'price_below') return `Target: $${condition.target}`
  if (alertType === 'daily_pct_change') return `Threshold: ${condition.threshold}%`
  if (alertType === 'volume_surge') return `Multiplier: ${condition.multiplier}x avg`
  if (alertType === 'rsi_above' || alertType === 'rsi_below') return `RSI Threshold: ${condition.threshold}`
  return JSON.stringify(condition)
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

export function AlertsPage() {
  const qc = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [symbol, setSymbol] = useState('')
  const [alertType, setAlertType] = useState('price_above')
  const [threshold, setThreshold] = useState('')
  const [formError, setFormError] = useState('')
  const [tab, setTab] = useState<'all' | 'active' | 'triggered'>('all')

  const { data: alerts, isLoading } = useQuery({ queryKey: ['alerts'], queryFn: () => fetchAlerts() })

  const createMut = useMutation({
    mutationFn: () => {
      let condition: Record<string, unknown> = {}
      if (alertType === 'price_above' || alertType === 'price_below')
        condition = { target: parseFloat(threshold), direction: alertType === 'price_above' ? 'above' : 'below' }
      else if (alertType === 'daily_pct_change')
        condition = { threshold: parseFloat(threshold), direction: 'above' }
      else if (alertType === 'volume_surge')
        condition = { multiplier: parseFloat(threshold) }
      else if (alertType === 'rsi_above' || alertType === 'rsi_below')
        condition = { threshold: parseFloat(threshold), direction: alertType === 'rsi_above' ? 'above' : 'below' }
      return createAlert({ symbol: symbol.toUpperCase().trim(), alert_type: alertType, condition })
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['alerts'] })
      setShowForm(false)
      setSymbol(''); setThreshold(''); setFormError('')
      toast('Alert created', 'success')
    },
    onError: (error: Error) => { setFormError(extractError(error)) },
  })

  const toggleMut = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) => updateAlert(id, { is_active }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['alerts'] }) },
    onError: (error: Error) => { toast(extractError(error), 'error') },
  })

  const deleteMut = useMutation({
    mutationFn: (id: string) => deleteAlert(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['alerts'] }); toast('Alert deleted', 'success') },
    onError: (error: Error) => { toast(extractError(error), 'error') },
  })

  const handleSubmit = () => {
    setFormError('')
    if (!symbol.trim()) { setFormError('Symbol is required'); return }
    if (!threshold || parseFloat(threshold) <= 0) { setFormError('Threshold must be greater than 0'); return }
    const n = parseFloat(threshold)
    if ((alertType === 'rsi_above' || alertType === 'rsi_below') && (n < 0 || n > 100)) {
      setFormError('RSI threshold must be between 0 and 100'); return
    }
    createMut.mutate()
  }

  const filtered = (alerts || []).filter((a) => {
    if (tab === 'active') return a.is_active && !a.triggered_at
    if (tab === 'triggered') return a.triggered_at
    return true
  })

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Alerts</h2>
        <Button onClick={() => setShowForm(!showForm)} disabled={createMut.isPending}>{showForm ? 'Cancel' : 'New Alert'}</Button>
      </div>

      {showForm && (
        <Card className="flex flex-col gap-3">
          <Input label="Symbol" value={symbol} onChange={(e) => setSymbol(e.target.value.toUpperCase())} placeholder="AAPL" />
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Type</label>
            <select value={alertType} onChange={(e) => setAlertType(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100">
              {ALERT_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </div>
          <Input label={
            alertType === 'price_above' || alertType === 'price_below' ? 'Target Price ($)' :
            alertType === 'volume_surge' ? 'Volume Multiplier' :
            alertType === 'daily_pct_change' ? '% Change Threshold' :
            'RSI Threshold (0-100)'
          } type="number" value={threshold} onChange={(e) => setThreshold(e.target.value)} placeholder="150" min="0" step="any" />
          {formError && <p className="text-xs text-red-400">{formError}</p>}
          <Button onClick={handleSubmit} disabled={createMut.isPending}>{createMut.isPending ? 'Creating...' : 'Create Alert'}</Button>
        </Card>
      )}

      <div className="flex gap-2 border-b border-gray-800 pb-2">
        {(['all', 'active', 'triggered'] as const).map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-3 py-1.5 text-sm rounded-t transition-colors ${tab === t ? 'bg-gray-800 text-gray-100 border-b-2 border-primary-500' : 'text-gray-500 hover:text-gray-300'}`}>
            {t === 'all' ? 'All' : t === 'active' ? 'Active' : 'Triggered'}
          </button>
        ))}
      </div>

      {isLoading ? <Spinner /> : filtered.length === 0 ? (
        <Card><p className="text-gray-500 text-sm">{tab === 'all' ? 'No alerts yet.' : 'No alerts in this view.'}</p></Card>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-gray-500">
                <th className="text-left py-2 px-2">Symbol</th>
                <th className="text-left py-2 px-2">Type</th>
                <th className="text-left py-2 px-2">Condition</th>
                <th className="text-center py-2 px-2">Status</th>
                <th className="text-right py-2 px-2">Triggered</th>
                <th className="text-right py-2 px-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((a) => (
                <tr key={a.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                  <td className="py-2 px-2 font-medium">{a.symbol}</td>
                  <td className="py-2 px-2"><Badge variant={typeBadge(a.alert_type)}>{typeLabel(a.alert_type)}</Badge></td>
                  <td className="py-2 px-2 text-gray-400 text-xs">{renderCondition(a.condition, a.alert_type)}</td>
                  <td className="py-2 px-2 text-center">
                    {a.triggered_at ? <Badge variant="warning">Triggered</Badge> : a.is_active ? <Badge variant="success">Active</Badge> : <Badge variant="default">Paused</Badge>}
                  </td>
                  <td className="py-2 px-2 text-right text-xs text-gray-500 tabular-nums">
                    {a.triggered_at ? new Date(a.triggered_at).toLocaleString() : '-'}
                  </td>
                  <td className="py-2 px-2 text-right whitespace-nowrap">
                    <Button variant="ghost" size="sm" onClick={() => toggleMut.mutate({ id: a.id, is_active: !a.is_active })} title={a.is_active ? 'Pause' : 'Activate'}>
                      {a.is_active ? '⏸' : '▶'}
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => deleteMut.mutate(a.id)} title="Delete">✕</Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
