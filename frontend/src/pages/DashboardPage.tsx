import { useQuery } from '@tanstack/react-query'
import { Card, MetricCard } from '../components/ui/Card'
import { Spinner } from '../components/ui/Spinner'
import { fetchDashboardSummary } from '../api/portfolios'
import { PriceChange } from '../components/shared/PriceChange'
import { Link } from 'react-router-dom'
import { num, fmtPct } from '../utils/formatters'

function fmt(n: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2 }).format(num(n))
}

export function DashboardPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: fetchDashboardSummary,
    refetchInterval: 30000,
  })

  if (isLoading) return <Spinner />

  const p = data?.portfolio
  const market = data?.market || []

  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-2xl font-bold">Dashboard</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard label="Total Value" value={p ? fmt(p.total_value) : '$0.00'} />
        <MetricCard
          label="Day P&L"
          value={p ? fmt(p.day_pnl) : '$0.00'}
          change={p ? fmt(p.day_pnl) : '$0.00'}
          changePct={p && p.total_value > 0 ? num(p.day_pnl) / num(p.total_value - p.day_pnl) * 100 : 0}
        />
        <MetricCard
          label="Total P&L"
          value={p ? fmt(p.total_pnl) : '$0.00'}
          change={p ? fmt(p.total_pnl) : '$0.00'}
          changePct={p?.total_pnl_pct || 0}
        />
        <MetricCard label="Holdings" value={String(p?.holding_count || 0)} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card title="Portfolio Overview">
          {p && p.portfolio_count > 0 ? (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Portfolios</span>
                <span className="font-medium">{p.portfolio_count}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Total Cost Basis</span>
                <span className="font-medium">{fmt(p.total_cost)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Unrealized P&L</span>
                <span className={p.total_pnl >= 0 ? 'text-gain' : 'text-loss'}>
                  {fmtPct(p.total_pnl_pct)}
                </span>
              </div>
              <Link to="/portfolios" className="text-sm text-primary-400 hover:underline mt-2 inline-block">View all portfolios &rarr;</Link>
            </div>
          ) : (
            <div>
              <p className="text-gray-500 text-sm mb-2">No portfolios yet.</p>
              <Link to="/portfolios" className="text-sm text-primary-400 hover:underline">Create a portfolio &rarr;</Link>
            </div>
          )}
        </Card>

        <Card title="Market Overview">
          <div className="space-y-3">
            {market.map((m) => (
              <div key={m.symbol} className="flex justify-between items-center">
                <div>
                  <span className="text-sm font-medium">{m.symbol}</span>
                  <span className="text-xs text-gray-500 ml-2">{m.name}</span>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium">{m.value?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '-'}</div>
                  {m.change_pct != null && <PriceChange value={m.change_pct} pct={m.change_pct} />}
                </div>
              </div>
            ))}
            {market.length === 0 && <p className="text-gray-500 text-sm">Market data loading...</p>}
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card title="Quick Actions">
          <div className="flex flex-col gap-2">
            <Link to="/portfolios" className="text-sm text-primary-400 hover:underline">Manage portfolios</Link>
            <Link to="/watchlists" className="text-sm text-primary-400 hover:underline">Manage watchlists</Link>
            <Link to="/analysis" className="text-sm text-primary-400 hover:underline">Run stock analysis</Link>
            <Link to="/technical" className="text-sm text-primary-400 hover:underline">View technical indicators</Link>
          </div>
        </Card>
        <Card title="Recent Activity">
          <p className="text-gray-500 text-sm">Transaction history will appear here as you trade.</p>
        </Card>
        <Card title="Active Alerts">
          <p className="text-gray-500 text-sm">Set price alerts from the Alerts page.</p>
          <Link to="/alerts" className="text-sm text-primary-400 hover:underline mt-2 inline-block">Manage alerts &rarr;</Link>
        </Card>
      </div>
    </div>
  )
}
