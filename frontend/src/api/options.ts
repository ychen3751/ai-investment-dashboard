import client from './client'

export interface FlowAnalysis {
  symbol: string
  timestamp: string
  overall_signal: 'bullish' | 'bearish' | 'neutral' | 'mixed'
  confidence: number
  summary: string
  ai_summary?: string | null
  bullish_factors: string[]
  bearish_factors: string[]
  risk_factors: string[]
  key_metrics: {
    call_volume: number
    put_volume: number
    call_put_volume_ratio: number
    call_premium: number
    put_premium: number
    call_put_premium_ratio: number
    unusual_count: number
    unusual_volume: number
    avg_implied_volatility: number | null
    max_implied_volatility: number | null
    near_term_premium_pct: number
    atm_premium_pct: number
    total_premium: number
    total_contracts: number
  }
  top_unusual_contracts: Array<{
    option_type: string
    strike: number
    volume: number
    premium: number
    volume_oi_ratio: number
    unusual_score: number
    signal: string
  }>
}

export async function fetchFlowAnalysis(symbol: string): Promise<FlowAnalysis> {
  const { data } = await client.get('/options/flow/analysis', { params: { symbol } })
  return data
}

export interface OptionContract {
  strike: number
  expiration: string
  last_price: number
  bid: number
  ask: number
  volume: number
  open_interest: number
  volume_oi_ratio: number
  implied_volatility: number
  premium: number
  unusual_score: number
  signal: string
  option_type: 'call' | 'put'
}

export interface OptionChainResponse {
  symbol: string
  expiration: string
  underlying_price: number
  contracts: OptionContract[]
  total_contracts: number
}

export async function fetchExpirations(symbol: string): Promise<string[]> {
  const { data } = await client.get('/options/expirations', { params: { symbol } })
  return data
}

export async function fetchOptionChain(
  symbol: string,
  params?: {
    expiration?: string
    min_premium?: number
    option_type?: 'call' | 'put'
    unusual_only?: boolean
  },
): Promise<OptionChainResponse> {
  const { data } = await client.get('/options/chain', {
    params: { symbol, ...params },
  })
  return data
}
