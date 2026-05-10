import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'
import { Badge } from '../ui/Badge'
import { recommendStrategy } from '../../api/strategy'
import type { StrategyRecommendation } from '../../api/strategy'

function riskBadge(level: string) {
  if (level === 'low') return 'success' as const
  if (level === 'moderate') return 'warning' as const
  return 'danger' as const
}

function biasColor(bias: string) {
  if (bias.includes('bullish')) return 'text-gain'
  if (bias.includes('bearish')) return 'text-loss'
  return 'text-yellow-400'
}

export function StrategyBuilder() {
  const [bias, setBias] = useState('bullish')
  const [volatility, setVolatility] = useState('moderate')
  const [riskTolerance, setRiskTolerance] = useState('moderate')
  const [capital, setCapital] = useState('1000')
  const [horizon, setHorizon] = useState('medium')
  const [result, setResult] = useState<StrategyRecommendation | null>(null)

  const mutation = useMutation({
    mutationFn: () =>
      recommendStrategy({
        bias,
        volatility,
        risk_tolerance: riskTolerance,
        capital: parseFloat(capital) || 1000,
        time_horizon: horizon,
      }),
    onSuccess: (data) => setResult(data),
  })

  return (
    <div>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 mb-4">
        <div>
          <label className="text-xs text-gray-500 mb-1 block">Outlook</label>
          <select value={bias} onChange={(e) => setBias(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-2 py-2 text-sm text-gray-100">
            <option value="bullish">Bullish ↑</option>
            <option value="bearish">Bearish ↓</option>
            <option value="neutral">Neutral →</option>
          </select>
        </div>
        <div>
          <label className="text-xs text-gray-500 mb-1 block">Volatility</label>
          <select value={volatility} onChange={(e) => setVolatility(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-2 py-2 text-sm text-gray-100">
            <option value="low">Low</option>
            <option value="moderate">Moderate</option>
            <option value="high">High</option>
          </select>
        </div>
        <div>
          <label className="text-xs text-gray-500 mb-1 block">Risk</label>
          <select value={riskTolerance} onChange={(e) => setRiskTolerance(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-2 py-2 text-sm text-gray-100">
            <option value="low">Conservative</option>
            <option value="moderate">Moderate</option>
            <option value="high">Aggressive</option>
          </select>
        </div>
        <div>
          <label className="text-xs text-gray-500 mb-1 block">Capital ($)</label>
          <Input type="number" value={capital} onChange={(e) => setCapital(e.target.value)} min="100" />
        </div>
        <div>
          <label className="text-xs text-gray-500 mb-1 block">Timeframe</label>
          <select value={horizon} onChange={(e) => setHorizon(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-2 py-2 text-sm text-gray-100">
            <option value="short">Short (days)</option>
            <option value="medium">Medium (weeks)</option>
            <option value="long">Long (months)</option>
          </select>
        </div>
      </div>

      <Button onClick={() => mutation.mutate()} disabled={mutation.isPending} className="w-full">
        {mutation.isPending ? 'Analyzing...' : 'Recommend Strategy'}
      </Button>

      {result && (
        <div className="mt-4 bg-gray-800/40 rounded-lg p-4 border border-gray-700/50">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h4 className="text-lg font-semibold text-gray-100">{result.strategy}</h4>
              <div className="flex items-center gap-2 mt-1">
                <Badge variant={riskBadge(result.risk_level)}>{result.risk_level.toUpperCase()}</Badge>
                <span className={`text-sm font-medium ${biasColor(result.bias)}`}>
                  {result.bias.replace('_', ' ').toUpperCase()}
                </span>
              </div>
            </div>
          </div>

          <p className="text-sm text-gray-300 leading-relaxed mb-4">{result.ai_explanation || result.description}</p>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <div className="bg-gray-800/40 rounded-lg p-2.5"><div className="text-[10px] text-gray-500 uppercase">Max Profit</div><div className="text-xs text-gain mt-0.5">{result.max_profit}</div></div>
            <div className="bg-gray-800/40 rounded-lg p-2.5"><div className="text-[10px] text-gray-500 uppercase">Max Loss</div><div className="text-xs text-loss mt-0.5">{result.max_loss}</div></div>
            <div className="bg-gray-800/40 rounded-lg p-2.5"><div className="text-[10px] text-gray-500 uppercase">Breakeven</div><div className="text-xs text-gray-300 mt-0.5">{result.breakeven}</div></div>
            <div className="bg-gray-800/40 rounded-lg p-2.5"><div className="text-[10px] text-gray-500 uppercase">Capital</div><div className="text-xs text-gray-300 mt-0.5">{result.capital_required}</div></div>
          </div>
        </div>
      )}
    </div>
  )
}
