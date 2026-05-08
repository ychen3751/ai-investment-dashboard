export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
}

export interface ApiError {
  detail: string
}

export interface PriceTick {
  symbol: string
  price: number
  change: number
  change_pct: number
  volume: number
  timestamp: string
}

export interface OHLCV {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}
