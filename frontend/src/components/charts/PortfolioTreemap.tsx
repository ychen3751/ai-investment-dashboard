/** Lightweight SVG treemap — no extra dependencies.
 *
 * Each block size represents allocation %, and color represents P&L.
 * Uses a simple squarified tiling algorithm.
 */
import { useState, useMemo } from 'react'
import { num } from '../../utils/formatters'

interface TreemapItem {
  symbol: string
  value: number        // allocation % (determines block size)
  pnlPct: number       // total P&L % (determines color)
  dayPct?: number      // daily change
  marketValue?: number
}

interface TreemapTile {
  symbol: string
  x: number
  y: number
  w: number
  h: number
  value: number
  pnlPct: number
  dayPct?: number
  marketValue?: number
}

interface PortfolioTreemapProps {
  data: TreemapItem[]
  width?: number
  height?: number
  onSelect?: (symbol: string) => void
}

function pnlColor(pct: number): string {
  if (pct > 50) return '#15803d'   // dark green — very strong
  if (pct > 20) return '#16a34a'   // green — strong
  if (pct > 5) return '#22c55e'    // light green — gains
  if (pct > 0) return '#4ade80'    // lighter green — small gains
  if (pct > -5) return '#f87171'   // light red — small loss
  if (pct > -20) return '#ef4444'  // red — loss
  return '#b91c1c'                 // dark red — heavy loss
}

function squarify(items: TreemapItem[], w: number, h: number): TreemapTile[] {
  // Simple recursive layout: sort descending, lay out in rows
  const sorted = [...items].sort((a, b) => b.value - a.value)
  const tiles: TreemapTile[] = []
  const total = sorted.reduce((s, i) => s + i.value, 0) || 1

  let x = 0, y = 0
  const rowH = h / 2
  const firstHalf = sorted.filter((_, i) => i < sorted.length / 2)
  const secondHalf = sorted.filter((_, i) => i >= sorted.length / 2)

  const layoutRow = (row: TreemapItem[], rowY: number, rowH: number) => {
    const rowTotal = row.reduce((s, i) => s + i.value, 0) || 1
    let rowX = 0
    for (const item of row) {
      const colW = (item.value / rowTotal) * w
      tiles.push({
        symbol: item.symbol,
        x: rowX, y: rowY, w: colW, h: rowH,
        value: item.value,
        pnlPct: item.pnlPct,
        dayPct: item.dayPct,
        marketValue: item.marketValue,
      })
      rowX += colW
    }
  }

  layoutRow(firstHalf, 0, h / 2)
  layoutRow(secondHalf, h / 2, h / 2)

  return tiles
}

export function PortfolioTreemap({ data, width = 600, height = 360, onSelect }: PortfolioTreemapProps) {
  const [hovered, setHovered] = useState<string | null>(null)
  const [tooltip, setTooltip] = useState<{ x: number; y: number; item: TreemapItem } | null>(null)

  const tiles = useMemo(() => squarify(data, width, height), [data, width, height])

  if (data.length === 0) {
    return (
      <div className="bg-gray-900 rounded-xl border border-gray-800 flex items-center justify-center" style={{ width, height }}>
        <p className="text-sm text-gray-600">No holdings to display</p>
      </div>
    )
  }

  return (
    <div className="relative bg-gray-900 rounded-xl border border-gray-800 overflow-hidden" style={{ width, height }}>
      <svg width={width} height={height} className="block">
        {tiles.map((tile) => {
          const isHovered = hovered === tile.symbol
          const color = pnlColor(tile.pnlPct)
          const labelSize = Math.max(9, Math.min(14, tile.w / 6))
          const showLabel = tile.w > 40 && tile.h > 20
          const showPct = tile.w > 60 && tile.h > 30

          return (
            <g key={tile.symbol}
              onMouseEnter={() => setHovered(tile.symbol)}
              onMouseLeave={() => setHovered(null)}
              onClick={() => onSelect?.(tile.symbol)}
              className="cursor-pointer"
            >
              <rect
                x={tile.x + 1} y={tile.y + 1}
                width={tile.w - 2} height={tile.h - 2}
                rx={4}
                fill={isHovered ? '#374151' : color}
                opacity={isHovered ? 0.9 : 0.75}
                stroke={isHovered ? '#6366f1' : '#1f2937'}
                strokeWidth={isHovered ? 2 : 1}
                style={{ transition: 'all 0.15s ease' }}
              />
              {showLabel && (
                <text
                  x={tile.x + tile.w / 2}
                  y={tile.y + tile.h / 2 - (showPct ? 6 : 0)}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fill="#f3f4f6"
                  fontSize={labelSize}
                  fontWeight={600}
                  fontFamily="system-ui"
                >
                  {tile.symbol}
                </text>
              )}
              {showPct && (
                <text
                  x={tile.x + tile.w / 2}
                  y={tile.y + tile.h / 2 + 12}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fill="#d1d5db"
                  fontSize={labelSize - 2}
                  fontFamily="system-ui"
                  fontWeight={400}
                >
                  {tile.pnlPct >= 0 ? '+' : ''}{tile.pnlPct.toFixed(1)}%
                </text>
              )}
              {showLabel && (
                <text
                  x={tile.x + tile.w / 2}
                  y={tile.y + tile.h - 6}
                  textAnchor="middle"
                  fill="#9ca3af"
                  fontSize={labelSize - 3}
                  fontFamily="system-ui"
                >
                  {tile.value.toFixed(1)}%
                </text>
              )}
            </g>
          )
        })}
      </svg>

      {/* Tooltip */}
      {tooltip && (
        <div
          className="absolute z-10 bg-gray-900 border border-gray-700 rounded-lg p-3 shadow-xl pointer-events-none"
          style={{ left: Math.min(tooltip.x, width - 200), top: Math.min(tooltip.y - 80, height - 120) }}
        >
          <p className="text-sm font-semibold text-gray-100">{tooltip.item.symbol}</p>
          <div className="text-xs text-gray-400 mt-1 space-y-0.5">
            <p>Allocation: {tooltip.item.value.toFixed(1)}%</p>
            {tooltip.item.dayPct != null && <p>Day: <span className={tooltip.item.dayPct >= 0 ? 'text-gain' : 'text-loss'}>{tooltip.item.dayPct >= 0 ? '+' : ''}{tooltip.item.dayPct.toFixed(2)}%</span></p>}
            <p>Total Return: <span className={tooltip.item.pnlPct >= 0 ? 'text-gain' : 'text-loss'}>{tooltip.item.pnlPct >= 0 ? '+' : ''}{tooltip.item.pnlPct.toFixed(2)}%</span></p>
            {tooltip.item.marketValue != null && <p>Value: ${num(tooltip.item.marketValue).toLocaleString(undefined, { maximumFractionDigits: 0 })}</p>}
          </div>
        </div>
      )}
    </div>
  )
}
