import client from './client'

export interface UpcomingEarnings {
  symbol: string
  company_name: string
  report_date: string
  timing: string
  eps_estimate: number | null
  revenue_estimate: number | null
  previous_eps: number | null
  market_cap: number | null
}

export interface EarningsHistory {
  fiscal_quarter?: number
  fiscal_year?: number
  eps_actual?: number
  eps_estimate?: number
  eps_surprise_pct?: number | null
  report_date?: string
}

export interface EarningsDetail {
  symbol: string
  company_name: string
  sector: string | null
  market_cap: number | null
  next_earnings_date: string | null
  eps_estimate: number | null
  revenue_estimate: number | null
  price: number | null
  pe_ratio: number | null
  forward_pe: number | null
  dividend_yield: number | null
  history: EarningsHistory[]
  error?: string
}

export interface NewsItem {
  title: string | null
  publisher: string | null
  link: string | null
  published: string | null
  summary: string | null
  type: string | null
}

export async function fetchUpcomingEarnings(symbols?: string, daysAhead?: number): Promise<UpcomingEarnings[]> {
  const { data } = await client.get('/earnings/upcoming', {
    params: { symbols, days_ahead: daysAhead },
  })
  return data
}

export async function fetchEarningsDetail(symbol: string): Promise<EarningsDetail> {
  const { data } = await client.get(`/earnings/${symbol}`)
  return data
}

export interface EarningsAnalysis {
  symbol: string
  overall_signal: 'bullish' | 'bearish' | 'neutral' | 'mixed' | 'high_risk'
  confidence: number
  summary: string
  ai_summary?: string | null
  beginner_explanation: string
  bullish_factors: string[]
  bearish_factors: string[]
  risk_factors: string[]
  key_signals: Record<string, string>
}

export async function fetchEarningsNews(symbol: string): Promise<NewsItem[]> {
  const { data } = await client.get(`/earnings/${symbol}/news`)
  return data
}

export async function fetchEarningsAnalysis(symbol: string): Promise<EarningsAnalysis> {
  const { data } = await client.get(`/earnings/${symbol}/analysis`)
  return data
}
