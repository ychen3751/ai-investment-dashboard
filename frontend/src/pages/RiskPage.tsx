import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, MetricCard } from '../components/ui/Card'
import { Spinner } from '../components/ui/Spinner'
import { Badge } from '../components/ui/Badge'
import { fetchPortfolios } from '../api/portfolios'
import { fetchRiskSummary, fetchStressTest } from '../api/risk'
import { fetchAdvisorAnalysis } from '../api/advisor'
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

function scoreColor(s: number) {
  if (s >= 70) return '#22c55e'
  if (s >= 50) return '#eab308'
  return '#ef4444'
}

function severityBadge(s: string) {
  if (s === 'high') return 'danger' as const
  if (s === 'medium') return 'warning' as const
  return 'default' as const
}

function ScoreGauge({ score, label }: { score: number; label: string }) {
  const color = scoreColor(score)
  const r = 28
  const circ = 2 * Math.PI * r
  const offset = circ - (score / 100) * circ
  return (
    <div className="flex flex-col items-center">
      <svg width="72" height="72" viewBox="0 0 72 72">
        <circle cx="36" cy="36" r={r} fill="none" stroke="#1f2937" strokeWidth="6" />
        <circle cx="36" cy="36" r={r} fill="none" stroke={color} strokeWidth="6"
          strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round" transform="rotate(-90 36 36)" />
        <text x="36" y="40" textAnchor="middle" className="text-lg font-bold" fill="#e5e7eb" fontSize="18">{score}</text>
      </svg>
      <span className="text-xs text-gray-500 mt-1">{label}</span>
    </div>
  )
}

export function RiskPage() {
  const [selectedPortfolio, setSelectedPortfolio] = useState('')

  const { data: portfolios } = useQuery({ queryKey: ['portfolios'], queryFn: fetchPortfolios })

  const { data: risk, isLoading: riskLoading } = useQuery({
    queryKey: ['risk-summary', selectedPortfolio],
    queryFn: () => fetchRiskSummary(selectedPortfolio),
    enabled: !!selectedPortfolio,
  })

  const { data: advisor, isLoading: advLoading } = useQuery({
    queryKey: ['advisor', selectedPortfolio],
    queryFn: () => fetchAdvisorAnalysis(selectedPortfolio),
    enabled: !!selectedPortfolio,
  })

  const { data: stressTest } = useQuery({
    queryKey: ['stress-test', selectedPortfolio],
    queryFn: () => fetchStressTest(selectedPortfolio),
    enabled: !!selectedPortfolio,
  })

  const hasData = risk?.data_available

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Risk & Portfolio Advisor</h2>
          <p className="text-sm text-gray-500 mt-0.5">Institutional-grade risk analytics and AI portfolio insights</p>
        </div>
        <select value={selectedPortfolio} onChange={(e) => setSelectedPortfolio(e.target.value)}
          className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100">
          <option value="">Select a portfolio...</option>
          {(portfolios || []).map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
      </div>

      {!selectedPortfolio && <Card><p className="text-gray-500 text-sm">Select a portfolio above to view analytics.</p></Card>}

      {(riskLoading || advLoading) && <Spinner />}

      {/* Advisor Scores */}
      {advisor && (
        <div className="bg-gray-900/80 rounded-xl border border-gray-800 p-5">
          <div className="flex items-center gap-2 mb-4">
            <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Portfolio Health</h3>
            <Badge variant={advisor.portfolio_score >= 70 ? 'success' : advisor.portfolio_score >= 50 ? 'warning' : 'danger'}>
              {advisor.portfolio_score >= 70 ? 'Good' : advisor.portfolio_score >= 50 ? 'Fair' : 'Needs Attention'}
            </Badge>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <ScoreGauge score={advisor.portfolio_score} label="Portfolio Score" />
            <ScoreGauge score={advisor.diversification_score} label="Diversification" />
            <ScoreGauge score={advisor.risk_score} label="Risk Level" />
            <div className="flex flex-col items-center justify-center">
              <div className="text-2xl font-bold tabular-nums" style={{ color: advisor.market_beta != null ? (advisor.market_beta > 1.2 ? '#ef4444' : advisor.market_beta > 0.8 ? '#eab308' : '#22c55e') : '#9ca3af' }}>
                {advisor.market_beta != null ? advisor.market_beta.toFixed(2) : '—'}
              </div>
              <span className="text-xs text-gray-500">Beta</span>
            </div>
          </div>

          <p className="text-sm text-gray-300 leading-relaxed mb-4">{advisor.ai_summary}</p>

          {advisor.beginner_explanation && (
            <div className="bg-gray-800/30 rounded-lg p-3 mb-4">
              <p className="text-xs text-gray-500 mb-1">What this means</p>
              <p className="text-sm text-gray-400 leading-relaxed">{advisor.beginner_explanation}</p>
            </div>
          )}

          {/* Sector Exposure */}
          {advisor.sector_exposure.length > 0 && (
            <div className="mb-4">
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Sector Allocation</p>
              <div className="flex flex-wrap gap-1">
                {advisor.sector_exposure.map((s) => (
                  <span key={s.sector} className="inline-flex items-center gap-1 px-2 py-1 bg-gray-800 rounded text-xs">
                    <span className="text-gray-300">{s.sector}</span>
                    <span className="text-gray-500 font-medium">{s.weight}%</span>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Top Risks */}
          {advisor.top_risks.length > 0 && (
            <div className="mb-4">
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Top Risks</p>
              <div className="space-y-1">
                {advisor.top_risks.map((r, i) => (
                  <div key={i} className="flex items-start gap-2 text-sm">
                    <Badge variant={severityBadge(r.severity)}>{r.severity}</Badge>
                    <div><span className="text-gray-200 font-medium">{r.risk}</span><p className="text-xs text-gray-500">{r.detail}</p></div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Suggestions */}
          {advisor.suggestions.length > 0 && (
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Suggestions</p>
              <ul className="space-y-1">
                {advisor.suggestions.map((s, i) => (
                  <li key={i} className="text-sm text-gray-400 flex items-start gap-2 before:content-['•'] before:text-primary-400">{s}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Risk Metrics */}
      {hasData && advisor && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {advisor.risk_metrics.volatility_annualized != null && (
            <MetricCard label="Ann. Volatility" value={`${advisor.risk_metrics.volatility_annualized.toFixed(2)}%`} />
          )}
          {advisor.risk_metrics.sharpe_ratio != null && (
            <MetricCard label="Sharpe Ratio" value={advisor.risk_metrics.sharpe_ratio.toFixed(4)} />
          )}
          {advisor.risk_metrics.max_drawdown != null && (
            <MetricCard label="Max Drawdown" value={fmtPct(advisor.risk_metrics.max_drawdown)} />
          )}
          {advisor.risk_metrics.var_95 != null && (
            <MetricCard label="VaR 95%" value={fmtPct(advisor.risk_metrics.var_95)} />
          )}
        </div>
      )}

      {/* Correlation Analysis */}
      {advisor?.correlation_analysis?.available && advisor.correlation_analysis.pairs && (
        <Card title="Correlation Analysis">
          <div className="space-y-1">
            {advisor.correlation_analysis.pairs.map((p, i) => (
              <div key={i} className="flex items-center justify-between py-1 text-sm border-b border-gray-800/30 last:border-0">
                <span className="text-gray-300">{p.pair}</span>
                <span className={`tabular-nums font-medium ${Math.abs(p.correlation) > 0.7 ? 'text-yellow-400' : Math.abs(p.correlation) > 0.4 ? 'text-gray-300' : 'text-gain'}`}>
                  {p.correlation.toFixed(4)}
                </span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Top Contributors */}
      {advisor?.top_contributors && advisor.top_contributors.length > 0 && (
        <Card title="Performance Attribution">
          <div className="space-y-1">
            {advisor.top_contributors.map((c, i) => (
              <div key={i} className="flex items-center justify-between py-1 text-sm border-b border-gray-800/30 last:border-0">
                <span className="text-gray-300">{c.symbol} <span className="text-xs text-gray-600">({c.weight}% of portfolio)</span></span>
                <span className={c.pnl_pct >= 0 ? 'text-gain tabular-nums font-medium' : 'text-loss tabular-nums font-medium'}>{fmtPct(c.pnl_pct)}</span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Existing risk data */}
      {hasData && risk && (
        <>
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

          {/* Concentration */}
          {risk.concentration && !risk.concentration.error && (
            <Card title="Concentration">
              <div className="flex items-center gap-3 mb-4">
                <Badge variant={(risk.concentration.hhi ?? 0) > 2500 ? 'danger' : (risk.concentration.hhi ?? 0) > 1500 ? 'warning' : 'success'}>
                  {(risk.concentration.hhi ?? 0) > 2500 ? 'Highly Concentrated' : (risk.concentration.hhi ?? 0) > 1500 ? 'Moderate' : 'Well Diversified'}
                </Badge>
                <span className="text-xs text-gray-500">HHI: {risk.concentration.hhi}</span>
              </div>
              {risk.concentration.top_holdings && (
                <div className="mb-4">
                  <h4 className="text-xs text-gray-500 uppercase tracking-wider mb-2">Top Holdings</h4>
                  <div className="space-y-1">{risk.concentration.top_holdings.map((h: Record<string, unknown>) => (
                    <div key={String(h.symbol)} className="flex justify-between text-sm">
                      <span className="font-medium">{String(h.symbol)}</span>
                      <span className="tabular-nums text-gray-400">{Number(h.pct).toFixed(1)}%</span>
                    </div>
                  ))}</div>
                </div>
              )}
              {risk.concentration.sectors ? Object.entries(risk.concentration.sectors as Record<string, number>).sort(([, a], [, b]) => b - a).map(([sector, pct]) => (
                <div key={sector} className="flex justify-between text-sm"><span className="text-gray-300">{sector}</span><span className="tabular-nums text-gray-400">{pct.toFixed(1)}%</span></div>
              )) : <p className="text-xs text-gray-600">Not enough data available</p>}
            </Card>
          )}

          {/* Risk Narrative */}
          <Card title="Risk Narrative">
            <div className="space-y-2 text-sm text-gray-400">
              {risk.volatility?.annualized != null && <p><strong className="text-gray-200">Volatility:</strong> Annualized volatility of <strong>{risk.volatility.annualized.toFixed(1)}%</strong>. {risk.volatility.annualized > 40 ? 'High-risk typical of concentrated equity.' : risk.volatility.annualized > 25 ? 'Above-average risk.' : 'Moderate range, comparable to diversified equity.'}</p>}
              {risk.sharpe_ratio != null && <p><strong className="text-gray-200">Risk-Adjusted Return:</strong> Sharpe {risk.sharpe_ratio.toFixed(2)}. {risk.sharpe_ratio > 2 ? 'Excellent returns relative to risk.' : risk.sharpe_ratio > 1 ? 'Good — returns compensate well for risk.' : 'Moderate risk-adjusted returns.'}</p>}
              {risk.drawdown?.max_pct != null && <p><strong className="text-gray-200">Drawdown:</strong> Max peak-to-trough decline of <strong className="text-loss">{risk.drawdown.max_pct.toFixed(1)}%</strong>.{risk.drawdown.current_pct < -5 ? ` Currently ${risk.drawdown.current_pct.toFixed(1)}% below peak.` : ' Near peak value.'}</p>}
            </div>
          </Card>

          {/* Stress Test */}
          {stressTest && !stressTest.error && stressTest.scenarios && (
            <Card title="Stress Test Scenarios">
              <p className="text-xs text-gray-500 mb-3">Estimated portfolio impact under adverse market scenarios, based on historical betas and current holdings.</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {stressTest.scenarios.map((s) => (
                  <div key={s.scenario_id} className="bg-gray-800/40 rounded-lg p-3 border border-gray-800/50">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-200">{s.scenario_name}</span>
                      <span className={`text-sm font-bold tabular-nums ${s.impact_pct < 0 ? 'text-loss' : 'text-gain'}`}>
                        {s.impact_pct >= 0 ? '+' : ''}{s.impact_pct.toFixed(1)}%
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 mb-1.5">{s.description}</p>
                    <div className="flex items-center gap-3 text-[10px] text-gray-600">
                      <span>Market: {s.market_shock_pct}%</span>
                      <span>Vol: +{s.volatility_shock_pct}%</span>
                      <span>Impact: ${Math.abs(s.impact_value).toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                    </div>
                    {stressTest.worst_case && s.scenario_name === stressTest.worst_case.scenario && (
                      <span className="inline-block mt-1.5 text-[10px] text-yellow-500 font-medium">Worst Case</span>
                    )}
                  </div>
                ))}
              </div>
            </Card>
          )}
        </>
      )}

      {selectedPortfolio && !riskLoading && risk && !hasData && (
        <Card><p className="text-sm text-gray-400">{risk.error || 'Not enough historical data to compute risk metrics.'}</p></Card>
      )}
    </div>
  )
}
