/**
 * Safely convert a value to a number. Returns `fallback` (default 0) for
 * null, undefined, NaN, Infinity, or non-coercible values.
 */
export function num(value: unknown, fallback = 0): number {
  if (typeof value === 'number' && Number.isFinite(value)) return value
  const n = Number(value)
  return Number.isFinite(n) ? n : fallback
}

/** Format a percentage value with sign and fixed decimals. */
export function fmtPct(value: unknown, decimals = 2): string {
  const n = num(value)
  const sign = n >= 0 ? '+' : ''
  return `${sign}${n.toFixed(decimals)}%`
}

/** Format a number as USD currency. */
export function fmtCurrency(value: unknown, fallback = '-'): string {
  const n = num(value)
  if (n === 0 && value !== 0 && value != null) return fallback
  if (Math.abs(n) >= 1e12) return `$${(n / 1e12).toFixed(2)}T`
  if (Math.abs(n) >= 1e9) return `$${(n / 1e9).toFixed(2)}B`
  if (Math.abs(n) >= 1e6) return `$${(n / 1e6).toFixed(2)}M`
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2 }).format(n)
}
