import { useEffect, useRef } from 'react'
import { createChart, IChartApi, DeepPartial, ChartOptions } from 'lightweight-charts'
import { Spinner } from '../ui/Spinner'

const DARK_THEME: DeepPartial<ChartOptions> = {
  layout: {
    background: { color: '#111827' },
    textColor: '#9ca3af',
    fontSize: 11,
    fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
  },
  grid: {
    vertLines: { color: '#1f2937' },
    horzLines: { color: '#1f2937' },
  },
  crosshair: {
    mode: 1,
    vertLine: { color: '#6366f1', width: 1, style: 2, labelBackgroundColor: '#6366f1' },
    horzLine: { color: '#6366f1', width: 1, style: 2, labelBackgroundColor: '#6366f1' },
  },
  timeScale: {
    borderColor: '#374151',
    timeVisible: false,
    secondsVisible: false,
    tickMarkFormatter: (time: number) => {
      const date = new Date(time * 1000)
      return `${date.getMonth() + 1}/${date.getDate()}`
    },
  },
  rightPriceScale: {
    borderColor: '#374151',
    scaleMargins: { top: 0.05, bottom: 0.05 },
  },
}

interface ChartContainerProps {
  children: (chart: IChartApi, containerRef: React.RefObject<HTMLDivElement | null>) => void
  height?: number
  className?: string
  isLoading?: boolean
}

export function ChartContainer({ children, height = 400, className = '', isLoading }: ChartContainerProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)

  useEffect(() => {
    if (!containerRef.current) return
    const chart = createChart(containerRef.current, {
      ...DARK_THEME,
      width: containerRef.current.clientWidth,
      height,
    })
    chartRef.current = chart

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth })
      }
    }
    window.addEventListener('resize', handleResize)

    // Call the render function
    children(chart, containerRef)

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
      chartRef.current = null
    }
    // We intentionally only run this once on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [height])

  if (isLoading) {
    return (
      <div className={`bg-gray-900 rounded-xl border border-gray-800 flex items-center justify-center ${className}`} style={{ height }}>
        <Spinner />
      </div>
    )
  }

  return (
    <div className={`bg-gray-900 rounded-xl border border-gray-800 overflow-hidden ${className}`}>
      <div ref={containerRef} />
    </div>
  )
}
