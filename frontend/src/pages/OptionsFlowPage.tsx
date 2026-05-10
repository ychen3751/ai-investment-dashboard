import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Spinner } from '../components/ui/Spinner'
import { Badge } from '../components/ui/Badge'
import { fetchExpirations, fetchOptionChain, fetchFlowAnalysis } from '../api/options'
import { num, fmtCurrency } from '../utils/formatters'
import type { OptionContract, FlowAnalysis } from '../api/options'

function scoreBadge(score: number) {
  if (score >= 60) return 'danger' as const
  if (score >= 30) return 'warning' as const
  return 'default' as const
}

function signalBadge(signal: string) {
  if (signal === 'Unusual Volume') return 'danger' as const
  if (signal === 'High Premium') return 'warning' as const
  if (signal === 'Abnormal Flow') return 'info' as const
  return 'default' as const
}

type SortKey = keyof OptionContract

function fmtLocale(n: number): string {
  if (n <= 0) return '—'
  return Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(n)
}

export function OptionsFlowPage() {
  const [symbol, setSymbol] = useState('')
  const [expiration, setExpiration] = useState('')
  const [optionType, setOptionType] = useState('')
  const [minPremium, setMinPremium] = useState(0)
  const [unusualOnly, setUnusualOnly] = useState(false)
  const [sortKey, setSortKey] = useState<SortKey>('unusual_score')
  const [sortAsc, setSortAsc] = useState(false)

  const { data: expirations } = useQuery({
    queryKey: ['expirations', symbol],
    queryFn: () => fetchExpirations(symbol),
    enabled: !!symbol,
  })

  const { data: chain, isLoading } = useQuery({
    queryKey: ['option-chain', symbol, expiration, minPremium, optionType, unusualOnly],
    queryFn: () =>
      fetchOptionChain(symbol, {
        expiration: expiration || undefined,
        min_premium: minPremium > 0 ? minPremium : undefined,
        option_type: (optionType as 'call' | 'put') || undefined,
        unusual_only: unusualOnly || undefined,
      }),
    enabled: !!symbol,
  })

  const { data: analysis, isLoading: analysisLoading } = useQuery({
    queryKey: ['flow-analysis', symbol],
    queryFn: () => fetchFlowAnalysis(symbol),
    enabled: !!symbol,
  })

  useEffect(() => {
    if (expirations && expirations.length > 0 && !expiration) {
      setExpiration(expirations[0])
    }
  }, [expirations, expiration])

  const sorted = [...(chain?.contracts || [])].sort((a, b) => {
    const av = a[sortKey] ?? 0
    const bv = b[sortKey] ?? 0
    return (Number(av) < Number(bv) ? -1 : 1) * (sortAsc ? 1 : -1)
  })

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Options Flow Scanner</h2>
          <p className="text-sm text-gray-500 mt-0.5">Option chain analysis with unusual activity scoring</p>
        </div>
      </div>

      <div className="flex flex-wrap items-end gap-3">
        <div className="w-36">
          <Input value={symbol} onChange={(e) => { setSymbol(e.target.value.toUpperCase()); setExpiration('') }} placeholder="AAPL" className="w-full" />
        </div>
        <div>
          <label className="text-xs text-gray-500 mb-1 block">Expiration</label>
          <select value={expiration} onChange={(e) => setExpiration(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 min-w-[130px]">
            {(!expirations || expirations.length === 0) && <option value="">Loading...</option>}
            {(expirations || []).map((e) => <option key={e} value={e}>{e}</option>)}
          </select>
        </div>
        <div>
          <label className="text-xs text-gray-500 mb-1 block">Type</label>
          <select value={optionType} onChange={(e) => setOptionType(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100">
            <option value="">All</option><option value="call">Calls</option><option value="put">Puts</option>
          </select>
        </div>
        <div className="w-28">
          <Input label="Min Premium $" type="number" value={minPremium || ''} onChange={(e) => setMinPremium(Number(e.target.value) || 0)} placeholder="0" />
        </div>
        <label className="flex items-center gap-2 cursor-pointer pb-1.5">
          <input type="checkbox" checked={unusualOnly} onChange={(e) => setUnusualOnly(e.target.checked)}
            className="w-4 h-4 rounded border-gray-700 bg-gray-800 text-primary-500 focus:ring-primary-500" />
          <span className="text-sm text-gray-400">Unusual only</span>
        </label>
      </div>

      <p className="text-xs text-gray-600">Data sourced from Yahoo Finance (delayed). Options flow is informational only — not financial advice.</p>

      {/* Flow Analysis — only when a symbol is actively entered */}
      {symbol && analysis && (
        <div className="bg-gray-900/80 rounded-xl border border-gray-800 p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Flow Analysis</h3>
              <Badge variant={analysis.overall_signal === 'bullish' ? 'success' : analysis.overall_signal === 'bearish' ? 'danger' : analysis.overall_signal === 'mixed' ? 'warning' : 'default'}>
                {`${analysis.overall_signal.toUpperCase()}  ${analysis.confidence}%`}
              </Badge>
            </div>
            <span className="text-[10px] text-gray-600">{analysis.symbol} &middot; {analysis.timestamp ? new Date(analysis.timestamp).toLocaleTimeString() : ''}</span>
          </div>

          <p className="text-sm text-gray-300 leading-relaxed mb-4">{analysis.ai_summary || analysis.summary}</p>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            <div className="bg-gray-800/40 rounded-lg p-3"><div className="text-xs text-gray-500">Call/Put Vol</div><div className="text-sm font-medium tabular-nums mt-0.5">{num(analysis?.key_metrics?.call_put_volume_ratio).toFixed(2)}x</div></div>
            <div className="bg-gray-800/40 rounded-lg p-3"><div className="text-xs text-gray-500">Call/Put Premium</div><div className="text-sm font-medium tabular-nums mt-0.5">{num(analysis?.key_metrics?.call_put_premium_ratio).toFixed(2)}x</div></div>
            <div className="bg-gray-800/40 rounded-lg p-3"><div className="text-xs text-gray-500">Unusual Contracts</div><div className="text-sm font-medium tabular-nums mt-0.5">{analysis?.key_metrics?.unusual_count ?? '—'}</div></div>
            <div className="bg-gray-800/40 rounded-lg p-3"><div className="text-xs text-gray-500">Avg IV</div><div className="text-sm font-medium tabular-nums mt-0.5">{analysis?.key_metrics?.avg_implied_volatility != null ? `${num(analysis.key_metrics.avg_implied_volatility).toFixed(1)}%` : '—'}</div></div>
            <div className="bg-gray-800/40 rounded-lg p-3"><div className="text-xs text-gray-500">Total Premium</div><div className="text-sm font-medium tabular-nums mt-0.5">{fmtCurrency(analysis?.key_metrics?.total_premium)}</div></div>
            <div className="bg-gray-800/40 rounded-lg p-3"><div className="text-xs text-gray-500">Call Premium</div><div className="text-sm font-medium text-gain tabular-nums mt-0.5">{fmtCurrency(analysis?.key_metrics?.call_premium)}</div></div>
            <div className="bg-gray-800/40 rounded-lg p-3"><div className="text-xs text-gray-500">Put Premium</div><div className="text-sm font-medium text-loss tabular-nums mt-0.5">{fmtCurrency(analysis?.key_metrics?.put_premium)}</div></div>
            <div className="bg-gray-800/40 rounded-lg p-3"><div className="text-xs text-gray-500">ATM Concentration</div><div className="text-sm font-medium tabular-nums mt-0.5">{num(analysis?.key_metrics?.atm_premium_pct).toFixed(1)}%</div></div>
          </div>

          {analysis.bullish_factors.length > 0 && (
            <div className="mb-2"><p className="text-xs text-gain font-medium mb-1">Bullish Factors</p>
              {analysis.bullish_factors.map((f, i) => <p key={i} className="text-xs text-gray-400 pl-3 leading-relaxed">+ {f}</p>)}
            </div>
          )}
          {analysis.bearish_factors.length > 0 && (
            <div className="mb-2"><p className="text-xs text-loss font-medium mb-1">Bearish Factors</p>
              {analysis.bearish_factors.map((f, i) => <p key={i} className="text-xs text-gray-400 pl-3 leading-relaxed">− {f}</p>)}
            </div>
          )}
          {analysis.risk_factors.length > 0 && (
            <div><p className="text-xs text-yellow-500 font-medium mb-1">Risk Factors</p>
              {analysis.risk_factors.map((f, i) => <p key={i} className="text-xs text-gray-400 pl-3 leading-relaxed">! {f}</p>)}
            </div>
          )}
        </div>
      )}

      {analysisLoading && <Spinner />}

      {!symbol && <Card><p className="text-gray-500 text-sm">Enter a ticker symbol to scan options flow.</p></Card>}

      {chain && chain.contracts.length > 0 && symbol && (
        <Card>
          <div className="flex items-center gap-2 mb-3">
            <span className="text-sm font-semibold">{chain.symbol}</span>
            <span className="text-xs text-gray-500">{chain.expiration} &middot; {chain.total_contracts} contracts{chain.underlying_price ? ` &middot; Underlying: $${num(chain.underlying_price).toFixed(2)}` : ''}</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800 text-gray-500">
                  {[
                    { k: 'option_type' as SortKey, label: 'Type' },
                    { k: 'strike' as SortKey, label: 'Strike' },
                    { k: 'last_price' as SortKey, label: 'Last' },
                    { k: 'bid' as SortKey, label: 'Bid' },
                    { k: 'ask' as SortKey, label: 'Ask' },
                    { k: 'volume' as SortKey, label: 'Vol' },
                    { k: 'open_interest' as SortKey, label: 'OI' },
                    { k: 'volume_oi_ratio' as SortKey, label: 'Vol/OI' },
                    { k: 'implied_volatility' as SortKey, label: 'IV%' },
                    { k: 'premium' as SortKey, label: 'Premium' },
                    { k: 'unusual_score' as SortKey, label: 'Score' },
                    { k: 'signal' as SortKey, label: 'Signal' },
                  ].map((col) => (
                    <th key={col.k} className={`py-2 px-1.5 text-xs uppercase tracking-wider cursor-pointer hover:text-gray-300 ${col.k === 'option_type' ? 'text-left' : 'text-right'}`}
                      onClick={() => {
                        if (sortKey === col.k) setSortAsc(!sortAsc)
                        else { setSortKey(col.k); setSortAsc(false) }
                      }}>
                      {col.label}{sortKey === col.k && <span className="ml-1">{sortAsc ? '↑' : '↓'}</span>}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sorted.map((c, i) => (
                  <tr key={i} className="border-b border-gray-800/30 hover:bg-gray-800/30 transition-colors">
                    <td className="py-1.5 px-1.5"><Badge variant={c.option_type === 'call' ? 'success' : 'danger'}>{c.option_type.toUpperCase()}</Badge></td>
                    <td className="py-1.5 px-1.5 text-right tabular-nums">${num(c.strike).toFixed(2)}</td>
                    <td className="py-1.5 px-1.5 text-right tabular-nums">{c.last_price > 0 ? `$${num(c.last_price).toFixed(2)}` : '—'}</td>
                    <td className="py-1.5 px-1.5 text-right tabular-nums">{c.bid > 0 ? `$${num(c.bid).toFixed(2)}` : '—'}</td>
                    <td className="py-1.5 px-1.5 text-right tabular-nums">{c.ask > 0 ? `$${num(c.ask).toFixed(2)}` : '—'}</td>
                    <td className="py-1.5 px-1.5 text-right tabular-nums">{c.volume > 0 ? fmtLocale(c.volume) : '—'}</td>
                    <td className="py-1.5 px-1.5 text-right tabular-nums">{c.open_interest > 0 ? fmtLocale(c.open_interest) : '—'}</td>
                    <td className="py-1.5 px-1.5 text-right tabular-nums">{c.volume_oi_ratio > 0 ? num(c.volume_oi_ratio).toFixed(2) : '—'}</td>
                    <td className="py-1.5 px-1.5 text-right tabular-nums">{c.implied_volatility > 0 ? `${num(c.implied_volatility).toFixed(1)}%` : '—'}</td>
                    <td className="py-1.5 px-1.5 text-right tabular-nums">${c.premium > 0 ? fmtLocale(c.premium) : '—'}</td>
                    <td className="py-1.5 px-1.5 text-right"><Badge variant={scoreBadge(c.unusual_score)}>{num(c.unusual_score).toFixed(0)}</Badge></td>
                    <td className="py-1.5 px-1.5 text-right"><Badge variant={signalBadge(c.signal)}>{c.signal}</Badge></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {chain && chain.contracts.length === 0 && symbol && !isLoading && (
        <Card><p className="text-gray-500 text-sm">No contracts match the current filters.</p></Card>
      )}
    </div>
  )
}
