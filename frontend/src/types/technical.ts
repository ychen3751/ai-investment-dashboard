import { OHLCV } from './common'

export interface TechnicalAnalysis {
  symbol: string
  dates: string[]
  prices: number[]
  ohlcv: OHLCV[]
  sma_20: (number | null)[]
  sma_50: (number | null)[]
  ema_12: (number | null)[]
  ema_26: (number | null)[]
  rsi_14: (number | null)[]
  macd: {
    macd: (number | null)[]
    signal: (number | null)[]
    histogram: (number | null)[]
  }
  bollinger: {
    upper: (number | null)[]
    middle: (number | null)[]
    lower: (number | null)[]
  }
  volume: {
    volume: number[]
    avg_volume: number | null
    volume_ratio: number | null
  }
  signals: TechnicalSignal[]
}

export interface TechnicalSignal {
  indicator: string
  signal: 'bullish' | 'bearish' | 'neutral'
  message: string
}
