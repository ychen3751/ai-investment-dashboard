import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Spinner } from '../components/ui/Spinner'
import { Badge } from '../components/ui/Badge'
import { MetricCard } from '../components/ui/Card'
import { fetchUpcomingEarnings, fetchEarningsDetail, fetchEarningsNews, fetchEarningsAnalysis } from '../api/earnings'
import { num, fmtCurrency } from '../utils/formatters'

function fmtLarge(n: number | null | undefined): string {
  if (n == null) return '—'
  if (Math.abs(n) >= 1e12) return `$${(n / 1e12).toFixed(2)}T`
  if (Math.abs(n) >= 1e9) return `$${(n / 1e9).toFixed(2)}B`
  if (Math.abs(n) >= 1e6) return `$${(n / 1e6).toFixed(2)}M`
  return `$${n.toFixed(2)}`
}

const RANGES = [
  { label: 'This Week', days: 7 },
  { label: 'Next Week', days: 14 },
  { label: 'This Month', days: 30 },
] as const

export function EarningsPage() {
  const [rangeDays, setRangeDays] = useState(14)
  const [symbol, setSymbol] = useState('')
  const [searchSymbol, setSearchSymbol] = useState('')

  const { data: upcoming, isLoading: upLoading } = useQuery({
    queryKey: ['earnings-upcoming', rangeDays],
    queryFn: () => fetchUpcomingEarnings(undefined, rangeDays),
    refetchInterval: 300_000,
  })

  const { data: detail, isLoading: detLoading } = useQuery({
    queryKey: ['earnings-detail', searchSymbol],
    queryFn: () => fetchEarningsDetail(searchSymbol),
    enabled: !!searchSymbol,
  })

  const { data: news, isLoading: newsLoading } = useQuery({
    queryKey: ['earnings-news', searchSymbol],
    queryFn: () => fetchEarningsNews(searchSymbol),
    enabled: !!searchSymbol,
  })

  const { data: analysis, isLoading: analysisLoading } = useQuery({
    queryKey: ['earnings-analysis', searchSymbol],
    queryFn: () => fetchEarningsAnalysis(searchSymbol),
    enabled: !!searchSymbol,
  })

  const handleSearch = () => {
    if (symbol.trim()) setSearchSymbol(symbol.trim().toUpperCase())
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Earnings Calendar</h2>
          <p className="text-sm text-gray-500 mt-0.5">Upcoming earnings dates, estimates, and historical results</p>
        </div>
      </div>

      {/* Range filter */}
      <div className="flex gap-1 bg-gray-800 rounded-lg p-1 w-fit">
        {RANGES.map((r) => (
          <button key={r.days} onClick={() => setRangeDays(r.days)}
            className={`px-3 py-1.5 text-sm rounded-md transition-colors ${rangeDays === r.days ? 'bg-primary-600 text-white' : 'text-gray-400 hover:text-gray-200'}`}>
            {r.label}
          </button>
        ))}
      </div>

      <p className="text-xs text-gray-600">Data sourced from Yahoo Finance (delayed). Informational only — not financial advice.</p>

      {/* Upcoming table */}
      {upLoading ? <Spinner /> : (
        <Card title={`Upcoming Earnings (${upcoming?.length || 0})`}>
          {!upcoming || upcoming.length === 0 ? (
            <p className="text-gray-500 text-sm">No upcoming earnings in this period.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-800 text-gray-500">
                    <th className="text-left py-2 px-2">Date</th>
                    <th className="text-left py-2 px-2">Symbol</th>
                    <th className="text-left py-2 px-2">Company</th>
                    <th className="text-left py-2 px-2">Time</th>
                    <th className="text-right py-2 px-2">EPS Est.</th>
                    <th className="text-right py-2 px-2">Revenue Est.</th>
                    <th className="text-right py-2 px-2">Prev EPS</th>
                    <th className="text-right py-2 px-2">Mkt Cap</th>
                  </tr>
                </thead>
                <tbody>
                  {upcoming.map((e, i) => (
                    <tr key={i} className="border-b border-gray-800/50 hover:bg-gray-800/30 cursor-pointer"
                      onClick={() => { setSymbol(e.symbol); setSearchSymbol(e.symbol) }}>
                      <td className="py-2 px-2 tabular-nums text-xs">{e.report_date}</td>
                      <td className="py-2 px-2 font-medium">{e.symbol}</td>
                      <td className="py-2 px-2 text-gray-400 truncate max-w-[200px]">{e.company_name}</td>
                      <td className="py-2 px-2"><Badge variant={e.timing === 'After Market' ? 'warning' : 'info'}>{e.timing === 'After Market' ? 'AMC' : e.timing === 'Before Market' ? 'BMO' : '—'}</Badge></td>
                      <td className="py-2 px-2 text-right tabular-nums">{e.eps_estimate != null ? `$${num(e.eps_estimate).toFixed(2)}` : '—'}</td>
                      <td className="py-2 px-2 text-right tabular-nums">{e.revenue_estimate != null ? fmtLarge(e.revenue_estimate) : '—'}</td>
                      <td className="py-2 px-2 text-right tabular-nums">{e.previous_eps != null ? `$${num(e.previous_eps).toFixed(2)}` : '—'}</td>
                      <td className="py-2 px-2 text-right tabular-nums">{e.market_cap != null ? fmtLarge(e.market_cap) : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {/* Symbol earnings detail */}
      <div className="flex gap-2 items-end">
        <div className="w-48">
          <Input value={symbol} onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            placeholder="Search ticker..." onKeyDown={(e) => e.key === 'Enter' && handleSearch()} />
        </div>
        <Button onClick={handleSearch} disabled={!symbol.trim()}>Search</Button>
      </div>

      {/* Earnings Analysis */}
      {searchSymbol && analysis && (
        <div className="bg-gray-900/80 rounded-xl border border-gray-800 p-5">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Earnings Setup</h3>
              <Badge variant={analysis.overall_signal === 'bullish' ? 'success' : analysis.overall_signal === 'bearish' ? 'danger' : analysis.overall_signal === 'high_risk' ? 'warning' : 'default'}>
                {`${analysis.overall_signal.toUpperCase()} ${analysis.confidence}%`}
              </Badge>
            </div>
          </div>

          <p className="text-sm text-gray-300 leading-relaxed mb-3">{analysis.ai_summary || analysis.summary}</p>

          {analysis.beginner_explanation && (
            <div className="bg-gray-800/30 rounded-lg p-3 mb-4">
              <p className="text-xs text-gray-500 mb-1">What this means</p>
              <p className="text-sm text-gray-400 leading-relaxed">{analysis.beginner_explanation}</p>
            </div>
          )}

          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
            {Object.entries(analysis.key_signals).filter(([, v]) => v !== 'N/A').map(([key, val]) => (
              <div key={key} className="bg-gray-800/40 rounded-lg p-2.5">
                <div className="text-[10px] text-gray-500 uppercase tracking-wider">{key.replace(/_/g, ' ')}</div>
                <div className="text-sm font-medium tabular-nums mt-0.5 text-gray-200">{val}</div>
              </div>
            ))}
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

      {detLoading && <Spinner />}

      {detail && !detail.error && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Detail card */}
          <Card title={detail.company_name}>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div><span className="text-gray-500">Symbol</span><p className="font-medium">{detail.symbol}</p></div>
              <div><span className="text-gray-500">Sector</span><p className="font-medium">{detail.sector || '—'}</p></div>
              <div><span className="text-gray-500">Next Earnings</span><p className="font-medium">{detail.next_earnings_date || '—'}</p></div>
              <div><span className="text-gray-500">Market Cap</span><p className="font-medium">{fmtLarge(detail.market_cap)}</p></div>
              <div><span className="text-gray-500">Current Price</span><p className="font-medium">{detail.price != null ? `$${num(detail.price).toFixed(2)}` : '—'}</p></div>
              <div><span className="text-gray-500">P/E (TTM)</span><p className="font-medium">{detail.pe_ratio != null ? num(detail.pe_ratio).toFixed(2) : '—'}</p></div>
              <div><span className="text-gray-500">Forward P/E</span><p className="font-medium">{detail.forward_pe != null ? num(detail.forward_pe).toFixed(2) : '—'}</p></div>
              <div><span className="text-gray-500">Dividend Yield</span><p className="font-medium">{detail.dividend_yield != null ? `${(num(detail.dividend_yield) * 100).toFixed(2)}%` : '—'}</p></div>
              <div><span className="text-gray-500">EPS Estimate</span><p className="font-medium">{detail.eps_estimate != null ? `$${num(detail.eps_estimate).toFixed(2)}` : '—'}</p></div>
              <div><span className="text-gray-500">Revenue Est.</span><p className="font-medium">{detail.revenue_estimate != null ? fmtLarge(detail.revenue_estimate) : '—'}</p></div>
            </div>

            {detail.history && detail.history.length > 0 && (
              <div className="mt-4">
                <h4 className="text-xs text-gray-500 uppercase tracking-wider mb-2">Recent Earnings History</h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-gray-800 text-gray-500">
                        <th className="text-left py-1 pr-2">Q</th>
                        <th className="text-right py-1 px-2">Estimate</th>
                        <th className="text-right py-1 px-2">Actual</th>
                        <th className="text-right py-1 pl-2">Surprise</th>
                      </tr>
                    </thead>
                    <tbody>
                      {detail.history.slice(0, 8).map((h, i) => (
                        <tr key={i} className="border-b border-gray-800/30">
                          <td className="py-1 pr-2 text-gray-500">{h.fiscal_quarter ? `Q${h.fiscal_quarter}${h.fiscal_year ? ` ${h.fiscal_year}` : ''}` : '—'}</td>
                          <td className="py-1 px-2 text-right tabular-nums">{h.eps_estimate != null ? `$${num(h.eps_estimate).toFixed(2)}` : '—'}</td>
                          <td className="py-1 px-2 text-right tabular-nums">{h.eps_actual != null ? `$${num(h.eps_actual).toFixed(2)}` : '—'}</td>
                          <td className={`py-1 pl-2 text-right tabular-nums ${h.eps_surprise_pct != null ? (h.eps_surprise_pct >= 0 ? 'text-gain' : 'text-loss') : ''}`}>
                            {h.eps_surprise_pct != null ? `${h.eps_surprise_pct >= 0 ? '+' : ''}${h.eps_surprise_pct.toFixed(2)}%` : '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </Card>

          {/* News card */}
          <Card title="Related News">
            {newsLoading ? <Spinner /> : !news || news.length === 0 ? (
              <p className="text-gray-500 text-sm">No recent news for this symbol.</p>
            ) : (
              <div className="flex flex-col gap-3 max-h-[400px] overflow-y-auto pr-1">
                {news.map((item, i) => (
                  <div key={i} className="bg-gray-800/30 rounded-lg p-3 hover:bg-gray-800/50 transition-colors">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-gray-200 leading-snug">{item.title || 'Untitled'}</p>
                        <div className="flex items-center gap-2 mt-1 text-[10px] text-gray-600">
                          {item.publisher && <span>{item.publisher}</span>}
                          {item.published && <span>{new Date(item.published).toLocaleDateString()}</span>}
                        </div>
                        {item.summary && (
                          <p className="text-xs text-gray-500 mt-1.5 leading-relaxed line-clamp-2">{item.summary}</p>
                        )}
                      </div>
                    </div>
                    {item.link && (
                      <a href={item.link} target="_blank" rel="noopener noreferrer"
                        className="text-xs text-primary-400 hover:underline mt-1.5 inline-block">Read more →</a>
                    )}
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      )}

      {detail?.error && <Card><p className="text-red-400 text-sm">{detail.error}</p></Card>}
    </div>
  )
}
