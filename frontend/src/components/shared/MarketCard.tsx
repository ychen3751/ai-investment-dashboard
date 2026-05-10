import { num, fmtCurrency } from '../../utils/formatters'

interface MarketCardProps {
  symbol: string
  name: string
  price: number | null
  change: number | null
  changePct: number | null
  sparkline?: number[]
}

function Sparkline({ data, color }: { data: number[]; color: string }) {
  if (data.length < 2) return null
  const min = Math.min(...data)
  const max = Math.max(...data)
  const range = max - min || 1
  const w = 80
  const h = 28
  const pts = data.map((v, i) => `${((i / (data.length - 1)) * w).toFixed(1)},${(h - ((v - min) / range) * h).toFixed(1)}`).join(' ')
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} className="flex-shrink-0">
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function MarketCard({ symbol, name, price, change, changePct, sparkline }: MarketCardProps) {
  const isPositive = (change ?? 0) >= 0
  const color = isPositive ? '#22c55e' : '#ef4444'

  return (
    <div className="card-interactive group relative overflow-hidden">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-gray-100">{symbol.replace('^', '')}</span>
            <span className="text-[10px] text-gray-600 truncate max-w-[100px]">{name}</span>
          </div>
          <div className="mt-1.5 flex items-baseline gap-2">
            <span className="text-xl font-bold tabular-nums text-gray-50">
              {price != null
                ? (price >= 1000 ? price.toLocaleString(undefined, { minimumFractionDigits: 2 }) : price.toFixed(2))
                : '-'}
            </span>
          </div>
          <div className="flex items-center gap-1.5 mt-0.5">
            <span className={`text-xs font-medium tabular-nums ${isPositive ? 'text-gain' : 'text-loss'}`}>
              {isPositive ? '+' : ''}{change != null ? change.toFixed(2) : '0.00'}
            </span>
            <span className={`text-xs tabular-nums ${isPositive ? 'text-gain' : 'text-loss'}`}>
              ({isPositive ? '+' : ''}{(changePct ?? 0).toFixed(2)}%)
            </span>
          </div>
        </div>
        <div className="opacity-60 group-hover:opacity-100 transition-opacity">
          <Sparkline data={sparkline || []} color={color} />
        </div>
      </div>
    </div>
  )
}
