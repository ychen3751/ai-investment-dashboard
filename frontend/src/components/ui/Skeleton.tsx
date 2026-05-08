import clsx from 'clsx'

interface SkeletonProps {
  className?: string
  /** Number of skeleton lines to render (for text blocks) */
  lines?: number
  /** Width of each line — single value or array per line */
  widths?: string | string[]
  height?: string
}

export function Skeleton({ className, lines = 1, widths = '100%', height = '1rem' }: SkeletonProps) {
  const widthsArr = Array.isArray(widths) ? widths : Array(lines).fill(widths)

  if (lines === 1) {
    return (
      <div
        className={clsx('bg-gray-800 rounded animate-pulse', className)}
        style={{ width: widthsArr[0], height }}
      />
    )
  }

  return (
    <div className={clsx('flex flex-col gap-2', className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="bg-gray-800 rounded animate-pulse"
          style={{ width: widthsArr[Math.min(i, widthsArr.length - 1)], height }}
        />
      ))}
    </div>
  )
}

export function ChartSkeleton({ height = 400 }: { height?: number }) {
  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden animate-pulse" style={{ height }}>
      <div className="flex items-end gap-1 p-4 h-full" style={{ paddingBottom: '30%' }}>
        {Array.from({ length: 40 }).map((_, i) => (
          <div
            key={i}
            className="flex-1 bg-gray-800 rounded-t"
            style={{ height: `${20 + Math.random() * 60}%` }}
          />
        ))}
      </div>
    </div>
  )
}

export function MetricCardSkeleton() {
  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-4 animate-pulse">
      <Skeleton widths="40%" height="0.75rem" className="mb-2" />
      <Skeleton widths="60%" height="1.5rem" className="mb-1" />
      <Skeleton widths="30%" height="0.75rem" />
    </div>
  )
}
