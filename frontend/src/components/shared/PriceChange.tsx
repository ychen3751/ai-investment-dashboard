import clsx from 'clsx'
import { num } from '../../utils/formatters'

export function PriceChange({ value, pct }: { value: number; pct: number }) {
  const isPositive = pct >= 0
  return (
    <span className={clsx('font-medium', isPositive ? 'text-gain' : 'text-loss')}>
      {isPositive ? '+' : ''}{num(value).toFixed(2)} ({isPositive ? '+' : ''}{num(pct).toFixed(2)}%)
    </span>
  )
}
