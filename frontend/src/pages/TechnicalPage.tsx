import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card } from '../components/ui/Card'
import { Spinner } from '../components/ui/Spinner'
import { Badge } from '../components/ui/Badge'
import { SymbolSearch } from '../components/shared/SymbolSearch'
import { CandlestickChart } from '../components/charts/CandlestickChart'
import { LineChart } from '../components/charts/LineChart'
import { fetchTechnicalAnalysis } from '../api/technical'
import { useQuote } from '../hooks/useMarketData'
import { num, fmtCurrency } from '../utils/formatters'
import type { TechnicalSignal } from '../types/technical'

const RANGES = [
  { value: '1mo', label: '1M' },
  { value: '3mo', label: '3M' },
  { value: '6mo', label: '6M' },
  { value: '1y', label: '1Y' },
] as const

function signalBadgeVariant(s: string) {
  if (s === 'bullish') return 'success' as const
  if (s === 'bearish') return 'danger' as const
  return 'default' as const
}

function SignalCard({ label, count, color }: { label: string; count: number; color: string }) {
  return (
    <div className="flex flex-col items-center p-3 bg-gray-800/50 rounded-lg">
      <span className="text-2xl font-bold" style={{ color }}>{count}</span>
      <span className="text-xs text-gray-500">{label}</span>
    </div>
  )
}

export function TechnicalPage() {
  const [symbol, setSymbol] = useState('')
  const [range, setRange] = useState('3mo')

  const { data, isLoading, error } = useQuery({
    queryKey: ['technical', symbol, range],
    queryFn: () => fetchTechnicalAnalysis(symbol, '1d', range),
    enabled: !!symbol,
  })

  const { data: liveQuote } = useQuote(symbol)
  const lastPrice = liveQuote?.price ?? (data?.prices ? data.prices[data.prices.length - 1] : null)

  const bullishCount = useMemo(
    () => data?.signals?.filter((s: TechnicalSignal) => s.signal === 'bullish').length ?? 0,
    [data]
  )
  const bearishCount = useMemo(
    () => data?.signals?.filter((s: TechnicalSignal) => s.signal === 'bearish').length ?? 0,
    [data]
  )

  // Build overlay lines for candlestick chart
  const overlays = useMemo(() => {
    if (!data) return []
    const lines: Array<{ data: (number | null)[]; color: string; label: string }> = []
    if (data.sma_20.length > 0) lines.push({ data: data.sma_20, color: '#3b82f6', label: 'SMA 20' })
    if (data.sma_50.length > 0) lines.push({ data: data.sma_50, color: '#22c55e', label: 'SMA 50' })
    if (data.ema_12.length > 0) lines.push({ data: data.ema_12, color: '#a855f7', label: 'EMA 12' })
    if (data.bollinger.upper.length > 0) lines.push({ data: data.bollinger.upper, color: '#ef4444', label: 'BB Upper' })
    if (data.bollinger.middle.length > 0) lines.push({ data: data.bollinger.middle, color: '#3b82f6', label: 'BB Mid' })
    if (data.bollinger.lower.length > 0) lines.push({ data: data.bollinger.lower, color: '#22c55e', label: 'BB Lower' })
    return lines
  }, [data])

  // Build RSI subchart data
  const rsiData = useMemo(() => {
    if (!data?.rsi_14 || !data.dates) return []
    return [{ data: data.rsi_14, color: '#eab308', label: 'RSI 14' }]
  }, [data])

  // Build MACD subchart data
  const macdSeries = useMemo(() => {
    if (!data?.macd || !data.dates) return []
    const s = []
    if (data.macd.macd.length > 0) s.push({ data: data.macd.macd, color: '#3b82f6', label: 'MACD' })
    if (data.macd.signal.length > 0) s.push({ data: data.macd.signal, color: '#f97316', label: 'Signal' })
    return s
  }, [data])

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-2xl font-bold">Technical Analysis</h2>
          {symbol && (
            <p className="text-sm text-gray-500 mt-1 flex items-center gap-2">
              <span className="inline-block w-2 h-2 rounded-full bg-gain animate-pulse" />
              {data?.symbol || symbol.toUpperCase()}
              {lastPrice != null && (
                <span className="text-gray-300 font-medium tabular-nums">{fmtCurrency(lastPrice)}</span>
              )}
              <span className="text-gray-600">&middot;</span>
              <span>{data?.prices.length || 0} data points</span>
              {liveQuote?.change != null && (
                <span className={liveQuote.change >= 0 ? 'text-gain' : 'text-loss'}>
                  {liveQuote.change >= 0 ? '+' : ''}{liveQuote.change.toFixed(2)} ({liveQuote.change_pct?.toFixed(2) ?? ''}%)
                </span>
              )}
            </p>
          )}
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-end gap-4 flex-wrap">
        <div className="w-64">
          <SymbolSearch onSelect={(sym) => setSymbol(sym)} placeholder="Search ticker..." />
        </div>
        <div className="flex gap-1 bg-gray-800 rounded-lg p-1">
          {RANGES.map((r) => (
            <button
              key={r.value}
              onClick={() => setRange(r.value)}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                range === r.value ? 'bg-primary-600 text-white' : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>
        {data && (
          <div className="flex gap-2 ml-auto">
            <SignalCard label="Bullish Signals" count={bullishCount} color="#22c55e" />
            <SignalCard label="Bearish Signals" count={bearishCount} color="#ef4444" />
          </div>
        )}
      </div>

      {/* Empty state */}
      {!symbol && (
        <Card><p className="text-gray-500 text-sm">Search a ticker to view professional technical analysis.</p></Card>
      )}

      {/* Loading */}
      {isLoading && <Spinner />}

      {/* Error */}
      {error && (
        <Card><p className="text-red-400 text-sm">Failed to load data. Symbol may not exist.</p></Card>
      )}

      {/* Chart area */}
      {data && (
        <>
          {/* Main candlestick chart */}
          <CandlestickChart
            key={`${symbol}-${range}`}
            data={data.ohlcv || []}
            overlays={overlays}
            height={480}
            className="w-full"
          />

          {/* Indicator grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* RSI */}
            <Card title={`RSI (14) — ${num(data.rsi_14[data.rsi_14.length - 1]).toFixed(1)}`}>
              <div className="flex gap-3 mb-2 text-xs">
                <span className="text-red-400">Overbought: 70</span>
                <span className="text-gray-600">|</span>
                <span className="text-green-400">Oversold: 30</span>
              </div>
              <LineChart
                series={rsiData}
                height={160}
                dates={data.dates}
              />
            </Card>

            {/* MACD */}
            <Card title="MACD">
              <LineChart
                series={macdSeries}
                height={160}
                dates={data.dates}
              />
            </Card>

            {/* Signal Summary */}
            <Card title="Signal Summary" className="lg:col-span-2">
              {data.signals.length === 0 ? (
                <p className="text-gray-500 text-xs">No clear signals detected. Waiting for more data points.</p>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                  {data.signals.map((s: TechnicalSignal, i: number) => (
                    <div key={i} className="flex items-start gap-2 p-2 bg-gray-800/30 rounded-lg">
                      <Badge variant={signalBadgeVariant(s.signal)}>{s.signal}</Badge>
                      <div className="min-w-0">
                        <div className="text-xs text-gray-400 font-medium">{s.indicator}</div>
                        <div className="text-xs text-gray-500">{s.message}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>
        </>
      )}
    </div>
  )
}
