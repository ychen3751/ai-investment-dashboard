import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Card, MetricCard } from '../components/ui/Card'
import { Spinner } from '../components/ui/Spinner'
import { Skeleton, MetricCardSkeleton } from '../components/ui/Skeleton'
import { MarketCard } from '../components/shared/MarketCard'
import { fetchDashboardSummary } from '../api/portfolios'
import { useQuotes } from '../hooks/useMarketData'
import { num } from '../utils/formatters'

function fmt(n: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2 }).format(num(n))
}

const MARKET_SYMBOLS = ['SPY', 'QQQ', 'DIA', 'IWM', '^VIX', '^TNX']

export function DashboardPage() {
  const now = Date.now()

  const { data, isLoading, dataUpdatedAt } = useQuery({
    queryKey: ['dashboard'],
    queryFn: fetchDashboardSummary,
    refetchInterval: 30000,
  })

  // Parallel live poller for market cards — independent of dashboard summary
  const { data: liveQuotes } = useQuotes(MARKET_SYMBOLS)

  const secondsSinceUpdate = Math.floor((now - (dataUpdatedAt || 0)) / 1000)
  const isLive = secondsSinceUpdate < 35

  const p = data?.portfolio
  const market = data?.market || []

  const sortedMarket = useMemo(
    () => MARKET_SYMBOLS.map((sym) => market.find((m) => m.symbol === sym)).filter((m): m is NonNullable<typeof m> => m != null),
    [market],
  )

  const isPositive = (p?.total_pnl ?? 0) >= 0

  return (
    <div className="flex flex-col gap-6 h-full">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-100">Dashboard</h2>
          <p className="text-sm text-gray-500 mt-0.5">
            {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}
          </p>
        </div>
        {/* Live indicator */}
        <div className="flex items-center gap-2 text-xs">
          <span className={`inline-block w-2 h-2 rounded-full ${isLive ? 'bg-gain animate-pulse' : 'bg-gray-600'}`} />
          <span className="text-gray-500">
            {isLive ? 'Live' : `${secondsSinceUpdate}s ago`}
          </span>
        </div>
      </div>

      {/* Portfolio P&L */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1,2,3,4].map((i) => <MetricCardSkeleton key={i} />)}
        </div>
      ) : p && p.portfolio_count > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard label="Total Value" value={fmt(p.total_value)} />
          <MetricCard
            label="Day P&L"
            value={fmt(p.day_pnl)}
            change={fmt(p.day_pnl)}
            changePct={p.total_value > 0 ? num(p.day_pnl) / num(p.total_value - p.day_pnl) * 100 : 0}
          />
          <MetricCard
            label="Total P&L"
            value={fmt(p.total_pnl)}
            change={fmt(p.total_pnl)}
            changePct={p.total_pnl_pct}
          />
          <MetricCard label="Holdings" value={String(p.holding_count)} />
        </div>
      ) : (
        <Card className="bg-gradient-to-r from-gray-900 to-gray-800/50 border-dashed border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">No portfolio data yet.</p>
              <p className="text-xs text-gray-600 mt-1">Create a portfolio to see your P&L headline.</p>
            </div>
            <Link to="/portfolios" className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white text-sm rounded-lg transition-colors">Create Portfolio</Link>
          </div>
        </Card>
      )}

      {/* Market Overview */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Market Overview</h3>
          <div className="h-px flex-1 bg-gradient-to-r from-gray-800 to-transparent" />
        </div>
        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3">
            {[1,2,3,4,5,6].map((i) => (
              <div key={i} className="card"><Skeleton widths="60%" height="1rem" /><Skeleton widths="40%" height="1.5rem" className="mt-2" /></div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3">
            {sortedMarket.map((m) => {
              // Use live quote if available, fall back to dashboard summary data
              const liveSym = m.symbol.replace('^', '')
              const live = liveQuotes?.[liveSym]
              return (
                <MarketCard
                  key={m.symbol}
                  symbol={m.symbol}
                  name={m.name}
                  price={live?.price ?? m.value}
                  change={live?.change ?? m.change}
                  changePct={live?.change_pct ?? m.change_pct}
                />
              )
            })}
          </div>
        )}
      </div>

      {/* Quick Links */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Research</h3>
          <div className="h-px flex-1 bg-gradient-to-r from-gray-800 to-transparent" />
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {[
            { to: '/technical', label: 'Technical', icon: '📈', desc: 'Charts & indicators' },
            { to: '/analysis', label: 'AI Analysis', icon: '🤖', desc: 'Fundamental insights' },
            { to: '/options-flow', label: 'Options Flow', icon: '🔄', desc: 'Unusual activity' },
            { to: '/earnings', label: 'Earnings', icon: '📅', desc: 'Calendar & estimates' },
            { to: '/watchlists', label: 'Watchlists', icon: '👁️', desc: 'Track symbols' },
            { to: '/risk', label: 'Risk', icon: '🛡️', desc: 'VaR & analytics' },
          ].map((mod) => (
            <Link key={mod.to} to={mod.to} className="card-interactive group flex flex-col">
              <span className="text-lg mb-1">{mod.icon}</span>
              <span className="text-sm font-medium text-gray-200 group-hover:text-primary-400 transition-colors">{mod.label}</span>
              <span className="text-[10px] text-gray-600 mt-0.5">{mod.desc}</span>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
