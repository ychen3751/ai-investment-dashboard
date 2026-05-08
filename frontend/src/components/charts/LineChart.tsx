import { LineSeries, LineData } from 'lightweight-charts'
import { ChartContainer } from './ChartContainer'
import { num } from '../../utils/formatters'

interface LineChartSeries {
  data: (number | null)[]
  color: string
  label?: string
  lineStyle?: 0 | 1 | 2 | 3 | 4
}

interface LineChartProps {
  series: LineChartSeries[]
  height?: number
  isLoading?: boolean
  className?: string
  dates?: string[]
}

function toUnix(dateStr: string): number {
  return Math.floor(new Date(dateStr).getTime() / 1000)
}

export function LineChart({ series, height = 200, isLoading, className, dates = [] }: LineChartProps) {
  const hasData = series.some((s) => s.data.some((v) => v !== null && v !== undefined))

  return (
    <ChartContainer isLoading={isLoading} height={height} className={className}>
      {(chart) => {
        if (!hasData) return

        series.forEach((s) => {
          const lineSeries = chart.addSeries(LineSeries, {
            color: s.color,
            lineWidth: 2,
            priceLineVisible: false,
            lastValueVisible: true,
            title: s.label,
            lineStyle: s.lineStyle ?? 0,
          })
          const lineData: LineData[] = s.data
            .map((v, i) => ({
              time: dates[i] ? (toUnix(dates[i]) as any) : (i as any),
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
