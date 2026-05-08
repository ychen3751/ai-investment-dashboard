import { useRef } from 'react'
import { IChartApi, CandlestickSeries, HistogramSeries, LineSeries, CandlestickData, HistogramData, LineData } from 'lightweight-charts'
import { ChartContainer } from './ChartContainer'
import { num } from '../../utils/formatters'

interface OHLCVData {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

interface OverlayLine {
  data: (number | null)[]
  color: string
  label: string
  lineStyle?: 0 | 1 | 2 | 3 | 4
}

interface CandlestickChartProps {
  data: OHLCVData[]
  overlays?: OverlayLine[]
  height?: number
  isLoading?: boolean
  className?: string
}

function toUnix(dateStr: string): number {
  return Math.floor(new Date(dateStr).getTime() / 1000)
}

export function CandlestickChart({ data, overlays, height, isLoading, className }: CandlestickChartProps) {
  const chartRef = useRef<IChartApi | null>(null)

  return (
    <ChartContainer isLoading={isLoading} height={height} className={className}>
      {(chart) => {
        chartRef.current = chart

        // Candlestick series
        const candleSeries = chart.addSeries(CandlestickSeries, {
          upColor: '#22c55e',
          downColor: '#ef4444',
          borderDownColor: '#ef4444',
          borderUpColor: '#22c55e',
          wickDownColor: '#ef4444',
          wickUpColor: '#22c55e',
        })

        if (data.length > 0) {
          const candleData: CandlestickData[] = data.map((d) => ({
            time: toUnix(d.date) as any,
            open: num(d.open),
            high: num(d.high),
            low: num(d.low),
            close: num(d.close),
          }))
          candleSeries.setData(candleData)
        }

        // Volume histogram
        const volumeSeries = chart.addSeries(HistogramSeries, {
          priceFormat: { type: 'volume' },
          priceScaleId: 'volume',
          color: '#22c55e33',
        })
        chart.priceScale('volume').applyOptions({
          scaleMargins: { top: 0.8, bottom: 0 },
        })

        if (data.length > 0) {
          const volumeData: HistogramData[] = data.map((d) => ({
            time: toUnix(d.date) as any,
            value: num(d.volume),
            color: d.close >= d.open ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)',
          }))
          volumeSeries.setData(volumeData)
        }

        // Overlay lines
        overlays?.forEach((overlay) => {
          const lineSeries = chart.addSeries(LineSeries, {
            color: overlay.color,
            lineWidth: 1,
            priceLineVisible: false,
            lastValueVisible: true,
            title: overlay.label,
            lineStyle: overlay.lineStyle ?? 0,
          })
          const lineData: LineData[] = overlay.data
            .map((v, i) => ({
              time: data[i] ? (toUnix(data[i].date) as any) : (i as any),
              value: num(v),
            }))
            .filter((d) => d.value > 0 || d.value === 0)
          if (lineData.length > 0) {
            lineSeries.setData(lineData)
          }
        })

        chart.timeScale().fitContent()
      }}
    </ChartContainer>
  )
}
