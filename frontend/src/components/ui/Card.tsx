import { ReactNode } from 'react'
import clsx from 'clsx'
import { num } from '../../utils/formatters'

interface CardProps {
  children: ReactNode
  className?: string
  title?: string
}

export function Card({ children, className, title }: CardProps) {
  return (
    <div className={clsx('card', className)}>
      {title && <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">{title}</h3>}
      {children}
    </div>
  )
}

export function MetricCard({ label, value, change, changePct, className }: {
  label: string
  value: string
  change?: string
  changePct?: number
  className?: string
}) {
  const isPositive = changePct != null && changePct >= 0
  return (
    <Card className={clsx('flex flex-col', className)}>
      <span className="text-xs text-gray-500 uppercase tracking-wider">{label}</span>
      <span className="text-2xl font-bold mt-1">{value}</span>
      {change && (
        <span className={clsx('text-sm mt-1', isPositive ? 'text-gain' : 'text-loss')}>
          {change}
          {changePct != null && ` (${changePct >= 0 ? '+' : ''}${num(changePct).toFixed(2)}%)`}
        </span>
      )}
    </Card>
  )
}
