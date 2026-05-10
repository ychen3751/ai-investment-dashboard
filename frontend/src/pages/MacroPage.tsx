import { useQuery } from '@tanstack/react-query'
import { Card } from '../components/ui/Card'
import { Spinner } from '../components/ui/Spinner'
import { Badge } from '../components/ui/Badge'
import { fetchMacroOverview } from '../api/macro'
import { num } from '../utils/formatters'

function regimeBadge(regime: string) {
  if (regime === 'Risk On' || regime === 'AI Momentum') return 'success' as const
  if (regime === 'Risk Off' || regime === 'Recession Risk') return 'danger' as const
  if (regime === 'High Volatility' || regime === 'Caution') return 'warning' as const
  return 'default' as const
}

function signalBadge(signal: string) {
  if (signal === 'bullish') return 'success' as const
  if (signal === 'bearish') return 'danger' as const
  return 'warning' as const
}

function impactBadge(impact: string) {
  if (impact === 'Very High' || impact === 'Extreme') return 'danger' as const
  if (impact === 'High') return 'warning' as const
  return 'default' as const
}

function Sparkline({ data, color }: { data: number[]; color: string }) {
  if (data.length < 2) return null
  const mn = Math.min(...data), mx = Math.max(...data), r = mx - mn || 1
  const w = 60, h = 24
  const pts = data.map((v, i) => `${((i / (data.length - 1)) * w).toFixed(1)},${(h - ((v - mn) / r) * h).toFixed(1)}`).join(' ')
  return <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}><polyline points={pts} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" /></svg>
}

function fmtPct(n: number | null | undefined): string {
  if (n == null) return '—'
  return `${n >= 0 ? '+' : ''}${n.toFixed(2)}%`
}

export function MacroPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['macro-overview'],
    queryFn: fetchMacroOverview,
    refetchInterval: 120_000,
  })

  if (isLoading) return <Spinner />

  const regime = data?.market_regime
  const indicators = data?.macro_indicators || []
  const signals = data?.macro_signals || ({} as Record<string, { signal: string; explanation: string }>)
  const sectors = data?.sector_rotation || []
  const events = data?.economic_events || []
  const ai = data?.ai_analysis

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Macro Dashboard</h2>
          <p className="text-sm text-gray-500 mt-0.5">Institutional-grade macro intelligence</p>
        </div>
      </div>

      {regime && (
        <div className="bg-gray-900/80 rounded-xl border border-gray-800 p-5">
          <div className="flex items-start justify-between flex-wrap gap-4">
            <div className="flex items-center gap-3">
              <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Market Regime</h3>
              <Badge variant={regimeBadge(regime.regime)}>{`${regime.regime} ${regime.confidence}%`}</Badge>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">Bear</span>
              <div className="w-24 h-2 bg-gray-800 rounded-full overflow-hidden">
                <div className="h-full rounded-full transition-all" style={{ width: `${regime.bullish_pct}%`, background: regime.bullish_pct > 60 ? '#22c55e' : regime.bullish_pct > 40 ? '#eab308' : '#ef4444' }} />
              </div>
              <span className="text-xs text-gray-500">Bull</span>
            </div>
          </div>
          <p className="text-sm text-gray-400 mt-2 leading-relaxed">{regime.explanation}</p>
        </div>
      )}

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {indicators.map((ind) => {
          const pos = (ind.change_pct ?? 0) >= 0
          const color = pos ? '#22c55e' : '#ef4444'
          return (
            <div key={ind.symbol} className="bg-gray-900/60 rounded-xl border border-gray-800/80 p-3 hover:border-gray-700/80 transition-colors">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-gray-300">{ind.symbol}</span>
                <Sparkline data={ind.sparkline} color={color} />
              </div>
              <div className="text-lg font-bold tabular-nums mt-1">{ind.price != null ? (ind.price >= 1000 ? ind.price.toLocaleString(undefined, { maximumFractionDigits: 0 }) : ind.price.toFixed(2)) : '—'}</div>
              <div className="flex items-center gap-2 mt-0.5">
                <span className={`text-xs font-medium tabular-nums ${pos ? 'text-gain' : 'text-loss'}`}>{fmtPct(ind.change_pct)}</span>
                {ind.week_change_pct != null && (
                  <span className={`text-[10px] tabular-nums ${ind.week_change_pct >= 0 ? 'text-gain' : 'text-loss'}`}>Wk: {fmtPct(ind.week_change_pct)}</span>
                )}
              </div>
            </div>
          )
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {ai && (
          <Card title="Macro Analysis" className="lg:col-span-2">
            <p className="text-sm text-gray-300 leading-relaxed">{ai.narrative}</p>
            {ai.key_risks.length > 0 && (
              <div className="mt-3"><p className="text-xs text-loss font-medium mb-1">Key Risks</p>
                {ai.key_risks.map((r, i) => <p key={i} className="text-xs text-gray-400 pl-3 leading-relaxed">! {r}</p>)}
              </div>
            )}
            {ai.key_opportunities.length > 0 && (
              <div className="mt-2"><p className="text-xs text-gain font-medium mb-1">Opportunities</p>
                {ai.key_opportunities.map((o, i) => <p key={i} className="text-xs text-gray-400 pl-3 leading-relaxed">+ {o}</p>)}
              </div>
            )}
          </Card>
        )}

        <Card title="Macro Signals">
          <div className="space-y-3">
            {Object.entries(signals).map(([key, sig]) => (
              <div key={key}>
                <div className="flex items-center gap-2 mb-0.5">
                  <Badge variant={signalBadge(sig.signal)}>{sig.signal.toUpperCase()}</Badge>
                  <span className="text-xs text-gray-400 capitalize">{key.replace(/_/g, ' ')}</span>
                </div>
                <p className="text-[11px] text-gray-600">{sig.explanation}</p>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card title="Sector Rotation">
          <div className="space-y-1 max-h-[300px] overflow-y-auto pr-1">
            {sectors.map((s) => (
              <div key={s.symbol} className="flex items-center justify-between py-1.5 border-b border-gray-800/30 last:border-0">
                <span className="text-sm text-gray-200">{s.name}</span>
                <div className="flex items-center gap-3 text-xs tabular-nums">
                  <span className={s.daily_pct != null ? (s.daily_pct >= 0 ? 'text-gain' : 'text-loss') : 'text-gray-600'}>{fmtPct(s.daily_pct)}</span>
                  <span className={s.weekly_pct != null ? (s.weekly_pct >= 0 ? 'text-gain' : 'text-loss') : 'text-gray-600'}>{fmtPct(s.weekly_pct)}</span>
                  <span className={s.momentum != null ? (s.momentum >= 0 ? 'text-gain' : 'text-loss') : 'text-gray-600'}>{fmtPct(s.momentum)}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Economic Calendar">
          <div className="space-y-1">
            {events.map((e, i) => (
              <div key={i} className="flex items-center justify-between py-1.5 border-b border-gray-800/30 last:border-0">
                <div><span className="text-sm text-gray-200">{e.event}</span><p className="text-xs text-gray-600">{e.date}</p></div>
                <div className="flex items-center gap-2">
                  <Badge variant={impactBadge(e.impact)}>{e.impact}</Badge>
                  <Badge variant={impactBadge(e.volatility)}>{e.volatility}</Badge>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <p className="text-xs text-gray-600">Data sourced from Yahoo Finance (delayed). Educational purposes only — not financial advice.</p>
    </div>
  )
}
