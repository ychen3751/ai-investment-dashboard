import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, MetricCard } from '../components/ui/Card'
import { Spinner } from '../components/ui/Spinner'
import { Badge } from '../components/ui/Badge'
import { fetchPortfolios } from '../api/portfolios'
import { fetchRiskSummary } from '../api/risk'
import { num } from '../utils/formatters'

function fmt(n: number | null | undefined) {
  if (n == null) return 'N/A'
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2 }).format(n)
}

function fmtPct(n: number | null | undefined) {
  if (n == null) return 'N/A'
  const sign = n >= 0 ? '+' : ''
  return `${sign}${n.toFixed(2)}%`
}

function fmtNum(n: number | null | undefined) {
  if (n == null) return 'N/A'
  return n.toFixed(4)
}

function concentrationBadge(hhi: number) {
  if (hhi > 2500) return 'danger' as const
  if (hhi > 1500) return 'warning' as const
  return 'success' as const
}

function concentrationLabel(hhi: number) {
  if (hhi > 2500) return 'Highly Concentrated'
  if (hhi > 1500) return 'Moderately Concentrated'
  return 'Well Diversified'
}

export function RiskPage() {
  const [selectedPortfolio, setSelectedPortfolio] = useState('')

  const { data: portfolios } = useQuery({ queryKey: ['portfolios'], queryFn: fetchPortfolios })

  const { data: risk, isLoading, error } = useQuery({
    queryKey: ['risk-summary', selectedPortfolio],
    queryFn: () => fetchRiskSummary(selectedPortfolio),
    enabled: !!selectedPortfolio,
  })

  const hasData = risk?.data_available

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Risk Analytics</h2>
          <p className="text-sm text-gray-500 mt-0.5">Institutional-grade portfolio risk metrics</p>
        </div>
        <select
          value={selectedPortfolio}
          onChange={(e) => setSelectedPortfolio(e.target.value)}
          className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100"
        >
          <option value="">Select a portfolio...</option>
          {(portfolios || []).map((p) => (
            <option key={p.id} value={p.id}>{p.name}</option>
          ))}
        </select>
      </div>

      {!selectedPortfolio && (
        <Card><p className="text-gray-500 text-sm">Select a portfolio above to view risk analytics.</p></Card>
      )}

      {isLoading && <Spinner />}
      {error && <Card><p className="text-red-400 text-sm">Failed to load risk data.</p></Card>}

      {hasData && risk && (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard label="Ann. Volatility" value={risk.volatility?.annualized != null ? `${risk.volatility.annualized.toFixed(2)}%` : 'N/A'} />
            <MetricCard label="Sharpe Ratio" value={risk.sharpe_ratio != null ? risk.sharpe_ratio.toFixed(4) : 'N/A'} />
            <MetricCard label="Max Drawdown" value={risk.drawdown?.max_pct != null ? fmtPct(risk.drawdown.max_pct) : 'N/A'} />
            <MetricCard label="Current Drawdown" value={risk.drawdown?.current_pct != null ? fmtPct(risk.drawdown.current_pct) : 'N/A'} />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard label="VaR 95% (Daily)" value={risk.value_at_risk?.var_95_pct != null ? fmtPct(risk.value_at_risk.var_95_pct) : 'N/A'}
              change={risk.value_at_risk?.var_95_value != null ? fmt(risk.value_at_risk.var_95_value) : undefined} />
            <MetricCard label="CVaR 95% (Daily)" value={risk.value_at_risk?.cvar_95_pct != null ? fmtPct(risk.value_at_risk.cvar_95_pct) : 'N/A'}
              change={risk.value_at_risk?.cvar_95_value != null ? fmt(risk.value_at_risk.cvar_95_value) : undefined} />
            <MetricCard label="Beta vs SPY" value={risk.beta?.beta != null ? risk.beta.beta.toFixed(4) : 'N/A'} />
            <MetricCard label="R² vs SPY" value={risk.beta?.r_squared != null ? risk.beta.r_squared.toFixed(4) : 'N/A'} />
          </div>

          {/* Beta details */}
          {risk.beta && !risk.beta.error && risk.beta.beta != null && (
            <Card title="Beta Analysis vs SPY">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div><span className="text-gray-500">Beta</span><p className="font-medium tabular-nums mt-0.5">{risk.beta.beta.toFixed(4)}</p></div>
                <div><span className="text-gray-500">Alpha (Ann.)</span><p className={`font-medium tabular-nums mt-0.5 ${(risk.beta.alpha ?? 0) >= 0 ? 'text-gain' : 'text-loss'}`}>{risk.beta.alpha != null ? fmtPct(risk.beta.alpha) : 'N/A'}</p></div>
                <div><span className="text-gray-500">Correlation</span><p className="font-medium tabular-nums mt-0.5">{risk.beta.correlation?.toFixed(4)}</p></div>
                <div><span className="text-gray-500">R-Squared</span><p className="font-medium tabular-nums mt-0.5">{risk.beta.r_squared?.toFixed(4)}</p></div>
              </div>
              <p className="text-xs text-gray-600 mt-3">
                {risk.beta.beta > 1.2
                  ? 'Beta above 1.2 — portfolio is significantly more volatile than the market.'
                  : risk.beta.beta > 0.8
                  ? 'Beta between 0.8 and 1.2 — portfolio moves broadly in line with the market.'
                  : 'Beta below 0.8 — portfolio is less volatile than the market.'}
              </p>
            </Card>
          )}

          {/* Concentration */}
          {risk.concentration && !risk.concentration.error && (
            <Card title="Concentration">
              <div className="flex items-center gap-3 mb-4">
                <Badge variant={concentrationBadge(risk.concentration.hhi ?? 0)}>
                  {concentrationLabel(risk.concentration.hhi ?? 0)}
                </Badge>
                <span className="text-xs text-gray-500">HHI: {risk.concentration.hhi}</span>
              </div>

              {risk.concentration.top_holdings && risk.concentration.top_holdings.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-xs text-gray-500 uppercase tracking-wider mb-2">Top Holdings</h4>
                  <div className="space-y-1">
                    {risk.concentration.top_holdings.map((h) => (
                      <div key={h.symbol} className="flex justify-between text-sm">
                        <span className="font-medium">{h.symbol}</span>
                        <span className="tabular-nums text-gray-400">{h.pct.toFixed(1)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {risk.concentration.sectors && Object.keys(risk.concentration.sectors).length > 0 && (
                <div>
                  <h4 className="text-xs text-gray-500 uppercase tracking-wider mb-2">Sector Allocation</h4>
                  <div className="space-y-1">
                    {risk.concentration.sectors ? Object.entries(risk.concentration.sectors)
                      .sort(([, a], [, b]) => b - a)
                      .map(([sector, pct]) => (
                        <div key={sector} className="flex justify-between text-sm">
                          <span className="text-gray-300">{sector}</span>
                          <span className="tabular-nums text-gray-400">{pct.toFixed(1)}%</span>
                        </div>
                      )) : <p className="text-xs text-gray-600">Not enough data available</p>}
                  </div>
                </div>
              )}
            </Card>
          )}

          {/* Risk Narrative */}
          <Card title="Risk Narrative">
            <div className="space-y-2 text-sm text-gray-400">
              {risk.volatility?.annualized != null && (
                <p>
                  <strong className="text-gray-200">Volatility:</strong>{' '}
                  Annualized volatility of <strong>{risk.volatility.annualized.toFixed(1)}%</strong>{' '}
                  {risk.volatility.annualized > 40
                    ? 'indicates a high-risk portfolio typical of concentrated equity positions.'
                    : risk.volatility.annualized > 25
                    ? 'is above the typical S&P 500 range (~15-20%), suggesting above-average risk.'
                    : 'is in the moderate range, comparable to a diversified equity portfolio.'}
                </p>
              )}
              {risk.sharpe_ratio != null && (
                <p>
                  <strong className="text-gray-200">Risk-Adjusted Return:</strong>{' '}
                  Sharpe ratio of <strong>{risk.sharpe_ratio.toFixed(2)}</strong>{' '}
                  {risk.sharpe_ratio > 2
                    ? 'is excellent — strong returns relative to the risk taken.'
                    : risk.sharpe_ratio > 1
                    ? 'is good — returns compensate well for the risk level.'
                    : risk.sharpe_ratio > 0
                    ? 'indicates returns are slightly above the risk-free rate.'
                    : 'suggests returns have not compensated for the risk taken.'}
                </p>
              )}
              {risk.drawdown?.max_pct != null && (
                <p>
                  <strong className="text-gray-200">Drawdown:</strong>{' '}
                  The portfolio experienced a maximum peak-to-trough decline of{' '}
                  <strong className="text-loss">{risk.drawdown.max_pct.toFixed(1)}%</strong>.
                  {risk.drawdown.current_pct < -5
                    ? ` Currently ${risk.drawdown.current_pct.toFixed(1)}% below the previous peak.`
                    : ' Currently near its peak value.'}
                </p>
              )}
              {risk.value_at_risk?.var_95_pct != null && (
                <p>
                  <strong className="text-gray-200">Value at Risk:</strong>{' '}
                  There is a 95% probability that daily losses will not exceed{' '}
                  <strong className="text-loss">{fmt(risk.value_at_risk.var_95_value)}</strong>{' '}
                  ({risk.value_at_risk.var_95_pct.toFixed(1)}% of portfolio value).
                  The expected shortfall (CVaR) in the worst 5% of days is{' '}
                  <strong className="text-loss">{fmt(risk.value_at_risk.cvar_95_value)}</strong>.
                </p>
              )}
              {risk.beta?.beta != null && (
                <p>
                  <strong className="text-gray-200">Market Sensitivity:</strong>{' '}
                  A beta of <strong>{risk.beta.beta.toFixed(2)}</strong> means the portfolio{' '}
                  {risk.beta.beta > 1
                    ? `amplifies market moves by ${((risk.beta.beta - 1) * 100).toFixed(0)}%.`
                    : `dampens market moves by ${((1 - risk.beta.beta) * 100).toFixed(0)}%.`}
                </p>
              )}
              {risk.concentration?.hhi != null && (
                <p>
                  <strong className="text-gray-200">Diversification:</strong>{' '}
                  HHI of <strong>{risk.concentration.hhi}</strong> indicates{' '}
                  {risk.concentration.hhi > 2500
                    ? 'a highly concentrated portfolio. Consider adding uncorrelated positions.'
                    : risk.concentration.hhi > 1500
                    ? 'moderate concentration. Additional diversification may reduce risk.'
                    : 'good diversification across positions.'}
                </p>
              )}
            </div>
          </Card>
        </>
      )}

      {/* No-data state */}
      {selectedPortfolio && !isLoading && risk && !hasData && (
        <Card>
          <p className="text-sm text-gray-400">{risk.error || 'Not enough historical price data to compute risk metrics. Holdings need at least 20 trading days of price history.'}</p>
        </Card>
      )}
    </div>
  )
}
