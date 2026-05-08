import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Spinner } from '../components/ui/Spinner'
import { Badge } from '../components/ui/Badge'
import { SymbolSearch } from '../components/shared/SymbolSearch'
import { fetchFundamentalAnalysis } from '../api/analysis'
import { num } from '../utils/formatters'

function ScoreGauge({ score }: { score: number }) {
  const color = score >= 65 ? '#22c55e' : score >= 40 ? '#eab308' : '#ef4444'
  const r = 36
  const circ = 2 * Math.PI * r
  const offset = circ - (score / 100) * circ
  return (
    <div className="flex flex-col items-center">
      <svg width="96" height="96" viewBox="0 0 96 96">
        <circle cx="48" cy="48" r={r} fill="none" stroke="#1f2937" strokeWidth="8" />
        <circle cx="48" cy="48" r={r} fill="none" stroke={color} strokeWidth="8"
          strokeDasharray={circ} strokeDashoffset={offset}
          strokeLinecap="round" transform="rotate(-90 48 48)" />
        <text x="48" y="52" textAnchor="middle" className="text-lg font-bold" fill="#e5e7eb" fontSize="20">{score}</text>
      </svg>
      <span className="text-sm font-medium mt-1" style={{ color }}>{score >= 65 ? 'Bullish' : score >= 40 ? 'Neutral' : 'Bearish'}</span>
    </div>
  )
}

function SectionCard({ title, factors, score }: { title: string; factors?: string[]; score?: number }) {
  if (!factors || factors.length === 0) return null
  const color = score != null ? (score >= 60 ? 'text-gain' : score >= 40 ? 'text-yellow-400' : 'text-loss') : 'text-gray-300'
  return (
    <Card>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold text-gray-300">{title}</h3>
        {score != null && <span className={`text-xl font-bold ${color}`}>{score}</span>}
      </div>
      <ul className="space-y-1">
        {factors.map((f, i) => (
          <li key={i} className="text-xs text-gray-500 flex items-start gap-2 before:content-['•'] before:text-gray-600">{f}</li>
        ))}
      </ul>
    </Card>
  )
}

function fmtMarketCap(n: number | null | undefined) {
  const v = num(n)
  if (!v) return '-'
  if (Math.abs(v) >= 1e12) return `$${(v / 1e12).toFixed(2)}T`
  if (Math.abs(v) >= 1e9) return `$${(v / 1e9).toFixed(2)}B`
  return `$${v.toFixed(2)}`
}

export function AnalysisPage() {
  const [symbol, setSymbol] = useState('')

  const { data, isLoading, error } = useQuery({
    queryKey: ['analysis', symbol],
    queryFn: () => fetchFundamentalAnalysis(symbol),
    enabled: !!symbol,
  })

  const analysis = data?.analysis
  const verdict = analysis?.overall_assessment || 'neutral'
  const verdictColor = verdict === 'bullish' ? 'success' : verdict === 'bearish' ? 'danger' : 'default'
  const score = analysis?.confidence_score ?? 0

  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-2xl font-bold">AI Stock Analysis</h2>

      <div className="max-w-xs">
        <SymbolSearch onSelect={(sym) => setSymbol(sym)} placeholder="Search ticker..." />
      </div>

      {!symbol && <Card><p className="text-gray-500 text-sm">Search a ticker to view analysis.</p></Card>}

      {isLoading && <Spinner />}
      {error && <Card><p className="text-red-400 text-sm">Failed to load analysis. Symbol may not exist.</p></Card>}

      {analysis && (
        <>
          <Card>
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-lg font-bold">{symbol.toUpperCase()}</h3>
                  <Badge variant={verdictColor}>{verdict.toUpperCase()}</Badge>
                  {analysis.source && <span className="text-xs text-gray-600">via {analysis.source}</span>}
                </div>
                <p className="text-sm text-gray-400">{analysis.company_summary}</p>
              </div>
              <ScoreGauge score={score} />
            </div>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <SectionCard title="Valuation" factors={analysis.valuation?.factors} score={analysis.valuation?.score} />
            <SectionCard title="Trend" factors={analysis.trend?.factors} score={analysis.trend?.score} />
            <SectionCard title="Risk" factors={analysis.risk?.factors} score={analysis.risk?.score} />
          </div>

          <Card title="Key Metrics">
            {analysis.key_metrics ? (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {Object.entries(analysis.key_metrics).map(([key, val]) => (
                  <div key={key}>
                    <div className="text-xs text-gray-500 capitalize">{key.replace(/_/g, ' ')}</div>
                    <div className="text-sm font-medium">{val != null ? (typeof val === 'number' ? (key.includes('yield') || key.includes('margin') || key.includes('growth') ? `${num(val * 100).toFixed(2)}%` : val.toLocaleString()) : String(val)) : '-'}</div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-sm">No key metrics available.</p>
            )}
          </Card>

          {analysis.strengths && analysis.strengths.length > 0 && (
            <Card title="Strengths">
              <ul className="space-y-1">
                {analysis.strengths.map((s, i) => (
                  <li key={i} className="text-sm text-gain flex items-start gap-2 before:content-['+'] before:text-gain before:font-bold">{s}</li>
                ))}
              </ul>
            </Card>
          )}

          {analysis.weaknesses && analysis.weaknesses.length > 0 && (
            <Card title="Weaknesses / Risks">
              <ul className="space-y-1">
                {analysis.weaknesses.map((w, i) => (
                  <li key={i} className="text-sm text-loss flex items-start gap-2 before:content-['−'] before:text-loss before:font-bold">{w}</li>
                ))}
              </ul>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
