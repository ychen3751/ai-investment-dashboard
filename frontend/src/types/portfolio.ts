import { OHLCV } from './common'

export interface Portfolio {
  id: string
  name: string
  description: string | null
  created_at: string
  updated_at: string
  total_value?: number
  total_cost?: number
  total_pnl?: number
  total_pnl_pct?: number
  holding_count: number
}

export interface PortfolioCreate {
  name: string
  description?: string
}

export interface Holding {
  id: string
  symbol: string
  quantity: number
  average_cost_basis: number
  current_price: number | null
  day_change: number | null
  day_change_pct: number | null
  market_value: number | null
  total_cost: number | null
  total_pnl: number | null
  total_pnl_pct: number | null
  allocation_pct: number | null
}

export interface HoldingCreate {
  symbol: string
  quantity: number
  average_cost_basis: number
}

export interface Transaction {
  id: string
  symbol: string
  transaction_type: 'BUY' | 'SELL'
  quantity: number
  price: number
  commission: number
  transaction_date: string
  notes: string | null
  created_at: string
}

export interface TransactionCreate {
  symbol: string
  transaction_type: 'BUY' | 'SELL'
  quantity: number
  price: number
  commission?: number
  transaction_date: string
  notes?: string
}

export interface Performance {
  total_return_pct: number | null
  annualized_return_pct: number | null
  volatility_pct: number | null
  sharpe_ratio: number | null
  max_drawdown_pct: number | null
  total_value: number | null
  total_cost: number | null
  total_pnl: number | null
}
